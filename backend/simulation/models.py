"""Simulation execution fabric data models and experiment manifest schemas."""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SimulationRunMode(str, Enum):
    """Simulation run mode."""
    DRY_RUN = "DRY_RUN"                      # Validates case dictionaries, mesh, boundary conditions without solver execution
    VALIDATION_RUN = "VALIDATION_RUN"        # Executes small test iteration (10 steps) to verify numerical stability
    FULL_RUN = "FULL_RUN"                    # Full iterative convergence sweep


class SolverAvailability(str, Enum):
    """Host system availability status for scientific solvers."""
    AVAILABLE = "AVAILABLE"                  # Binary found and operational
    NOT_AVAILABLE = "NOT_AVAILABLE"          # Binary missing from host PATH and WSL
    DETECTION_ERROR = "DETECTION_ERROR"      # Detection threw an environment exception (e.g. disk unattached)


class SolverInfo(BaseModel):
    """Metadata describing a scientific solver and its host status."""
    solver_name: str = Field(..., description="Solver name e.g. OpenFOAM, SU2, XFOIL, XFLR5")
    version: Optional[str] = Field(None, description="Installed or targeted version string")
    executable_path: Optional[str] = Field(None, description="Path to binary on host or WSL")
    is_available: bool = Field(False, description="Whether solver is currently executable on this machine")
    status: SolverAvailability = Field(SolverAvailability.NOT_AVAILABLE, description="Availability status")
    supported_domains: List[str] = Field(default_factory=list, description="Supported domains: aerodynamics, thermal, structures")
    supported_physics: List[str] = Field(default_factory=list, description="Supported physics: RANS, LES, Euler, Potential")
    supported_dimensions: List[str] = Field(default_factory=lambda: ["2D"], description="2D, 3D")
    execution_environment: str = Field("host", description="host, wsl2, container")
    detection_diagnostic: Optional[str] = Field(None, description="Diagnostic message explaining availability status")


class SimulationCase(BaseModel):
    """Structured configuration describing a simulation case to be run."""
    case_id: str = Field(..., description="Unique simulation case identifier")
    solver: str = Field("OpenFOAM", description="Target solver e.g. OpenFOAM, SU2, XFOIL")
    geometry: str = Field("NACA 0012", description="Airfoil or CAD geometry")
    mach: float = Field(0.3, description="Freestream Mach number")
    reynolds: float = Field(500000.0, description="Reynolds number")
    aoa_deg: float = Field(8.0, description="Angle of attack in degrees")
    turbulence_model: str = Field("k-omega SST", description="Turbulence closure model")
    mesh_cells: int = Field(16384, description="Nominal cell count")
    run_mode: SimulationRunMode = Field(SimulationRunMode.DRY_RUN, description="DRY_RUN, VALIDATION_RUN, FULL_RUN")
    max_iterations: int = Field(1000, description="Maximum solver iterations")
    convergence_tolerance: float = Field(1e-6, description="Residual convergence tolerance")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional thermodynamic and fluid parameters")


class SimulationManifest(BaseModel):
    """Reproducible experiment manifest tracking all inputs, settings, hashes, and outputs."""
    experiment_id: str = Field(..., description="Unique reproducible experiment identifier")
    solver: str = Field(..., description="Solver name")
    solver_version: str = Field("v2312", description="Solver version")
    geometry: str = Field(..., description="Geometry identifier")
    input_parameters: Dict[str, Any] = Field(..., description="Operating conditions and fluid properties")
    units: Dict[str, str] = Field(default_factory=dict, description="Dimensional units specification")
    mesh_specification: Dict[str, Any] = Field(default_factory=dict, description="Grid topology, resolution, y+ target")
    boundary_conditions: Dict[str, Any] = Field(default_factory=dict, description="Inlet, outlet, wall specifications")
    turbulence_model: str = Field(..., description="Turbulence closure")
    numerical_settings: Dict[str, Any] = Field(default_factory=dict, description="Solvers, relaxation factors, schemes")
    execution_timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    git_revision: str = Field("33325ff", description="Git commit hash under which case was run")
    input_checksum: str = Field(..., description="SHA-256 of all input files")
    output_checksum: Optional[str] = Field(None, description="SHA-256 of output fields / logs")
    run_mode: SimulationRunMode = Field(..., description="DRY_RUN, VALIDATION_RUN, FULL_RUN")
    is_converged: bool = Field(False, description="Whether simulation converged")
    cl: Optional[float] = Field(None, description="Extracted lift coefficient")
    cd: Optional[float] = Field(None, description="Extracted drag coefficient")
    cm: Optional[float] = Field(None, description="Extracted pitching moment coefficient")
    residuals: Dict[str, float] = Field(default_factory=dict, description="Final residual values")
    logs: List[str] = Field(default_factory=list, description="Execution and parser logs")
    result_files: List[str] = Field(default_factory=list, description="Paths to generated solution artifacts")
    result_status: str = Field("PENDING", description="SUCCESS, DRY_RUN_VERIFIED, CONVERGED, DIVERGED, ERROR")
    epistemic_status: str = Field("LOCAL_CFD", description="LOCAL_CFD, UNVALIDATED_CFD, DRY_RUN_VERIFIED")
