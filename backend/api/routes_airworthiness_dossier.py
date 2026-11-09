"""
Stage 37: FastAPI Routes for Autonomous FAA Part 23/25 & DGCA Airworthiness Dossier Synthesizer
================================================================================================
Endpoints:
- POST /api/v1/airworthiness/airspeeds: Evaluate 14 CFR § 25.335 design airspeeds
- POST /api/v1/airworthiness/pratt-gust: Evaluate 14 CFR § 25.341 discrete Pratt gust loads
- POST /api/v1/airworthiness/synthesize-dossier: Generate tamper-evident certification dossier
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/airworthiness", tags=["Stage 37: Airworthiness Certification & MOC"])


class AirspeedRequest(BaseModel):
    gross_weight_kg: float = Field(45000.0, description="Gross take-off weight in kg")
    wing_area_m2: float = Field(122.4, description="Reference wing planform area in m^2")
    cl_max_clean: float = Field(1.45, description="Clean configuration maximum lift coefficient")
    cl_max_flaps: float = Field(2.20, description="Full flaps maximum lift coefficient")
    altitude_m: float = Field(3000.0, description="Altitude in meters")


class PrattGustRequest(BaseModel):
    gross_weight_kg: float = Field(45000.0, description="Gross weight in kg")
    wing_area_m2: float = Field(122.4, description="Wing area in m^2")
    mean_aerodynamic_chord_m: float = Field(4.15, description="Mean aerodynamic chord in meters")
    cl_alpha_per_rad: float = Field(5.25, description="Wing lift curve slope in 1/rad")
    v_cruise_mps: float = Field(180.0, description="Cruise true airspeed in m/s")
    altitude_m: float = Field(3000.0, description="Altitude in meters")


class DossierSynthesizeRequest(BaseModel):
    aircraft_name: str = Field("AeroCraft-X40 Sovereign Transport", description="Aircraft designation")
    tail_number: str = Field("VT-AASI-001", description="Aircraft registration / tail number")
    gross_weight_kg: float = Field(45000.0, description="Gross weight in kg")
    wing_area_m2: float = Field(122.4, description="Wing area in m^2")
    mean_aerodynamic_chord_m: float = Field(4.15, description="Mean aerodynamic chord in meters")
    cl_max_clean: float = Field(1.45, description="Clean C_L max")
    cl_max_flaps: float = Field(2.20, description="Flaps C_L max")
    cl_alpha_per_rad: float = Field(5.25, description="Wing lift curve slope")
    cruise_altitude_m: float = Field(9500.0, description="Nominal cruise altitude in meters")
    authority_key: str = Field("FAA_PART_25", description="Regulatory authority key: FAA_PART_25, FAA_PART_23, DGCA_CAR_SEC2, EASA_CS_25")


@router.post("/airspeeds")
async def evaluate_airspeeds(req: AirspeedRequest) -> Dict[str, Any]:
    try:
        res = NeuralOperatorAdapter.execute_airworthiness_airspeeds(
            gross_weight_kg=req.gross_weight_kg,
            wing_area_m2=req.wing_area_m2,
            cl_max_clean=req.cl_max_clean,
            cl_max_flaps=req.cl_max_flaps,
            altitude_m=req.altitude_m,
        )
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Airspeed calculation error: {str(e)}")


@router.post("/pratt-gust")
async def evaluate_pratt_gust(req: PrattGustRequest) -> Dict[str, Any]:
    try:
        res = NeuralOperatorAdapter.execute_pratt_gust_analysis(
            gross_weight_kg=req.gross_weight_kg,
            wing_area_m2=req.wing_area_m2,
            mean_aerodynamic_chord_m=req.mean_aerodynamic_chord_m,
            cl_alpha_per_rad=req.cl_alpha_per_rad,
            v_cruise_mps=req.v_cruise_mps,
            altitude_m=req.altitude_m,
        )
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pratt gust calculation error: {str(e)}")


@router.post("/synthesize-dossier")
async def synthesize_airworthiness_dossier(req: DossierSynthesizeRequest) -> Dict[str, Any]:
    try:
        res = NeuralOperatorAdapter.execute_airworthiness_dossier_generation(
            aircraft_name=req.aircraft_name,
            tail_number=req.tail_number,
            gross_weight_kg=req.gross_weight_kg,
            wing_area_m2=req.wing_area_m2,
            mean_aerodynamic_chord_m=req.mean_aerodynamic_chord_m,
            cl_max_clean=req.cl_max_clean,
            cl_max_flaps=req.cl_max_flaps,
            cl_alpha_per_rad=req.cl_alpha_per_rad,
            cruise_altitude_m=req.cruise_altitude_m,
            authority_key=req.authority_key,
        )
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Airworthiness dossier generation error: {str(e)}")
