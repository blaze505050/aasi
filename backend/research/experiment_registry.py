"""
AASI Phase 20 Persistent Experiment Registry & Model Promotion Engine.

Features:
1. Immutable experiment records (AASI-P20-EXP-XXX) capturing data provenance,
   geometry hashes, splits, configs, metrics, DAG ancestry, and weights digests.
2. Strict 6-stage scientific model promotion hierarchy:
   TRAINED -> PHYSICS_VALIDATED -> REPRODUCIBLE -> OOD_EVALUATED -> UNCERTAINTY_AUDITED -> SCIENTIFICALLY_VERIFIED
3. Hard-gate enforcement: No skipping stages; unverified or uncalibrated models fail closed.
"""

from __future__ import annotations
import os
import json
import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PromotionStage(str, Enum):
    # Phase 20 stages (backward compatibility)
    TRAINED = "TRAINED"
    PHYSICS_VALIDATED = "PHYSICS_VALIDATED"
    REPRODUCIBLE = "REPRODUCIBLE"
    OOD_EVALUATED = "OOD_EVALUATED"
    UNCERTAINTY_AUDITED = "UNCERTAINTY_AUDITED"
    SCIENTIFICALLY_VERIFIED = "SCIENTIFICALLY_VERIFIED"
    TRAINED_UNVERIFIED = "TRAINED_UNVERIFIED"
    PROMOTION_BLOCKED = "PROMOTION_BLOCKED"

    # Phase 21 Extended 8-Stage Hierarchy
    STAGE_1_UNTRAINED = "UNTRAINED"
    STAGE_2_IN_DOMAIN_VALIDATED = "IN_DOMAIN_VALIDATED"
    STAGE_3_PHYSICS_VERIFIED = "PHYSICS_VERIFIED"
    STAGE_4_UNCERTAINTY_CALIBRATED = "UNCERTAINTY_CALIBRATED"
    STAGE_5_OOD_TESTED = "OOD_TESTED"
    STAGE_6_EXTERNALLY_VALIDATED = "EXTERNALLY_VALIDATED"
    STAGE_7_REPRODUCIBLE = "REPRODUCIBLE"
    STAGE_8_SCIENTIFICALLY_TRUSTED = "SCIENTIFICALLY_TRUSTED"

    # Phase 22 Extended 10-Stage Hierarchy
    STAGE_9_REAL_CFD_VALIDATED = "REAL_CFD_VALIDATED"
    STAGE_10_CLOSED_LOOP_SCIENTIFICALLY_VALIDATED = "CLOSED_LOOP_SCIENTIFICALLY_VALIDATED"


class ExperimentRecord(BaseModel):
    """Immutable persistent experiment record."""
    experiment_id: str
    parent_experiment_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_name: str
    representation_name: str
    dataset_manifest_hash: str
    geometry_hashes: List[str]
    split_definition: Dict[str, List[str]]
    hyperparameters: Dict[str, Any]
    training_metrics: Dict[str, float]
    ood_metrics: Dict[str, Any]
    calibration_metrics: Dict[str, Any]
    physical_admissibility: Dict[str, Any]
    checkpoint_hash: str
    environment_hash: str
    provenance_dag_hash: str
    scientific_conclusion: str
    promotion_stage: PromotionStage = PromotionStage.TRAINED
    is_verified: bool = False


class PersistentExperimentRegistry:
    """
    Manages persistent experiment records and audits model promotion gates.
    """

    def __init__(self, registry_file: str = "data/experiments/registry.json"):
        self.registry_file = registry_file
        os.makedirs(os.path.dirname(os.path.abspath(self.registry_file)), exist_ok=True)
        self.experiments: Dict[str, ExperimentRecord] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r") as f:
                    raw = json.load(f)
                    for k, v in raw.items():
                        self.experiments[k] = ExperimentRecord(**v)
            except Exception as e:
                print(f"Warning: could not load experiment registry: {e}")

    def _save(self):
        serializable = {k: v.model_dump() for k, v in self.experiments.items()}
        with open(self.registry_file, "w") as f:
            json.dump(serializable, f, indent=2)

    def register_experiment(self, record: ExperimentRecord) -> ExperimentRecord:
        """Saves experiment to persistent registry."""
        self.experiments[record.experiment_id] = record
        self._save()
        return record

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentRecord]:
        return self.experiments.get(experiment_id)

    def list_experiments(self) -> List[ExperimentRecord]:
        return list(self.experiments.values())

    @classmethod
    def audit_promotion(
        cls,
        physics_valid: bool,
        reproducible: bool,
        ood_evaluated: bool,
        uncertainty_calibrated: bool,
        geometry_ood_r2: float
    ) -> Tuple[PromotionStage, bool, str]:
        """
        Enforces strict 6-stage promotion hierarchy:
        TRAINED -> PHYSICS_VALIDATED -> REPRODUCIBLE -> OOD_EVALUATED -> UNCERTAINTY_AUDITED -> SCIENTIFICALLY_VERIFIED
        """
        # Stage 1: Physics Validation Gate
        if not physics_valid:
            return (
                PromotionStage.PROMOTION_BLOCKED,
                False,
                "Model failed physics validation (negative drag or non-monotonic lift observed)."
            )

        # Stage 2: Reproducibility Gate
        if not reproducible:
            return (
                PromotionStage.PHYSICS_VALIDATED,
                False,
                "Model passed physics validation, but two-run reproducibility verification failed."
            )

        # Stage 3: OOD Evaluation Gate
        if not ood_evaluated:
            return (
                PromotionStage.REPRODUCIBLE,
                False,
                "Model is reproducible, but out-of-distribution evaluation is pending."
            )

        # Stage 4: Uncertainty Audit Gate
        if not uncertainty_calibrated:
            return (
                PromotionStage.OOD_EVALUATED,
                False,
                "Model evaluated on OOD data, but uncertainty remains UNCERTAINTY_NOT_CALIBRATED (coverage < 87%)."
            )

        # Stage 5: Scientific Generalization Gate
        if geometry_ood_r2 < 0.0:
            return (
                PromotionStage.UNCERTAINTY_AUDITED,
                False,
                f"Model has calibrated uncertainty, but exhibits negative OOD transfer (R^2={geometry_ood_r2:.3f}). Locked at UNCERTAINTY_AUDITED."
            )

        # Full Verification
        return (
            PromotionStage.SCIENTIFICALLY_VERIFIED,
            True,
            "All physical, reproducibility, OOD, and uncertainty calibration gates passed. Promoted to SCIENTIFICALLY_VERIFIED."
        )

    @classmethod
    def audit_promotion_phase21(
        cls,
        in_domain_valid: bool,
        physics_valid: bool,
        uncertainty_calibrated: bool,
        ood_tested: bool,
        externally_validated: bool,
        reproducible: bool,
        ood_r2: float = 0.0,
    ) -> Tuple[PromotionStage, bool, str]:
        """
        Enforces Phase 21 strict 8-stage promotion hierarchy:
        1. UNTRAINED
        2. IN_DOMAIN_VALIDATED
        3. PHYSICS_VERIFIED
        4. UNCERTAINTY_CALIBRATED
        5. OOD_TESTED
        6. EXTERNALLY_VALIDATED
        7. REPRODUCIBLE
        8. SCIENTIFICALLY_TRUSTED
        No model may skip a stage.
        """
        if not in_domain_valid:
            return (
                PromotionStage.STAGE_1_UNTRAINED,
                False,
                "Model has not achieved in-domain validation threshold."
            )

        if not physics_valid:
            return (
                PromotionStage.PROMOTION_BLOCKED,
                False,
                "PHYSICS_GATE_FAILED: Physical violation detected (negative drag or unphysical forces)."
            )

        if not uncertainty_calibrated:
            return (
                PromotionStage.STAGE_3_PHYSICS_VERIFIED,
                False,
                "Model is physics verified, but epistemic uncertainty is UNCERTAINTY_NOT_CALIBRATED."
            )

        if not ood_tested or ood_r2 < 0.0:
            return (
                PromotionStage.STAGE_4_UNCERTAINTY_CALIBRATED,
                False,
                f"Model has calibrated uncertainty, but OOD generalization is unverified or negative (R^2={ood_r2:.3f})."
            )

        if not externally_validated:
            return (
                PromotionStage.STAGE_5_OOD_TESTED,
                False,
                "Model generalizes to OOD test geometries, but lacks external cross-dataset or experimental validation."
            )

        if not reproducible:
            return (
                PromotionStage.STAGE_6_EXTERNALLY_VALIDATED,
                False,
                "Model externally validated, but bitwise reproduction verifier failed."
            )

        return (
            PromotionStage.STAGE_8_SCIENTIFICALLY_TRUSTED,
            True,
            "All 8 scientific promotion stages verified: in-domain, physics, calibrated uncertainty, OOD, external, reproduction."
        )

    @classmethod
    def audit_promotion_phase22(
        cls,
        stage8_passed: bool,
        real_cfd_available: bool,
        cfd_provenance_verified: bool,
        convergence_verified: bool,
        physical_checks_passed: bool,
        independent_reproduction_passed: bool,
        frozen_eval_passed: bool,
        closed_loop_completed: bool,
        solver_executable_on_host: bool = True,
    ) -> Tuple[PromotionStage, bool, str]:
        """
        Enforces Phase 22 strict 10-stage promotion hierarchy:
        1-8. STAGE_1 through STAGE_8 (from Phase 21)
        9. STAGE_9_REAL_CFD_VALIDATED (authentic CFD, verified convergence, physical checks pass, reproduction passes, frozen eval passes)
        10. STAGE_10_CLOSED_LOOP_SCIENTIFICALLY_VALIDATED (complete autonomous loop: candidate -> CFD -> ingest -> retrain -> validate -> next candidate)
        Strict fail-closed rule: If host solver is unavailable, promotion beyond STAGE_8 is strictly blocked.
        """
        if not stage8_passed:
            return (
                PromotionStage.STAGE_8_SCIENTIFICALLY_TRUSTED,
                False,
                "Model has not achieved STAGE_8_SCIENTIFICALLY_TRUSTED verification.",
            )

        if not solver_executable_on_host:
            return (
                PromotionStage.STAGE_8_SCIENTIFICALLY_TRUSTED,
                False,
                "USER_EXECUTED_REQUIRED: Promotion to STAGE_9/10 blocked because host OpenFOAM solver execution is pending client environment.",
            )

        if not real_cfd_available:
            return (
                PromotionStage.STAGE_8_SCIENTIFICALLY_TRUSTED,
                False,
                "Promotion blocked: No authenticated real CFD execution data available.",
            )

        if not cfd_provenance_verified:
            return (
                PromotionStage.STAGE_8_SCIENTIFICALLY_TRUSTED,
                False,
                "Promotion blocked: CFD cryptographic provenance DAG verification failed.",
            )

        if not convergence_verified:
            return (
                PromotionStage.STAGE_8_SCIENTIFICALLY_TRUSTED,
                False,
                "Promotion blocked: CFD solver convergence was not verified (CFD_NOT_CONVERGED).",
            )

        if not physical_checks_passed:
            return (
                PromotionStage.PROMOTION_BLOCKED,
                False,
                "PHYSICS_GATE_FAILED: Physical checks failed on CFD fields or aerodynamic forces.",
            )

        if not independent_reproduction_passed:
            return (
                PromotionStage.STAGE_8_SCIENTIFICALLY_TRUSTED,
                False,
                "Promotion blocked: Independent reproduction verification failed.",
            )

        if not frozen_eval_passed:
            return (
                PromotionStage.STAGE_8_SCIENTIFICALLY_TRUSTED,
                False,
                "Promotion blocked: Retrained model failed validation on frozen test set.",
            )

        if not closed_loop_completed:
            return (
                PromotionStage.STAGE_9_REAL_CFD_VALIDATED,
                True,
                "STAGE_9_REAL_CFD_VALIDATED achieved: Real CFD verified, convergence established, physics passed, frozen eval verified.",
            )

        return (
            PromotionStage.STAGE_10_CLOSED_LOOP_SCIENTIFICALLY_VALIDATED,
            True,
            "STAGE_10_CLOSED_LOOP_SCIENTIFICALLY_VALIDATED achieved: Full autonomous closed loop successfully executed and verified.",
        )

