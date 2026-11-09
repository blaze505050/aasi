"""
Stage 39: FastAPI Routes for Sustainable Aviation Fuel (SAF) & ICAO CORSIA Carbon Twin
========================================================================================
Endpoints:
- POST /api/v1/saf-carbon/evaluate-blend: Evaluates ASTM D7566 physical blend properties
- POST /api/v1/saf-carbon/simulate-mission: Simulates flight mission CO2 and issues ICAO CORSIA certificate
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/saf-carbon", tags=["Stage 39: SAF & ICAO CORSIA Carbon Twin"])


class BlendEvaluationRequest(BaseModel):
    saf_pathway_key: str = Field("HEFA_SPK", description="SAF pathway: HEFA_SPK, PTL_E_KEROSENE, FT_SPK, ATJ_SPK")
    blend_ratio_saf_pct: float = Field(50.0, description="Volume percentage of SAF in blend (0 - 100%)")


class MissionAssessmentRequest(BaseModel):
    flight_distance_km: float = Field(3500.0, description="Flight stage length in km")
    aircraft_type: str = Field("AeroCraft-X40 Sovereign Transport", description="Aircraft designation")
    payload_kg: float = Field(18000.0, description="Payload weight in kg")
    blend_ratio_saf_pct: float = Field(50.0, description="SAF blend percentage (0 - 100%)")
    saf_pathway_key: str = Field("HEFA_SPK", description="SAF pathway key")
    carbon_price_usd_per_tonne: float = Field(48.0, description="CORSIA carbon credit trading price ($/tonne)")


@router.post("/evaluate-blend")
async def evaluate_blend(req: BlendEvaluationRequest) -> Dict[str, Any]:
    try:
        res = NeuralOperatorAdapter.execute_saf_blend_evaluation(
            saf_pathway_key=req.saf_pathway_key,
            blend_ratio_saf_pct=req.blend_ratio_saf_pct,
        )
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SAF blend evaluation error: {str(e)}")


@router.post("/simulate-mission")
async def simulate_flight_mission(req: MissionAssessmentRequest) -> Dict[str, Any]:
    try:
        res = NeuralOperatorAdapter.execute_corsia_mission_assessment(
            flight_distance_km=req.flight_distance_km,
            aircraft_type=req.aircraft_type,
            payload_kg=req.payload_kg,
            blend_ratio_saf_pct=req.blend_ratio_saf_pct,
            saf_pathway_key=req.saf_pathway_key,
            carbon_price_usd_per_tonne=req.carbon_price_usd_per_tonne,
        )
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CORSIA mission simulation error: {str(e)}")
