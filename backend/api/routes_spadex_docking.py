"""
API Routes for Stage 12: NavIC Carrier-Phase Relative Orbit Determination & SpaDeX Docking.
===========================================================================================
Provides endpoints for 6-DOF autonomous rendezvous and docking (ARPO),
NavIC LAMBDA carrier-phase integer ambiguity resolution, and approach cone monitoring.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/spadex", tags=["Stage 12: SpaDeX Autonomous Docking"])


class SpaDeXSimulationRequest(BaseModel):
    preset_key: str = Field("SPADEX_NOMINAL_VBAR", description="Docking scenario preset")
    initial_distance_m: float = Field(225.0, ge=1.0, le=5000.0, description="Initial standoff distance in meters")
    approach_corridor_deg: float = Field(15.0, ge=5.0, le=30.0, description="Maximum admissible approach cone half-angle")
    enable_navic_lambda: bool = Field(True, description="Enable NavIC carrier-phase integer ambiguity resolution")
    max_duration_s: float = Field(300.0, ge=10.0, le=1800.0, description="Maximum simulation duration in seconds")
    time_step_s: float = Field(1.0, ge=0.1, le=5.0, description="Simulation integration step size")


@router.post("/simulate")
def simulate_spadex_docking(request: SpaDeXSimulationRequest) -> Dict[str, Any]:
    """
    Simulates 6-DOF relative Clohessy-Wiltshire proximity operations down to 40mm BDS latch entry.
    """
    try:
        return NeuralOperatorAdapter.simulate_spadex_docking(
            preset_key=request.preset_key,
            initial_distance_m=request.initial_distance_m,
            approach_corridor_deg=request.approach_corridor_deg,
            enable_navic_lambda=request.enable_navic_lambda,
            max_duration_s=request.max_duration_s,
            time_step_s=request.time_step_s,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SpaDeX docking simulation failed: {str(e)}")


@router.get("/presets")
def get_spadex_presets() -> Dict[str, Any]:
    """Returns SpaDeX docking scenario presets."""
    try:
        return NeuralOperatorAdapter.get_spadex_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch SpaDeX presets: {str(e)}")
