"""
API Routes for Stage 25: Autonomous Deep Space Optical Communications & Quantum Key Distribution (QKD).
========================================================================================================
Endpoints for:
- Simulating DSOC link budgets, PPM data rates, and atmospheric turbulence / Adaptive Optics Strehl ratio.
- Evaluating Decoy-State BB84 QKD protocol under GLLP formulation (QBER, secure key rates, PNS eavesdropping).
- Simulating Fast Steering Mirror (FSM) fine pointing assembly sub-nanoradian jitter suppression.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/optical-qkd", tags=["Stage 25: Deep Space Optical Communications & QKD"])


class OpticalQKDSimulateRequest(BaseModel):
    mission_id: str = Field("ISRO_LEO_GROUND_QKD", description="Optical QKD mission preset ID")
    custom_params: Optional[Dict[str, Any]] = Field(None, description="Custom mission override parameters")


@router.post("/simulate")
def simulate_optical_qkd(request: OpticalQKDSimulateRequest) -> Dict[str, Any]:
    """
    Simulates optical link budget, adaptive optics Strehl ratio, FSM fine pointing,
    and decoy-state BB84 QKD security.
    """
    try:
        return NeuralOperatorAdapter.execute_optical_qkd_simulation(
            mission_id=request.mission_id,
            custom_params=request.custom_params
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optical QKD simulation failed: {str(e)}")


@router.get("/presets")
def get_optical_qkd_presets() -> Dict[str, Any]:
    """Returns available optical communications and QKD presets."""
    try:
        return NeuralOperatorAdapter.get_optical_qkd_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch optical QKD presets: {str(e)}")


@router.get("/status")
def get_optical_qkd_status() -> Dict[str, Any]:
    """Returns the operational status of the Optical Communications & QKD Engine."""
    return {
        "status": "OPERATIONAL",
        "supported_protocols": ["BB84_3STATE_DECOY", "GLLP_SECURE_BOUND", "PPM_16", "PPM_64", "PPM_256"],
        "fsm_pointing_precision": "sub-nanoradian",
        "detector_quantum_efficiency": 0.75,
        "shor_preskill_qber_threshold_pct": 11.0,
    }
