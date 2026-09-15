"""
AASI Aerodynamic Similarity Engine.
Computes geometric, flow condition, and Mahalanobis distances between experiment targets and dataset cases.
"""

import math
from typing import Dict, Any, Optional


class AerodynamicSimilarity:
    """Computes multidimensional aerodynamic distance metrics."""

    @classmethod
    def compute_distance(
        cls,
        target_geom: str,
        target_alpha: float,
        target_re: float,
        target_mach: float,
        candidate_geom: str,
        candidate_alpha: float,
        candidate_re: float,
        candidate_mach: float,
    ) -> float:
        """
        Returns normalized composite distance D >= 0.0.
        D = 0.0 indicates an identical flow and geometry condition.
        """
        # 1. Geometry distance
        geom_dist = 0.0
        tg = target_geom.upper().replace(" ", "")
        cg = candidate_geom.upper().replace(" ", "")
        if tg != cg:
            # Check NACA 4-digit parameter distance if both are NACA
            if tg.startswith("NACA") and cg.startswith("NACA") and len(tg) == 8 and len(cg) == 8:
                camber_diff = abs(int(tg[4]) - int(cg[4])) / 9.0
                thick_diff = abs(int(tg[6:8]) - int(cg[6:8])) / 30.0
                geom_dist = 0.2 + 0.4 * camber_diff + 0.4 * thick_diff
            else:
                geom_dist = 0.8  # Distinct airfoil family

        # 2. AoA distance (normalized by 15 deg operational span)
        alpha_dist = abs(target_alpha - candidate_alpha) / 15.0

        # 3. Reynolds distance (logarithmic scale)
        log_re_target = math.log10(max(target_re, 1e4))
        log_re_cand = math.log10(max(candidate_re, 1e4))
        re_dist = abs(log_re_target - log_re_cand) / 2.0

        # 4. Mach distance
        mach_dist = abs(target_mach - candidate_mach) / 0.3

        # Weighted Euclidean composite distance
        composite_sq = (
            1.5 * (geom_dist ** 2) +
            1.0 * (alpha_dist ** 2) +
            0.5 * (re_dist ** 2) +
            0.5 * (mach_dist ** 2)
        )
        return round(math.sqrt(composite_sq), 4)
