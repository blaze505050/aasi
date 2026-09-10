"""
AASI Active Learning & Uncertainty-Driven Simulation Dispatch.

Evaluates surrogate prediction uncertainty across aerodynamic condition envelopes,
identifies under-sampled weak regions, and proposes targeted simulation cases.
"""

from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field


class ActiveLearningCandidate(BaseModel):
    candidate_id: str
    geometry: str
    mach: float
    reynolds: float
    aoa_deg: float
    estimated_uncertainty: float  # 0.0 to 1.0
    sampling_priority: str        # "HIGH", "MEDIUM", "LOW"
    recommendation_reason: str


class ActiveLearningEngine:
    """Recommends targeted CFD simulation runs to optimize surrogate retrain efficiency."""

    @classmethod
    def identify_sampling_candidates(
        cls,
        geometry: str,
        existing_training_points: List[Dict[str, float]],
        mach_grid: List[float] = [0.15, 0.30, 0.45, 0.60],
        aoa_grid: List[float] = [-4.0, 0.0, 4.0, 8.0, 12.0, 16.0],
        reynolds: float = 3.0e6
    ) -> List[ActiveLearningCandidate]:
        """
        Sweeps parameter grid, measures distance to nearest existing training point,
        and assigns higher uncertainty to isolated points, especially near transonic
        rise (M > 0.5) or stall regime (AoA > 10°).
        """
        candidates = []
        idx = 1

        for m in mach_grid:
            for aoa in aoa_grid:
                # Calculate minimum Euclidean distance in normalized (M, alpha) space
                min_dist = 999.0
                for pt in existing_training_points:
                    dm = (m - pt.get("mach", 0.0)) / 0.5
                    da = (aoa - pt.get("aoa", 0.0)) / 20.0
                    dist = (dm**2 + da**2) ** 0.5
                    if dist < min_dist:
                        min_dist = dist

                # Base uncertainty correlates with point sparseness
                unc = min(1.0, min_dist * 1.8)

                # Physic-informed uncertainty amplification near stall and transonic onset
                if aoa >= 12.0:
                    unc = min(1.0, unc * 1.5)  # Flow separation & stall sensitivity
                if m >= 0.55:
                    unc = min(1.0, unc * 1.4)  # Compressibility shock formation

                priority = "LOW"
                reason = "Well-sampled regime."
                if unc > 0.65:
                    priority = "HIGH"
                    reason = "Critical under-sampled region with high aerodynamic nonlinearity."
                elif unc > 0.35:
                    priority = "MEDIUM"
                    reason = "Moderate distance to nearest high-fidelity benchmark."

                if priority in ["HIGH", "MEDIUM"]:
                    candidates.append(ActiveLearningCandidate(
                        candidate_id=f"AL-CAND-{geometry.replace(' ', '')}-{idx:03d}",
                        geometry=geometry,
                        mach=m,
                        reynolds=reynolds,
                        aoa_deg=aoa,
                        estimated_uncertainty=round(unc, 3),
                        sampling_priority=priority,
                        recommendation_reason=reason
                    ))
                    idx += 1

        # Sort highest uncertainty first
        candidates.sort(key=lambda c: c.estimated_uncertainty, reverse=True)
        return candidates
