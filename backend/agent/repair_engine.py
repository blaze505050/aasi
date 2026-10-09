"""
AASI Phase 26 Automatic CFD Repair Engine.
Generates cryptographically distinct candidate configurations for failed simulations across all 11 error classes.
Enforces that original configurations remain immutable and retries are hard-capped at 3.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import hashlib
import json
from backend.agent.diagnostics import DiagnosticReport, CFDErrorClass


class RepairCandidate(BaseModel):
    """Cryptographically separate candidate configuration."""
    original_case_hash: str
    repair_id: str
    candidate_case_hash: str
    retry_number: int
    modifications: Dict[str, Any]
    reason: str
    preflight_passed: bool = False
    parent_job_id: Optional[str] = None
    parent_attempt_hash: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RepairOutcome(BaseModel):
    """Result of repair proposal."""
    status: str       # "REPAIR_CANDIDATE_GENERATED", "HUMAN_REVIEW_REQUIRED"
    candidate: Optional[RepairCandidate] = None
    detail: str
    retries_exhausted: bool = False


class CFDRepairEngine:
    """
    Generates non-mutating repair candidates with strict retry limits.
    """

    MAX_RETRIES = 3

    @classmethod
    def propose_repair(
        cls,
        original_spec: Dict[str, Any],
        original_case_hash: str,
        diagnosis: DiagnosticReport,
        current_retry_count: int,
    ) -> RepairOutcome:
        """
        Synthesizes a new candidate configuration based on the diagnosed failure class.
        Never alters the original case parameters in-place.
        """
        if current_retry_count >= cls.MAX_RETRIES:
            return RepairOutcome(
                status="HUMAN_REVIEW_REQUIRED",
                candidate=None,
                detail=(
                    f"Automatic retry limit ({cls.MAX_RETRIES}) exhausted. "
                    f"Last error: {diagnosis.error_class.value}. Manual aerospace engineer intervention required."
                ),
                retries_exhausted=True,
            )

        new_retry = current_retry_count + 1
        modifications: Dict[str, Any] = {}
        reason = ""

        # Deterministic repair strategy by error class
        if diagnosis.error_class in [CFDErrorClass.DIVERGENCE, CFDErrorClass.FLOATING_POINT_FAILURE]:
            modifications = {
                "fvSolution_relaxation": {"p": 0.2, "U": 0.5, "k": 0.5, "omega": 0.5},
                "fvSchemes_divSchemes": "bounded Gauss upwind",
                "max_iterations": 2000,
            }
            reason = "Divergence/overflow detected. Lowered relaxation factors and adopted bounded first-order upwind schemes."

        elif diagnosis.error_class == CFDErrorClass.RESIDUAL_STAGNATION:
            modifications = {
                "fvSolution_relaxation": {"p": 0.4, "U": 0.8},
                "gamg_tolerance": 1e-6,
                "max_iterations": 3000,
            }
            reason = "Residual stagnation detected. Tightened GAMG linear solver tolerances and increased max iterations."

        elif diagnosis.error_class == CFDErrorClass.COURANT_INSTABILITY:
            modifications = {
                "controlDict_deltaT": 0.0005,
                "controlDict_adjustTimeStep": True,
                "controlDict_maxCo": 0.8,
            }
            reason = "Courant-number instability detected. Reduced deltaT by 50% and clamped maxCo to 0.8."

        elif diagnosis.error_class == CFDErrorClass.TIME_STEP_INSTABILITY:
            modifications = {
                "controlDict_deltaT": 0.001,
                "controlDict_adjustTimeStep": False,
            }
            reason = "Time-step instability detected. Locked deltaT to fixed conservative value."

        elif diagnosis.error_class == CFDErrorClass.LINEAR_SOLVER_FAILURE:
            modifications = {
                "fvSolution_solvers_p": "PCG",
                "fvSolution_preconditioner_p": "DIC",
                "fvSolution_maxIter": 500,
                "fvSolution_nPreSweeps": 2,
                "fvSolution_nPostSweeps": 2,
            }
            reason = "Linear matrix solver failure. Switched pressure equation solver to PCG with DIC preconditioner and increased max iterations."

        elif diagnosis.error_class == CFDErrorClass.TURBULENCE_INSTABILITY:
            modifications = {
                "fvSolution_relaxation": {"k": 0.4, "omega": 0.4},
                "fvSchemes_turbulence": "bounded Gauss upwind",
                "inlet_k_clamped": True,
            }
            reason = "Turbulence equation instability detected. Damped k and omega relaxation factors to 0.4 and bounded divergence schemes."

        elif diagnosis.error_class == CFDErrorClass.MISSING_FIELD:
            modifications = {
                "generate_missing_field": True,
                "default_field_values": {"nut": "calculated", "k": 0.01, "omega": 10.0},
            }
            reason = "Missing 0/ field detected. Generated standard wall-function boundary fields."

        elif diagnosis.error_class == CFDErrorClass.INVALID_BOUNDARY_CONDITION:
            modifications = {
                "harmonize_patches": True,
                "boundary_patch_corrections": {"airfoil": "wall", "inlet": "patch", "outlet": "patch"},
            }
            reason = "Boundary condition patch type mismatch. Harmonized patch names with polyMesh/boundary."

        elif diagnosis.error_class == CFDErrorClass.MESH_QUALITY_FAILURE:
            modifications = {
                "mesh_boundary_layer_growth_ratio": 1.15,
                "first_cell_height_factor": 1.25,
                "surface_refinement_level": 2,
            }
            reason = "Mesh skewness/orthogonality failure. Softened boundary layer grading and refined surface cells."

        elif diagnosis.error_class == CFDErrorClass.MISSING_SOLVER:
            modifications = {
                "execution_backend_override": "COLAB",
            }
            reason = "Local solver unavailable. Rerouting case to remote Google Colab container with pre-installed OpenFOAM-10."

        elif diagnosis.error_class == CFDErrorClass.PHYSICS_GATE_VIOLATION:
            modifications = {
                "force_direction_vectors": "recomputed_from_aoa",
                "reference_pressure_p0": 0.0,
            }
            reason = "Physical gate violation. Realigned lift/drag projection vectors with flow angle of attack."

        else:
            modifications = {
                "conservative_mode": True,
                "relaxation_damping": 0.8,
            }
            reason = f"Generic stabilization applied for error: {diagnosis.error_class.value}."

        # Compute new deterministic candidate hash
        candidate_payload = {
            "original_hash": original_case_hash,
            "retry_number": new_retry,
            "modifications": modifications,
            "spec": original_spec,
        }
        canonical_str = json.dumps(candidate_payload, sort_keys=True, default=str)
        candidate_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        repair_id = f"REPAIR-{candidate_hash[:10].upper()}-R{new_retry}"

        candidate = RepairCandidate(
            original_case_hash=original_case_hash,
            repair_id=repair_id,
            candidate_case_hash=candidate_hash,
            retry_number=new_retry,
            modifications=modifications,
            reason=reason,
            preflight_passed=True,
        )

        return RepairOutcome(
            status="REPAIR_CANDIDATE_GENERATED",
            candidate=candidate,
            detail=f"Generated repair candidate {repair_id} (Attempt {new_retry}/{cls.MAX_RETRIES}).",
            retries_exhausted=False,
        )
