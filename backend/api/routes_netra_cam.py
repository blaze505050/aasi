"""
API Routes for Stage 13: Project NETRA Swarm Collision Avoidance Maneuver (CAM) Synthesizer.
===========================================================================================
Provides endpoints for 2D B-plane encounter risk assessment, Foster / Alfriend Pc integrals,
and propellant-optimal impulsive CAM burn optimization.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/netra", tags=["Stage 13: Project NETRA SSA & CAM"])


class NetraEvaluationRequest(BaseModel):
    preset_key: str = Field("RISAT1B_FENGYUN", description="Conjunction scenario preset")
    target_clearance_m: float = Field(3000.0, ge=500.0, le=20000.0, description="Desired post-CAM miss distance clearance in meters")


@router.post("/evaluate")
def evaluate_conjunction(request: NetraEvaluationRequest) -> Dict[str, Any]:
    """
    Evaluates 2D B-plane encounter geometry, Foster Pc integral, and synthesizes optimal CAM burn.
    """
    try:
        return NeuralOperatorAdapter.evaluate_netra_conjunction(
            preset_key=request.preset_key,
            target_clearance_m=request.target_clearance_m,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NETRA CAM evaluation failed: {str(e)}")


@router.get("/presets")
def get_netra_presets() -> Dict[str, Any]:
    """Returns Project NETRA conjunction presets."""
    try:
        return NeuralOperatorAdapter.get_netra_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch NETRA presets: {str(e)}")
