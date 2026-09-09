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
