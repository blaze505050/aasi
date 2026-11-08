"""
API Routes for Stage 24: Neuromorphic Event-Camera Micro-Debris & Asteroid Orbit Determination.
==============================================================================================
Provides endpoints for asynchronous microsecond event stream processing, spatiotemporal
Hough streak extraction, Angles-Only Initial Orbit Determination (IOD), and covariance collapse.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/ssa", tags=["Stage 24: Neuromorphic Event-Camera SSA"])


class SSATrackingRequest(BaseModel):
    preset_key: str = Field("LEO_STARLINK_CONSTELLATION_DEBRIS", description="Target SSA tracking preset")


@router.post("/track")
def track_neuromorphic_debris(request: SSATrackingRequest) -> Dict[str, Any]:
    """
    Simulates asynchronous DVS event stream, extracts hypervelocity streaks, and computes IOD.
    """
    try:
        return NeuralOperatorAdapter.execute_ssa_tracking(preset_key=request.preset_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neuromorphic SSA tracking failed: {str(e)}")


@router.get("/presets")
def get_ssa_presets() -> Dict[str, Any]:
    """Returns available SSA tracking presets (LEO Starlink, ISRO NETRA, Apophis, Lunar Gateway)."""
    try:
        return NeuralOperatorAdapter.get_ssa_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch SSA presets: {str(e)}")
