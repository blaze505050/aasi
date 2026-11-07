"""
AASI API: Stage 7 Fluid-Structure Interaction (FSI) & Transonic Flutter Prediction.
Exposes p-k aeroelastic eigenvalue solver, frequency coalescence, damping crossing (g=0),
transonic dip identification (M=0.85-1.05), and FAR 25.629 / MIL-A-8870C clearance.
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
    AEROELASTIC_BENCHMARKS,
)

router = APIRouter(prefix="/aero/flutter", tags=["Stage 7 FSI & Transonic Flutter"])


class FlutterSolveRequest(BaseModel):
    wing_name: str = Field(default="AGARD 445.6 Standard Aeroelastic Wing", description="Aeroelastic wing configuration")
    mach: float = Field(default=0.90, ge=0.2, le=1.6, description="Freestream Mach number")
    altitude_km: float = Field(default=0.0, ge=0.0, le=25.0, description="Altitude in kilometers")
    semichord_b: float = Field(default=0.279, ge=0.01, le=5.0, description="Reference semichord b = c/2 in meters")
    mass_ratio_mu: float = Field(default=33.2, ge=1.0, le=500.0, description="Aeroelastic mass ratio mu = m / (pi * rho * b^2)")
    omega_h_rad_s: float = Field(default=60.3, ge=1.0, le=1000.0, description="Uncoupled plunge/bending frequency in rad/s")
    omega_alpha_rad_s: float = Field(default=240.0, ge=1.0, le=2000.0, description="Uncoupled pitch/torsion frequency in rad/s")
    v_min: float = Field(default=100.0, ge=10.0, le=500.0, description="Minimum sweep velocity in m/s")
    v_max: float = Field(default=480.0, ge=50.0, le=1200.0, description="Maximum sweep velocity in m/s")
    num_v_steps: int = Field(default=35, ge=15, le=100, description="Number of velocity evaluation stations")


@router.post("/solve", summary="Solve Dynamic Aeroelastic Flutter Stability & V-g / V-f Curves")
async def solve_flutter_boundary(req: FlutterSolveRequest) -> Dict[str, Any]:
    """
    Executes iterative p-k eigenvalue method to detect bending-torsion flutter coalescence,
    flutter speed Vf, flutter dynamic pressure qf, and transonic dip reduction.
    """
    try:
        result = NeuralOperatorAdapter.solve_aeroelastic_flutter(
            wing_name=req.wing_name,
            mach=req.mach,
            altitude_km=req.altitude_km,
            semichord_b=req.semichord_b,
            mass_ratio_mu=req.mass_ratio_mu,
            omega_h_rad_s=req.omega_h_rad_s,
            omega_alpha_rad_s=req.omega_alpha_rad_s,
            v_min=req.v_min,
            v_max=req.v_max,
            num_v_steps=req.num_v_steps,
        )
        return {
            "status": "SUCCESS",
            "stage": 7,
            "architecture": "Iterative_PK_Method_GAF_Aeroelastic_Solver",
            "data": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Aeroelastic flutter calculation failed: {str(exc)}")


@router.get("/benchmarks", summary="Retrieve Aeroelastic Flutter Validation Benchmarks")
async def get_aeroelastic_benchmarks() -> Dict[str, Any]:
    """
    Returns standard aeroelastic benchmark datasets including NASA AGARD 445.6 wing
    transonic dip data and Isogai 2-DOF pitch-plunge nonlinear airfoil benchmark.
    """
    return {
        "status": "SUCCESS",
        "stage": 7,
        "standard": "NASA TM-88358 / AIAA JFM / ASME V&V 20-2009",
        "benchmarks": NeuralOperatorAdapter.get_aeroelastic_benchmarks(),
    }

