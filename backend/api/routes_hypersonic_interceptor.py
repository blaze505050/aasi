"""
API Routes for Stage 27: Hypersonic Boost-Glide Interceptor Guidance Engine.
=============================================================================
Endpoints for:
- Simulating hypersonic missile engagements against maneuvering glide vehicles (Mach 6 to 12).
- Comparing Differential Game Guidance (DGG / ZEM), APN, and classical Proportional Navigation.
- Tracking closing speeds, structural g-loads, Sutton-Graves stagnation heat flux, and DACS divert pulses.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/interceptor", tags=["Stage 27: Hypersonic Interceptor Guidance Engine"])


class InterceptorSimulateRequest(BaseModel):
    mission_id: str = Field("GLIDE_PHASE_INTERCEPTOR", description="Preset engagement ID")
    guidance_law: str = Field("DIFFERENTIAL_GAME_ZEM", description="Guidance algorithm (DIFFERENTIAL_GAME_ZEM, AUGMENTED_PN, PROPORTIONAL_NAVIGATION)")
    target_evasion: str = Field("SINUSOIDAL_WEAVE", description="Target evasive maneuver (BALLISTIC, SINUSOIDAL_WEAVE, BARREL_ROLL, TERMINAL_PULL_UP)")
    nav_ratio: float = Field(4.2, description="Effective navigation ratio N (3.0 to 6.0)")
    enable_dacs_divert: bool = Field(True, description="Enable terminal Divert and Attitude Control System (DACS) pulse assist")


@router.post("/simulate")
def simulate_interceptor(request: InterceptorSimulateRequest) -> Dict[str, Any]:
    """
    Executes a high-fidelity 3D hypersonic boost-glide target engagement simulation.
    """
    try:
        return NeuralOperatorAdapter.execute_interceptor_simulation(
            mission_id=request.mission_id,
            guidance_law=request.guidance_law,
            target_evasion=request.target_evasion,
            nav_ratio=request.nav_ratio,
            enable_dacs_divert=request.enable_dacs_divert,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hypersonic interceptor simulation failed: {str(e)}")


@router.get("/presets")
def get_interceptor_presets() -> Dict[str, Any]:
    """Returns available hypersonic engagement presets."""
    try:
        return NeuralOperatorAdapter.get_interceptor_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch interceptor presets: {str(e)}")


@router.get("/status")
def get_interceptor_status() -> Dict[str, Any]:
    """Returns the operational status of the Hypersonic Interceptor Guidance Engine."""
    return {
        "status": "OPERATIONAL",
        "supported_guidance_laws": ["DIFFERENTIAL_GAME_ZEM", "AUGMENTED_PN", "PROPORTIONAL_NAVIGATION"],
        "max_mach_engagement": 12.0,
        "max_altitude_km": 100.0,
        "hit_to_kill_criterion_m": 0.65,
    }
