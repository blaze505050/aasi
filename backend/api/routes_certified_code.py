"""
API Routes for Stage 18: Formally Verified DO-178C Level A & ECSS Flight Code Synthesizer.
===========================================================================================
Provides endpoints for deterministic MISRA-C:2012 and Safe-Rust (no_std) code generation,
formal invariance verification proofs in Lean-4, and MC/DC structural coverage dossiers.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/certified-code", tags=["Stage 18: Formally Verified Flight Code Synthesizer"])


class CodeSynthesisRequest(BaseModel):
    preset_id: str = Field("ISRO_GAGANYAAN_CM_DESCENT_RTA", description="Target flight preset ID")
    alpha_max: Optional[float] = Field(None, description="Maximum angle of attack bound in deg")
    nz_max: Optional[float] = Field(None, description="Maximum normal load factor in g")
    u_min: Optional[float] = Field(None, description="Minimum actuator physical saturation limit")
    u_max: Optional[float] = Field(None, description="Maximum actuator physical saturation limit")
    cbf_gamma: Optional[float] = Field(None, description="Control barrier function class-K decay gain")


@router.post("/synthesize")
def synthesize_certified_flight_software(request: CodeSynthesisRequest) -> Dict[str, Any]:
    """
    Synthesizes MISRA-C:2012 code, Safe-Rust no_std firmware, and Lean-4 formal proof certificates.
    """
    try:
        return NeuralOperatorAdapter.synthesize_certified_flight_software(
            preset_id=request.preset_id,
            alpha_max=request.alpha_max,
            nz_max=request.nz_max,
            u_min=request.u_min,
            u_max=request.u_max,
            cbf_gamma=request.cbf_gamma,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flight code synthesis failed: {str(e)}")


@router.get("/presets")
def get_certified_code_presets() -> Dict[str, Any]:
    """Returns available flight certification presets."""
    try:
        return NeuralOperatorAdapter.get_certified_code_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch certification presets: {str(e)}")
