"""
AASI API: Stage 9 Deep Reinforcement Learning Closed-Loop Active Flow Control (AFC).
Exposes ZNMF synthetic jet and DBD plasma actuation, boundary layer reattachment,
dynamic stall delay (> 6 deg), and net coefficient of performance (COP) energy accounting.
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
    FLOW_CONTROL_BENCHMARKS,
)

router = APIRouter(prefix="/aero/afc", tags=["Stage 9 Active Flow Control"])


class AFCEvaluateRequest(BaseModel):
    airfoil: str = Field(default="NACA 0015 Standard Flow Control Section", description="Airfoil section name")
    mach: float = Field(default=0.15, ge=0.05, le=0.60, description="Freestream Mach number")
    reynolds: float = Field(default=1.0e6, ge=1.0e5, le=1.0e7, description="Chord Reynolds number")
    alpha_deg: float = Field(default=16.0, ge=0.0, le=26.0, description="Operating angle of attack in degrees")
    actuator_type: str = Field(default="ZNMF_Synthetic_Jet", description="Actuator category: ZNMF_Synthetic_Jet or DBD_Plasma_Actuator")
    actuation_frequency_f_plus: float = Field(default=1.20, ge=0.2, le=4.0, description="Non-dimensional actuation frequency F+ = f * c / U_infty")
    momentum_coefficient_c_mu: float = Field(default=0.015, ge=0.001, le=0.06, description="Actuator momentum coefficient C_mu")
    slot_location_x_c: float = Field(default=0.12, ge=0.05, le=0.30, description="Chordwise slot position x_slot / c")
    is_afc_active: bool = Field(default=True, description="Enable closed-loop active flow control")


@router.post("/evaluate", summary="Evaluate Closed-Loop Active Flow Control & Stall Suppression")
async def evaluate_flow_control(req: AFCEvaluateRequest) -> Dict[str, Any]:
    """
    Executes closed-loop active flow control simulation. Computes wall shear stress recovery,
    dynamic stall margin extension, and coefficient of performance (COP) energy balance.
    """
    try:
        result = NeuralOperatorAdapter.evaluate_flow_control(
            airfoil=req.airfoil,
            mach=req.mach,
            reynolds=req.reynolds,
            alpha_deg=req.alpha_deg,
            actuator_type=req.actuator_type,
            actuation_frequency_f_plus=req.actuation_frequency_f_plus,
            momentum_coefficient_c_mu=req.momentum_coefficient_c_mu,
            slot_location_x_c=req.slot_location_x_c,
            is_afc_active=req.is_afc_active,
        )
        return {
            "status": "SUCCESS",
            "stage": 9,
            "architecture": "SAC_DeepRL_ZNMF_Synthetic_Jet_ClosedLoop_Controller",
            "data": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Active flow control evaluation failed: {str(exc)}")


@router.get("/benchmarks", summary="Retrieve Flow Control Wind Tunnel Benchmarks")
async def get_flow_control_benchmarks() -> Dict[str, Any]:
    """
    Returns standard flow control wind tunnel benchmarks including Seifert NACA 0015
    and Greenblatt-Wygnanski periodic excitation datasets.
    """
    return {
        "status": "SUCCESS",
        "stage": 9,
        "standard": "AIAA Journal / Prog. Aerospace Sci. / ASME V&V 20-2009",
        "benchmarks": NeuralOperatorAdapter.get_flow_control_benchmarks(),
    }
