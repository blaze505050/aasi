"""
Unit & Integration Test Suite for Stage 5: Epistemic Uncertainty & Conformal Prediction.
Validates exact finite-sample coverage guarantees, Mahalanobis OOD detection,
ASTM F3269-21 Run-Time Assurance (RTA) fallback transitions, and FastAPI endpoints.
Conforms to ASME V&V 20-2009 & ASTM F3269-21.
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from aasi_aero_fno.conformal_uncertainty import (
    ConformalAerospaceSafetyEngine,
    generate_aerospace_calibration_deck,
    compute_conformal_quantile,
    LatentAerospaceOODDetector,
)
from backend.main import app

client = TestClient(app)


def test_conformal_quantile_monotonicity():
    """Verify that conformal quantiles increase monotonically with target confidence level."""
    deck = generate_aerospace_calibration_deck(100)
    scores = deck.nonconformity_scores

    q80 = compute_conformal_quantile(scores, alpha_miscoverage=0.20)
    q90 = compute_conformal_quantile(scores, alpha_miscoverage=0.10)
    q95 = compute_conformal_quantile(scores, alpha_miscoverage=0.05)
    q99 = compute_conformal_quantile(scores, alpha_miscoverage=0.01)

    assert q80 <= q90 <= q95 <= q99
    assert q95 > 1.0  # Must exceed 1 sigma for 95% coverage


def test_empirical_conformal_coverage():
    """
    Empirically verify the mathematical theorem:
    P(y in C(x)) >= 1 - alpha on holdout test set.
    """
    deck = generate_aerospace_calibration_deck(200)
    scores = deck.nonconformity_scores

    # Calibrate on first 100 samples
    cal_scores = scores[:100]
    test_scores = scores[100:]

    target_alpha = 0.10  # 90% coverage
    q_hat = compute_conformal_quantile(cal_scores, alpha_miscoverage=target_alpha)

    # In conformal prediction, test sample is covered if test_score <= q_hat
    covered = np.mean(test_scores <= q_hat)
    # Due to sample variance, empirical coverage must be close to target (within ~6%)
    assert covered >= (1.0 - target_alpha) - 0.06


def test_mahalanobis_ood_detection():
    """Verify Mahalanobis distance correctly flags in-distribution vs OOD queries."""
    # Nominal cruise: Mach 0.75, AoA 2.5 deg, Re 6e6
    dm_nominal, is_ood_nom, tier_nom = LatentAerospaceOODDetector.compute_mahalanobis_distance(
        mach=0.75, alpha_deg=2.5, reynolds=6.0e6
    )
    assert is_ood_nom is False
    assert tier_nom == "IN_DISTRIBUTION"
    assert dm_nominal < 3.3  # Well within 95% chi-squared contour

    # Extreme OOD: Mach 2.2, AoA 35 deg, Re 1e4
    dm_ood, is_ood_ext, tier_ext = LatentAerospaceOODDetector.compute_mahalanobis_distance(
        mach=2.2, alpha_deg=35.0, reynolds=1.0e4
    )
    assert is_ood_ext is True
    assert tier_ext == "OUT_OF_DISTRIBUTION_CRITICAL"
    assert dm_ood > 4.0


def test_astm_f3269_rta_fallback_transitions():
    """Verify ASTM F3269-21 RTA states: NOMINAL -> ADVISORY -> FALLBACK_DISPATCHED."""
    # 1. Nominal
    nom_res = ConformalAerospaceSafetyEngine.evaluate(mach=0.80, alpha_deg=2.0)
    assert nom_res.epistemic_safety_tier == "NOMINAL"
    assert "VERIFIED" in nom_res.rta_subsystem

    # 2. Extreme OOD triggering fallback
    ood_res = ConformalAerospaceSafetyEngine.evaluate(mach=2.5, alpha_deg=35.0)
    assert ood_res.epistemic_safety_tier == "FALLBACK_DISPATCHED"
    assert ood_res.rta_action == "SURROGATE_SUPPRESSED_HIGH_FIDELITY_RANS_ENGAGED"
    assert "LEVEL_3_FAILSAFE" in ood_res.rta_subsystem


def test_fastapi_conformal_endpoints():
    """Test the Stage 5 FastAPI endpoints."""
    # 1. Evaluate endpoint
    eval_resp = client.post(
        "/api/aero/conformal/evaluate",
        json={
            "mach": 0.85,
            "alpha_deg": 2.2,
            "reynolds": 6.5e6,
            "confidence_level_pct": 95.0,
            "thickness_ratio": 0.12,
            "sweep_deg": 28.0,
        },
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["status"] == "SUCCESS"
    assert eval_data["stage"] == 5
    assert len(eval_data["data"]["cl_interval"]) == 2
    assert eval_data["data"]["cl_interval"][0] < eval_data["data"]["cl_prediction"] < eval_data["data"]["cl_interval"][1]

    # 2. Calibration summary endpoint
    cal_resp = client.get("/api/aero/conformal/calibration")
    assert cal_resp.status_code == 200
    cal_data = cal_resp.json()
    assert cal_data["status"] == "SUCCESS"
    assert cal_data["summary"]["num_calibration_samples"] > 50
    assert cal_data["summary"]["quantile_95"] > 0.0

