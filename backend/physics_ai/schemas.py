"""
AASI Physics-AI Schemas.

Pydantic schemas and enums for airfoil samples, geometry representations,
aerodynamic predictions, uncertainty envelopes, and training configurations.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class DomainStatusEnum(str, Enum):
    """Domain classification status for flow condition input."""
    IN_DOMAIN = "IN_DOMAIN"
    EXTRAPOLATION_NEAR_BOUNDARY = "EXTRAPOLATION_NEAR_BOUNDARY"
    SURROGATE_OUT_OF_DOMAIN = "SURROGATE_OUT_OF_DOMAIN"


class ValidationStatusEnum(str, Enum):
    """Scientific validation status of surrogate prediction or model."""
    VALIDATED_ON_TEST_SET = "VALIDATED_ON_TEST_SET"
    EXPERIMENTAL = "EXPERIMENTAL"
    BENCHMARK = "BENCHMARK"
    REJECTED = "REJECTED"


class AerodynamicTarget(BaseModel):
    """Aerodynamic coefficient targets."""
    cl: float = Field(..., description="Lift coefficient CL")
    cd: float = Field(..., description="Drag coefficient CD")
    cm: float = Field(..., description="Quarter-chord pitching moment coefficient CM")


class AirfoilSample(BaseModel):
    """Individual aerodynamic training or evaluation sample."""
    sample_id: str
    dataset_id: str
    source_id: str
    geometry: str
    mach: float
    reynolds: float
    aoa_deg: float
    cl: float
    cd: float
    cm: float
    target: Optional[AerodynamicTarget] = None
    provenance_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GeometryFeatures(BaseModel):
    """Processed airfoil geometric metrics and sanity flags."""
    geometry_name: str
    n_points: int
    max_thickness_ratio: float
    max_camber_ratio: float
    leading_edge_point: List[float]
    trailing_edge_gap: float
    is_closed: bool
    is_symmetric: bool
    quality_flags: List[str] = Field(default_factory=list)


class UncertaintyMetrics(BaseModel):
    """Epistemic uncertainty and distribution density metrics."""
    confidence_level: str = "HIGH"  # HIGH, MEDIUM, LOW, OOD
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    ood_score: float = Field(..., ge=0.0)
    feature_distance: float
    nearest_neighbor_density: float
    cl_uncertainty: float = 0.0
    cd_uncertainty: float = 0.0
    cm_uncertainty: float = 0.0
    is_calibrated: bool = False
    calibration_status: str = "UNCERTAINTY_NOT_CALIBRATED"  # UNCERTAINTY_NOT_CALIBRATED, CONFORMAL_CALIBRATED
    epistemic_tag: str = "SURROGATE — VERIFIED DOMAIN"


class AirfoilGeometryDefinition(BaseModel):
    """Airfoil profile contour definition."""
    geometry_name: str
    coordinates: List[List[float]] = Field(default_factory=list)
    description: Optional[str] = None


class AerodynamicPrediction(BaseModel):
    """First-class scientific prediction produced by AeroSurrogate."""
    model_id: str
    model_version: str
    geometry: str
    mach: float
    reynolds: float
    aoa_deg: float
    cl: float
    cd: float
    cm: float
    uncertainty: UncertaintyMetrics
    domain_status: DomainStatusEnum
    epistemic_tag: str = "SURROGATE — VERIFIED DOMAIN"
    validation_status: ValidationStatusEnum = ValidationStatusEnum.VALIDATED_ON_TEST_SET
    physics_checks: Dict[str, bool] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())



class PolarSweepPoint(BaseModel):
    """A single AoA slice in an aerodynamic polar sweep."""
    aoa_deg: float
    cl: float
    cd: float
    cm: float
    uncertainty: float
    domain_status: str


class PolarSweepResponse(BaseModel):
    """Full aerodynamic polar curve across angle of attack."""
    geometry: str
    mach: float
    reynolds: float
    model_id: str
    model_version: str
    points: List[PolarSweepPoint]


class TrainingRunConfig(BaseModel):
    """Configuration for reproducible surrogate training."""
    training_run_id: str
    model_family: str = "AeroSurrogateV1"
    dataset_id: str = "DATASET-AUTHENTIC-AIRFOILS-V1"
    dataset_version: str = "1.0.0"
    split_version: str = "GEOMETRY_LEVEL_SPLIT_V1"
    seed: int = 42
    epochs: int = 250
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5
    loss_weights: Dict[str, float] = Field(
        default_factory=lambda: {"cl": 1.0, "cd": 5.0, "cm": 2.0}
    )
    hardware: str = "LOCAL_CPU"


class EvaluationMetrics(BaseModel):
    """Comprehensive performance and physics evaluation report."""
    split_name: str
    sample_count: int
    geometry_count: int
    cl_mae: float
    cl_rmse: float
    cl_r2: float
    cd_mae: float
    cd_rmse: float
    cd_r2: float
    cm_mae: float
    cm_rmse: float
    cm_r2: float
    mean_relative_error_pct: float
    physics_violation_count: int
    monotonicity_violations: int
    symmetry_violations: int
    drag_violations: int
