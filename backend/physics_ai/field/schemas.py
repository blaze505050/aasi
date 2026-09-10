"""
AASI Aerodynamic Flow-Field & Surface Distribution Schemas.

Defines spatial field representations including surface Cp distributions,
wall shear stress, and field evaluation points.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SurfaceCoordinatePoint(BaseModel):
    x_c: float
    y_c: float
    surface: str = "UPPER"  # UPPER, LOWER


class SurfaceFlowPoint(BaseModel):
    x_c: float
    y_c: float
    surface: str  # UPPER, LOWER
    cp: float
    cf: Optional[float] = None
    mach_local: Optional[float] = None


class SurfacePressureDistribution(BaseModel):
    """Complete chordwise surface pressure coefficient distribution."""
    geometry: str
    mach: float
    reynolds: float
    aoa_deg: float
    upper_surface: List[SurfaceFlowPoint] = Field(default_factory=list)
    lower_surface: List[SurfaceFlowPoint] = Field(default_factory=list)
    cp_min: float = 0.0
    cp_max: float = 1.0
    cl_integrated: float = 0.0
    cd_integrated: float = 0.0


class FlowFieldEvaluationGrid(BaseModel):
    """2D planar grid evaluation for flow velocity and pressure."""
    x_coords: List[float]
    y_coords: List[float]
    mach_field: List[List[float]] = Field(default_factory=list)
    pressure_field: List[List[float]] = Field(default_factory=list)
