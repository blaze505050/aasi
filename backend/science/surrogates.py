"""Physics AI neural surrogate model registry and operational envelope validator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from .models import EpistemicStatus, NormalizedConditions, ScientificResult


class SurrogateMetadata(BaseModel):
    """Metadata describing a neural operator or physics-informed surrogate model."""
    model_id: str = Field(..., description="Unique model identifier")
    architecture: str = Field(..., description="AeroGraphNet, MeshGraphNet, FNO, PINO, PINN, DoMINO, PhysicsNeMo")
    training_dataset_id: str = Field(..., description="Dataset ID used for training/supervision")
    training_version: str = Field("v1.0", description="Model training version")
    supported_geometries: List[str] = Field(default_factory=lambda: ["NACA 0012"], description="Supported geometries")
    supported_flow_regimes: List[str] = Field(default_factory=lambda: ["subsonic"], description="Supported flow regimes")
    input_domain: Dict[str, Tuple[float, float]] = Field(
        default_factory=lambda: {
            "mach": (0.1, 0.7),
            "reynolds": (100000.0, 2000000.0),
            "aoa_deg": (-5.0, 12.0),
        },
        description="Declared validated operational envelope [min, max]",
    )
    output_variables: List[str] = Field(default_factory=lambda: ["CD", "CL", "CM"], description="Predicted output fields")
    validation_metrics: Dict[str, float] = Field(default_factory=lambda: {"L2_rel_error": 0.025, "R2": 0.985}, description="Validation accuracy")
    uncertainty_method: str = Field("Ensemble Variance (Deep Ensembles)", description="Method for estimating uncertainty")
    model_checksum: str = Field("sha256-weights-placeholder", description="Cryptographic hash of neural weights")
    status: str = Field("REGISTERED_STUB", description="REGISTERED_STUB, TRAINED, EXPERIMENTAL")


class SurrogateRegistry:
    """Registry managing physics surrogate models and domain envelope validation."""

    def __init__(self):
        self._surrogates: Dict[str, SurrogateMetadata] = {}
        self._seed_surrogates()

    def _seed_surrogates(self):
        self.register(SurrogateMetadata(
            model_id="MODEL-AERO-SURROGATE-V1",
            architecture="Dual-Stream Geometry+Condition Residual GELU Neural Operator",
            training_dataset_id="DATASET-AUTHENTIC-AIRFOILS-V1",
            training_version="v1.0.0",
            supported_geometries=["NACA 0012", "NACA 0009", "NACA 0006", "NACA 2412", "NACA 4412", "Clark Y", "RAE 2822", "naca0012", "naca2412"],
            supported_flow_regimes=["subsonic"],
            input_domain={
                "mach": (0.05, 0.40),
                "reynolds": (500000.0, 6000000.0),
                "aoa_deg": (-8.0, 18.0),
            },
            output_variables=["CL", "CD", "CM"],
            validation_metrics={"cl_rmse": 0.1349, "cd_rmse": 0.00134, "cl_r2": 0.9495, "cd_r2": 0.9250},
            uncertainty_method="Mahalanobis & Nearest-Neighbor Epistemic Quantification",
            model_checksum="bc549596f676c5d336fe33333845c53c6d2c170bce2eb964516c51dc8f4ee433",
            status="TRAINED_AND_VALIDATED"
        ))


    def register(self, surrogate: SurrogateMetadata):
        """Register surrogate model metadata."""
        self._surrogates[surrogate.model_id] = surrogate

    def get(self, model_id: str) -> Optional[SurrogateMetadata]:
        """Retrieve surrogate metadata by ID."""
        return self._surrogates.get(model_id)

    def list_surrogates(self) -> List[SurrogateMetadata]:
        """List all registered surrogates."""
        return list(self._surrogates.values())

    def check_validity_envelope(
        self,
        query: NormalizedConditions,
        model_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[SurrogateMetadata], str]:
        """Check if query conditions fall strictly within declared validation domain.

        Returns (is_valid, surrogate_meta, reason).
        If outside domain: returns (False, surrogate_meta, 'SURROGATE_OUT_OF_DOMAIN: ...').
        """
        candidates = list(self._surrogates.values())
        if model_id:
            candidates = [s for s in candidates if s.model_id == model_id]

        if not candidates:
            return False, None, "NO_SURROGATE_AVAILABLE"

        for s in candidates:
            # Check geometry
            if query.geometry:
                clean_query_geo = query.geometry.replace(" ", "").replace("-", "").lower()
                geo_supported = any(
                    clean_query_geo in g.replace(" ", "").replace("-", "").lower()
                    for g in s.supported_geometries
                )
                if not geo_supported:
                    continue

            # Check domain boundaries
            env = s.input_domain
            if query.mach is not None and "mach" in env:
                min_m, max_m = env["mach"]
                if query.mach < min_m or query.mach > max_m:
                    return False, s, f"SURROGATE_OUT_OF_DOMAIN: Mach {query.mach} outside calibrated range [{min_m}, {max_m}]"

            if query.reynolds is not None and "reynolds" in env:
                min_re, max_re = env["reynolds"]
                if query.reynolds < min_re or query.reynolds > max_re:
                    return False, s, f"SURROGATE_OUT_OF_DOMAIN: Reynolds {query.reynolds:.0f} outside range [{min_re:.0f}, {max_re:.0f}]"

            if query.aoa_deg is not None and "aoa_deg" in env:
                min_a, max_a = env["aoa_deg"]
                if query.aoa_deg < min_a or query.aoa_deg > max_a:
                    return False, s, f"SURROGATE_OUT_OF_DOMAIN: AoA {query.aoa_deg}° outside range [{min_a}°, {max_a}°]"

            # Query lies strictly inside validated envelope
            return True, s, "WITHIN_VALIDATION_DOMAIN"

        return False, candidates[0] if candidates else None, "SURROGATE_NO_MATCHING_GEOMETRY"
