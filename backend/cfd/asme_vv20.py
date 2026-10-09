"""
AASI ASME V&V 20-2009 Grid Convergence Index (GCI) & Numerical Uncertainty Engine.

Implements the complete, formal ASME V&V 20-2009 standard:
"Standard for Verification and Validation in Computational Fluid Dynamics and Heat Transfer"

Calculates:
1. Systematic grid refinement ratios (r_21, r_32)
2. Apparent / observed order of accuracy (p) via transcendental fixed-point solve
3. Richardson extrapolated benchmark solution (phi_ext)
4. Approximate and extrapolated relative errors (e_a, e_ext)
5. Fine and medium Grid Convergence Indices (GCI_fine, GCI_med) with ASME safety factor F_s = 1.25
6. Asymptotic range of convergence verification ratio
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class GridLevel(BaseModel):
    """Represents a discrete CFD grid level."""
    name: str                           # e.g. "Fine (h1)", "Medium (h2)", "Coarse (h3)"
    cell_count: int                     # Total element count N
    h_representative: float             # Representative mesh size h = sqrt(A / N)
    value: float                        # Observed key output, e.g. CL, CD, pressure drop


class ASMEConvergenceStatus(str):
    MONOTONIC_CONVERGENCE = "MONOTONIC_CONVERGENCE"
    OSCILLATORY_CONVERGENCE = "OSCILLATORY_CONVERGENCE"
    MONOTONIC_DIVERGENCE = "MONOTONIC_DIVERGENCE"
    OSCILLATORY_DIVERGENCE = "OSCILLATORY_DIVERGENCE"


class ASMEVerificationReport(BaseModel):
    """Complete ASME V&V 20 calculation dossier."""
    quantity_name: str
    grid_levels: List[Dict[str, Any]]
    refinement_ratio_21: float
    refinement_ratio_32: float
    convergence_status: str
    observed_order_p: float
    theoretical_order: float
    richardson_extrapolated: float
    relative_approx_error_21_pct: float
    relative_extrap_error_21_pct: float
    gci_fine_pct: float
    gci_medium_pct: float
    asymptotic_ratio: float
    in_asymptotic_range: bool
    numerical_uncertainty_plus_minus: float
    safety_factor: float = 1.25
    summary_verdict: str


class ASMEVV20Engine:
    """
    Standard ASME V&V 20-2009 verification calculator.
    """

    @staticmethod
    def calculate_gci(
        phi_1: float,
        phi_2: float,
        phi_3: float,
        n_1: int,
        n_2: int,
        n_3: int,
        quantity_name: str = "Lift Coefficient (CL)",
        theoretical_order: float = 2.0,
        safety_factor: float = 1.25,
        dimension: int = 2,
    ) -> ASMEVerificationReport:
        """
        Executes ASME V&V 20 procedure on three systematically refined grids.
        Grid 1 = Fine (highest cell count n_1)
        Grid 2 = Medium (intermediate cell count n_2)
        Grid 3 = Coarse (lowest cell count n_3)
        """
        if not (n_1 > n_2 > n_3):
            raise ValueError(f"Cell counts must satisfy n_1 > n_2 > n_3. Got ({n_1}, {n_2}, {n_3})")

        # 1. Representative grid size h = (1 / N)^(1/D)
        h_1 = (1.0 / n_1) ** (1.0 / dimension)
        h_2 = (1.0 / n_2) ** (1.0 / dimension)
        h_3 = (1.0 / n_3) ** (1.0 / dimension)

        r_21 = h_2 / h_1
        r_32 = h_3 / h_2

        # 2. Differences
        eps_21 = phi_2 - phi_1
        eps_32 = phi_3 - phi_2

        # Handle zero difference
        if abs(eps_21) < 1e-12:
            eps_21 = 1e-12
        if abs(eps_32) < 1e-12:
            eps_32 = 1e-12

        ratio_32_21 = eps_32 / eps_21
        R = eps_21 / eps_32
        s = 1.0 if R > 0 else -1.0

        # Classify convergence type per ASME V&V 20-2009 / Celik et al. (2008)
        if 0.0 < R <= 1.0:
            status = ASMEConvergenceStatus.MONOTONIC_CONVERGENCE
        elif -1.0 <= R < 0.0:
            status = ASMEConvergenceStatus.OSCILLATORY_CONVERGENCE
        elif R > 1.0:
            status = ASMEConvergenceStatus.MONOTONIC_DIVERGENCE
        else:
            status = ASMEConvergenceStatus.OSCILLATORY_DIVERGENCE

        # 3. Observed order of accuracy (p)
        # For non-uniform refinement: p = (1 / ln(r_21)) * |ln|eps_32/eps_21| + q(p)|
        # Solved via fixed-point iteration
        p = theoretical_order
        for _ in range(25):
            try:
                num = (r_21 ** p) - s
                den = (r_32 ** p) - s
                if den <= 0 or num <= 0:
                    break
                q_p = math.log(num / den)
                p_next = (1.0 / math.log(r_21)) * abs(math.log(abs(ratio_32_21)) + q_p)
                if abs(p_next - p) < 1e-5:
                    p = p_next
                    break
                p = 0.5 * (p + p_next)
            except (ValueError, ZeroDivisionError, OverflowError):
                break

        # Bound p physically (between 0.5 and 4.0 for standard CFD schemes)
        p_bounded = float(max(0.5, min(p, 4.0)))

        # 4. Richardson Extrapolated value
        denom_21 = (r_21 ** p_bounded) - 1.0
        if abs(denom_21) < 1e-6:
            denom_21 = 1e-6
        phi_ext_21 = (r_21 ** p_bounded * phi_1 - phi_2) / denom_21

        denom_32 = (r_32 ** p_bounded) - 1.0
        if abs(denom_32) < 1e-6:
            denom_32 = 1e-6
        phi_ext_32 = (r_32 ** p_bounded * phi_2 - phi_3) / denom_32

        # 5. Relative Errors
        e_a_21 = abs((phi_1 - phi_2) / max(abs(phi_1), 1e-6))
        e_ext_21 = abs((phi_ext_21 - phi_1) / max(abs(phi_ext_21), 1e-6))

        e_a_32 = abs((phi_2 - phi_3) / max(abs(phi_2), 1e-6))

        # 6. Grid Convergence Index (GCI)
        gci_fine = (safety_factor * e_a_21) / denom_21
        gci_medium = (safety_factor * e_a_32) / denom_32

        # 7. Asymptotic Range Verification
        # Check: GCI_med / (r_21^p * GCI_fine) ~ 1.0
        asymptotic_denom = (r_21 ** p_bounded) * max(gci_fine, 1e-12)
        asymptotic_ratio = gci_medium / asymptotic_denom
        in_asymptotic_range = bool(0.90 <= asymptotic_ratio <= 1.10)

        # Numerical uncertainty u_num = GCI_fine * |phi_1|
        u_num = float(gci_fine * abs(phi_1))

        if in_asymptotic_range and status == ASMEConvergenceStatus.MONOTONIC_CONVERGENCE:
            verdict = f"VERIFIED: Observed order p={p_bounded:.2f} confirms systematic monotonic grid convergence within asymptotic range."
        elif status == ASMEConvergenceStatus.MONOTONIC_CONVERGENCE:
            verdict = f"ACCEPTABLE: Monotonic convergence established (GCI_fine={gci_fine*100:.2f}%); near-asymptotic boundary."
        else:
            verdict = f"CAUTION: {status}; higher resolution or localized boundary-layer refinement required."

        grid_summary = [
            {"level": "Fine (h1)", "cells": n_1, "h": round(h_1, 6), "value": round(phi_1, 5)},
            {"level": "Medium (h2)", "cells": n_2, "h": round(h_2, 6), "value": round(phi_2, 5)},
            {"level": "Coarse (h3)", "cells": n_3, "h": round(h_3, 6), "value": round(phi_3, 5)},
        ]

        return ASMEVerificationReport(
            quantity_name=quantity_name,
            grid_levels=grid_summary,
            refinement_ratio_21=round(r_21, 3),
            refinement_ratio_32=round(r_32, 3),
            convergence_status=status,
            observed_order_p=round(p_bounded, 3),
            theoretical_order=theoretical_order,
            richardson_extrapolated=round(phi_ext_21, 5),
            relative_approx_error_21_pct=round(e_a_21 * 100.0, 3),
            relative_extrap_error_21_pct=round(e_ext_21 * 100.0, 3),
            gci_fine_pct=round(gci_fine * 100.0, 3),
            gci_medium_pct=round(gci_medium * 100.0, 3),
            asymptotic_ratio=round(asymptotic_ratio, 3),
            in_asymptotic_range=in_asymptotic_range,
            numerical_uncertainty_plus_minus=round(u_num, 5),
            safety_factor=safety_factor,
            summary_verdict=verdict,
        )
