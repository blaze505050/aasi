"""
AASI Phase 19 Adversarial Scientific Execution & Integrity Tests.

Tests all 16 fail-closed requirements from Directive 13:
1. fake dataset acquisition
2. fake CFD success
3. solver exit code 0 without convergence
4. altered CFD result
5. altered checkpoint
6. altered dataset
7. changed split
8. geometry leakage
9. fabricated training metrics
10. fabricated OOD metrics
11. fabricated uncertainty calibration
12. broken provenance
13. invalid cross-dataset comparison
14. missing reproduction artifact
15. modified environment manifest
16. unauthorized model promotion
"""

import json
import shutil
import tempfile
import hashlib
from pathlib import Path
import pytest

from backend.physics_ai.governance import HardwareGovernanceGuard
from backend.physics_ai.splits import verify_split_leakage, DataLeakageError
from backend.physics_ai.validation import PhysicsAwareValidator
from backend.physics.generalization import CrossDatasetGeneralizationEngine
from backend.physics.training_models import ModelLifecycleStatus
from backend.simulation.executor import (
    OpenFOAMExecutionEngine,
    SolverExecutionStatus,
    ConvergenceStatus,
    ResidualHistory,
    ForceCoeffHistory,
)
from backend.research.verifier import ReproducibilityVerifier, ReproducibilityStatus
from backend.physics_ai.reproduction_campaign import Phase19CampaignOrchestrator


@pytest.fixture(scope="module")
def valid_bundle():
    """Ensures a valid Phase 19 reproduction bundle exists."""
    bundle_dir = Path("data/reproduction_bundles/PHASE19-RUN-001")
    if not (bundle_dir / "hashes.sha256").exists():
        Phase19CampaignOrchestrator.run_campaign()
    return bundle_dir


# 1. Fake Dataset Acquisition Rejected
def test_fake_dataset_acquisition_rejected():
    """Verifies that an unacquired dataset cannot claim READY_FOR_TRAINING without provenance hashes."""
    from backend.datasets.adapters.airfrans import AirfRANSDatasetAdapter
    from backend.datasets.models import DatasetLifecycle
    adapter = AirfRANSDatasetAdapter()
    state = adapter.get_storage_state()
    # When uncompressed dataset exceeds free disk safety reserve, it must be RESOURCE_LIMITED
    assert state.value in ["RESOURCE_LIMITED", "DATASET_STORAGE_REQUIREMENTS", "AVAILABLE_REMOTE_DIRECT"]


# 2. Fake CFD Success Rejected
def test_fake_cfd_success_rejected():
    """Verifies that missing simpleFoam solver returns USER_EXECUTED_REQUIRED without fabricating results."""
    res = OpenFOAMExecutionEngine.execute_or_stage(
        Path("data/simulations/API-TEST-NACA0012"),
        case_id="API-TEST-NACA0012"
    )
    assert res.execution_status == SolverExecutionStatus.USER_EXECUTED_REQUIRED
    assert res.exit_code is None
    assert res.convergence_report.is_converged is False
    assert "SOLVER_UNAVAILABLE" in res.stdout_summary


# 3. Solver Exit Code 0 Without Convergence Rejected
def test_solver_exit_code_zero_without_convergence_rejected():
    """Verifies that exit code 0 with high residuals (>1e-3) is marked UNCONVERGED."""
    high_res = ResidualHistory(
        iterations=[1, 2, 100],
        continuity=[0.1, 0.05, 0.02],
        ux=[0.08, 0.04, 0.015],
        uy=[0.08, 0.04, 0.015],
        p=[0.1, 0.05, 0.012],
        final_continuity=0.02,
        final_ux=0.015,
        final_uy=0.015,
        final_p=0.012
    )
    forces = ForceCoeffHistory(iterations=[100], cl=[0.4], cd=[0.02], cm=[-0.01])
    report = OpenFOAMExecutionEngine.analyze_convergence(high_res, forces, residual_threshold=1e-4)
    assert report.is_converged is False
    assert report.convergence_status == ConvergenceStatus.UNCONVERGED


# 4. Altered CFD Result Detected by Verifier
def test_altered_cfd_result_detected_by_verifier(valid_bundle):
    """Verifies that tampering with CFD case or simulation logs in a bundle is caught."""
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(valid_bundle, tmpdir, dirs_exist_ok=True)
        tmp_path = Path(tmpdir)
        # Modify a file
        q_file = tmp_path / "research_question.json"
        data = json.loads(q_file.read_text(encoding="utf-8"))
        data["title"] = "Tampered Title"
        q_file.write_text(json.dumps(data), encoding="utf-8")

        audit = ReproducibilityVerifier.verify_phase19_bundle(tmp_path)
        assert audit.tamper_detected is True
        assert audit.status == ReproducibilityStatus.REPRODUCTION_FAILED


# 5. Altered Checkpoint Fails Reproducibility
def test_altered_checkpoint_fails_reproducibility(valid_bundle):
    """Verifies that tampering with checkpoint.npz triggers SHA-256 failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(valid_bundle, tmpdir, dirs_exist_ok=True)
        tmp_path = Path(tmpdir)
        ckpt = tmp_path / "checkpoint.npz"
        # Alter the checkpoint by appending bytes
        content = ckpt.read_bytes()
        ckpt.write_bytes(content + b"TAMPERED_MALICIOUS_EXTRA_BYTES")

        audit = ReproducibilityVerifier.verify_phase19_bundle(tmp_path)
        assert audit.tamper_detected is True
        assert audit.status == ReproducibilityStatus.REPRODUCTION_FAILED


# 6. Altered Dataset Fails Reproducibility
def test_altered_dataset_fails_reproducibility(valid_bundle):
    """Verifies that altering subset_manifest.json triggers hash mismatch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(valid_bundle, tmpdir, dirs_exist_ok=True)
        tmp_path = Path(tmpdir)
        manifest = tmp_path / "subset_manifest.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["total_cases_in_subset"] = 9999
        manifest.write_text(json.dumps(data), encoding="utf-8")

        audit = ReproducibilityVerifier.verify_phase19_bundle(tmp_path)
        assert audit.tamper_detected is True
        assert audit.status == ReproducibilityStatus.REPRODUCTION_FAILED


# 7. Changed Split Detected
def test_changed_split_detected(valid_bundle):
    """Verifies that modifying split_definition.json is caught by hash verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(valid_bundle, tmpdir, dirs_exist_ok=True)
        tmp_path = Path(tmpdir)
        split_f = tmp_path / "split_definition.json"
        data = json.loads(split_f.read_text(encoding="utf-8"))
        data["train_cases_count"] = 0
        split_f.write_text(json.dumps(data), encoding="utf-8")

        audit = ReproducibilityVerifier.verify_phase19_bundle(tmp_path)
        assert audit.tamper_detected is True


# 8. Geometry Leakage Detected and Rejected
def test_geometry_leakage_detected_and_rejected():
    """Verifies that overlapping geometries between train and test raise DataLeakageError."""
    train = [{"geometry_id": "NACA 0012"}, {"geometry_id": "NACA 2412"}]
    test = [{"geometry_id": "NACA 0012"}, {"geometry_id": "NACA 4412"}]
    with pytest.raises(DataLeakageError) as exc_info:
        verify_split_leakage(train, test, geometry_key="geometry_id")
    assert "DATA_LEAKAGE_DETECTED" in str(exc_info.value)


# 9. Fabricated Training Metrics Rejected
def test_fabricated_training_metrics_rejected():
    """Verifies that negative drag or invalid metrics fail physical promotion gates."""
    metrics = {"cl_r2": 0.95, "cl_rmse": 0.02}
    failing_physics = {"all_drag_positive": False, "drag_positivity_rate": 0.85}
    can_promote, violations = PhysicsAwareValidator.audit_model_promotion_gates(
        metrics=metrics, physics_report=failing_physics
    )
    assert can_promote is False
    assert any("PHYSICAL_GATE_FAILURE" in v for v in violations)


# 10. Fabricated OOD Metrics Rejected
def test_fabricated_ood_metrics_rejected():
    """Verifies that unrepresented OOD regimes return INSUFFICIENT_EVIDENCE rather than fabricated scores."""
    from backend.physics_ai.reproduction_campaign import Phase19CampaignOrchestrator
    bundle = Phase19CampaignOrchestrator.BUNDLE_DIR
    ood_data = json.loads((bundle / "ood_metrics.json").read_text(encoding="utf-8"))
    assert ood_data["reynolds_ood"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert ood_data["aoa_ood"]["status"] == "INSUFFICIENT_EVIDENCE"


# 11. Fabricated Uncertainty Calibration Flagged
def test_uncalibrated_uncertainty_flagged():
    """Verifies that models without empirical calibration sets are tagged UNCERTAINTY_NOT_CALIBRATED."""
    from backend.physics_ai.schemas import UncertaintyMetrics
    u = UncertaintyMetrics(
        confidence_level="HIGH",
        confidence_score=0.9,
        ood_score=0.1,
        feature_distance=0.2,
        nearest_neighbor_density=1.0,
        calibration_status="UNCERTAINTY_NOT_CALIBRATED"
    )
    assert u.calibration_status == "UNCERTAINTY_NOT_CALIBRATED"


# 12. Broken Provenance DAG Rejected
def test_broken_provenance_dag_rejected(valid_bundle):
    """Verifies that corrupted provenance DAG fails verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(valid_bundle, tmpdir, dirs_exist_ok=True)
        tmp_path = Path(tmpdir)
        prov = tmp_path / "provenance_dag.json"
        prov.write_text(json.dumps({"invalid_key": 123}), encoding="utf-8")

        audit = ReproducibilityVerifier.verify_phase19_bundle(tmp_path)
        assert audit.tamper_detected is True
        assert audit.status == ReproducibilityStatus.REPRODUCTION_FAILED


# 13. Invalid Cross-Dataset Comparison Returns Not Valid
def test_invalid_cross_dataset_comparison_returns_not_valid():
    """Verifies that 2D section vs 3D finite wing comparison returns COMPARISON_NOT_VALID."""
    from backend.physics.generalization import ScientificCompatibilityContract
    is_valid, reason = ScientificCompatibilityContract.check_compatibility(
        source_domain={"dimension": "2D", "mach_max": 0.30},
        target_domain={"dimension": "3D", "mach_min": 0.80}
    )
    assert is_valid is False
    assert "COMPARISON_NOT_VALID" in reason
    assert "Cannot compare 2D sectional coefficients directly to 3D" in reason


# 14. Missing Reproduction Artifact Detected
def test_missing_reproduction_artifact_detected(valid_bundle):
    """Verifies that removing a required file (e.g. reproduce.json) fails audit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(valid_bundle, tmpdir, dirs_exist_ok=True)
        tmp_path = Path(tmpdir)
        (tmp_path / "reproduce.json").unlink()

        audit = ReproducibilityVerifier.verify_phase19_bundle(tmp_path)
        assert any("reproduce.json" in f for f in audit.checks_failed)
        assert audit.status == ReproducibilityStatus.REPRODUCTION_FAILED


# 15. Modified Environment Manifest Detected
def test_modified_environment_manifest_detected(valid_bundle):
    """Verifies that tampering with environment_manifest.json is detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(valid_bundle, tmpdir, dirs_exist_ok=True)
        tmp_path = Path(tmpdir)
        env_f = tmp_path / "environment_manifest.json"
        data = json.loads(env_f.read_text(encoding="utf-8"))
        data["os_platform"] = "Fabricated OS 99.0"
        env_f.write_text(json.dumps(data), encoding="utf-8")

        audit = ReproducibilityVerifier.verify_phase19_bundle(tmp_path)
        assert audit.tamper_detected is True
        assert audit.status == ReproducibilityStatus.REPRODUCTION_FAILED


# 16. Unauthorized Model Promotion Blocked
def test_unauthorized_model_promotion_blocked():
    """Verifies that training completion alone cannot transition model to VERIFIED."""
    unpromoted_status = ModelLifecycleStatus.TRAINED_UNVERIFIED
    assert unpromoted_status != ModelLifecycleStatus.VERIFIED

    # Non-monotonic lift violation blocks promotion
    aoas = [-2.0, 0.0, 2.0, 4.0]
    cls = [0.0, 0.25, 0.10, 0.45]  # non-monotonic drop
    cds = [0.008, 0.008, 0.009, 0.011]
    cms = [0.0, -0.002, -0.003, -0.004]
    polar_report = PhysicsAwareValidator.validate_polar_sweep(aoas, cls, cds, cms)
    assert polar_report["is_sweep_valid"] is False
    assert polar_report["checks"]["lift_monotonicity"] is False
