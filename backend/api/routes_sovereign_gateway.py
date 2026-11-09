"""
Stage 38: FastAPI Routes for Enterprise Sovereign Cloud SaaS Gateway & Token Metering
======================================================================================
Endpoints:
- GET  /api/v1/sovereign-gateway/tenants: Lists enterprise tenants with live token fill
- POST /api/v1/sovereign-gateway/consume-tokens: Token-bucket metering & deduction
- POST /api/v1/sovereign-gateway/export-clearance: Air-gapped ITAR/EAR clearance vault
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/sovereign-gateway", tags=["Stage 38: Sovereign Cloud Gateway & Token Metering"])


class TokenConsumptionRequest(BaseModel):
    tenant_id: str = Field("TENANT-DEFENSE-DRDO", description="Enterprise tenant ID")
    task_type_key: str = Field("SCIML_FNO_INFERENCE", description="Compute task type key")
    user_role_key: str = Field("AERODYNAMICS_SPECIALIST", description="Caller user role")


class ExportClearanceRequest(BaseModel):
    tenant_id: str = Field("TENANT-DEFENSE-DRDO", description="Enterprise tenant ID")
    asset_name: str = Field("Hypersonic_Scramjet_Aero_Polar_Deck_v4.h5", description="Asset filename / ID")
    classification: str = Field("DEFENSE_ITAR_RESTRICTED", description="Export classification string")


@router.get("/tenants")
async def list_tenants() -> Dict[str, Any]:
    try:
        tenants = NeuralOperatorAdapter.execute_gateway_list_tenants()
        return {"status": "success", "data": {"tenants": tenants}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tenants: {str(e)}")


@router.post("/consume-tokens")
async def consume_tokens(req: TokenConsumptionRequest) -> Dict[str, Any]:
    try:
        res = NeuralOperatorAdapter.execute_gateway_token_consumption(
            tenant_id=req.tenant_id,
            task_type_key=req.task_type_key,
            user_role_key=req.user_role_key,
        )
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token consumption error: {str(e)}")


@router.post("/export-clearance")
async def request_export_clearance(req: ExportClearanceRequest) -> Dict[str, Any]:
    try:
        res = NeuralOperatorAdapter.execute_gateway_export_clearance(
            tenant_id=req.tenant_id,
            asset_name=req.asset_name,
            classification=req.classification,
        )
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export clearance error: {str(e)}")
