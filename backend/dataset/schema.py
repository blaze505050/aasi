"""
AASI Scalable CFD Dataset Schema.
Defines the comprehensive data structure for aerodynamic CFD records, flow fields, and provenance.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class GeometrySpec(BaseModel):
    geometry_id: str
    geometry_hash: str
    coordinates: Optional[List[List[float]]] = None
    parameterization: Optional[Dict[str, Any]] = None
    topology: str = "2D_AIRFOIL"


class FlowConditions(BaseModel):
    reynolds: float
    mach: float
    aoa_deg: float
    velocity_ms: Optional[float] = None
    density: Optional[float] = 1.225
    viscosity: Optional[float] = 1.81e-5
    temperature_k: Optional[float] = 288.15


class MeshMetrics(BaseModel):
    cell_count: int
    mesh_quality: Optional[str] = "ASME_VV20_COMPLIANT"
    y_plus: Optional[float] = None
    max_skewness: Optional[float] = None
    max_non_orthogonality: Optional[float] = None
    refinement_level: Optional[int] = 1


class SolverConfig(BaseModel):
    openfoam_version: str = "OpenFOAM-10"
    solver: str = "simpleFoam"
    turbulence_model: str = "kOmegaSST"
    numerical_schemes: Optional[Dict[str, str]] = None
    convergence_criteria: Optional[Dict[str, float]] = None


class SimulationResults(BaseModel):
    cl: Optional[float] = None
    cd: Optional[float] = None
    cm: Optional[float] = None
    cp_distribution: Optional[List[Dict[str, float]]] = None
    residual_history: Optional[Dict[str, List[float]]] = None
    flow_field_artifacts: Optional[Dict[str, str]] = None  # Storage references


class ValidationMetrics(BaseModel):
    physical_validation_status: str = "PASSED"
    mesh_convergence_status: Optional[str] = None
    asme_vv_status: Optional[str] = None
    uncertainty: Optional[Dict[str, float]] = None
    experimental_comparison: Optional[Dict[str, Any]] = None


class ProvenanceMetadata(BaseModel):
    case_hash: str
    solver_hash: Optional[str] = None
    runtime_metadata: Optional[Dict[str, Any]] = None
    merkle_provenance_root: str
    reproduction_bundle_id: Optional[str] = None
    epistemic_source: str = "DATABASE_REAL"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CFDRecord(BaseModel):
    """Full comprehensive CFD aerodynamic dataset record."""
    record_id: str
    dataset_name: str
    geometry: GeometrySpec
    flow: FlowConditions
    mesh: MeshMetrics
    solver: SolverConfig
    results: SimulationResults
    validation: ValidationMetrics
    provenance: ProvenanceMetadata
