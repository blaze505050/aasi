"""Condition matching engine with tolerance evaluation, domain boundary checking, and interpolation candidacy."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
from .models import ConditionMatchStatus, NormalizedConditions


class ConditionMatchingEngine:
    """Matches query conditions against registered experimental polars, CFD databases, and surrogate envelopes."""

    def __init__(
        self,
        exact_mach_tol: float = 0.01,
        near_mach_tol: float = 0.05,
        exact_re_rel_tol: float = 0.05,
        near_re_rel_tol: float = 0.25,
        exact_aoa_tol: float = 0.1,
        near_aoa_tol: float = 0.5,
    ):
        self.exact_mach_tol = exact_mach_tol
        self.near_mach_tol = near_mach_tol
        self.exact_re_rel_tol = exact_re_rel_tol
        self.near_re_rel_tol = near_re_rel_tol
        self.exact_aoa_tol = exact_aoa_tol
        self.near_aoa_tol = near_aoa_tol

    def evaluate_point_match(
        self,
        query: NormalizedConditions,
        target_mach: Optional[float],
        target_reynolds: Optional[float],
        target_aoa: Optional[float],
        domain_envelope: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> Tuple[ConditionMatchStatus, Dict[str, float]]:
        """Evaluate match quality between query conditions and a reference point or dataset envelope."""
        discrepancies: Dict[str, float] = {}

        # 1. First check if outside validation domain envelope
        if domain_envelope:
            if query.mach is not None and "mach" in domain_envelope:
                min_m, max_m = domain_envelope["mach"]
                if query.mach < min_m or query.mach > max_m:
                    discrepancies["mach_out_of_domain"] = query.mach
                    return ConditionMatchStatus.OUTSIDE_VALIDATION_DOMAIN, discrepancies

            if query.reynolds is not None and "reynolds" in domain_envelope:
                min_re, max_re = domain_envelope["reynolds"]
                if query.reynolds < min_re or query.reynolds > max_re:
                    discrepancies["reynolds_out_of_domain"] = query.reynolds
                    return ConditionMatchStatus.OUTSIDE_VALIDATION_DOMAIN, discrepancies

            if query.aoa_deg is not None and "aoa_deg" in domain_envelope:
                min_a, max_a = domain_envelope["aoa_deg"]
                if query.aoa_deg < min_a or query.aoa_deg > max_a:
                    discrepancies["aoa_out_of_domain"] = query.aoa_deg
                    return ConditionMatchStatus.OUTSIDE_VALIDATION_DOMAIN, discrepancies

        # 2. Check individual dimension matches
        is_exact = True
        is_near = True

        # Mach evaluation
        if query.mach is not None and target_mach is not None:
            m_diff = abs(query.mach - target_mach)
            discrepancies["delta_mach"] = m_diff
            if m_diff > self.exact_mach_tol:
                is_exact = False
            if m_diff > self.near_mach_tol:
                is_near = False

        # Reynolds evaluation
        if query.reynolds is not None and target_reynolds is not None and target_reynolds > 0:
            re_rel = abs(query.reynolds - target_reynolds) / target_reynolds
            discrepancies["delta_re_rel"] = re_rel
            if re_rel > self.exact_re_rel_tol:
                is_exact = False
            if re_rel > self.near_re_rel_tol:
                is_near = False

        # AoA evaluation
        if query.aoa_deg is not None and target_aoa is not None:
            a_diff = abs(query.aoa_deg - target_aoa)
            discrepancies["delta_aoa_deg"] = a_diff
            if a_diff > self.exact_aoa_tol:
                is_exact = False
            if a_diff > self.near_aoa_tol:
                is_near = False

        if is_exact:
            return ConditionMatchStatus.EXACT_MATCH, discrepancies
        elif is_near:
            return ConditionMatchStatus.NEAR_MATCH, discrepancies
        else:
            return ConditionMatchStatus.NO_MATCH, discrepancies

    def find_interpolation_candidates(
        self,
        target_aoa: float,
        data_points: List[Dict[str, Any]],
        aoa_key: str = "aoa",
    ) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Find two bounding data points if the requested condition lies strictly between them.

        Note: AASI does NOT interpolate automatically without explicit user/dataset permission.
        """
        sorted_points = sorted(
            [pt for pt in data_points if aoa_key in pt and pt[aoa_key] is not None],
            key=lambda x: float(x[aoa_key]),
        )

        lower_bound = None
        upper_bound = None

        for pt in sorted_points:
            pt_val = float(pt[aoa_key])
            if pt_val < target_aoa:
                lower_bound = pt
            elif pt_val > target_aoa:
                upper_bound = pt
                break

        if lower_bound and upper_bound:
            return lower_bound, upper_bound
        return None
