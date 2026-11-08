"""
API Routes for Stage 17: Cryogenic & Rotating Detonation Engine (RDE) Propulsion Digital Twin.
=============================================================================================
Provides endpoints for Chapman-Jouguet supersonic detonation modeling, pressure-gain combustion
analysis, annular wave frequency simulation, and regenerative cooling verification.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/rde", tags=["Stage 17: Cryogenic RDE Propulsion Digital Twin"])


class RdeSimulationRequest(BaseModel):
    preset_key: str = Field("ISRO_CE20_HYDROLOX", description="Propellant and engine preset key")
    injection_pressure_bar: float = Field(40.0, ge=10.0, le=150.0, description="Chamber injection pressure in bar")
    mass_flow_kg_s: float = Field(38.0, ge=2.0, le=1200.0, description="Total propellant mass flow rate in kg/s")
    number_of_waves: int = Field(2, ge=1, le=5, description="Number of co-rotating detonation waves")
    chamber_diameter_mm: float = Field(180.0, ge=50.0, le=600.0, description="Chamber outer diameter in mm")
    annulus_gap_mm: float = Field(9.0, ge=3.0, le=30.0, description="Combustor annulus radial gap in mm")


@router.post("/simulate")
def simulate_rde_propulsion(request: RdeSimulationRequest) -> Dict[str, Any]:
    """
    Simulates rotating detonation wave dynamics, pressure gain, Isp advantage, and thermal state.
    """
    try:
        return NeuralOperatorAdapter.simulate_rde_digital_twin(
            preset_key=request.preset_key,
            injection_pressure_bar=request.injection_pressure_bar,
            mass_flow_kg_s=request.mass_flow_kg_s,
            number_of_waves=request.number_of_waves,
            chamber_diameter_mm=request.chamber_diameter_mm,
            annulus_gap_mm=request.annulus_gap_mm,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RDE simulation failed: {str(e)}")


@router.get("/presets")
def get_rde_presets() -> Dict[str, Any]:
    """Returns RDE propulsion presets."""
    try:
        return NeuralOperatorAdapter.get_rde_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch RDE presets: {str(e)}")
