"""
AASI API: Stage 6 Hypersonic Non-Equilibrium Aerothermodynamics (Mach 5 to 25).
Exposes planetary re-entry stagnation heat flux (Fay-Riddell convective & Tauber-Sutton radiative),
Park 7-species reacting chemistry, shock standoff distance, and plasma blackout RF frequency.
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
    HYPERSONIC_BENCHMARKS,
)

router = APIRouter(prefix="/aero/hypersonic", tags=["Stage 6 Hypersonic Aerothermodynamics"])


class HypersonicSolveRequest(BaseModel):
    vehicle_name: str = Field(default="ISRO Gaganyaan Crew Module", description="Re-entry vehicle configuration")
    altitude_km: float = Field(default=65.0, ge=10.0, le=110.0, description="Altitude in kilometers")
    mach: float = Field(default=18.0, ge=4.0, le=35.0, description="Re-entry Mach number")
    nose_radius_m: float = Field(default=1.8, ge=0.05, le=10.0, description="Effective nose radius Rn in meters")
    flight_path_angle_deg: float = Field(default=-1.6, ge=-15.0, le=0.0, description="Inertial flight path angle gamma in degrees")
    reentry_duration_s: float = Field(default=480.0, ge=30.0, le=1800.0, description="Total re-entry heating pulse duration in seconds")


@router.post("/solve", summary="Solve Hypersonic Stagnation Heat Flux, Real Gas Dissociation & Blackout")
async def solve_hypersonic_aerothermodynamics(req: HypersonicSolveRequest) -> Dict[str, Any]:
    """
    Solves non-equilibrium Park 7-species reacting chemistry {O2, N2, O, N, NO, NO+, e-},
    Fay-Riddell catalytic convective heat flux, Tauber-Sutton radiative flux,
    Billig shock standoff distance, and microwave communication blackout frequency.
    """
    try:
        result = NeuralOperatorAdapter.solve_hypersonic_aerothermodynamics(
            vehicle_name=req.vehicle_name,
            altitude_km=req.altitude_km,
            mach=req.mach,
            nose_radius_m=req.nose_radius_m,
            flight_path_angle_deg=req.flight_path_angle_deg,
            reentry_duration_s=req.reentry_duration_s,
        )
        return {
            "status": "SUCCESS",
            "stage": 6,
            "architecture": "Park_7Species_TwoTemperature_FayRiddell_TauberSutton_Solver",
            "data": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Hypersonic aerothermodynamic calculation failed: {str(exc)}")


@router.get("/benchmarks", summary="Get Planetary Re-entry Benchmarks (RAM-C II, SRE-1, Gaganyaan, Apollo 4)")
async def get_hypersonic_benchmarks() -> Dict[str, Any]:
    """
    Returns standard planetary re-entry validation benchmark datasets.
    """
    return {
        "status": "SUCCESS",
        "stage": 6,
        "benchmarks": HYPERSONIC_BENCHMARKS,
    }

