"""
AASI Phase 20 Quantitative Out-of-Distribution (OOD) Engine.

Evaluates performance across 7 distinct evaluation tiers:
1. In-Distribution (ID)
2. Geometry-OOD (Unseen airfoil profiles)
3. Reynolds-OOD (Extrapolated Reynolds numbers)
4. AoA-OOD (Angles of attack outside training envelope)
5. Joint-OOD (Simultaneous geometry and flow shift)
6. Thickness-OOD (Airfoils with t/c outside training distribution)
7. Camber-OOD (Airfoils with camber outside training distribution)

Computes quantitative distance metrics and strictly returns INSUFFICIENT_EVIDENCE
when authentic samples are unavailable.
"""

from __future__ import annotations
import math
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field

from backend.physics_ai.benchmark_models import AeroSurrogateBase
from backend.physics_ai.geometry_representation import GeometryRepresentationEngine, GeometryProfile


class OODTier(str, Enum):
    IN_DISTRIBUTION = "IN_DISTRIBUTION"
    GEOMETRY_OOD = "GEOMETRY_OOD"
    REYNOLDS_OOD = "REYNOLDS_OOD"
    AOA_OOD = "AOA_OOD"
    JOINT_OOD = "JOINT_OOD"
    THICKNESS_OOD = "THICKNESS_OOD"
    CAMBER_OOD = "CAMBER_OOD"


class OODEvaluationResult(BaseModel):
    """Result of an evaluation on a specific OOD tier."""
    tier: OODTier
    status: str  # "EVALUATED" or "INSUFFICIENT_EVIDENCE"
    sample_count: int
    r2: Optional[float] = None
    r2_cl: Optional[float] = None
    r2_cd: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    max_error: Optional[float] = None
    physical_violations: int = 0
    mean_ood_distance: Optional[float] = None
    test_airfoils: List[str] = Field(default_factory=list)
    scientific_interpretation: str = ""


class OODGeneralizationEngine:
    """
    Executes multi-tier OOD evaluations and computes distribution distances.
    """

    def __init__(
        self,
        train_geometries: List[str],
        train_features: np.ndarray,
        train_profiles: Dict[str, GeometryProfile]
    ):
        self.train_geometries = set(train_geometries)
        self.train_mean = np.mean(train_features, axis=0)
        if len(train_features) > 1:
            cov = np.cov(train_features, rowvar=False) + np.eye(train_features.shape[1]) * 1e-4
        else:
            cov = np.eye(train_features.shape[1]) * 1.0
        self.inv_cov = np.linalg.pinv(cov)
        self.train_profiles = train_profiles

    def evaluate_tier(
        self,
        model: AeroSurrogateBase,
        X_test: np.ndarray,
        y_test: np.ndarray,
        tier: OODTier,
        test_airfoils: List[str]
    ) -> OODEvaluationResult:
        """Evaluates model against a specific tier or reports INSUFFICIENT_EVIDENCE."""
        if len(X_test) == 0:
            return OODEvaluationResult(
                tier=tier,
                status="INSUFFICIENT_EVIDENCE",
                sample_count=0,
                scientific_interpretation=f"Zero authentic benchmark cases available for tier {tier.value}."
            )

        # Compute predictions
        preds = model.predict(X_test)
        residuals = y_test - preds
        ss_res = np.sum(residuals ** 2, axis=0)
        ss_tot = np.sum((y_test - np.mean(y_test, axis=0)) ** 2, axis=0)

        # Honest R^2 per dimension without clamping
        r2_dims = np.where(ss_tot > 1e-8, 1.0 - (ss_res / ss_tot), 0.0)
        mean_r2 = float(np.mean(r2_dims))
        rmse = float(np.sqrt(np.mean(residuals ** 2)))
        mae = float(np.mean(np.abs(residuals)))
        max_err = float(np.max(np.abs(residuals)))

        # Physical checks
        violations = int(np.sum(preds[:, 1] < 0.0)) if preds.shape[1] >= 2 else 0

        # Mean Mahalanobis distance
        diff = X_test - self.train_mean
        mahal_dists = np.sqrt(np.maximum(0.0, np.sum((diff @ self.inv_cov) * diff, axis=1)))
        mean_dist = float(np.mean(mahal_dists))

        # Scientific interpretation
        if mean_r2 >= 0.80:
            interp = f"Strong generalization on {tier.value} (R^2={mean_r2:.3f})."
        elif mean_r2 >= 0.0:
            interp = f"Moderate transfer on {tier.value} (R^2={mean_r2:.3f}); degraded from in-distribution."
        else:
            interp = (
                f"Severe out-of-distribution degradation on {tier.value} (R^2={mean_r2:.3f}). "
                f"Model performs worse than the simple sample mean predictor on unseen domain."
            )

        return OODEvaluationResult(
            tier=tier,
            status="EVALUATED",
            sample_count=len(X_test),
            r2=round(mean_r2, 4),
            r2_cl=round(float(r2_dims[0]), 4) if len(r2_dims) > 0 else 0.0,
            r2_cd=round(float(r2_dims[1]), 4) if len(r2_dims) > 1 else 0.0,
            rmse=round(rmse, 4),
            mae=round(mae, 4),
            max_error=round(max_err, 4),
            physical_violations=violations,
            mean_ood_distance=round(mean_dist, 4),
            test_airfoils=list(set(test_airfoils)),
            scientific_interpretation=interp
        )

    def evaluate_all_tiers(
        self,
        model: AeroSurrogateBase,
        tier_data: Dict[OODTier, Tuple[np.ndarray, np.ndarray, List[str]]]
    ) -> Dict[str, OODEvaluationResult]:
        """Runs evaluation across all 7 tiers."""
        results = {}
        for tier in OODTier:
            if tier in tier_data and len(tier_data[tier][0]) > 0:
                X_t, y_t, airfoils = tier_data[tier]
                results[tier.value] = self.evaluate_tier(model, X_t, y_t, tier, airfoils)
            else:
                results[tier.value] = OODEvaluationResult(
                    tier=tier,
                    status="INSUFFICIENT_EVIDENCE",
                    sample_count=0,
                    scientific_interpretation=f"Insufficient authentic cases in current manifest for {tier.value}."
                )
        return results
