"""
AASI API: Stage 5 Epistemic Uncertainty Quantification & Out-of-Distribution Conformal Prediction.
Exposes Split Conformal Prediction intervals (1 - alpha coverage guarantee),
Mahalanobis latent manifold distance OOD screening, and ASTM F3269-21 Run-Time Assurance (RTA) fallback.
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

from backend.adapters.neuraloperator_adapter import NeuralOperatorAdapter

router = APIRouter(prefix="/aero/conformal", tags=["Stage 5 Epistemic Conformal Uncertainty & RTA"])


class ConformalEvaluateRequest(BaseModel):
    mach: float = Field(default=0.85, ge=0.1, le=5.0, description="Mach number")
    alpha_deg: float = Field(default=2.2, ge=-10.0, le=45.0, description="Angle of attack in degrees")
    reynolds: float = Field(default=6.5e6, ge=1e4, le=1e8, description="Reynolds number")
    confidence_level_pct: float = Field(default=95.0, ge=80.0, le=99.9, description="Target coverage level 1 - alpha in percent")
    thickness_ratio: float = Field(default=0.12, ge=0.01, le=0.30, description="Airfoil thickness-to-chord ratio t/c")
    sweep_deg: float = Field(default=28.0, ge=0.0, le=75.0, description="Leading-edge wing sweep in degrees")


@router.post("/evaluate", summary="Evaluate Split Conformal Prediction Interval & ASTM F3269 RTA Tier")
async def evaluate_conformal_safety(req: ConformalEvaluateRequest) -> Dict[str, Any]:
    """
    Computes rigorous finite-sample coverage intervals P(y in C(x)) >= 1 - alpha
    without Gaussian assumptions. Computes Mahalanobis distance D_M from training manifold.
    Triggers ASTM F3269-21 RTA failsafe if OOD is detected.
    """
    try:
        result = NeuralOperatorAdapter.evaluate_conformal_safety(
            mach=req.mach,
            alpha_deg=req.alpha_deg,
            reynolds=req.reynolds,
            confidence_level_pct=req.confidence_level_pct,
            thickness_ratio=req.thickness_ratio,
            sweep_deg=req.sweep_deg,
        )
        return {
            "status": "SUCCESS",
            "stage": 5,
            "architecture": "Split_Conformal_Prediction_Mahalanobis_ASTM_F3269_RTA",
            "data": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Conformal uncertainty evaluation failed: {str(exc)}")


@router.get("/calibration", summary="Get Conformal Calibration Deck Metrics and Non-conformity Quantiles")
async def get_calibration_deck_summary() -> Dict[str, Any]:
    """
    Returns empirical nonconformity score distribution and verified quantiles (q_90, q_95, q_99).
    """
    try:
        summary = NeuralOperatorAdapter.get_conformal_calibration_summary()
        return {
            "status": "SUCCESS",
            "stage": 5,
            "summary": summary,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch calibration summary: {str(exc)}")
