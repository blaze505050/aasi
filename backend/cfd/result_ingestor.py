"""
AASI Phase 21: CFD Result Ingestor and Physical Validation Gate.
Governing Rule: Absolute Anti-Fabrication Rule.
Enforces physical realism gates before CFD observations can be consumed by downstream AI models.
"""

from typing import Any, Dict, List, Optional
from backend.cfd.solver_interface import PhysicalValidationState


class CFDResultIngestor:
    """Validates physical consistency and prepares verified training observations."""

    MIN_CD = 0.0
    MAX_CD = 1.5
    MIN_CL = -3.0
    MAX_CL = 3.0
    MAX_CM_ABS = 1.5

    @classmethod
    def validate_physics(cls, force_data: Dict[str, Any], flow_condition: Dict[str, Any]) -> Dict[str, Any]:
        """Validate physical sanity of computed force coefficients."""
        checks: Dict[str, Any] = {}
        errors: List[str] = []

        if not force_data.get("parsed", False):
            return {
                "valid": False,
                "state": PhysicalValidationState.PHYSICS_GATE_FAILED.value,
                "errors": ["Force data is missing or could not be parsed."],
                "checks": checks,
            }

        cl_final = force_data.get("CL", {}).get("final", 0.0)
        cd_final = force_data.get("CD", {}).get("final", 0.0)
        cm_final = force_data.get("CM", {}).get("final", 0.0)

        # 1. Drag non-negativity
        cd_non_neg = cd_final >= cls.MIN_CD
        checks["drag_non_negative"] = {
            "passed": cd_non_neg,
            "value": cd_final,
            "threshold": cls.MIN_CD,
        }
        if not cd_non_neg:
            errors.append(f"Unphysical negative drag: CD = {cd_final} < {cls.MIN_CD}")

        # 2. Drag upper bound
        cd_bounded = cd_final <= cls.MAX_CD
        checks["drag_upper_bounded"] = {
            "passed": cd_bounded,
            "value": cd_final,
            "threshold": cls.MAX_CD,
        }
        if not cd_bounded:
            errors.append(f"Unphysical excessive drag: CD = {cd_final} > {cls.MAX_CD}")

        # 3. Lift bounds
        cl_bounded = cls.MIN_CL <= cl_final <= cls.MAX_CL
        checks["lift_bounded"] = {
            "passed": cl_bounded,
            "value": cl_final,
            "min": cls.MIN_CL,
            "max": cls.MAX_CL,
        }
        if not cl_bounded:
            errors.append(f"Unphysical lift coefficient: CL = {cl_final} outside [{cls.MIN_CL}, {cls.MAX_CL}]")

        # 4. Moment bounds
        cm_bounded = abs(cm_final) <= cls.MAX_CM_ABS
        checks["moment_bounded"] = {
            "passed": cm_bounded,
            "value": cm_final,
            "threshold": cls.MAX_CM_ABS,
        }
        if not cm_bounded:
            errors.append(f"Unphysical pitching moment: |CM| = {abs(cm_final)} > {cls.MAX_CM_ABS}")

        # 5. Lift sign consistency with AoA for symmetric airfoils or normal positive camber
        alpha = flow_condition.get("alpha_deg", 0.0)
        camber = flow_condition.get("camber_m", 0.0)
        if alpha >= 6.0 and camber >= 0.0 and cl_final < 0.0:
            errors.append(f"Severe physical inconsistency: negative lift CL={cl_final} at positive AoA alpha={alpha} deg")

        is_valid = len(errors) == 0
        state = PhysicalValidationState.PHYSICALLY_VALID if is_valid else PhysicalValidationState.PHYSICS_GATE_FAILED

        return {
            "valid": is_valid,
            "state": state.value,
            "errors": errors,
            "checks": checks,
        }

    @classmethod
    def ingest_to_observation(
        cls,
        case_name: str,
        geometry_id: str,
        geometry_hash: str,
        flow_condition: Dict[str, Any],
        force_data: Dict[str, Any],
        convergence_data: Dict[str, Any],
        provenance_hash: str,
    ) -> Dict[str, Any]:
        """Convert validated CFD run into an authenticated observation."""
        phys_val = cls.validate_physics(force_data, flow_condition)
        if not phys_val["valid"]:
            raise ValueError(f"CFD result failed physical validation gates: {phys_val['errors']}")

        if not convergence_data.get("converged", False):
            raise ValueError(f"CFD result is not converged: {convergence_data.get('reason')}")

        return {
            "case_name": case_name,
            "geometry_id": geometry_id,
            "geometry_hash": geometry_hash,
            "fidelity_level": "FIDELITY_3",  # Refined RANS
            "solver": "OpenFOAM_simpleFoam",
            "alpha_deg": flow_condition.get("alpha_deg"),
            "reynolds": flow_condition.get("reynolds"),
            "mach": flow_condition.get("mach", 0.15),
            "CL": force_data["CL"]["final"],
            "CD": force_data["CD"]["final"],
            "CM": force_data["CM"]["final"],
            "convergence_state": convergence_data.get("convergence_state"),
            "provenance_hash": provenance_hash,
            "ingestion_status": "AUTHENTICATED_OBSERVATION",
        }
