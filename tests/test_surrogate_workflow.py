"""
Unit and Integration Tests for Milestone 8: Active-Learning Surrogate Workflow.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Section 8 of MVP Backlog & Prompt 9:
- Lightweight scikit-learn surrogate workflow with strict train/validation separation.
- Out-of-distribution extrapolation detection with explicit scientific warnings.
- STRICT RULE: Never label surrogate predictions as CFD.
- Active-learning candidate sample suggestions.
- REST API routes in backend/api/routes_surrogate.py.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.science.surrogate import (
    AeroSurrogateWorkflow,
    SurrogatePrediction,
    TrainingEnvelope,
    aero_surrogate,
)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Train / Validation Separation
# ---------------------------------------------------------------------------

def test_surrogate_train_validation_separation():
    """Verify that surrogate trains with explicit train/val split and high validation R2."""
    workflow = AeroSurrogateWorkflow(seed=42)
    X, y_cl, y_cd = workflow._generate_authentic_baseline_data()
    metrics = workflow.fit(X, y_cl, y_cd, val_ratio=0.20)

    assert "train_r2_cl" in metrics
    assert "val_r2_cl" in metrics
    assert "train_r2_cd" in metrics
    assert "val_r2_cd" in metrics

    # Statistical surrogate on thin-airfoil data must achieve R2 > 0.85
    assert metrics["train_r2_cl"] > 0.85
    assert metrics["val_r2_cl"] > 0.85
    assert metrics["train_r2_cd"] > 0.85
    assert metrics["val_r2_cd"] > 0.85

    # Verification of envelope metrics
    assert workflow.envelope.num_samples == len(X)
    assert workflow.envelope.val_r2_cl > 0.85


# ---------------------------------------------------------------------------
# 2. Strict Anti-CFD Epistemic Rules
# ---------------------------------------------------------------------------

def test_surrogate_prediction_never_labeled_as_cfd():
    """Verify surrogate output is strictly tagged SURROGATE and is_cfd is False."""
    pred = aero_surrogate.predict(geometry="NACA 0012", alpha_deg=4.0, reynolds=3.0e6, mach=0.15)
    assert pred.epistemic_tier == "SURROGATE"
    assert pred.is_cfd is False
    assert "NOT a numerical Navier-Stokes CFD solution" in pred.disclaimer
    assert pred.predicted_cl > 0.35  # Realistic lift at 4 deg
    assert pred.predicted_cd > 0.005 # Realistic drag


def test_surrogate_prediction_rejects_cfd_label_fabrication():
    """Attempting to set is_cfd=True or tier=VERIFIED must raise ValueError."""
    with pytest.raises(ValueError, match="CRITICAL PROVENANCE VIOLATION: Surrogate predictions cannot be labeled as CFD"):
        SurrogatePrediction(
            geometry="NACA 0012",
            operating_conditions={"alpha_deg": 4.0},
            predicted_cl=0.44,
            predicted_cd=0.008,
            is_cfd=True,  # FABRICATION VIOLATION! Must fail!
        )

    with pytest.raises(ValueError, match="CRITICAL PROVENANCE VIOLATION: Invalid tier"):
        SurrogatePrediction(
            geometry="NACA 0012",
            operating_conditions={"alpha_deg": 4.0},
            predicted_cl=0.44,
            predicted_cd=0.008,
            epistemic_tier="VERIFIED",  # FABRICATION VIOLATION! Must fail!
            is_cfd=False,
        )


# ---------------------------------------------------------------------------
# 3. Rigorous Extrapolation Detection
# ---------------------------------------------------------------------------

def test_in_domain_prediction_no_extrapolation():
    """Inside training envelope: is_extrapolation is False and warning is None."""
    pred = aero_surrogate.predict(geometry="NACA 0012", alpha_deg=4.0, reynolds=3.0e6, mach=0.15)
    assert pred.is_extrapolation is False
    assert pred.extrapolation_warning is None


def test_out_of_domain_alpha_triggers_extrapolation_warning():
    """Querying alpha=25.0° (well above alpha_max=14°) triggers extrapolation hazard."""
    pred = aero_surrogate.predict(geometry="NACA 0012", alpha_deg=25.0, reynolds=3.0e6, mach=0.15)
    assert pred.is_extrapolation is True
    assert pred.extrapolation_warning is not None
    assert "EXTRAPOLATION HAZARD" in pred.extrapolation_warning
    assert "exceeds training maximum" in pred.extrapolation_warning


def test_out_of_domain_reynolds_triggers_extrapolation_warning():
    """Querying Re=5e7 (above reynolds_max=6e6) triggers extrapolation hazard."""
    pred = aero_surrogate.predict(geometry="NACA 0012", alpha_deg=4.0, reynolds=5.0e7, mach=0.15)
    assert pred.is_extrapolation is True
    assert pred.extrapolation_warning is not None
    assert "Reynolds number" in pred.extrapolation_warning


def test_out_of_domain_mach_triggers_extrapolation_warning():
    """Querying Mach=0.60 (above mach_max=0.30) triggers extrapolation hazard."""
    pred = aero_surrogate.predict(geometry="NACA 0012", alpha_deg=4.0, reynolds=3.0e6, mach=0.60)
    assert pred.is_extrapolation is True
    assert pred.extrapolation_warning is not None
    assert "Mach number" in pred.extrapolation_warning


# ---------------------------------------------------------------------------
# 4. Active Learning Sample Suggestions
# ---------------------------------------------------------------------------

def test_active_learning_suggestions():
    """Verify active learning suggests candidate points with non-zero acquisition scores."""
    suggestions = aero_surrogate.suggest_active_learning_samples(geometry="NACA 0012", n_suggestions=3)
    assert len(suggestions) == 3
    for s in suggestions:
        assert s.geometry == "NACA 0012"
        assert s.acquisition_score > 0.0
        assert s.rationale != ""


# ---------------------------------------------------------------------------
# 5. REST API Routes
# ---------------------------------------------------------------------------

def test_api_surrogate_envelope(client):
    """GET /api/surrogate/envelope returns training envelope and metrics."""
    resp = client.get("/api/surrogate/envelope")
    assert resp.status_code == 200
    env = resp.json()
    assert env["alpha_min"] <= -4.0
    assert env["alpha_max"] >= 14.0
    assert env["val_r2_cl"] > 0.85


def test_api_surrogate_predict_in_domain(client):
    """POST /api/surrogate/predict for normal in-domain condition."""
    payload = {
        "geometry": "NACA 0012",
        "alpha_deg": 4.0,
        "reynolds": 3000000.0,
        "mach": 0.15,
    }
    resp = client.post("/api/surrogate/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["epistemic_tier"] == "SURROGATE"
    assert data["is_cfd"] is False
    assert data["is_extrapolation"] is False
    assert data["extrapolation_warning"] is None
    assert data["predicted_cl"] > 0.35


def test_api_surrogate_predict_extrapolation(client):
    """POST /api/surrogate/predict with out-of-domain alpha emits warning."""
    payload = {
        "geometry": "NACA 0012",
        "alpha_deg": 22.0,
        "reynolds": 3000000.0,
        "mach": 0.15,
    }
    resp = client.post("/api/surrogate/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_extrapolation"] is True
    assert "EXTRAPOLATION HAZARD" in data["extrapolation_warning"]


def test_api_surrogate_active_learning(client):
    """POST /api/surrogate/active-learning returns sample suggestions."""
    payload = {"geometry": "NACA 0012", "n_suggestions": 3}
    resp = client.post("/api/surrogate/active-learning", json=payload)
    assert resp.status_code == 200
    suggestions = resp.json()
    assert len(suggestions) == 3


def test_api_surrogate_retrain(client):
    """POST /api/surrogate/retrain triggers training and returns metrics."""
    resp = client.post("/api/surrogate/retrain")
    assert resp.status_code == 200
    metrics = resp.json()
    assert "val_r2_cl" in metrics
    assert metrics["val_r2_cl"] > 0.85
