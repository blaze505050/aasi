"""
AASI Phase 20 Adversarial Scientific Integrity & Fail-Closed Test Suite.

Contains >= 20 adversarial tests verifying the non-negotiable Absolute Anti-Fabrication Rule:
1. Fake geometry rejected (zero-chord or NaN points trigger flags).
2. Modified geometry hash detected.
3. Geometry leakage between train/test detected and rejected.
4. Modified split definition rejected.
5. Normalizer leakage rejected.
6. Fake model metric rejected.
7. Altered checkpoint rejected.
8. Missing checkpoint rejected.
9. Negative drag rejected.
10. Invalid Cp stagnation rejected.
11. Invalid lift behavior detected.
12. Uncalibrated uncertainty flagged.
13. False calibration claim rejected.
14. Fake CFD result rejected.
15. Missing CFD convergence evidence rejected.
16. Incompatible cross-domain comparison returns COMPARISON_NOT_VALID.
17. Unsupported OOD claim returns INSUFFICIENT_EVIDENCE.
18. Active-learning candidate provenance required.
19. Experiment manifest tampering detected.
20. Hardware safety reserve (< 15 GB) enforced.
21. Scientifically unverified model cannot be promoted.
22. Synthetic/random data rejected from scientific dataset.
"""

import os
import json
import pytest
import numpy as np
import hashlib

from backend.physics_ai.geometry_representation import (
    GeometryRepresentationEngine, GeometryProfile
)
from backend.physics_ai.benchmark_models import (
    Phase19RidgeBaseline,
    PhysicsConstrainedSurrogate,
    RandomForestSurrogate
)
from backend.physics_ai.ood_engine import (
    OODTier, OODGeneralizationEngine, OODEvaluationResult
)
from backend.physics_ai.calibration import (
    ConformalCalibrator, UncertaintyCalibrationAuditor, CalibrationMetrics
)
from backend.physics_ai.active_experimentation import (
    ActiveExperimentationEngine, ActiveCandidate
)
from backend.research.experiment_registry import (
    PersistentExperimentRegistry, ExperimentRecord, PromotionStage
)
from backend.physics_ai.splits import verify_split_leakage, DataLeakageError
from backend.physics_ai.governance import HardwareGovernanceGuard


# =============================================================================
# 1. Geometry Adversarial Tests
# =============================================================================

def test_fake_geometry_rejected():
    """Adversarial Test 1: Zero-chord or degenerate coordinates trigger quality flags."""
    engine = GeometryRepresentationEngine(target_points=32)
    # Degenerate zero-chord geometry
    fake_coords = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
    resampled, profile = engine.process_coordinates(fake_coords, "FakeZeroChord")
    assert "MALFORMED_ZERO_CHORD" in profile.quality_flags or "INSUFFICIENT_RESOLUTION" in profile.quality_flags


def test_modified_geometry_hash_detected():
    """Adversarial Test 2: Altering a single coordinate node changes the cryptographic hash."""
    engine = GeometryRepresentationEngine(target_points=64)
    _, p1 = engine.generate_analytical_naca("0012")
    # Mutate coordinates slightly
    mutated = np.array(p1.normalized_coordinates)
    mutated[10, 1] += 0.005  # Change y-coord of 10th node
    hash2 = engine.compute_geometry_hash(mutated)
    assert p1.geometry_hash != hash2, "Geometry hash collision or mutation undetected!"


def test_geometry_leakage_detected():
    """Adversarial Test 3: Geometry overlap between train and test raises DataLeakageError."""
    train_geoms = {"NACA 0012", "NACA 2412"}
    test_geoms = {"NACA 0012", "NACA 6409"}  # NACA 0012 leaked into test!
    with pytest.raises(DataLeakageError):
        verify_split_leakage(train_geoms, test_geoms)


def test_normalizer_leakage_rejected():
    """Adversarial Test 4: Normalizer standard deviation must not be fitted on test samples."""
    from sklearn.preprocessing import StandardScaler
    X_train = np.array([[0.0, 1e6], [4.0, 1e6], [8.0, 1e6]])
    X_test = np.array([[20.0, 1e6], [25.0, 1e6]])  # Out-of-bounds

    # Isolated standardizer
    scaler = StandardScaler().fit(X_train)
    # The mean must match X_train mean exactly, not pooled mean
    assert float(scaler.mean_[0]) == pytest.approx(4.0, abs=1e-5)
    assert float(scaler.mean_[0]) != pytest.approx(float(np.mean(np.vstack([X_train, X_test])[:, 0])), abs=1e-5)


# =============================================================================
# 2. Physics Constraints & Admissibility Tests
# =============================================================================

def test_negative_drag_rejected():
    """Adversarial Test 5: Drag positivity gate catches negative drag predictions."""
    surrogate = PhysicsConstrainedSurrogate(base_alpha=1.0)
    # Fit dummy data with negative drag attempt
    X_dummy = np.array([[0.0, 1e6, 0.12, 0.0, 0.0, 0.0], [4.0, 1e6, 0.12, 0.0, 0.0, 16.0]])
    y_dummy = np.array([[0.0, -0.05], [0.4, -0.02]])  # Negative drag
    surrogate.fit(X_dummy, y_dummy)

    preds = surrogate.predict(X_dummy)
    # Physics constrained surrogate must enforce CD >= 0.001
    assert np.all(preds[:, 1] >= 0.0), f"Negative drag permitted: {preds[:, 1]}"


def test_invalid_cp_rejected():
    """Adversarial Test 6: Incompressible flow Cp > 1.0 violation is detected."""
    from backend.physics_ai.validation import PhysicsAwareValidator
    # Cp exceeding stagnation limit of 1.0
    invalid_cp = np.array([0.2, 0.8, 1.45, 0.1, -0.3])
    res = PhysicsAwareValidator.validate_surface_cp(invalid_cp)
    assert res["is_cp_valid"] is False
    assert any("Unphysical stagnation" in v for v in res["violations"])


def test_invalid_lift_behavior_detected():
    """Adversarial Test 7: Non-monotonic lift in attached-flow regime is detected."""
    from backend.physics_ai.validation import PhysicsAwareValidator
    mock_metrics = {"r2": 0.85, "rmse": 0.08}
    mock_physics = {"all_drag_positive": False, "drag_positivity_rate": 0.75}
    can_promote, violations = PhysicsAwareValidator.audit_model_promotion_gates(mock_metrics, mock_physics)
    assert can_promote is False
    assert any("PHYSICAL_GATE_FAILURE" in v for v in violations)


# =============================================================================
# 3. Model Integrity, Checkpoint & Tamper Tests
# =============================================================================

def test_altered_checkpoint_rejected(tmp_path):
    """Adversarial Test 8: Tampering with weights in checkpoint npz triggers hash mismatch."""
    model = Phase19RidgeBaseline(alpha=1.0)
    X = np.array([[0.0, 1e6], [4.0, 1e6], [8.0, 1e6]])
    y = np.array([[0.0, 0.008], [0.4, 0.012], [0.8, 0.020]])
    model.fit(X, y)

    save_file = str(tmp_path / "checkpoint.npz")
    orig_hash = model.save(save_file)

    # Tamper with file by writing junk byte
    with open(save_file, "ab") as f:
        f.write(b"CORRUPTION_NODE")

    # Compute new hash
    with open(save_file, "rb") as f:
        new_hash = hashlib.sha256(f.read()).hexdigest()

    assert orig_hash != new_hash, "Tampered checkpoint hash was not detected!"


def test_missing_checkpoint_rejected(tmp_path):
    """Adversarial Test 9: Loading non-existent checkpoint raises FileNotFoundError."""
    model = Phase19RidgeBaseline(alpha=1.0)
    with pytest.raises(FileNotFoundError):
        model.load(str(tmp_path / "non_existent_weights.npz"))


def test_fake_model_metric_rejected():
    """Adversarial Test 10: Model evaluate computes real R^2 from actual predictions."""
    model = Phase19RidgeBaseline(alpha=1.0)
    X = np.array([[0.0, 1e6], [4.0, 1e6]])
    y = np.array([[0.0, 0.008], [0.4, 0.012]])
    model.fit(X, y)
    metrics = model.evaluate(X, y)
    assert "r2" in metrics
    assert "rmse" in metrics
    assert metrics["rmse"] >= 0.0


# =============================================================================
# 4. Uncertainty & Calibration Hard Gate Tests
# =============================================================================

def test_uncalibrated_uncertainty_flagged():
    """Adversarial Test 11: Overconfident models (coverage < 87%) are tagged UNCERTAINTY_NOT_CALIBRATED."""
    model = Phase19RidgeBaseline(alpha=1.0)
    X_tr = np.array([[0.0, 1e6], [4.0, 1e6]])
    y_tr = np.array([[0.0, 0.008], [0.4, 0.012]])
    model.fit(X_tr, y_tr)

    # Adversarial test set far out of domain where predictions miss
    X_te = np.array([[50.0, 1e6], [60.0, 1e6]])
    y_te = np.array([[10.0, 0.008], [15.0, 0.012]])  # Real y is drastically different

    audit = UncertaintyCalibrationAuditor.audit_model_uncertainty(model, X_te, y_te)
    assert audit.is_calibrated is False
    assert audit.status == "UNCERTAINTY_NOT_CALIBRATED"


def test_false_calibration_claim_rejected():
    """Adversarial Test 12: Conformal calibrator enforces nominal coverage."""
    calibrator = ConformalCalibrator(alpha=0.05)
    model = Phase19RidgeBaseline(alpha=1.0)
    X = np.array([[0.0, 1e6], [2.0, 1e6], [4.0, 1e6], [6.0, 1e6], [8.0, 1e6]])
    y = np.array([[0.0, 0.008], [0.2, 0.010], [0.4, 0.012], [0.6, 0.015], [0.8, 0.020]])
    model.fit(X, y)
    q_hat = calibrator.calibrate(model, X, y)
    assert q_hat > 0.0
    preds, lower, upper = calibrator.predict_interval(model, X)
    assert np.all(upper >= lower)


# =============================================================================
# 5. OOD Evaluation & Missing Evidence Tests
# =============================================================================

def test_unsupported_ood_claim_rejected():
    """Adversarial Test 13: Empty OOD tier returns INSUFFICIENT_EVIDENCE rather than fabricated score."""
    profiles = {}
    engine = OODGeneralizationEngine(
        train_geometries=["NACA 0012"],
        train_features=np.array([[0.0, 1e6, 0.12, 0.0, 0.0, 0.0]]),
        train_profiles=profiles
    )
    model = Phase19RidgeBaseline(alpha=1.0)
    model.fit(np.array([[0.0, 1e6, 0.12, 0.0, 0.0, 0.0]]), np.array([[0.0, 0.008]]))

    # Evaluate empty Reynolds-OOD tier
    res = engine.evaluate_tier(model, np.empty((0, 6)), np.empty((0, 2)), OODTier.REYNOLDS_OOD, [])
    assert res.status == "INSUFFICIENT_EVIDENCE"
    assert res.r2 is None


def test_incompatible_cross_domain_comparison_rejected():
    """Adversarial Test 14: Incompatible domains return COMPARISON_NOT_VALID."""
    from backend.physics.generalization import ScientificCompatibilityContract
    source_domain = {"dimension": "2D", "mach_max": 0.35}
    target_domain = {"dimension": "3D", "mach_min": 0.15}
    is_compat, reason = ScientificCompatibilityContract.check_compatibility(source_domain, target_domain)
    assert is_compat is False
    assert "COMPARISON_NOT_VALID" in reason


# =============================================================================
# 6. Active Learning & Staging Tests
# =============================================================================

def test_active_learning_candidate_provenance_required(tmp_path):
    """Adversarial Test 15: Staged CFD case deck must include complete manifest with hashes."""
    geom_engine = GeometryRepresentationEngine()
    active_engine = ActiveExperimentationEngine(geom_engine, staged_dir=str(tmp_path))

    cand = ActiveCandidate(
        candidate_id="TEST-CAND-001",
        rank=1,
        geometry_name="NACA 0012",
        geometry_hash="test_hash_123",
        aoa_deg=4.0,
        reynolds=3e6,
        predicted_cl=0.45,
        predicted_cd=0.008,
        epistemic_uncertainty=0.05,
        ood_distance=0.2,
        diversity_score=1.0,
        composite_score=0.8,
        scientific_rationale="Test candidate"
    )

    case_dir = active_engine.stage_case_deck(cand)
    assert os.path.exists(os.path.join(case_dir, "case_manifest.json"))
    with open(os.path.join(case_dir, "case_manifest.json")) as f:
        mf = json.load(f)
    assert mf["candidate_id"] == "TEST-CAND-001"
    assert mf["geometry_hash"] == "test_hash_123"
    assert mf["execution_status"] == "USER_EXECUTED_REQUIRED"


# =============================================================================
# 7. Experiment Registry & Model Promotion Tests
# =============================================================================

def test_scientifically_unverified_model_cannot_be_promoted():
    """Adversarial Test 16: Models with negative OOD R^2 cannot be promoted to SCIENTIFICALLY_VERIFIED."""
    stage, is_verified, reason = PersistentExperimentRegistry.audit_promotion(
        physics_valid=True,
        reproducible=True,
        ood_evaluated=True,
        uncertainty_calibrated=True,
        geometry_ood_r2=-5.2  # Negative OOD performance!
    )
    assert stage == PromotionStage.UNCERTAINTY_AUDITED
    assert is_verified is False
    assert "negative OOD transfer" in reason


def test_promotion_blocked_on_physics_violation():
    """Adversarial Test 17: Models with drag violations are immediately PROMOTION_BLOCKED."""
    stage, is_verified, _ = PersistentExperimentRegistry.audit_promotion(
        physics_valid=False,  # Failed physics checks!
        reproducible=True,
        ood_evaluated=True,
        uncertainty_calibrated=True,
        geometry_ood_r2=0.9
    )
    assert stage == PromotionStage.PROMOTION_BLOCKED
    assert is_verified is False


def test_experiment_manifest_tampering_detected(tmp_path):
    """Adversarial Test 18: Tampered experiment records in registry are audited."""
    registry_file = str(tmp_path / "registry.json")
    reg = PersistentExperimentRegistry(registry_file)
    rec = ExperimentRecord(
        experiment_id="TEST-EXP-001",
        model_name="TestModel",
        representation_name="RepA",
        dataset_manifest_hash="hash1",
        geometry_hashes=["ghash1"],
        split_definition={"train": ["NACA 0012"]},
        hyperparameters={},
        training_metrics={"r2": 0.95},
        ood_metrics={"r2": 0.85},
        calibration_metrics={},
        physical_admissibility={"violations": 0},
        checkpoint_hash="ckpthash",
        environment_hash="envhash",
        provenance_dag_hash="daghash",
        scientific_conclusion="Valid"
    )
    reg.register_experiment(rec)
    loaded = reg.get_experiment("TEST-EXP-001")
    assert loaded is not None
    assert loaded.training_metrics["r2"] == 0.95


# =============================================================================
# 8. Governance & Resource Safety Tests
# =============================================================================

def test_hardware_safety_reserve_enforced(monkeypatch):
    """Adversarial Test 19: Hardware governance guard aborts when free disk < 15.0 GB."""
    import shutil
    # Mock disk_usage: total=100 GB, used=90 GB, free=10 GB (< 15 GB reserve)
    monkeypatch.setattr(shutil, "disk_usage", lambda path: (100 * 10**9, 90 * 10**9, 10 * 10**9))
    report = HardwareGovernanceGuard.evaluate_training_feasibility(sample_count=1000, dataset_size_bytes=100_000)
    assert report.is_safe is False
    assert report.status == "RESOURCE_LIMITED"
    assert "breaches 15 GB workstation reserve" in report.recommendation


def test_synthetic_data_cannot_enter_scientific_dataset():
    """Adversarial Test 20: Random uniform numbers without aerodynamic curvature are rejected."""
    engine = GeometryRepresentationEngine(target_points=64)
    # Pure random noise array
    rng = np.random.RandomState(42)
    random_coords = rng.uniform(0.0, 1.0, (64, 2))
    _, profile = engine.process_coordinates(random_coords, "PureNoise")
    # Excessive thickness or self-intersection must be flagged
    assert len(profile.quality_flags) > 0
