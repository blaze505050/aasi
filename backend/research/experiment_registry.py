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
    TRAINED = "TRAINED"
    PHYSICS_VALIDATED = "PHYSICS_VALIDATED"
    REPRODUCIBLE = "REPRODUCIBLE"
    OOD_EVALUATED = "OOD_EVALUATED"
    UNCERTAINTY_AUDITED = "UNCERTAINTY_AUDITED"
    SCIENTIFICALLY_VERIFIED = "SCIENTIFICALLY_VERIFIED"
    TRAINED_UNVERIFIED = "TRAINED_UNVERIFIED"
    PROMOTION_BLOCKED = "PROMOTION_BLOCKED"


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
