"""
API Routes for Stage 23: Magnetohydrodynamic (MHD) Hypersonic Plasma Shielding & Blackout Mitigation.
=====================================================================================================
Provides endpoints for Lorentz force shock standoff distance extension, aerothermal convective heat flux
mitigation, Whistler-mode RF window transmission through hypersonic plasma, and Faraday MHD power generation.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/mhd", tags=["Stage 23: MHD Hypersonic Plasma Shielding"])


class MHDSimulationRequest(BaseModel):
    preset_key: str = Field("ISRO_GAGANYAAN_MHD_REENTRY", description="Target MHD hypersonic shield preset")
    override_magnetic_field_tesla: Optional[float] = Field(None, description="Optional magnetic coil field override [Tesla]")


@router.post("/simulate")
def simulate_mhd_shield(request: MHDSimulationRequest) -> Dict[str, Any]:
    """
    Simulates coupled MHD hypersonic aerothermodynamics, shock standoff, heat flux reduction, and RF window.
    """
    try:
        return NeuralOperatorAdapter.execute_mhd_simulation(
            preset_key=request.preset_key,
            override_magnetic_field_tesla=request.override_magnetic_field_tesla,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MHD shield simulation failed: {str(e)}")


@router.get("/presets")
def get_mhd_presets() -> Dict[str, Any]:
    """Returns available MHD plasma shield presets (Gaganyaan, HGV Shavit, Starship, Venus Probe)."""
    try:
        return NeuralOperatorAdapter.get_mhd_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch MHD presets: {str(e)}")
