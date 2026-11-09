"""
Stage 40: FastAPI Routes for Turbofan Remaining Useful Life (RUL) & Fleet Health Digital Twin
=============================================================================================
Endpoints:
- POST /api/v1/fleet-rul/diagnose-engine: High-bypass degradation, Paris-Erdogan LCF crack growth, Weibull RUL
- GET  /api/v1/fleet-rul/fleet-overview: Commercial fleet overview deck and avoided AOG dollar savings
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/fleet-rul", tags=["Stage 40: Turbofan Fleet RUL & Predictive Maintenance"])


class EngineDiagnosisRequest(BaseModel):
    engine_model_key: str = Field("CFM_LEAP_1A", description="Engine model: CFM_LEAP_1A, GE90_115B, KAVERI_GTX_35VS")
    flight_cycles: int = Field(6800, description="Cumulative flight cycles completed")
    serial_number: str = Field("ESN-LEAP-98421", description="Engine Serial Number (ESN)")


@router.post("/diagnose-engine")
async def diagnose_turbofan(req: EngineDiagnosisRequest) -> Dict[str, Any]:
    try:
        res = NeuralOperatorAdapter.execute_turbofan_diagnosis(
            engine_model_key=req.engine_model_key,
            flight_cycles=req.flight_cycles,
            serial_number=req.serial_number,
        )
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine diagnosis error: {str(e)}")


@router.get("/fleet-overview")
async def get_fleet_health_overview() -> Dict[str, Any]:
    try:
        res = NeuralOperatorAdapter.execute_fleet_health_overview()
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fleet overview error: {str(e)}")
