"""
Tests for Aerodynamic Physics Validation Rules.

Verifies:
- Positive drag (CD > 0)
- Monotonic lift curve slope in attached pre-stall flow (dCL/dAoA > 0)
- Symmetry condition at zero angle of attack for symmetric airfoils
- Continuous polar sweep detection without non-physical oscillations.
"""

import pytest
import numpy as np
from backend.physics_ai.validation import PhysicsAwareValidator
from backend.physics_ai.service import PhysicsAIService


def test_single_prediction_physical_rules():
    # Valid physical point
    res = PhysicsAwareValidator.validate_prediction(
        cl=0.45, cd=0.0085, cm=-0.005, aoa_deg=4.0, is_symmetric=True
    )
    assert res["is_physically_valid"] is True
    assert res["checks"]["drag_positive"] is True

    # Negative drag violation
    res_neg = PhysicsAwareValidator.validate_prediction(
        cl=0.45, cd=-0.001, cm=-0.005, aoa_deg=4.0, is_symmetric=True
    )
    assert res_neg["is_physically_valid"] is False
    assert res_neg["checks"]["drag_positive"] is False


def test_symmetric_airfoil_zero_lift_sanity():
    # Non-zero lift on symmetric profile at alpha=0
    res = PhysicsAwareValidator.validate_prediction(
        cl=0.25, cd=0.008, cm=0.0, aoa_deg=0.0, is_symmetric=True
    )
    assert res["checks"]["symmetry_satisfied"] is False


def test_polar_sweep_monotonicity_check():
    aoas = [-4.0, -2.0, 0.0, 2.0, 4.0, 6.0, 8.0]
    cls_good = [-0.4, -0.2, 0.0, 0.22, 0.44, 0.65, 0.85]
    cds_good = [0.008, 0.007, 0.006, 0.0065, 0.008, 0.010, 0.013]
    cms_good = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    val = PhysicsAwareValidator.validate_polar_sweep(aoas, cls_good, cds_good, cms_good, is_symmetric=True)
    assert val["is_sweep_valid"] is True
    assert val["checks"]["lift_monotonicity"] is True

    # Invert slopes to simulate pathological failure
    cls_bad = [-0.4, -0.2, 0.0, 0.3, 0.1, 0.65, 0.85]
    val_bad = PhysicsAwareValidator.validate_polar_sweep(aoas, cls_bad, cds_good, cms_good, is_symmetric=True)
    assert val_bad["is_sweep_valid"] is False
    assert val_bad["checks"]["lift_monotonicity"] is False


def test_service_prediction_physical_sanity():
    service = PhysicsAIService.get_instance()
    pred = service.predict("naca0012", mach=0.2, reynolds=2.0e6, aoa_deg=4.0)
    assert pred.cd > 0.0
    assert pred.cl > 0.35  # Realistic subsonic lift
    assert pred.physics_checks.get("drag_positive") is True
