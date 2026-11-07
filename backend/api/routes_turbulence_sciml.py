"""
AASI API: Stage 3 High-Reynolds Turbulence SciML Closure (TBNN & Lumley Realizability).
Exposes Pope's 10-tensor integrity basis evaluation, Schumann & Lumley realizability projection,
boundary layer marching with Menter k-omega SST coupling, and NASA TMR / ERCOFTAC benchmark validation.
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
    TURBULENCE_BENCHMARKS,
)

router = APIRouter(prefix="/aero/turbulence", tags=["Stage 3 High-Reynolds Turbulence SciML Closure"])


class TBNNEvaluateRequest(BaseModel):
    velocity_gradient: List[List[float]] = Field(
        default=[[0.0, 1500.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        description="3x3 velocity gradient tensor dUi/dxj (1/s)",
    )
    turbulent_kinetic_energy_k: float = Field(
        default=25.0,
        gt=0.0,
        description="Turbulent kinetic energy k (m^2/s^2)",
    )
    specific_dissipation_omega: float = Field(
        default=1200.0,
        gt=0.0,
        description="Specific dissipation rate omega (1/s)",
    )
    enforce_lumley_realizability: bool = Field(
        default=True,
        description="Whether to project unphysical Reynolds stress states onto Lumley triangle boundary",
    )


class BoundaryLayerSolveRequest(BaseModel):
    airfoil: str = Field(default="RAE 2822", description="Airfoil profile name")
    reynolds: float = Field(default=6.5e6, ge=1e4, le=1e8, description="Reynolds number based on chord")
    mach: float = Field(default=0.730, ge=0.05, le=1.20, description="Free-stream Mach number")
    alpha_deg: float = Field(default=3.19, ge=-5.0, le=25.0, description="Angle of attack in degrees")
    num_stations: int = Field(default=60, ge=20, le=150, description="Number of chordwise evaluation stations")


@router.post("/tbnn/evaluate", summary="Evaluate Pope's 10-Tensor Integrity Basis & Lumley Invariants")
async def evaluate_tbnn(req: TBNNEvaluateRequest) -> Dict[str, Any]:
    """
    Evaluates Pope's 10 integrity basis tensors, 5 Cayley-Hamilton invariants,
    and Schumann / Lumley realizability projection for anisotropic Reynolds stress closure.
    """
    try:
        result = NeuralOperatorAdapter.evaluate_tbnn_closure(
            grad_u=req.velocity_gradient,
            k=req.turbulent_kinetic_energy_k,
            omega=req.specific_dissipation_omega,
            enforce_lumley_realizability=req.enforce_lumley_realizability,
        )
        return {
            "status": "SUCCESS",
            "stage": 3,
            "theory": "Pope_10_Tensor_Integrity_Basis_Schumann_Lumley_Realizability",
            "data": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TBNN evaluation failed: {str(exc)}")


@router.post("/boundary-layer", summary="Solve Boundary Layer Marching with Coupled SST & TBNN Anisotropy")
async def solve_turbulent_boundary_layer(req: BoundaryLayerSolveRequest) -> Dict[str, Any]:
    """
    Marches turbulent boundary layer along chord with coupled Menter k-omega SST blending
    and TBNN anisotropic Reynolds stress closure. Detects separation bubble and reattachment points.
    """
    try:
        result = NeuralOperatorAdapter.solve_turbulent_boundary_layer(
            airfoil=req.airfoil,
            reynolds=req.reynolds,
            mach=req.mach,
            alpha_deg=req.alpha_deg,
            num_stations=req.num_stations,
        )
        return {
            "status": "SUCCESS",
            "stage": 3,
            "architecture": "Coupled_Menter_SST_TBNN_Boundary_Layer_Solver",
            "data": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Boundary layer calculation failed: {str(exc)}")


@router.get("/benchmarks", summary="Get NASA TMR and ERCOFTAC Standard Turbulence Benchmarks")
async def get_turbulence_benchmarks() -> Dict[str, Any]:
    """
    Returns NASA TMR Flat Plate, Samuel & Joubert APG, Bachalo-Johnson Bump, and RAE 2822 Case 9 datasets.
    """
    return {
        "status": "SUCCESS",
        "stage": 3,
        "benchmarks": TURBULENCE_BENCHMARKS,
    }

