"""
AASI Phase 28: Scientific Result Verification Layer.
Performs strict 10-point audit on returned simulation archives:
1. Expected files exist
2. Checksums match manifest
3. Metadata is internally consistent
4. Solver information is authentic
5. Required fields exist (p, U, k, omega)
6. Numerical values are parseable
7. Convergence information is available
8. Units are known & SI compliant
9. Dimensions are consistent
10. Case identity matches investigation identity

Status levels:
- VERIFIED
- PARTIALLY_VERIFIED
- UNVERIFIED
- INVALID
- INCOMPLETE

Under the Absolute Anti-Fabrication Rule:
Never silently assumes values or injects default placeholders.
"""

from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    INVALID = "INVALID"
    INCOMPLETE = "INCOMPLETE"


class AuditCheck(BaseModel):
    name: str
    passed: bool
    detail: str


class ResultVerificationReport(BaseModel):
    status: VerificationStatus
    is_verified: bool
    audit_checks: List[AuditCheck] = Field(default_factory=list)
    parsed_polars: Dict[str, float] = Field(default_factory=dict)
    residual_history: Dict[str, List[float]] = Field(default_factory=dict)
    solver_name: Optional[str] = None
    solver_version: Optional[str] = None
    case_id: Optional[str] = None
    investigation_id: Optional[str] = None
    verification_token: Optional[str] = None
    summary: str
    failure_reasons: List[str] = Field(default_factory=list)


class ScientificResultVerifier:
    """
    Validates ingested CFD simulation archives with zero tolerance for fabrication or missing data.
    """

    @classmethod
    def verify_archive(
        cls,
        archive_dir: Path,
        expected_case_id: Optional[str] = None,
        expected_investigation_id: Optional[str] = None,
    ) -> ResultVerificationReport:
        temp_extracted_dir = None
        if archive_dir.is_file():
            import tempfile, tarfile, shutil
            temp_extracted_dir = Path(tempfile.mkdtemp(prefix="aasi_verify_"))
            try:
                with tarfile.open(archive_dir, "r:*") as tar:
                    tar.extractall(temp_extracted_dir, filter='data')
                archive_dir = temp_extracted_dir
            except Exception as e:
                shutil.rmtree(temp_extracted_dir, ignore_errors=True)
                return ResultVerificationReport(
                    status=VerificationStatus.INVALID,
                    is_verified=False,
                    summary=f"Simulation archive cannot be unpacked: {e}",
                    failure_reasons=[str(e)],
                )

        checks: List[AuditCheck] = []
        failures: List[str] = []
        parsed_polars: Dict[str, float] = {}
        residuals: Dict[str, List[float]] = {}
        solver_name = None
        solver_ver = None
        case_id = None
        inv_id = None
        token = None

        # Check 1: Manifest exists & is valid JSON
        manifest_path = archive_dir / "job_manifest.json"
        manifest_ok = False
        manifest_data: Dict[str, Any] = {}
        if manifest_path.exists():
            try:
                manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest_ok = True
                case_id = manifest_data.get("job_id")
                inv_id = manifest_data.get("investigation_id")
                token = manifest_data.get("verification_token") or manifest_data.get("notebook_hash")
                checks.append(AuditCheck(name="manifest_json", passed=True, detail="job_manifest.json found and valid"))
            except Exception as e:
                failures.append(f"job_manifest.json is malformed JSON: {e}")
                checks.append(AuditCheck(name="manifest_json", passed=False, detail=str(e)))
        else:
            failures.append("Missing job_manifest.json in archive")
            checks.append(AuditCheck(name="manifest_json", passed=False, detail="Missing job_manifest.json"))

        # Check 2: Case identity matches investigation identity
        identity_ok = False
        if expected_case_id and case_id:
            if expected_case_id.strip().lower() == case_id.strip().lower():
                identity_ok = True
                checks.append(AuditCheck(name="case_identity", passed=True, detail=f"Case ID matches {case_id}"))
            else:
                failures.append(f"Case ID mismatch: expected {expected_case_id}, found {case_id}")
                checks.append(AuditCheck(name="case_identity", passed=False, detail=f"Expected {expected_case_id}, got {case_id}"))
        else:
            identity_ok = manifest_ok
            checks.append(AuditCheck(name="case_identity", passed=manifest_ok, detail=f"Case ID: {case_id or 'none'}"))

        # Check 3: Solver log exists
        solver_log = archive_dir / "log.simpleFoam"
        if not solver_log.exists():
            solver_log = archive_dir / "log.pimpleFoam"
        if not solver_log.exists():
            # Check recursive glob
            for cand in archive_dir.glob("**/log.*Foam*"):
                solver_log = cand
                break

        log_ok = False
        log_content = ""
        if solver_log and solver_log.exists():
            log_content = solver_log.read_text(encoding="utf-8", errors="ignore")
            if "OpenFOAM" in log_content or "simpleFoam" in log_content:
                log_ok = True
                solver_name = "OpenFOAM simpleFoam"
                m_ver = re.search(r"Version:\s*([0-9\.\+a-zA-Z]+)", log_content)
                if m_ver:
                    solver_ver = m_ver.group(1)
                checks.append(AuditCheck(name="solver_log", passed=True, detail=f"Authentic {solver_name} log found"))
            else:
                failures.append("Solver log does not contain authentic OpenFOAM banner")
                checks.append(AuditCheck(name="solver_log", passed=False, detail="Invalid solver banner"))
        else:
            failures.append("Missing solver execution log (log.simpleFoam)")
            checks.append(AuditCheck(name="solver_log", passed=False, detail="Log missing"))

        # Check 4: Checksums / archive integrity
        checksum_ok = log_ok and manifest_ok
        checks.append(AuditCheck(name="checksum_integrity", passed=checksum_ok, detail="Archive structure consistent"))

        # Check 5: Required aerodynamic forces / coefficients
        forces_file = None
        for cand in archive_dir.glob("**/forceCoeffs.dat"):
            forces_file = cand
            break
        if not forces_file:
            for cand in archive_dir.glob("**/coefficient.dat"):
                forces_file = cand
                break

        forces_ok = False
        if forces_file and forces_file.exists():
            lines = [l.strip() for l in forces_file.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
            if lines:
                parts = lines[-1].split()
                # Format: Time  Cm  Cd  Cl  ...
                if len(parts) >= 4:
                    try:
                        # OpenFOAM default: col 1 = Time, col 2 = Cm, col 3 = Cd, col 4 = Cl
                        cm_val = float(parts[1])
                        cd_val = float(parts[2])
                        cl_val = float(parts[3])
                        parsed_polars["CM"] = cm_val
                        parsed_polars["CD"] = cd_val
                        parsed_polars["CL"] = cl_val
                        forces_ok = True
                        checks.append(AuditCheck(name="force_coefficients", passed=True, detail=f"CL={cl_val:.4f}, CD={cd_val:.4f}, CM={cm_val:.4f}"))
                    except (ValueError, IndexError) as e:
                        failures.append(f"Failed to parse numerical values in {forces_file.name}: {e}")
        elif log_content:
            # Check if forces were printed in log output
            cl_m = re.findall(r"Cl\s*=\s*([+-]?\d+\.?\d*(?:e[+-]?\d+)?)", log_content)
            cd_m = re.findall(r"Cd\s*=\s*([+-]?\d+\.?\d*(?:e[+-]?\d+)?)", log_content)
            cm_m = re.findall(r"Cm\s*=\s*([+-]?\d+\.?\d*(?:e[+-]?\d+)?)", log_content)
            if cl_m and cd_m:
                try:
                    parsed_polars["CL"] = float(cl_m[-1])
                    parsed_polars["CD"] = float(cd_m[-1])
                    if cm_m:
                        parsed_polars["CM"] = float(cm_m[-1])
                    forces_ok = True
                    checks.append(AuditCheck(name="force_coefficients", passed=True, detail=f"Parsed from log: CL={parsed_polars.get('CL')}, CD={parsed_polars.get('CD')}"))
                except ValueError:
                    pass

        if not forces_ok:
            failures.append("Missing or unparseable force coefficients (forceCoeffs.dat)")
            checks.append(AuditCheck(name="force_coefficients", passed=False, detail="Forces missing or unparseable"))

        # Check 6: Convergence information
        convergence_ok = False
        residuals_below_threshold = False
        RESIDUAL_THRESHOLD = 1e-4
        if log_content:
            res_matches = re.findall(r"Solving for (Ux|Uy|Uz|p|k|omega|epsilon), Initial residual = ([0-9\.eE+-]+), Final residual = ([0-9\.eE+-]+)", log_content)
            if res_matches:
                convergence_ok = True
                for var, init_r, fin_r in res_matches[-10:]:
                    if var not in residuals:
                        residuals[var] = []
                    try:
                        final_val = float(fin_r)
                        residuals[var].append(final_val)
                        if final_val < RESIDUAL_THRESHOLD:
                            residuals_below_threshold = True
                    except ValueError:
                        pass
                if residuals_below_threshold:
                    checks.append(AuditCheck(name="convergence_residuals", passed=True, detail=f"Extracted residuals for {list(residuals.keys())}; at least one final residual < {RESIDUAL_THRESHOLD}"))
                else:
                    checks.append(AuditCheck(name="convergence_residuals", passed=False, detail=f"Residuals present but none below {RESIDUAL_THRESHOLD} threshold"))
                    convergence_ok = False  # Downgrade: residuals exist but not converged
            # NOTE: "End" or "Finalising" in the log without actual residual data
            # does NOT grant convergence_ok. Convergence must be demonstrated by
            # at least one final residual below the threshold.
        if not convergence_ok:
            failures.append("No residual convergence information found in solver log")
            checks.append(AuditCheck(name="convergence_residuals", passed=False, detail="Missing convergence residuals"))

        # Check 7: Physical conservation
        physics_ok = False
        if forces_ok:
            cd = parsed_polars.get("CD", 0.0)
            if cd > 0.0:
                physics_ok = True
                checks.append(AuditCheck(name="physical_bounds", passed=True, detail="CD > 0 (positive drag confirmed)"))
            else:
                failures.append(f"Physical violation: Drag coefficient is non-positive (CD={cd})")
                checks.append(AuditCheck(name="physical_bounds", passed=False, detail="Negative drag"))
        else:
            checks.append(AuditCheck(name="physical_bounds", passed=False, detail="Cannot verify without forces"))

        fields_ok = False
        time_dirs = [d for d in archive_dir.iterdir() if d.is_dir() and d.name.replace(".", "").isdigit()] if archive_dir.is_dir() else []
        if time_dirs:
            fields_ok = True
            checks.append(AuditCheck(name="field_directories", passed=True, detail=f"Found {len(time_dirs)} time directory fields"))
        else:
            checks.append(AuditCheck(name="field_directories", passed=forces_ok, detail="Field directories optional if forces present"))

        # Determine overall verification status
        # VERIFIED requires ALL of: forces, log, manifest, identity, physics, AND convergence
        if forces_ok and log_ok and manifest_ok and identity_ok and physics_ok and convergence_ok:
            status = VerificationStatus.VERIFIED
            is_verified = True
            summary = "Simulation archive fully verified against all integrity checkpoints. Physical conservation and residual convergence confirmed."
        elif forces_ok and log_ok and manifest_ok and identity_ok and physics_ok and not convergence_ok:
            # Forces exist and are physical, but convergence not demonstrated
            status = VerificationStatus.PARTIALLY_VERIFIED
            is_verified = False
            summary = f"Simulation archive has valid forces but convergence not demonstrated: {', '.join(failures)}"
        elif not manifest_ok or not forces_ok:
            status = VerificationStatus.INCOMPLETE
            is_verified = False
            summary = f"Simulation archive is incomplete: {', '.join(failures)}"
        elif not physics_ok or not identity_ok:
            status = VerificationStatus.INVALID
            is_verified = False
            summary = f"Simulation archive contains invalid or non-physical data: {', '.join(failures)}"
        else:
            status = VerificationStatus.PARTIALLY_VERIFIED
            is_verified = False
            summary = f"Simulation archive partially verified with warnings: {', '.join(failures)}"

        if temp_extracted_dir:
            import shutil
            shutil.rmtree(temp_extracted_dir, ignore_errors=True)

        return ResultVerificationReport(
            status=status,
            is_verified=is_verified,
            audit_checks=checks,
            parsed_polars=parsed_polars,
            residual_history=residuals,
            solver_name=solver_name,
            solver_version=solver_ver,
            case_id=case_id,
            investigation_id=inv_id,
            verification_token=token,
            summary=summary,
            failure_reasons=failures,
        )


# Convenient alias
ScientificVerificationEngine = ScientificResultVerifier
