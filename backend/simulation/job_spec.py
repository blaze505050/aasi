"""
AASI Canonical CFD Job Specification.

Defines the universal contract between the AASI Scientific Agent,
Active Learning Planner, and computational solvers / user workstations.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import hashlib
import json
from backend.multifidelity.models import FlowConditions


class SolverType(str, Enum):
    OPENFOAM = "openfoam"
    SU2 = "su2"
    XFOIL = "xfoil"
    XFLR5 = "xflr5"


class ExecutionBackend(str, Enum):
    USER_EXECUTED = "USER_EXECUTED"
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"
    HPC = "HPC"


class MeshSpecification(BaseModel):
    topology: str = "C-GRID"
    target_cells: int = 45000
    target_yplus: float = 0.8
    refinement_ratio: float = 1.414
    farfield_chords: float = 25.0
    trailing_edge_cells: int = 32


class PhysicsSpecification(BaseModel):
    compressibility: str = "INCOMPRESSIBLE"  # or COMPRESSIBLE
    turbulence_model: str = "k-omega-SST"     # or Spalart-Allmaras, laminar
    energy_equation: bool = False
    air_model: str = "perfectGas"


class ValidationRequirements(BaseModel):
    residual_convergence_threshold: float = 1e-5
    force_oscillation_limit_pct: float = 0.5
    minimum_iterations: int = 500
    grid_convergence_required: bool = True
    target_gci_pct: float = 2.5


class EstimatedComputeCost(BaseModel):
    cpu_hours: float = 0.5
    ram_mb: int = 1024
    disk_mb: int = 150
    gpu_recommended: bool = False
    complexity_class: str = "MODERATE_2D"  # LIGHT_2D, MODERATE_2D, HEAVY_3D


class CFDJobSpec(BaseModel):
    """Canonical CFD simulation job specification."""
    job_id: str
    objective_id: Optional[str] = None
    geometry: str
    geometry_hash: str
    flow_conditions: FlowConditions
    solver: SolverType
    physics: PhysicsSpecification = Field(default_factory=PhysicsSpecification)
    mesh: MeshSpecification = Field(default_factory=MeshSpecification)
    required_outputs: List[str] = Field(default_factory=lambda: ["CL", "CD", "CM", "CP", "RESIDUALS"])
    validation_requirements: ValidationRequirements = Field(default_factory=ValidationRequirements)
    execution_backend: ExecutionBackend = ExecutionBackend.USER_EXECUTED
    estimated_cost: EstimatedComputeCost = Field(default_factory=EstimatedComputeCost)
    scientific_priority: float = Field(default=1.0, ge=0.0, le=10.0)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provenance_hash: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.provenance_hash:
            payload = f"{self.job_id}:{self.geometry}:{self.flow_conditions.mach}:{self.flow_conditions.aoa_deg}:{self.solver.value}:{self.mesh.target_cells}"
            self.provenance_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
