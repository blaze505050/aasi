"""
API Routes for Stage 15: Sovereign Airspace 4D Trajectory Negotiation Engine (AAI C-ATFM).
==========================================================================================
Provides endpoints for multi-flight 4D trajectory conflict detection, wake vortex separation
assurance, Controlled Time of Arrival (CTA) slot optimization, and monsoon weather rerouting.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/catfm", tags=["Stage 15: Sovereign Airspace C-ATFM"])


class CatfmNegotiationRequest(BaseModel):
    scenario_key: str = Field("BENGALURU_VOBL_MONSOON_RUSH", description="C-ATFM scenario preset key")
    enable_cta_optimization: bool = Field(True, description="Enable Controlled Time of Arrival (CTA) runway slot metering")
    enable_weather_avoidance: bool = Field(True, description="Enable convective monsoon weather cell rerouting")
    time_compression: float = Field(1.0, ge=0.1, le=10.0, description="Simulation playback time multiplier")


@router.post("/negotiate")
def negotiate_airspace_trajectories(request: CatfmNegotiationRequest) -> Dict[str, Any]:
    """
    Negotiates conflict-free 4D trajectories across Indian FIR airspace and vertiport networks.
    """
    try:
        return NeuralOperatorAdapter.negotiate_catfm_airspace(
            scenario_key=request.scenario_key,
            enable_cta_optimization=request.enable_cta_optimization,
            enable_weather_avoidance=request.enable_weather_avoidance,
            time_compression=request.time_compression,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"C-ATFM airspace negotiation failed: {str(e)}")


@router.get("/presets")
def get_catfm_presets() -> Dict[str, Any]:
    """Returns C-ATFM scenarios, Indian airports, and ICAO wake vortex separation standards."""
    try:
        return NeuralOperatorAdapter.get_catfm_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch C-ATFM presets: {str(e)}")

