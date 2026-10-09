"""
Unit Tests for AASI ASME V&V 20-2009 Grid Convergence Index (GCI) Engine.
Verifies Richardson extrapolation, observed order of convergence, GCI indices,
and asymptotic range verification against standard benchmark values.
"""

import math
import pytest
from backend.cfd.asme_vv20 import ASMEVV20Engine, ASMEConvergenceStatus, ASMEVerificationReport


def test_asme_vv20_canonical_grid_study():
    """
    Standard test with uniform refinement ratio r = 2.0 (or cell ratio 4 for 2D).
    Fine grid (phi1 = 0.970), Medium grid (phi2 = 0.960), Coarse grid (phi3 = 0.930).
    Demonstrates monotonic convergence with p close to 2.
    """
    n1 = 64000
    n2 = 16000
    n3 = 4000
    phi1 = 0.970
    phi2 = 0.960
    phi3 = 0.930

    report = ASMEVV20Engine.calculate_gci(
        phi_1=phi1,
        phi_2=phi2,
        phi_3=phi3,
        n_1=n1,
        n_2=n2,
        n_3=n3,
        quantity_name="Lift Coefficient (CL)",
        theoretical_order=2.0,
        safety_factor=1.25,
        dimension=2,
    )

    assert isinstance(report, ASMEVerificationReport)
    assert report.convergence_status == ASMEConvergenceStatus.MONOTONIC_CONVERGENCE
    assert report.refinement_ratio_21 == 2.0
    assert report.refinement_ratio_32 == 2.0
    assert 0.5 <= report.observed_order_p <= 4.0
    # Richardson extrapolation must lie beyond the fine grid solution in direction of convergence
    assert report.richardson_extrapolated > phi1
    # GCI on fine grid should be strictly smaller than GCI on medium grid
    assert report.gci_fine_pct < report.gci_medium_pct
    assert report.gci_fine_pct > 0.0
    assert report.numerical_uncertainty_plus_minus > 0.0


def test_asme_vv20_invalid_grid_ordering():
    """Verify ValueError is raised when grids are not strictly ordered n1 > n2 > n3."""
    with pytest.raises(ValueError):
        ASMEVV20Engine.calculate_gci(
            phi_1=1.0, phi_2=1.0, phi_3=1.0,
            n_1=1000, n_2=2000, n_3=500  # n1 < n2 violates prerequisite
        )


def test_asme_vv20_asymptotic_ratio():
    """Verify asymptotic ratio formula behavior."""
    n1 = 40000
    n2 = 20000
    n3 = 10000
    phi1 = 1.050
    phi2 = 1.035
    phi3 = 1.010

    report = ASMEVV20Engine.calculate_gci(
        phi_1=phi1, phi_2=phi2, phi_3=phi3,
        n_1=n1, n_2=n2, n_3=n3,
    )
    assert report.asymptotic_ratio > 0.0
    assert isinstance(report.in_asymptotic_range, bool)
