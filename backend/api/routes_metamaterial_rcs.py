"""
API Routes for Stage 28: Electromagnetic Metamaterial Radar Cross Section (RCS) & Inverse Stealth Synthesizer.
==============================================================================================================
Endpoints for:
- Simulating 360-degree monostatic RCS angular distributions using Physical Optics.
- Evaluating Salisbury screen and metamaterial radar absorbent material (RAM) absorption across frequency bands.
- Validating VLO (Very Low Observable) stealth signatures for 5th/6th generation combat airframes (AMCA).
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/rcs", tags=["Stage 28: Metamaterial RCS & Inverse Stealth Synthesizer"])


class RCSSimulateRequest(BaseModel):
    model_name: str = Field("AMCA_5TH_GEN_STEALTH", description="Airframe model identifier")
    radar_band: str = Field("X_BAND", description="Radar illumination frequency band (S_BAND, C_BAND, X_BAND, KU_BAND)")
    frequency_ghz: float = Field(10.0, description="Center radar illumination frequency in GHz")
    enable_metamaterial_ram: bool = Field(True, description="Enable metamaterial radar absorbent coating")
    ram_thickness_mm: float = Field(2.8, description="Absorbent metamaterial layer thickness in mm")


@router.post("/simulate")
def simulate_rcs(request: RCSSimulateRequest) -> Dict[str, Any]:
    """
    Executes a high-frequency Physical Optics and Impedance Boundary Condition RCS simulation.
    """
    try:
        return NeuralOperatorAdapter.execute_rcs_simulation(
            model_name=request.model_name,
            radar_band=request.radar_band,
            frequency_ghz=request.frequency_ghz,
            enable_metamaterial_ram=request.enable_metamaterial_ram,
            ram_thickness_mm=request.ram_thickness_mm,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RCS simulation failed: {str(e)}")


@router.get("/presets")
def get_rcs_presets() -> Dict[str, Any]:
    """Returns available airframe stealth presets."""
    try:
        return NeuralOperatorAdapter.get_rcs_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch RCS presets: {str(e)}")


@router.get("/status")
def get_rcs_status() -> Dict[str, Any]:
    """Returns the operational status of the Metamaterial RCS Synthesizer."""
    return {
        "status": "OPERATIONAL",
        "solver_method": "PHYSICAL_OPTICS_IBC",
        "supported_bands": ["S_BAND", "C_BAND", "X_BAND", "KU_BAND"],
        "max_angular_resolution_deg": 1.0,
        "vlo_threshold_dbsm": -30.0,
    }
