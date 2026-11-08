"""
API Routes for Stage 14: Neural Lyapunov Flight Envelope Protection & ASTM F3269-21 RTA.
========================================================================================
Provides endpoints for closed-loop forward invariance verification, Control Barrier Function
evaluation, and ASTM F3269-21 Tri-Level Run-Time Assurance simulation.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/lyapunov", tags=["Stage 14: Neural Lyapunov Flight Envelope Protection"])


class LyapunovSimulationRequest(BaseModel):
    preset_key: str = Field("LCA_TEJAS_COMBAT_MANEUVER", description="Aircraft envelope preset key")
    enable_rta: bool = Field(True, description="Enable ASTM F3269-21 tri-level run-time assurance")
    gust_intensity: float = Field(1.0, ge=0.0, le=3.0, description="Wind gust / microburst severity multiplier")
    duration_s: float = Field(12.0, ge=3.0, le=30.0, description="Simulation duration in seconds")


@router.post("/simulate")
def simulate_neural_lyapunov_envelope(request: LyapunovSimulationRequest) -> Dict[str, Any]:
    """
    Simulates closed-loop flight envelope protection under aggressive neural control demands and microburst gusts.
    """
    try:
        return NeuralOperatorAdapter.simulate_neural_lyapunov_envelope(
            preset_key=request.preset_key,
            enable_rta=request.enable_rta,
            gust_intensity=request.gust_intensity,
            duration_s=request.duration_s,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neural Lyapunov simulation failed: {str(e)}")


@router.get("/presets")
def get_lyapunov_presets() -> Dict[str, Any]:
    """Returns aircraft flight envelope presets."""
    try:
        return NeuralOperatorAdapter.get_lyapunov_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Lyapunov presets: {str(e)}")

