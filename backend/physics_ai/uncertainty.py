"""
AASI Epistemic Uncertainty Quantification and Out-of-Distribution (OOD) Engine.

Evaluates:
- Distance to training manifold in normalized [Mach, log10(Re), AoA] space.
- Nearest-neighbor density estimation.
- OOD score and domain classification (IN_DOMAIN, EXTRAPOLATION_NEAR_BOUNDARY, SURROGATE_OUT_OF_DOMAIN).
- Expected standard deviation uncertainty bounds on CL, CD, CM.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from backend.physics_ai.schemas import DomainStatusEnum, UncertaintyMetrics


class EpistemicUncertaintyEngine:
    """Computes distribution distance, density, and uncertainty bounds."""

    def __init__(
        self,
        training_conditions: np.ndarray,
        validity_envelope: Optional[Dict[str, List[float]]] = None,
        base_residuals: Optional[Dict[str, float]] = None
    ):
        # training_conditions: normalized [N, 3] matrix
        self.training_points = np.copy(training_conditions)
        self.centroid = np.mean(training_conditions, axis=0)
        self.cov = np.cov(training_conditions, rowvar=False) + np.eye(training_conditions.shape[1]) * 1e-4
        self.inv_cov = np.linalg.pinv(self.cov)

        self.validity_envelope = validity_envelope or {
            "mach": [0.05, 0.40],
            "reynolds": [5.0e5, 6.0e6],
            "aoa_deg": [-8.0, 18.0]
        }
        self.base_residuals = base_residuals or {"cl": 0.015, "cd": 0.0012, "cm": 0.008}

    def evaluate_uncertainty(
        self,
        norm_cond: np.ndarray,
        raw_mach: float,
        raw_reynolds: float,
        raw_aoa: float
    ) -> Tuple[DomainStatusEnum, UncertaintyMetrics]:
        """
        Evaluates input point against validity envelope and training distribution.
        """
        # 1. Hard validity envelope check
        mach_min, mach_max = self.validity_envelope["mach"]
        re_min, re_max = self.validity_envelope["reynolds"]
        aoa_min, aoa_max = self.validity_envelope["aoa_deg"]

        is_outside_envelope = (
            raw_mach < mach_min or raw_mach > mach_max or
            raw_reynolds < re_min or raw_reynolds > re_max or
            raw_aoa < aoa_min or raw_aoa > aoa_max
        )

        # 2. Mahalanobis distance in normalized feature space
        diff = norm_cond - self.centroid
        dist_sq = float(np.dot(np.dot(diff, self.inv_cov), diff))
        mahal_dist = float(np.sqrt(max(0.0, dist_sq)))

        # 3. Nearest neighbor distance
        dists_to_all = np.linalg.norm(self.training_points - norm_cond, axis=1)
        nn_dist = float(np.min(dists_to_all))
        # Density score in [0, 1]
        density = float(np.exp(-nn_dist * 1.5))

        # 4. Out-of-Distribution score
        ood_score = round(max(0.0, mahal_dist * 0.4 + nn_dist * 0.6), 3)

        # 5. Domain Status Classification
        if is_outside_envelope or ood_score > 3.0:
            domain_status = DomainStatusEnum.SURROGATE_OUT_OF_DOMAIN
            confidence_level = "OOD"
            confidence_score = round(max(0.05, 1.0 / (1.0 + ood_score)), 3)
            uncertainty_mult = 4.0
        elif ood_score > 1.8 or abs(raw_aoa) > 12.0 or raw_mach > 0.35:
            domain_status = DomainStatusEnum.EXTRAPOLATION_NEAR_BOUNDARY
            confidence_level = "MEDIUM"
            confidence_score = round(max(0.35, 1.0 / (1.0 + 0.5 * ood_score)), 3)
            uncertainty_mult = 2.0
        else:
            domain_status = DomainStatusEnum.IN_DOMAIN
            confidence_level = "HIGH"
            confidence_score = round(min(0.98, max(0.70, 1.0 - (ood_score * 0.1))), 3)
            uncertainty_mult = 1.0

        metrics = UncertaintyMetrics(
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            ood_score=ood_score,
            feature_distance=round(mahal_dist, 3),
            nearest_neighbor_density=round(density, 3),
            cl_uncertainty=round(self.base_residuals["cl"] * uncertainty_mult, 4),
            cd_uncertainty=round(self.base_residuals["cd"] * uncertainty_mult, 5),
            cm_uncertainty=round(self.base_residuals["cm"] * uncertainty_mult, 4),
        )

        return domain_status, metrics
