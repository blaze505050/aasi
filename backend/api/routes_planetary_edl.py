"""
API Routes for Stage 22: Relativistic & Post-Newtonian Planetary EDL with Optical TRN.
======================================================================================
Provides endpoints for Parameterized Post-Newtonian (PPN) general relativistic gravity,
Sutton-Graves stagnation heat flux, guided hypersonic entry corridor, supersonic parachute
deployment, Optical Terrain Relative Navigation (TRN) crater matching, and Landing Hazard Avoidance.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/edl", tags=["Stage 22: Planetary Entry, Descent & Landing (EDL)"])


class PlanetaryEDLRequest(BaseModel):
    preset_key: str = Field("MARS_JEZERO_CRATER_SKYCRANE", description="Target planetary EDL mission preset")
    override_entry_mass_kg: Optional[float] = Field(None, description="Optional entry vehicle mass override [kg]")


@router.post("/simulate")
def simulate_planetary_edl(request: PlanetaryEDLRequest) -> Dict[str, Any]:
    """
    Simulates complete planetary entry, deceleration, parachute, optical TRN, and terminal landing.
    """
    try:
        return NeuralOperatorAdapter.execute_planetary_edl(
            preset_key=request.preset_key,
            override_entry_mass_kg=request.override_entry_mass_kg,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planetary EDL simulation failed: {str(e)}")


@router.get("/presets")
def get_edl_presets() -> Dict[str, Any]:
    """Returns available planetary EDL mission presets (Mars Jezero, Gaganyaan, Venus DAVINCI, Titan Dragonfly)."""
    try:
        return NeuralOperatorAdapter.get_edl_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch EDL presets: {str(e)}")


@router.get("/planets")
def get_planetary_environments() -> Dict[str, Any]:
    """Returns planetary physical parameters, atmosphere scale heights, and surface gravity."""
    try:
        return NeuralOperatorAdapter.get_planetary_environments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch planetary environments: {str(e)}")
