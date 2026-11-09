"""
Stage 36: Constellation Collision Insurance Risk Underwriting API.
Provides REST endpoints for:
- Actuarial constellation orbital collision underwriting and Solvency II 99.5% VaR/CVaR.
- NASA ORDEM / ESA MASTER debris flux and Poisson collision probabilities.
- Underwriting policy presets for mega-constellations and EO satellites.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter
from aasi_aero_fno.constellation_insurance_engine import INSURANCE_PRESETS

router = APIRouter(prefix="/insurance-risk", tags=["Stage 36: Constellation Collision Insurance & Actuarial Engine"])


class UnderwriteRequest(BaseModel):
    altitude_km: float = Field(default=550.0, ge=300.0, le=1500.0, description="Orbital altitude in km")
    constellation_size: int = Field(default=120, ge=1, le=5000, description="Number of satellites")
    satellite_unit_cost_usd: float = Field(default=1.5e6, ge=1e4, le=1e9, description="Cost per satellite in USD")
    mission_duration_years: float = Field(default=5.0, ge=0.5, le=25.0)
    has_autonomous_avoidance: bool = Field(default=True, description="Onboard autonomous CBF collision avoidance")


class ConjunctionRiskRequest(BaseModel):
    altitude_km: float = Field(default=550.0, ge=300.0, le=1500.0)
    constellation_size: int = Field(default=120, ge=1, le=5000)
    mission_duration_years: float = Field(default=5.0, ge=0.5, le=25.0)
    has_autonomous_avoidance: bool = Field(default=True)


@router.post("/underwrite")
def underwrite_policy(request: UnderwriteRequest) -> Dict[str, Any]:
    """Generates institutional Solvency II actuarial underwriting policy slip and VaR/CVaR."""
    try:
        result = NeuralOperatorAdapter.execute_constellation_underwriting(
            altitude_km=request.altitude_km,
            constellation_size=request.constellation_size,
            satellite_unit_cost_usd=request.satellite_unit_cost_usd,
            mission_duration_years=request.mission_duration_years,
            has_autonomous_avoidance=request.has_autonomous_avoidance,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insurance underwriting failed: {str(e)}")


@router.post("/conjunction-risk")
def calculate_conjunction_risk(request: ConjunctionRiskRequest) -> Dict[str, Any]:
    """Computes orbital debris flux, conjunction rates, and Poisson collision probability."""
    try:
        result = NeuralOperatorAdapter.execute_conjunction_risk_assessment(
            altitude_km=request.altitude_km,
            constellation_size=request.constellation_size,
            mission_duration_years=request.mission_duration_years,
            has_autonomous_avoidance=request.has_autonomous_avoidance,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conjunction risk calculation failed: {str(e)}")


@router.get("/presets")
def get_insurance_presets() -> Dict[str, Any]:
    """Returns standard constellation underwriting presets."""
    return {"status": "success", "data": {"presets": INSURANCE_PRESETS}}
