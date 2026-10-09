"""
Unit and Integration Tests for AASI Aerodynamic Database (Aero DB) Engine.
Verifies multi-condition envelope sweeps, stability & control derivative extraction,
lift-curve slopes, drag polar parabolic fits, and aerodynamic center calculations.
"""

import math
import pytest
from backend.physics.aerodb_engine import (
    AerodynamicDatabaseEngine,
    AeroDatabase,
    FlightConditionPolar,
    StabilityDerivatives,
)


def test_naca0012_polar_sweep():
    """Verify symmetric profile (NACA 0012) polar sweep properties."""
    db = AerodynamicDatabaseEngine.generate_aero_db(
        geometry_name="NACA 0012",
        alpha_min=-6.0,
        alpha_max=14.0,
        alpha_step=1.0,
        reynolds_list=[3_000_000.0],
        mach_list=[0.15],
    )

    assert isinstance(db, AeroDatabase)
    assert db.geometry_name == "NACA 0012"
    assert len(db.polars) == 1

    cond = db.polars[0]
    derivs = cond.derivatives

    # 1. Total points: from -6 to 14 with step 1 = 21 points
    assert len(cond.points) == 21

    # 2. Lift-curve slope: theoretical 2*pi*(1+0.77*0.12) ~ 6.86 rad^-1, pre-stall panel ~ 5.0 - 7.0 rad^-1
    assert 4.8 <= derivs.cl_alpha_per_rad <= 7.2
    assert 0.08 <= derivs.cl_alpha_per_deg <= 0.125

    # 3. Symmetric zero-lift angle: alpha_0L should be close to 0 deg (+/- 0.5 deg)
    assert abs(derivs.alpha_zero_lift_deg) < 0.5
    assert abs(derivs.cl_zero_alpha) < 0.05

    # 4. Drag minimum and efficiency
    assert 0.005 <= derivs.cd_0 <= 0.015
    assert derivs.l_over_d_max > 30.0
    assert derivs.alpha_cruise_deg >= 2.0

    # 5. Pitch stability: aerodynamic center near quarter-chord (0.25 +/- 0.05)
    assert 0.20 <= derivs.aerodynamic_center_x_over_c <= 0.30


def test_naca4412_camber_effect():
    """Verify cambered profile (NACA 4412) produces positive lift at zero alpha and negative alpha_0L."""
    db = AerodynamicDatabaseEngine.generate_aero_db(
        geometry_name="NACA 4412",
        alpha_min=-6.0,
        alpha_max=12.0,
        alpha_step=2.0,
        reynolds_list=[3_000_000.0],
        mach_list=[0.15],
    )

    derivs = db.polars[0].derivatives

    # Cambered airfoil must have positive lift at alpha = 0
    assert derivs.cl_zero_alpha > 0.30
    # Zero-lift angle must be negative (approx -3 deg to -5 deg for NACA 4412)
    assert -5.5 <= derivs.alpha_zero_lift_deg <= -2.5
    # Maximum lift should exceed symmetric airfoil
    assert derivs.cl_max > 1.20


def test_multi_condition_envelope():
    """Verify multiple Mach and Reynolds number combinations in a single database."""
    db = AerodynamicDatabaseEngine.generate_aero_db(
        geometry_name="NACA 0012",
        alpha_min=0.0,
        alpha_max=8.0,
        alpha_step=2.0,
        reynolds_list=[1_000_000.0, 6_000_000.0],
        mach_list=[0.15, 0.40],
    )

    # 2 Mach x 2 Reynolds = 4 conditions
    assert len(db.polars) == 4
    assert db.envelope_summary["num_conditions"] == 4
    assert db.envelope_summary["total_points_evaluated"] == 4 * 5  # 5 alpha points each
