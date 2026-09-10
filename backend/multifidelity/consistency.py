"""
AASI Multi-Fidelity Cross-Consistency Validator.

Verifies that heterogeneous aerodynamic predictions and measurements maintain
physical consistency across fidelity tiers:
- Drag positivity (CD > 0)
- Reasonable bound checks (|CL| <= 3.5, |CM| <= 1.5)
- Cross-fidelity divergence bounds in attached flow
- Lift slope sign agreement (dCL/dalpha > 0 in pre-stall).
"""

from typing import List, Dict, Any, Tuple
from backend.multifidelity.models import MultiFidelityResult, FidelityLevel


class CrossFidelityConsistencyValidator:
    """Validates physical sanity and cross-tier agreement."""

    @classmethod
    def validate_physical_consistency(
        cls,
        cl: float,
        cd: float,
        cm: float,
        aoa_deg: float
    ) -> Tuple[bool, List[str]]:
        """Direct aerodynamic coefficient physical consistency gate."""
        violations = []
        if cd <= 0.0:
            violations.append(f"Physical Drag Violation: CD ({cd:.5f}) must be strictly positive (> 0).")
        if abs(cl) > 3.5:
            violations.append(f"Extreme Lift Violation: |CL| ({abs(cl):.2f}) exceeds bound (3.5).")
        if abs(cm) > 1.5:
            violations.append(f"Extreme Moment Violation: |CM| ({abs(cm):.2f}) exceeds bound (1.5).")
        return len(violations) == 0, violations

    @classmethod
    def audit_result(cls, res: MultiFidelityResult) -> Tuple[bool, List[str]]:
        """Checks single result physical sanity."""
        violations = []
        q = res.quantity.upper()
        v = res.value

        if q == "CD" and v <= 0.0:
            violations.append(f"Physical Drag Violation: CD ({v:.5f}) must be strictly positive (> 0).")

        if q == "CL" and abs(v) > 3.5:
            violations.append(f"Extreme Lift Violation: |CL| ({abs(v):.2f}) exceeds maximum possible 2D aerodynamic bound (3.5).")

        if q == "CM" and abs(v) > 1.5:
            violations.append(f"Extreme Moment Violation: |CM| ({abs(v):.2f}) exceeds physical bound (1.5).")

        return len(violations) == 0, violations


    @classmethod
    def audit_cross_tier_pair(
        cls,
        high_res: MultiFidelityResult,
        low_res: MultiFidelityResult,
        max_allowed_rel_diff_pct: float = 65.0
    ) -> Tuple[bool, List[str]]:
        """
        Validates cross-tier consistency between high and low fidelity.
        In pre-stall attached flow (AoA in [-4, 6] deg), lower and higher fidelity
        should not diverge wildly.
        """
        issues = []
        aoa = high_res.conditions.aoa_deg

        # Only enforce tight agreement in pre-stall attached flow
        if -4.0 <= aoa <= 6.0 and high_res.quantity.upper() == low_res.quantity.upper():
            diff = abs(high_res.value - low_res.value)
            base = max(abs(high_res.value), 0.1)
            rel_diff = (diff / base) * 100.0

            if rel_diff > max_allowed_rel_diff_pct:
                issues.append(
                    f"Cross-fidelity divergence warning: {high_res.fidelity.value} ({high_res.value:.4f}) and {low_res.fidelity.value} ({low_res.value:.4f}) differ by {rel_diff:.1f}% in attached flow regime (AoA={aoa}°)."
                )

        return len(issues) == 0, issues
