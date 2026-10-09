"""
AASI Milestone 8: Aerodynamic Surrogate API Router.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Endpoints for fast statistical prediction, extrapolation audits,
anti-CFD epistemic labeling, and active-learning sample suggestion.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.science.surrogate import (
    ActiveLearningSuggestion,
    SurrogatePrediction,
    TrainingEnvelope,
    aero_surrogate,
)

router = APIRouter(prefix="/surrogate", tags=["Aerodynamic Surrogate"])


class SurrogatePredictRequest(BaseModel):
    geometry: str = Field(default="NACA 0012", json_schema_extra={"example": "NACA 0012"})
    alpha_deg: float = Field(default=4.0, json_schema_extra={"example": 4.0})
    reynolds: float = Field(default=3.0e6, json_schema_extra={"example": 3.0e6})
    mach: float = Field(default=0.15, json_schema_extra={"example": 0.15})


class ActiveLearningRequest(BaseModel):
    geometry: str = Field(default="NACA 0012", json_schema_extra={"example": "NACA 0012"})
    n_suggestions: int = Field(default=3, ge=1, le=10)


@router.post("/predict", response_model=SurrogatePrediction, summary="Fast Surrogate Aerodynamic Prediction")
async def predict_aerodynamics(req: SurrogatePredictRequest) -> SurrogatePrediction:
    """
    Generates fast statistical aerodynamic predictions (CL, CD, CM) using scikit-learn.
    Features:
    - Never labels predictions as CFD (epistemic_tier: 'SURROGATE', is_cfd: False).
    - Automatically audits for out-of-distribution extrapolation and emits scientific warning.
    - Includes statistical variance metric.
    """
    return aero_surrogate.predict(
        geometry=req.geometry,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
    )


@router.get("/envelope", response_model=TrainingEnvelope, summary="Get Training Bounding Envelope")
async def get_training_envelope() -> TrainingEnvelope:
    """
    Returns the multi-dimensional parameter bounds (alpha, Re, Mach, geometry)
    of the active surrogate training domain, along with train/val R^2 metrics.
    """
    return aero_surrogate.envelope


@router.get("/active-learning", response_model=List[ActiveLearningSuggestion], summary="Suggest Active Learning Samples (GET)")
async def suggest_samples_get(
    geometry: str = "NACA 0012",
    n_suggestions: int = 3,
) -> List[ActiveLearningSuggestion]:
    """Suggests next aerodynamic sampling points via GET query."""
    return aero_surrogate.suggest_active_learning_samples(
        geometry=geometry,
        n_suggestions=n_suggestions,
    )


@router.post("/active-learning", response_model=List[ActiveLearningSuggestion], summary="Suggest Active Learning Samples")
async def suggest_samples(req: ActiveLearningRequest) -> List[ActiveLearningSuggestion]:
    """
    Suggests next aerodynamic sampling points where surrogate epistemic uncertainty
    or parameter-space sparsity is highest to guide physical CFD experiment planning.
    """
    return aero_surrogate.suggest_active_learning_samples(
        geometry=req.geometry,
        n_suggestions=req.n_suggestions,
    )


@router.post("/retrain", response_model=Dict[str, float], summary="Retrain Surrogate Model")
async def retrain_surrogate() -> Dict[str, float]:
    """
    Retrains the surrogate model on baseline authentic aerodynamic data
    using strict 80/20 train/validation split and returns updated evaluation metrics.
    """
    X, y_cl, y_cd = aero_surrogate._generate_authentic_baseline_data()
    return aero_surrogate.fit(X, y_cl, y_cd, val_ratio=0.20)
