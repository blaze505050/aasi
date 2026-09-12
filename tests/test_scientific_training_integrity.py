"""
AASI Adversarial Scientific Integrity Test Suite.

Audits failure modes mandated by Phase 11 & Phase 18 of the Master Directive:
1. Geometry-level data leakage detection
2. Test-set contamination detection (normalization peeking)
3. Corrupted dataset rejection (fail closed)
4. Altered dataset hash rejection
5. Altered checkpoint hash rejection
6. Missing checkpoint returns MODEL_UNAVAILABLE
7. Physically impossible predictions rejected (negative drag, non-monotonic lift)
8. Pressure coefficient physical bounds verification
9. OOD inference tagging (SURROGATE — OOD WARNING / OUT OF DOMAIN)
10. Uncalibrated uncertainty flagged (UNCERTAINTY_NOT_CALIBRATED)
11. Incompatible dataset comparison returns COMPARISON_NOT_VALID
12. Fake training status rejection (cannot promote without test validation)
13. Incomplete provenance rejection
14. Altered reproducibility manifest checksum verification
15. Pre-flight hardware governance safety enforcement (RESOURCE_LIMITED)
"""

import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import numpy as np

from backend.physics_ai.schemas import AirfoilSample, DomainStatusEnum
from backend.physics_ai.splits import GeometryLevelSplitter, DataLeakageError
from backend.physics_ai.validation import PhysicsAwareValidator
from backend.physics_ai.checkpoints import CheckpointManager
from backend.physics_ai.inference import AerodynamicInferenceEngine, ModelUnavailableError
from backend.physics_ai.uncertainty import EpistemicUncertaintyEngine
from backend.physics.generalization import (
    ScientificCompatibilityContract,
    CrossDatasetGeneralizationEngine,
)
from backend.physics_ai.governance import HardwareGovernanceGuard
from backend.physics_ai.reproducibility import TrainingReproducibilityManifest
from backend.physics_ai.report import ModelExperimentReportGenerator, OverclaimingError
from backend.datasets.acquisition import (
    DatasetAcquisitionManager,
    AcquisitionContractViolationError,
)
from backend.datasets.models import DatasetManifest, DatasetLifecycle, StorageStatus


# --- 1. Geometry-Level Data Leakage Prevention ---

def test_adversarial_geometry_leakage_detection():
    """Verifies that GeometryLevelSplitter detects and fails closed on data leakage."""
    sample_train = AirfoilSample(
        sample_id="S1", dataset_id="D1", source_id="SRC1", geometry="NACA 0012",
        mach=0.15, reynolds=3e6, aoa_deg=0.0, cl=0.0, cd=0.006, cm=0.0, provenance_hash="H1"
    )
    # Contaminated sample with identical geometry in test partition
    sample_test_leaked = AirfoilSample(
        sample_id="S2", dataset_id="D1", source_id="SRC1", geometry="NACA 0012",
        mach=0.20, reynolds=3e6, aoa_deg=4.0, cl=0.42, cd=0.008, cm=-0.002, provenance_hash="H2"
    )
    with pytest.raises(DataLeakageError) as exc_info:
        GeometryLevelSplitter.verify_split_leakage([sample_train], [sample_test_leaked])
    assert "DATA_LEAKAGE_DETECTED" in str(exc_info.value)


# --- 2. Test-Set Contamination & Normalization Isolation ---

def test_normalization_isolation_guarantee():
    """Guarantees normalizer is fitted strictly on training data without test set peeking."""
    from backend.physics_ai.normalization import FlowConditionNormalizer
    train_conds = np.array([[0.1, 1e6, 0.0], [0.2, 2e6, 5.0]], dtype=np.float32)
    test_conds = np.array([[0.35, 5e6, 15.0]], dtype=np.float32)

    normalizer = FlowConditionNormalizer()
    normalizer.fit(train_conds)

    # Max Mach in normalizer should reflect ONLY training max (0.2), not test (0.35)
    assert normalizer.mean_[0] == pytest.approx(0.15, abs=1e-4)
    # Transform test set using frozen normalizer without altering training statistics
    transformed_test = normalizer.transform(test_conds)
    assert transformed_test.shape == (1, 3)
    assert normalizer.mean_[0] == pytest.approx(0.15, abs=1e-4)


# --- 3. Corrupted & Altered Dataset Rejection ---

def test_corrupted_dataset_acquisition_fail_closed():
    """Verifies that corrupted dataset or checksum mismatch fails closed in acquisition contract."""
    mgr = DatasetAcquisitionManager()
    manifest = DatasetManifest(
        dataset_id="TEST-CORRUPT-SET",
        name="Corrupted CFD Test Dataset",
        source="Test Laboratory",
        license="Public Domain",
        checksum="EXPECTED_VALID_HASH_12345",
        lifecycle_stage=DatasetLifecycle.DOWNLOADED
    )
    # Attempt advancing to HASH_VERIFIED with corrupted actual hash
    with pytest.raises(AcquisitionContractViolationError) as exc_info:
        mgr.advance_lifecycle(
            manifest=manifest,
            to_stage=DatasetLifecycle.HASH_VERIFIED,
            metadata={"actual_hash": "TAMPERED_OR_CORRUPTED_HASH_67890"}
        )
    assert "hash mismatch" in str(exc_info.value).lower()


# --- 4. Checkpoint Tampering & Missing Checkpoint ---

def test_altered_checkpoint_checksum_rejection(tmp_path):
    """Verifies that an altered model checkpoint fails cryptographic verification."""
    ckpt_mgr = CheckpointManager(checkpoints_dir=str(tmp_path))
    test_file = tmp_path / "tampered_model.npz"
    test_file.write_bytes(b"INITIAL_FAKE_WEIGHTS")
    initial_hash = hashlib.sha256(b"INITIAL_FAKE_WEIGHTS").hexdigest()

    # Tamper with the checkpoint
    test_file.write_bytes(b"TAMPERED_MALICIOUS_WEIGHTS")

    is_valid, actual_hash, msg = ckpt_mgr.verify_checkpoint_integrity(
        checkpoint_path=test_file,
        expected_sha256=initial_hash
    )
    assert is_valid is False
    assert "Checksum mismatch" in msg


def test_missing_checkpoint_returns_model_unavailable(tmp_path):
    """Verifies that missing checkpoint returns MODEL_UNAVAILABLE instead of fake predictions."""
    non_existent = tmp_path / "non_existent_model.npz"
    infer = AerodynamicInferenceEngine(checkpoint_path=str(non_existent))
    assert infer.weights_status == "MISSING"

    with pytest.raises(ModelUnavailableError) as exc_info:
        infer.predict(geometry="NACA 0012", mach=0.15, reynolds=3e6, aoa_deg=4.0)
    assert "MODEL_UNAVAILABLE" in str(exc_info.value)


# --- 5. Physically Impossible Predictions & Validation Gates ---

def test_negative_drag_rejection():
    """Asserts that unphysical negative drag is detected and fails validation."""
    report = PhysicsAwareValidator.validate_prediction(
        cl=0.5, cd=-0.005, cm=-0.01, aoa_deg=4.0
    )
    assert report["is_physically_valid"] is False
    assert report["checks"]["drag_positive"] is False


def test_non_monotonic_lift_slope_rejection():
    """Asserts that non-monotonic pre-stall lift slope is flagged as a physical violation."""
    aoas = [-2.0, 0.0, 2.0, 4.0, 6.0]
    # Pathological non-monotonic drop at alpha = 2 deg
    cls = [0.0, 0.25, 0.10, 0.45, 0.65]
    cds = [0.008, 0.008, 0.009, 0.011, 0.013]
    cms = [0.0, -0.002, -0.003, -0.004, -0.005]

    report = PhysicsAwareValidator.validate_polar_sweep(aoas, cls, cds, cms)
    assert report["checks"]["lift_monotonicity"] is False
    assert report["is_sweep_valid"] is False


def test_surface_pressure_stagnation_bounds():
    """Asserts that surface Cp exceeding the incompressible stagnation limit (Cp > 1.0) is rejected."""
    unphysical_cps = np.array([-1.5, -0.8, 0.2, 0.9, 1.35])  # Cp = 1.35 violates Bernoulli limit
    report = PhysicsAwareValidator.validate_surface_cp(unphysical_cps)
    assert report["is_cp_valid"] is False
    assert report["stagnation_satisfied"] is False


# --- 6. OOD Inference Tagging & Uncalibrated Uncertainty ---

def test_ood_inference_epistemic_tags():
    """Verifies that OOD conditions trigger explicit warning tags rather than normal status."""
    training_manifold = np.array([[0.15, 0.0, 0.0], [0.20, 0.5, 0.5]], dtype=np.float32)
    engine = EpistemicUncertaintyEngine(
        training_conditions=training_manifold,
        validity_envelope={"mach": [0.05, 0.35], "reynolds": [1e6, 5e6], "aoa_deg": [-4.0, 12.0]}
    )
    # Severe extrapolation condition (AoA = 22 deg, post-stall)
    status, metrics = engine.evaluate_uncertainty(
        norm_cond=np.array([2.5, 3.0, 5.0], dtype=np.float32),
        raw_mach=0.20,
        raw_reynolds=3e6,
        raw_aoa=22.0
    )
    assert status == DomainStatusEnum.SURROGATE_OUT_OF_DOMAIN
    assert metrics.epistemic_tag in ("OUT OF DOMAIN", "SURROGATE — HIGH UNCERTAINTY")
    assert metrics.calibration_status == "UNCERTAINTY_NOT_CALIBRATED"


# --- 7. Cross-Dataset Compatibility Contract ---

def test_incompatible_cross_dataset_comparison_fails_closed():
    """Verifies that comparing 2D airfoil to 3D finite wing returns COMPARISON_NOT_VALID."""
    source_domain = {"dimension": "2D", "mach_max": 0.30}
    target_domain = {"dimension": "3D", "mach_min": 0.80}

    is_comp, reason = ScientificCompatibilityContract.check_compatibility(source_domain, target_domain)
    assert is_comp is False
    assert "COMPARISON_NOT_VALID" in reason


# --- 8. No-Overclaiming Gate Enforcement ---

def test_no_overclaiming_gate_enforcement():
    """Asserts that claiming experimental validation on numerical CFD raises OverclaimingError."""
    claims = ["The surrogate model is experimentally validated against AirfRANS."]
    with pytest.raises(OverclaimingError) as exc_info:
        ModelExperimentReportGenerator.audit_scientific_claims(
            claims=claims,
            is_statistically_validated=True,
            is_physically_validated=True,
            is_experimental_ground_truth=False,  # AirfRANS is numerical CFD, NOT experimental
            is_cross_dataset_generalized=True
        )
    assert "UNEARNED_CLAIM" in str(exc_info.value)


# --- 9. Hardware Governance Guard ---

def test_hardware_governance_safety_threshold():
    """Verifies that requesting massive uncompressed dataset triggers RESOURCE_LIMITED."""
    report = HardwareGovernanceGuard.evaluate_training_feasibility(
        sample_count=500_000,
        dataset_size_bytes=50_000_000_000  # 50 GB dataset on 20 GB free disk
    )
    assert report.is_safe is False
    assert report.status == "RESOURCE_LIMITED"
    assert "breaches 15 GB workstation reserve" in report.recommendation


# --- 10. Reproducibility Manifest Integrity ---

def test_reproducibility_manifest_tamper_detection():
    """Verifies that altering a reproducibility manifest invalidates its cryptographic checksum."""
    manifest = TrainingReproducibilityManifest.create_and_sign(
        run_id="RUN-TEST-001",
        training_dataset_id="DATASET-AUTHENTIC-AIRFOILS-V1",
        training_dataset_hash="HASH_DATA_123",
        validation_dataset_hash="HASH_VAL_123",
        test_dataset_hash="HASH_TEST_123",
        geometry_split_manifest_hash="HASH_SPLIT_123",
        hyperparameters={"epochs": 100},
        checkpoint_file="weights.npz",
        checkpoint_sha256="HASH_WEIGHTS_123",
        training_metrics={"cl_rmse": 0.05},
        validation_metrics={"cl_rmse": 0.06},
        test_metrics={"cl_rmse": 0.07},
        ood_metrics={},
        physics_validation_summary={"all_drag_positive": True},
        normalization_params={},
        uncertainty_config={},
        seed=42
    )
    original_checksum = manifest.manifest_checksum
    assert manifest.compute_manifest_checksum() == original_checksum

    # Tamper with hyperparameters or metrics
    manifest.hyperparameters["epochs"] = 999
    tampered_checksum = manifest.compute_manifest_checksum()
    assert tampered_checksum != original_checksum


# --- 11. Fake Training Status Rejection ---

def test_fake_training_status_promotion_rejection():
    """Asserts that a model with good R2 but non-positive drag cannot be promoted to VERIFIED."""
    metrics = {"cl_r2": 0.94, "cl_rmse": 0.04}
    failing_physics = {"all_drag_positive": False, "drag_positivity_rate": 0.88}

    can_promote, violations = PhysicsAwareValidator.audit_model_promotion_gates(
        metrics=metrics, physics_report=failing_physics
    )
    assert can_promote is False
    assert any("PHYSICAL_GATE_FAILURE" in v for v in violations)


# --- 12. Incomplete Provenance Rejection ---

def test_incomplete_provenance_rejection():
    """Asserts that missing citation or source fails closed in acquisition contract."""
    mgr = DatasetAcquisitionManager()
    manifest = DatasetManifest(
        dataset_id="TEST-INCOMPLETE",
        name="Incomplete Dataset",
        source="",  # Missing source
        license="Public Domain",
        citation="",  # Missing citation
        lifecycle_stage=DatasetLifecycle.LICENSE_VERIFIED
    )
    with pytest.raises(AcquisitionContractViolationError) as exc_info:
        mgr.advance_lifecycle(manifest, to_stage=DatasetLifecycle.SOURCE_VERIFIED)
    assert "source or citation is missing" in str(exc_info.value).lower()


# --- 13. Pluggable Adapter Registration ---

def test_pluggable_dataset_catalog_registration():
    """Verifies that new dataset adapters can be registered dynamically without core modifications."""
    from backend.datasets.catalog import DatasetCatalog
    from backend.datasets.adapters.tmr2d import NASATMR2DDatasetAdapter
    catalog = DatasetCatalog()

    adapter = catalog.get_adapter("DATASET-NASA-TMR-2D")
    assert adapter is not None
    assert adapter.get_dataset_id() == "DATASET-NASA-TMR-2D"
    assert len(adapter.list_cases()) > 0

