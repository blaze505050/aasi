"""
API Routes for Stage 11: High-Precision Orbital Dynamics & Non-Spherical Gravity Field Engine.
=============================================================================================
Provides endpoints for symplectic Hamiltonian orbit propagation, J2-J4 geopotential,
atmospheric drag, SRP with eclipse detection, third-body gravity, and ISRO presets.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/orbital", tags=["Stage 11: Orbital Dynamics"])


class OrbitalPropagationRequest(BaseModel):
    preset_key: Optional[str] = Field("GAGANYAAN_LEO", description="Mission preset (GAGANYAAN_LEO, SPADEX_CHASER, CHANDRAYAAN4_TLI, NAVIC_GEO)")
    semi_major_axis_km: Optional[float] = Field(None, description="Semi-major axis in km")
    eccentricity: Optional[float] = Field(None, description="Orbital eccentricity [0, 1)")
    inclination_deg: Optional[float] = Field(None, description="Orbital inclination in degrees [0, 180]")
    raan_deg: Optional[float] = Field(None, description="Right Ascension of Ascending Node in degrees")
    arg_of_perigee_deg: Optional[float] = Field(None, description="Argument of perigee in degrees")
    true_anomaly_deg: Optional[float] = Field(None, description="Initial true anomaly in degrees")
    duration_hours: float = Field(3.0, ge=0.1, le=48.0, description="Propagation duration in hours")
    time_step_s: float = Field(30.0, ge=5.0, le=300.0, description="Symplectic integration step size in seconds")
    enable_drag: bool = Field(True, description="Enable dynamic upper atmospheric drag")
    enable_srp: bool = Field(True, description="Enable Solar Radiation Pressure with Earth shadow")
    enable_third_body: bool = Field(True, description="Enable Moon and Sun third-body gravitational perturbations")
    enable_relativity: bool = Field(True, description="Enable General Relativistic Schwarzschild acceleration")


@router.post("/propagate")
def propagate_orbit(request: OrbitalPropagationRequest) -> Dict[str, Any]:
    """
    Executes a high-precision 4th-order Symplectic Yoshida orbit propagation
    with non-spherical gravity field (J2, J3, J4, C22, S22).
    """
    try:
        return NeuralOperatorAdapter.propagate_orbit_trajectory(
            preset_key=request.preset_key,
            semi_major_axis_km=request.semi_major_axis_km,
            eccentricity=request.eccentricity,
            inclination_deg=request.inclination_deg,
            raan_deg=request.raan_deg,
            arg_of_perigee_deg=request.arg_of_perigee_deg,
            true_anomaly_deg=request.true_anomaly_deg,
            duration_hours=request.duration_hours,
            time_step_s=request.time_step_s,
            enable_drag=request.drag_enabled if hasattr(request, "drag_enabled") else request.enable_drag,
            enable_srp=request.enable_srp,
            enable_third_body=request.enable_third_body,
            enable_relativity=request.enable_relativity,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orbital propagation failed: {str(e)}")


@router.get("/presets")
def get_presets() -> Dict[str, Any]:
    """Returns official ISRO mission orbital presets."""
    try:
        return NeuralOperatorAdapter.get_orbital_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orbital presets: {str(e)}")
