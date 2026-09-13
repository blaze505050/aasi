"""
AASI Phase 21: Multi-Objective Active Acquisition & Experimental Design Engine.
Governing Rule: Absolute Anti-Fabrication Rule.
Combines epistemic uncertainty, model disagreement, geometry novelty, physics sensitivity,
expected information gain, and computational cost into Pareto-optimal scientific experiment ranking.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass
class AcquisitionCandidate:
    candidate_id: str
    geometry_id: str
    airfoil_name: str
    alpha_deg: float
    reynolds: float
    mach: float
    epistemic_uncertainty: float
    ensemble_disagreement: float
    ood_distance: float
    physics_sensitivity: float
    expected_information_gain: float
    estimated_cost_seconds: float
    total_acquisition_score: float
    selection_rationale: str
    is_pareto_optimal: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "geometry_id": self.geometry_id,
            "airfoil_name": self.airfoil_name,
            "alpha_deg": self.alpha_deg,
            "reynolds": self.reynolds,
            "mach": self.mach,
            "epistemic_uncertainty": round(self.epistemic_uncertainty, 4),
            "ensemble_disagreement": round(self.ensemble_disagreement, 4),
            "ood_distance": round(self.ood_distance, 4),
            "physics_sensitivity": round(self.physics_sensitivity, 4),
            "expected_information_gain": round(self.expected_information_gain, 4),
            "estimated_cost_seconds": round(self.estimated_cost_seconds, 1),
            "total_acquisition_score": round(self.total_acquisition_score, 4),
            "selection_rationale": self.selection_rationale,
            "is_pareto_optimal": self.is_pareto_optimal,
        }


class ActiveAcquisitionEngine:
    """Multi-objective acquisition engine for physical fluid dynamics experimentation."""

    def __init__(
        self,
        weight_uncertainty: float = 0.30,
        weight_disagreement: float = 0.20,
        weight_novelty: float = 0.20,
        weight_sensitivity: float = 0.15,
        weight_eig: float = 0.15,
    ):
        self.w_u = weight_uncertainty
        self.w_div = weight_disagreement
        self.w_d = weight_novelty
        self.w_s = weight_sensitivity
        self.w_eig = weight_eig

    def evaluate_physics_sensitivity(self, alpha_deg: float, camber: float, thickness: float) -> float:
        """
        Evaluate physics sensitivity / gradient proximity to non-linear stall.
        Higher sensitivity near potential stall region (alpha in [10 deg, 18 deg]).
        """
        # Proximity to typical clean stall alpha_stall ~ 12 + 10 * (t/c) deg
        nominal_stall_alpha = 12.0 + 10.0 * thickness
        alpha_diff = abs(alpha_deg - nominal_stall_alpha)
        # Gaussian bell curve centered at stall boundary
        sensitivity = float(np.exp(-0.5 * (alpha_diff / 3.0) ** 2))
        return sensitivity

    def compute_expected_information_gain(
        self, sigma_epistemic: float, ood_dist: float, disagreement: float
    ) -> float:
        """
        EIG proxy: proportional to Shannon entropy reduction of epistemic distribution.
        Delta H ~ 0.5 * log(1 + sigma^2 * d_ood / (sigma_noise^2 + 1e-4))
        """
        sigma_noise = 0.02
        snr = (sigma_epistemic**2 * (1.0 + ood_dist)) / (sigma_noise**2 + 1e-4)
        eig = float(0.5 * np.log1p(snr))
        return eig

    def rank_candidates(
        self,
        candidate_pool: List[Dict[str, Any]],
        training_ood_distances: Dict[str, float],
    ) -> List[AcquisitionCandidate]:
        """
        Score and rank candidate experiments across all criteria.
        """
        if not candidate_pool:
            return []

        # Extract raw arrays for normalization
        raw_u = np.array([c.get("uncertainty", 0.1) for c in candidate_pool], dtype=float)
        raw_div = np.array([c.get("disagreement", 0.05) for c in candidate_pool], dtype=float)
        raw_d = np.array(
            [training_ood_distances.get(c.get("geometry_id"), 1.0) for c in candidate_pool], dtype=float
        )
        raw_s = np.array(
            [
                self.evaluate_physics_sensitivity(
                    c.get("alpha_deg", 0.0),
                    c.get("camber_m", 0.0),
                    c.get("thickness_t", 0.12),
                )
                for c in candidate_pool
            ],
            dtype=float,
        )
        raw_eig = np.array(
            [
                self.compute_expected_information_gain(raw_u[i], raw_d[i], raw_div[i])
                for i in range(len(candidate_pool))
            ],
            dtype=float,
        )

        def normalize(arr: np.ndarray) -> np.ndarray:
            ptp = np.ptp(arr)
            return (arr - np.min(arr)) / ptp if ptp > 1e-8 else np.zeros_like(arr)

        norm_u = normalize(raw_u)
        norm_div = normalize(raw_div)
        norm_d = normalize(raw_d)
        norm_s = normalize(raw_s)
        norm_eig = normalize(raw_eig)

        scores = (
            self.w_u * norm_u
            + self.w_div * norm_div
            + self.w_d * norm_d
            + self.w_s * norm_s
            + self.w_eig * norm_eig
        )

        # Identify Pareto optimal candidates (Uncertainty vs Cost)
        # Cost proxy: higher Reynolds number and higher AoA require more mesh resolution and iterations
        costs = np.array(
            [
                300.0 + (c.get("reynolds", 3e6) / 1e6) * 60.0 + abs(c.get("alpha_deg", 0.0)) * 15.0
                for c in candidate_pool
            ],
            dtype=float,
        )

        candidates: List[AcquisitionCandidate] = []
        for i, c in enumerate(candidate_pool):
            # Formulate clear scientific justification
            reasons = []
            if norm_u[i] > 0.6:
                reasons.append("High epistemic uncertainty in surrogate predictions")
            if norm_s[i] > 0.6:
                reasons.append("High physics sensitivity near potential stall boundary")
            if norm_d[i] > 0.6:
                reasons.append("Novel geometric contour outside existing training hull")
            if norm_div[i] > 0.6:
                reasons.append("Significant surrogate ensemble disagreement")
            if not reasons:
                reasons.append("Balanced exploratory aerodynamic observation")

            rationale = "; ".join(reasons) + "."

            # Pareto check: no other candidate has strictly higher score and strictly lower cost
            is_pareto = True
            for j in range(len(candidate_pool)):
                if scores[j] > scores[i] and costs[j] < costs[i]:
                    is_pareto = False
                    break

            cand = AcquisitionCandidate(
                candidate_id=c.get("candidate_id", f"CAND-{i+1:03d}"),
                geometry_id=c.get("geometry_id", "UNKNOWN"),
                airfoil_name=c.get("airfoil_name", "NACA"),
                alpha_deg=float(c.get("alpha_deg", 0.0)),
                reynolds=float(c.get("reynolds", 3e6)),
                mach=float(c.get("mach", 0.15)),
                epistemic_uncertainty=float(raw_u[i]),
                ensemble_disagreement=float(raw_div[i]),
                ood_distance=float(raw_d[i]),
                physics_sensitivity=float(raw_s[i]),
                expected_information_gain=float(raw_eig[i]),
                estimated_cost_seconds=float(costs[i]),
                total_acquisition_score=float(scores[i]),
                selection_rationale=rationale,
                is_pareto_optimal=is_pareto,
            )
            candidates.append(cand)

        # Sort descending by composite score
        candidates.sort(key=lambda x: x.total_acquisition_score, reverse=True)
        return candidates
