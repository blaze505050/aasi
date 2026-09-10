"""
AASI Artifact Ingestion & Validation Interface.

Parses user-uploaded simulation outputs (OpenFOAM logs, forceCoeffs,
residual histories, CSVs, SU2 logs, XFOIL polars), attaches cryptographic
provenance, and validates convergence and physical boundaries.
"""

import os
import re
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.compute.models import UploadedArtifactPayload, IngestionResult


class ArtifactIngestionService:
    """Ingests and parses simulation output artifacts returned from external runs."""

    def __init__(self):
        pass

    def ingest_artifact(self, payload: UploadedArtifactPayload) -> IngestionResult:
        """
        Parses uploaded file content, computes SHA-256 hash, extracts aerodynamic
        coefficients and residuals, and runs validation checks.
        """
        content = payload.file_content
        file_name = payload.file_name.lower()
        content_bytes = content.encode("utf-8")
        provenance_hash = hashlib.sha256(content_bytes).hexdigest()

        solver = payload.solver.lower()
        coefficients: Dict[str, float] = {}
        residuals: Dict[str, float] = {}
        converged = False
        iterations = 0
        validation_notes: List[str] = []

        if "forcecoeffs" in file_name or "coefficient" in file_name or payload.solver == "openfoam":
            # Parse OpenFOAM force coefficients or standard log
            parsed_coeffs = self._parse_openfoam_force_coeffs(content)
            if parsed_coeffs:
                coefficients.update(parsed_coeffs)
            
            # Parse OpenFOAM residuals if present in log
            parsed_res, max_iter, has_converged = self._parse_openfoam_log_residuals(content)
            if parsed_res:
                residuals.update(parsed_res)
                iterations = max_iter
                converged = has_converged

        elif "history" in file_name or "su2" in solver:
            # Parse SU2 history CSV / text
            parsed_coeffs, parsed_res, max_iter, has_converged = self._parse_su2_history(content)
            coefficients.update(parsed_coeffs)
            residuals.update(parsed_res)
            iterations = max_iter
            converged = has_converged

        elif "polar" in file_name or "xfoil" in solver or file_name.endswith(".pol"):
            # Parse XFOIL polar file
            parsed_coeffs = self._parse_xfoil_polar(content)
            coefficients.update(parsed_coeffs)
            converged = True

        else:
            # Generic CSV parser
            parsed_coeffs = self._parse_generic_csv(content)
            coefficients.update(parsed_coeffs)

        # Validation checks
        val_status = "VALIDATED"
        if not coefficients:
            val_status = "NO_COEFFICIENTS_FOUND"
            validation_notes.append("Could not extract Cl/Cd/Cm from uploaded artifact.")
        else:
            cd = coefficients.get("cd")
            cl = coefficients.get("cl")
            if cd is not None and cd < 0:
                val_status = "PHYSICAL_ANOMALY"
                validation_notes.append("Warning: Negative drag coefficient Cd extracted.")
            if cd is not None and cd > 1.5:
                val_status = "SUSPICIOUS_HIGH_DRAG"
                validation_notes.append("Warning: Drag coefficient Cd > 1.5 is unusually high for airfoil.")
            if cl is not None and abs(cl) > 3.0:
                val_status = "SUSPICIOUS_HIGH_LIFT"
                validation_notes.append("Warning: Lift coefficient magnitude > 3.0 exceeds normal airfoil stall limit.")
            if not converged:
                validation_notes.append("Warning: Convergence criteria not explicitly confirmed in log.")

        return IngestionResult(
            case_id=payload.case_id,
            status="INGESTED",
            solver=payload.solver,
            converged=converged,
            iterations=iterations,
            residuals=residuals,
            coefficients=coefficients,
            provenance_hash=provenance_hash,
            validation_status=val_status,
            validation_notes=validation_notes,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def _parse_openfoam_force_coeffs(self, text: str) -> Dict[str, float]:
        """Parses OpenFOAM postProcessing/forceCoeffs or log coefficient lines."""
        results: Dict[str, float] = {}
        # Match lines like: 1000  0.00762  0.4412  -0.0123
        # Or: Cl = 0.4412, Cd = 0.00762, Cm = -0.0123
        lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
        for line in reversed(lines):
            # Try labeled format
            cl_m = re.search(r"Cl\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", line, re.IGNORECASE)
            cd_m = re.search(r"Cd\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", line, re.IGNORECASE)
            cm_m = re.search(r"Cm\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", line, re.IGNORECASE)
            if cd_m:
                results["cd"] = float(cd_m.group(1))
            if cl_m:
                results["cl"] = float(cl_m.group(1))
            if cm_m:
                results["cm"] = float(cm_m.group(1))
            if results:
                return results

            # Try space/tab delimited tabular: Time  Cd  Cl  Cm
            parts = line.split()
            if len(parts) >= 3:
                try:
                    vals = [float(p) for p in parts]
                    if len(vals) >= 3:
                        # Assuming Time, Cd, Cl, (Cm)
                        results["cd"] = vals[1]
                        results["cl"] = vals[2]
                        if len(vals) >= 4:
                            results["cm"] = vals[3]
                        return results
                except ValueError:
                    continue
        return results

    def _parse_openfoam_log_residuals(self, text: str) -> tuple[Dict[str, float], int, bool]:
        """Extracts residuals and iteration counts from simpleFoam log."""
        residuals: Dict[str, float] = {}
        max_iter = 0
        converged = False

        for line in text.splitlines():
            # Time = 500
            m_time = re.match(r"^Time\s*=\s*(\d+)", line)
            if m_time:
                max_iter = max(max_iter, int(m_time.group(1)))

            # Solving for Ux, Initial residual = 0.00012, Final residual = 0.00001
            m_res = re.search(r"Solving for (\w+),\s*Initial residual\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", line)
            if m_res:
                var = m_res.group(1).lower()
                val = float(m_res.group(2))
                residuals[var] = val

            if "SIMPLE solution converged" in line or "End" in line:
                converged = True

        if max_iter >= 500 and residuals.get("p", 1.0) < 1e-4:
            converged = True

        return residuals, max_iter, converged

    def _parse_su2_history(self, text: str) -> tuple[Dict[str, float], Dict[str, float], int, bool]:
        """Parses SU2 history.csv output."""
        coeffs: Dict[str, float] = {}
        res: Dict[str, float] = {}
        max_iter = 0
        converged = False

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return coeffs, res, max_iter, converged

        header = [h.strip('"').strip() for h in lines[0].split(",")]
        if len(lines) > 1:
            last_line = lines[-1].split(",")
            if len(last_line) == len(header):
                row = dict(zip(header, last_line))
                try:
                    if "Inner_Iter" in row:
                        max_iter = int(row["Inner_Iter"])
                    if "CD" in row or "Total_CD" in row:
                        coeffs["cd"] = float(row.get("CD", row.get("Total_CD", 0)))
                    if "CL" in row or "Total_CL" in row:
                        coeffs["cl"] = float(row.get("CL", row.get("Total_CL", 0)))
                    if "CSF" in row or "Total_CMz" in row:
                        coeffs["cm"] = float(row.get("Total_CMz", 0))
                    if "rms[Rho]" in row:
                        res["rho"] = float(row["rms[Rho]"])
                    converged = True
                except ValueError:
                    pass

        return coeffs, res, max_iter, converged

    def _parse_xfoil_polar(self, text: str) -> Dict[str, float]:
        """Parses XFOIL saved polar format."""
        coeffs: Dict[str, float] = {}
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        # Typical header: alpha   CL        CD        CDp       CM
        data_started = False
        last_data_line = None
        for line in lines:
            if "alpha" in line and "CL" in line and "CD" in line:
                data_started = True
                continue
            if data_started and not line.startswith("-"):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        [float(p) for p in parts]
                        last_data_line = parts
                    except ValueError:
                        pass
        if last_data_line:
            try:
                coeffs["aoa"] = float(last_data_line[0])
                coeffs["cl"] = float(last_data_line[1])
                coeffs["cd"] = float(last_data_line[2])
                if len(last_data_line) >= 5:
                    coeffs["cm"] = float(last_data_line[4])
            except (ValueError, IndexError):
                pass
        return coeffs

    def _parse_generic_csv(self, text: str) -> Dict[str, float]:
        """Generic fallback CSV parser."""
        coeffs: Dict[str, float] = {}
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if len(lines) >= 2:
            header = [h.strip().lower() for h in lines[0].split(",")]
            vals = [v.strip() for v in lines[-1].split(",")]
            if len(header) == len(vals):
                row = dict(zip(header, vals))
                for k in ["cd", "drag", "c_d"]:
                    if k in row:
                        try:
                            coeffs["cd"] = float(row[k])
                        except ValueError:
                            pass
                for k in ["cl", "lift", "c_l"]:
                    if k in row:
                        try:
                            coeffs["cl"] = float(row[k])
                        except ValueError:
                            pass
                for k in ["cm", "moment", "c_m"]:
                    if k in row:
                        try:
                            coeffs["cm"] = float(row[k])
                        except ValueError:
                            pass
        return coeffs
