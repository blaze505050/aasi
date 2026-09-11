"""
AASI Physics-AI Service Layer.

Provides singleton access to AerodynamicInferenceEngine and high-level endpoints
for surrogate evaluation, polar sweeps, and model management.
"""

from typing import Dict, Any, Optional, List, Union
from backend.physics_ai.inference import AerodynamicInferenceEngine
from backend.physics_ai.schemas import AerodynamicPrediction


class PhysicsAIService:
    """Singleton service manager for Physics-AI models."""

    _instance: Optional["PhysicsAIService"] = None
    _engine: Optional[AerodynamicInferenceEngine] = None

    @classmethod
    def get_instance(cls) -> "PhysicsAIService":
        if cls._instance is None:
            cls._instance = PhysicsAIService()
        return cls._instance

    @property
    def engine(self) -> AerodynamicInferenceEngine:
        if self._engine is None:
            self._engine = AerodynamicInferenceEngine()
        return self._engine

    def predict(
        self,
        geometry: Union[str, List[List[float]]],
        mach: float,
        reynolds: float,
        aoa_deg: float
    ) -> AerodynamicPrediction:
        """Runs point prediction."""
        return self.engine.predict(geometry=geometry, mach=mach, reynolds=reynolds, aoa_deg=aoa_deg)

    def polar_sweep(
        self,
        geometry: Union[str, List[List[float]]],
        mach: float,
        reynolds: float,
        aoa_start: float = -4.0,
        aoa_end: float = 14.0,
        aoa_step: float = 1.0
    ) -> Dict[str, Any]:
        """Runs polar sweep."""
        return self.engine.predict_polar(
            geometry=geometry,
            mach=mach,
            reynolds=reynolds,
            aoa_start=aoa_start,
            aoa_end=aoa_end,
            aoa_step=aoa_step
        )

    def get_model_status(self) -> Dict[str, Any]:
        """Returns model information and cryptographic checksum."""
        eng = self.engine
        is_ready = eng.model is not None and eng.weights_status == "VERIFIED_CHECKPOINT"
        return {
            "model_id": eng.model.model_id if eng.model else "AeroSurrogateV1",
            "model_version": eng.model.model_version if eng.model else "v1.0-unloaded",
            "is_ready": is_ready,
            "weights_status": eng.weights_status,
            "parameters": eng.model.count_parameters() if eng.model else 0,
            "sha256_checksum": eng.checksum,
            "checkpoint_path": str(eng.checkpoint_path),
            "known_geometries": list(eng.known_geometries.keys()),
            "validity_envelope": eng.uncertainty_engine.validity_envelope if hasattr(eng, "uncertainty_engine") else {}
        }
