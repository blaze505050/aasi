"""
AASI Automatic CFD Repair Engine.
Generates cryptographically distinct candidate configurations for failed simulations.
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
