"""
API Routes for Stage 16: Autonomous Popperian Hypothesis Falsification Engine.
==============================================================================
Provides endpoints for staging multi-agent scientific discovery campaigns,
ASME V&V 20 grid discretization, adversarial parameter corner testing,
and Bayesian epistemic hypothesis corroboration / falsification.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/discovery", tags=["Stage 16: Autonomous Popperian Discovery"])


class PopperianCampaignRequest(BaseModel):
    preset_key: str = Field("SUPERCRITICAL_BUFFET_DELAY", description="Discovery campaign preset key")
    adversarial_rigor: float = Field(1.0, ge=0.5, le=3.0, description="Adversarial parameter challenge intensity")
    enable_adaptive_meshing: bool = Field(True, description="Enable ASME V&V 20 adaptive 3-grid convergence")


@router.post("/execute")
def execute_discovery_campaign(request: PopperianCampaignRequest) -> Dict[str, Any]:
    """
    Executes end-to-end multi-agent Popperian scientific discovery loop.
    """
    try:
        return NeuralOperatorAdapter.execute_popperian_discovery(
            preset_key=request.preset_key,
            adversarial_rigor=request.adversarial_rigor,
            enable_adaptive_meshing=request.enable_adaptive_meshing,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery campaign execution failed: {str(e)}")


@router.get("/presets")
def get_discovery_presets() -> Dict[str, Any]:
    """Returns scientific hypothesis presets and falsification criteria."""
    try:
        return NeuralOperatorAdapter.get_popperian_discovery_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch discovery presets: {str(e)}")
