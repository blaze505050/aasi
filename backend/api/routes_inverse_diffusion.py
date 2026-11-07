"""
AASI API: Stage 8 Inverse Generative Diffusion for Shock-Free Supercritical Airframes & Wings.
Exposes score-based reverse SDE sampler conditioned on target Cl*, Mach*, and thickness (t/c)*,
recovering supercritical suction rooftop profiles and eliminating transonic wave drag shock jumps.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Ensure aasi-aero-fno is in path
_pkg_path = Path(__file__).resolve().parent.parent.parent / "aasi-aero-fno"
if str(_pkg_path) not in sys.path:
    sys.path.insert(0, str(_pkg_path))

from backend.adapters.neuraloperator_adapter import (
    NeuralOperatorAdapter,
    INVERSE_DIFFUSION_BENCHMARKS,
)

router = APIRouter(prefix="/aero/diffusion", tags=["Stage 8 Inverse Generative Diffusion"])


class DiffusionSampleRequest(BaseModel):
    target_mach: float = Field(default=0.78, ge=0.50, le=0.92, description="Target freestream Mach number")
    target_cl: float = Field(default=0.70, ge=0.20, le=1.30, description="Target design lift coefficient")
    target_thickness_pct: float = Field(default=12.0, ge=6.0, le=18.0, description="Target maximum thickness ratio (t/c)%")
    guidance_strength: float = Field(default=3.5, ge=0.5, le=10.0, description="Classifier-free / score guidance strength gamma")
    num_diffusion_steps: int = Field(default=50, ge=20, le=100, description="Number of reverse SDE integration steps")
    random_seed: int = Field(default=42, ge=0, le=1000000, description="Stochastic Langevin sampling seed")


@router.post("/sample", summary="Sample Shock-Free Supercritical Airfoil via Inverse Diffusion")
async def sample_shock_free_airfoil(req: DiffusionSampleRequest) -> Dict[str, Any]:
    """
    Executes score-based reverse SDE integration conditioned on target aerodynamic requirements.
    Eliminates wave drag shock discontinuities, generating Whitcomb-style supercritical rooftop profiles.
    """
    try:
        result = NeuralOperatorAdapter.sample_shock_free_airfoil(
            target_mach=req.target_mach,
            target_cl=req.target_cl,
            target_thickness_pct=req.target_thickness_pct,
            guidance_strength=req.guidance_strength,
            num_diffusion_steps=req.num_diffusion_steps,
            random_seed=req.random_seed,
        )
        return {
            "status": "SUCCESS",
            "stage": 8,
            "architecture": "Score_Based_Riemannian_SDE_Supercritical_Sampler",
            "data": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inverse diffusion sampling failed: {str(exc)}")


@router.get("/benchmarks", summary="Retrieve Transonic Supercritical Benchmarks")
async def get_inverse_diffusion_benchmarks() -> Dict[str, Any]:
    """
    Returns standard supercritical airfoil reference benchmarks including RAE 2822 Case 9
    and NASA SC(2)-0714 Whitcomb shock-free wind tunnel validation campaigns.
    """
    return {
        "status": "SUCCESS",
        "stage": 8,
        "standard": "AGARD AR-138 / NASA TP-1981 / ASME V&V 20-2009",
        "benchmarks": NeuralOperatorAdapter.get_inverse_diffusion_benchmarks(),
    }
