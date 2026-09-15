"""
AASI Fidelity Decision Engine.
Decides whether existing CFD, analytical models, surrogate operators, or new CFD simulations are needed.
Uses distance-to-training-data and epistemic uncertainty.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class FidelityLevel(str, Enum):
    DATABASE_MATCH = "DATABASE_MATCH"
    ANALYTICAL_APPROXIMATION = "ANALYTICAL_APPROXIMATION"
    SURROGATE_INFERENCE = "SURROGATE_INFERENCE"
    NEW_CFD_REQUIRED = "NEW_CFD_REQUIRED"
    MULTI_FIDELITY_COMPARISON = "MULTI_FIDELITY_COMPARISON"


class FidelityDecision(BaseModel):
    """Transparent, unhidden fidelity determination."""
    selected_fidelity: FidelityLevel
    is_new_cfd_required: bool
    database_distance: float
    database_match_quality: str   # "HIGH", "MEDIUM", "LOW", "NONE"
    surrogate_uncertainty: float
    uncertainty_quality: str      # "LOW", "MEDIUM", "HIGH"
    rationale: str
    recommended_backend: str      # "COLAB", "LOCAL_OPENFOAM", "DATABASE"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FidelityDecisionEngine:
    """
    Evaluates empirical distance and epistemic uncertainty to decide solver routing.
    """

    UNCERTAINTY_THRESHOLD_HIGH = 0.25
    DATABASE_DISTANCE_THRESHOLD_HIGH = 0.35

    @classmethod
    def evaluate(
        cls,
        geometry: str,
        alpha_deg: float,
        reynolds: float,
        mach: float,
        database_matches: Optional[list] = None,
        surrogate_uncertainty: float = 0.08,
        user_fidelity_req: str = "adaptive",
    ) -> FidelityDecision:
        """
        Determines the optimal scientific fidelity tier based on empirical gaps.
        """
        # 1. Evaluate database distance
        best_match_distance = 1.0
        if database_matches and len(database_matches) > 0:
            best_match_distance = database_matches[0].get("distance", 1.0)
        else:
            # Baseline heuristic: if common NACA 0012 / 4412 at standard Re=3M and alpha in [-4, 12]
            geom_upper = geometry.upper()
            if "0012" in geom_upper and 1e6 <= reynolds <= 6e6 and -4 <= alpha_deg <= 12:
                best_match_distance = 0.02
            elif "4412" in geom_upper and 1e6 <= reynolds <= 6e6 and -4 <= alpha_deg <= 10:
                best_match_distance = 0.04
            elif "6409" in geom_upper and 1e6 <= reynolds <= 4e6 and 0 <= alpha_deg <= 10:
                best_match_distance = 0.08
            else:
                best_match_distance = 0.55

        # Classify database match quality
        if best_match_distance < 0.05:
            db_quality = "HIGH"
        elif best_match_distance < 0.20:
            db_quality = "MEDIUM"
        elif best_match_distance < 0.50:
            db_quality = "LOW"
        else:
            db_quality = "NONE"

        # Classify surrogate uncertainty
        if surrogate_uncertainty < 0.12:
            unc_quality = "LOW"
        elif surrogate_uncertainty < cls.UNCERTAINTY_THRESHOLD_HIGH:
            unc_quality = "MEDIUM"
        else:
            unc_quality = "HIGH"

        # Explicit user requirement overrides
        if user_fidelity_req in ["live_cfd", "new_cfd"]:
            return FidelityDecision(
                selected_fidelity=FidelityLevel.NEW_CFD_REQUIRED,
                is_new_cfd_required=True,
                database_distance=best_match_distance,
                database_match_quality=db_quality,
                surrogate_uncertainty=surrogate_uncertainty,
                uncertainty_quality=unc_quality,
                rationale="User explicitly requested new live numerical CFD simulation.",
                recommended_backend="COLAB",
            )

        if user_fidelity_req == "adaptive_validation":
            return FidelityDecision(
                selected_fidelity=FidelityLevel.MULTI_FIDELITY_COMPARISON,
                is_new_cfd_required=True,
                database_distance=best_match_distance,
                database_match_quality=db_quality,
                surrogate_uncertainty=surrogate_uncertainty,
                uncertainty_quality=unc_quality,
                rationale="Adaptive validation requested: comparing surrogate prediction against high-fidelity CFD and literature polars.",
                recommended_backend="COLAB",
            )

        # Autonomous Decision Logic:
        # If database match is HIGH and uncertainty is LOW -> Answer from existing verified CFD / surrogate
        if db_quality == "HIGH" and unc_quality == "LOW":
            return FidelityDecision(
                selected_fidelity=FidelityLevel.DATABASE_MATCH,
                is_new_cfd_required=False,
                database_distance=best_match_distance,
                database_match_quality=db_quality,
                surrogate_uncertainty=surrogate_uncertainty,
                uncertainty_quality=unc_quality,
                rationale="DATABASE MATCH = HIGH, SURROGATE UNCERTAINTY = LOW. Pre-existing verified CFD and surrogate are trustworthy. New CFD not required.",
                recommended_backend="DATABASE",
            )

        # If surrogate uncertainty is HIGH or database match is LOW/NONE -> New CFD required
        if unc_quality == "HIGH" or db_quality in ["LOW", "NONE"] or abs(alpha_deg) > 12.0:
            return FidelityDecision(
                selected_fidelity=FidelityLevel.NEW_CFD_REQUIRED,
                is_new_cfd_required=True,
                database_distance=best_match_distance,
                database_match_quality=db_quality,
                surrogate_uncertainty=surrogate_uncertainty,
                uncertainty_quality=unc_quality,
                rationale="DATABASE MATCH = LOW / SURROGATE UNCERTAINTY = HIGH (high AoA or novel geometry). New physical CFD simulation is required.",
                recommended_backend="COLAB",
            )

        # Moderate uncertainty -> Surrogate inference with confidence intervals
        return FidelityDecision(
            selected_fidelity=FidelityLevel.SURROGATE_INFERENCE,
            is_new_cfd_required=False,
            database_distance=best_match_distance,
            database_match_quality=db_quality,
            surrogate_uncertainty=surrogate_uncertainty,
            uncertainty_quality=unc_quality,
            rationale="Surrogate operator uncertainty is within acceptable operational tolerance. Answering via AeroSurrogateV1 with epistemic bounds.",
            recommended_backend="DATABASE",
        )
