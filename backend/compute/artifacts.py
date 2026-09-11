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
        """Parses OpenFOAM postProcessing forceCoeffs.dat or labeled force coefficient text."""
        results: Dict[str, float] = {}
        header_map: Dict[str, int] = {}

        # Scan for header line
        for line in text.splitlines():
            line_str = line.strip()
            if line_str.startswith("#"):
                clean = line_str.replace("#", "").lower()
                tokens = clean.split()
                if "cd" in tokens or "cl" in tokens or "cm" in tokens:
                    for idx, t in enumerate(tokens):
                        if t in ("cd", "cl", "cm"):
                            header_map[t] = idx
                    break

        lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
        for line in reversed(lines):
            # Try labeled format
            cl_m = re.search(r"Cl\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", line, re.IGNORECASE)
            cd_m = re.search(r"Cd\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", line, re.IGNORECASE)
            cm_m = re.search(r"Cm\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", line, re.IGNORECASE)
            if cd_m or cl_m or cm_m:
                if cd_m: results["cd"] = float(cd_m.group(1))
                if cl_m: results["cl"] = float(cl_m.group(1))
                if cm_m: results["cm"] = float(cm_m.group(1))
                return results

            # Tabular space/tab delimited
            parts = line.split()
            try:
                vals = [float(p) for p in parts]
                if header_map:
                    for k, col_idx in header_map.items():
                        if col_idx < len(vals):
                            results[k] = vals[col_idx]
                    if results:
                        return results
                elif len(vals) >= 3:
                    # Default: Time, Cd, Cl, (Cm)
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

        # Steady-state convergence indicator
        if "SIMPLE solution converged" in text or "End" in text:
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
            last_line = [l.strip() for l in lines[-1].split(",")]
            if len(last_line) == len(header):
                row_upper = {k.strip().upper(): v for k, v in zip(header, last_line)}
                try:
                    if "INNER_ITER" in row_upper:
                        max_iter = int(row_upper["INNER_ITER"])
                    for cd_key in ["CD", "TOTAL_CD", "DRAG"]:
                        if cd_key in row_upper:
                            coeffs["cd"] = float(row_upper[cd_key])
                            break
                    for cl_key in ["CL", "TOTAL_CL", "LIFT"]:
                        if cl_key in row_upper:
                            coeffs["cl"] = float(row_upper[cl_key])
                            break
                    for cm_key in ["CM", "CSF", "TOTAL_CMZ", "MOMENT"]:
                        if cm_key in row_upper:
                            coeffs["cm"] = float(row_upper[cm_key])
                            break
                    if "RMS[RHO]" in row_upper:
                        res["rho"] = float(row_upper["RMS[RHO]"])
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

    def evaluate_mesh_convergence_study(
        self,
        fine_result: IngestionResult,
        medium_result: IngestionResult,
        coarse_result: IngestionResult,
        metric: str = "cl",
        r21: float = 1.4142,
        r32: float = 1.4142,
    ) -> Dict[str, Any]:
        """Calculates ASME V&V 20 GCI across 3 user-executed simulation runs."""
        from backend.validation.grid_convergence import GridConvergenceService
        f1 = fine_result.coefficients.get(metric.lower())
        f2 = medium_result.coefficients.get(metric.lower())
        f3 = coarse_result.coefficients.get(metric.lower())

        if f1 is None or f2 is None or f3 is None:
            return {
                "valid": False,
                "error": f"Metric '{metric}' not found in all three simulation results."
            }

        gci = GridConvergenceService.compute_gci(
            f1=f1, f2=f2, f3=f3, r21=r21, r32=r32, metric_name=metric
        )
        return {
            "valid": True,
            "metric": metric,
            "fine_case_id": fine_result.case_id,
            "medium_case_id": medium_result.case_id,
            "coarse_case_id": coarse_result.case_id,
            "gci_result": gci.model_dump(),
        }

