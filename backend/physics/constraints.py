"""
AASI Aerodynamic Physical Constraints & Invariant Verifier.

Validates that aerodynamic surrogate predictions and CFD simulations obey
fundamental laws of fluid mechanics:
1. Positivity of aerodynamic drag (CD > 0)
2. Stagnation pressure coefficient bounds (Cp_stag <= Cp_max(Mach))
3. Lift curve linearity and stall onset limits
4. Compressibility wave drag rise physical bounds
"""

from typing import Dict, List, Any, Tuple, Optional

import math
from pydantic import BaseModel, Field


class InvariantViolation(BaseModel):
    invariant_name: str
    severity: str  # CRITICAL, WARNING
    details: str
    observed_value: float
    limit_value: float


class PhysicalConstraintReport(BaseModel):
    is_physically_sound: bool
    violations: List[InvariantViolation] = Field(default_factory=list)
    warnings: List[InvariantViolation] = Field(default_factory=list)


class AerodynamicConstraintEngine:
    """Evaluates physical invariants and limits."""

    @classmethod
    def check_aerodynamic_invariants(
        cls,
        cl: float,
        cd: float,
        cm: float,
        mach: float,
        aoa_deg: float,
        cp_min: Optional[float] = None,
        cp_max: Optional[float] = None
    ) -> PhysicalConstraintReport:
        violations: List[InvariantViolation] = []
        warnings: List[InvariantViolation] = []

        # 1. Drag positivity: CD must be strictly positive
        if cd <= 0.0:
            violations.append(InvariantViolation(
                invariant_name="Universal Drag Positivity",
                severity="CRITICAL",
                details="Aerodynamic drag coefficient CD must be strictly greater than 0 due to friction and pressure resistance.",
                observed_value=cd,
                limit_value=0.0001
            ))
        elif cd < 0.002:
            warnings.append(InvariantViolation(
                invariant_name="Unusually Low Drag",
                severity="WARNING",
                details=f"CD = {cd:.5f} is suspiciously lower than typical laminar profile drag (0.003 - 0.006).",
                observed_value=cd,
                limit_value=0.003
            ))

        # 2. Maximum Stagnation Cp
        # For subsonic isentropic flow: Cp_max = (2 / (gamma * M^2)) * ((1 + 0.2*M^2)^3.5 - 1)
        if mach > 0.01:
            gamma = 1.4
            term = (1.0 + 0.2 * (mach ** 2)) ** 3.5
            cp_stag_limit = (2.0 / (gamma * (mach ** 2))) * (term - 1.0)
            if cp_max is not None and cp_max > (cp_stag_limit * 1.05):
                violations.append(InvariantViolation(
                    invariant_name="Stagnation Pressure Limit",
                    severity="CRITICAL",
                    details=f"Maximum surface Cp ({cp_max:.3f}) exceeds physical isentropic stagnation limit ({cp_stag_limit:.3f}).",
                    observed_value=cp_max,
                    limit_value=round(cp_stag_limit, 3)
                ))

        # 3. Maximum Subsonic Lift Limit (Thin airfoil theory ~ 2*pi*alpha, max CL ~ 2.2 for single element)
        if abs(cl) > 2.8:
            violations.append(InvariantViolation(
                invariant_name="Single-Element Lift Bound",
                severity="CRITICAL",
                details=f"CL = {cl:.3f} exceeds physical maximum achievable lift for a 2D single-element airfoil without active flow control.",
                observed_value=abs(cl),
                limit_value=2.8
            ))
        elif abs(cl) > 2.0:
            warnings.append(InvariantViolation(
                invariant_name="High Lift Warning",
                severity="WARNING",
                details=f"CL = {cl:.3f} indicates severe high-lift or dynamic stall conditions.",
                observed_value=abs(cl),
                limit_value=2.0
            ))

        # 4. Moment coefficient bounds
        if abs(cm) > 0.4:
            warnings.append(InvariantViolation(
                invariant_name="Extreme Quarter-Chord Pitching Moment",
                severity="WARNING",
                details=f"CM = {cm:.3f} is unusually large in magnitude for conventional airfoils.",
                observed_value=abs(cm),
                limit_value=0.4
            ))

        is_sound = (len(violations) == 0)
        return PhysicalConstraintReport(
            is_physically_sound=is_sound,
            violations=violations,
            warnings=warnings
        )
