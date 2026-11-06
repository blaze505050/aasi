"""
AASI API: Stage 2 Transonic Shock-Capturing Neural Operator (Transolver-3D / FNO-3D).
Exposes high-speed continuous-space inference (0.7 <= M_infty <= 1.25),
Rankine-Hugoniot normal & oblique shock jump condition enforcement,
and AGARD / NASA validation benchmark datasets.
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
    AGARD_BENCHMARKS,
)

router = APIRouter(prefix="/aero/transonic", tags=["Stage 2 Transonic Transolver Neural Operator"])


class TransonicSolveRequest(BaseModel):
    airfoil: str = Field(default="RAE 2822", description="Airfoil geometry name (e.g. RAE 2822, ONERA M6, NACA 0012)")
    mach_infinity: float = Field(default=0.730, ge=0.50, le=1.40, description="Free-stream Mach number M_infty")
    alpha_deg: float = Field(default=3.19, ge=-10.0, le=25.0, description="Angle of attack in degrees")
    reynolds: float = Field(default=6.5e6, ge=1e4, le=1e8, description="Reynolds number")
    num_surface_points: int = Field(default=120, ge=40, le=300, description="Number of cosine-clustered points")
    include_field_grid: bool = Field(default=True, description="Whether to compute 2D volumetric Mach and Cp fields")


@router.post("/solve", summary="Solve Transonic Flowfield with Rankine-Hugoniot Shock Capturing")
async def solve_transonic_flow(req: TransonicSolveRequest) -> Dict[str, Any]:
    """
    Executes continuous-space Transonic Transolver-3D / FNO evaluation in < 15 ms.
    Captures normal shock discontinuity, supersonic expansion bubble, and wave drag.
    """
    try:
        result = NeuralOperatorAdapter.predict_transonic_flow(
            airfoil=req.airfoil,
            mach_infinity=req.mach_infinity,
            alpha_deg=req.alpha_deg,
            reynolds=req.reynolds,
            num_surface_points=req.num_surface_points,
            include_field_grid=req.include_field_grid,
        )
        return {
            "status": "SUCCESS",
            "stage": 2,
            "architecture": "Transolver_3D_RankineHugoniot_Spectral_FNO",
            "data": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transonic solver evaluation failed: {str(exc)}")


@router.get("/benchmarks", summary="Get AGARD AR-138 and NASA Reference Transonic Datasets")
async def get_transonic_benchmarks() -> Dict[str, Any]:
    """
    Returns verified experimental reference cases (RAE 2822 Cases 6, 9, 10; ONERA M6; NACA 0012).
    """
    return {
        "status": "SUCCESS",
        "benchmarks": AGARD_BENCHMARKS,
        "citation": "AGARD Advisory Report AR-138 / NASA TP-1981",
        "verification_standard": "ASME V&V 20-2009",
    }

