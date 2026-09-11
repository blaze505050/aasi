"""
Unit and Integration Tests for Milestone D: Model Lifecycle, Authentic Checkpoint & Training Provenance.

Validates:
- ModelLifecycleStatus classification (VERIFIED_PRODUCTION vs UNTRAINED_SCAFFOLD)
- Checkpoint cryptographic SHA-256 integrity verification
- AerodynamicInferenceEngine fail-closed behavior on missing checkpoints
- Deterministic pure-CPU surrogate training reproducibility (seed=42)
- API endpoints: /api/physics/models/{model_id}/status and /api/physics/models/verify-checkpoints
"""

import pytest
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.physics.training_models import ModelLifecycleStatus, RegisteredModel
from backend.physics.model_registry import PhysicsModelRegistry
from backend.physics_ai.checkpoints import CheckpointManager
from backend.physics_ai.inference import AerodynamicInferenceEngine, ModelUnavailableError
from backend.physics_ai.train_surrogate import train_and_export_surrogate
from backend.physics_ai.models import AeroSurrogateV1

client = TestClient(app)


def test_model_registry_lifecycle_segregation():
    """Verifies that the model registry honestly declares scaffold vs verified models."""
    registry = PhysicsModelRegistry()

    # AeroSurrogateV1 must be VERIFIED_PRODUCTION with authentic checkpoint
    aero1 = registry.get_model("MODEL-AERO-SURROGATE-V1")
    assert aero1 is not None
    assert aero1.lifecycle_status == ModelLifecycleStatus.VERIFIED_PRODUCTION
    assert aero1.checkpoint_path is not None
    assert aero1.training_provenance is not None
    assert aero1.training_provenance.device_used.startswith("Local CPU")

    # AeroGraphNet and FNO are scaffolds without on-disk weights
    agn = registry.get_model("MODEL-AEROGRAPHNET-NACA-2D")
    assert agn is not None
    assert agn.lifecycle_status == ModelLifecycleStatus.UNTRAINED_SCAFFOLD
    assert agn.checkpoint_path is None

    fno = registry.get_model("MODEL-FNO-AIRFOIL-PRESSURE-2D")
    assert fno is not None
    assert fno.lifecycle_status == ModelLifecycleStatus.UNTRAINED_SCAFFOLD
    assert fno.checkpoint_path is None


def test_checkpoint_manager_integrity_verification():
    """Tests CheckpointManager.verify_checkpoint_integrity() on authentic and missing files."""
    real_ckpt = Path("data/checkpoints/aero_surrogate_v1.npz")
    if real_ckpt.exists():
        expected_sha = "bc549596f676c5d336fe33333845c53c6d2c170bce2eb964516c51dc8f4ee433"
        valid, sha, msg = CheckpointManager.verify_checkpoint_integrity(real_ckpt, expected_sha)
        assert valid is True
        assert sha == expected_sha

        # Test with wrong checksum
        valid_bad, sha_bad, msg_bad = CheckpointManager.verify_checkpoint_integrity(real_ckpt, "badhash"*8)
        assert valid_bad is False
        assert "mismatch" in msg_bad.lower()

    # Test non-existent file
    valid_none, _, msg_none = CheckpointManager.verify_checkpoint_integrity(Path("data/checkpoints/non_existent.npz"))
    assert valid_none is False
    assert "does not exist" in msg_none.lower()


def test_registry_verify_checkpoint_method():
    """Tests PhysicsModelRegistry.verify_checkpoint() helper."""
    registry = PhysicsModelRegistry()

    # Authentic model
    res_aero1 = registry.verify_checkpoint("MODEL-AERO-SURROGATE-V1")
    assert res_aero1["valid"] is True
    assert res_aero1["lifecycle_status"] == ModelLifecycleStatus.VERIFIED_PRODUCTION.value

    # Scaffold model
    res_agn = registry.verify_checkpoint("MODEL-AEROGRAPHNET-NACA-2D")
    assert res_agn["valid"] is False
    assert res_agn["lifecycle_status"] == ModelLifecycleStatus.UNTRAINED_SCAFFOLD.value

    # Unknown model
    res_unknown = registry.verify_checkpoint("MODEL-DOES-NOT-EXIST")
    assert res_unknown["valid"] is False


def test_inference_engine_fails_closed_on_missing_checkpoint():
    """Verifies that AerodynamicInferenceEngine raises ModelUnavailableError if checkpoint is missing."""
    engine = AerodynamicInferenceEngine(checkpoint_path="data/checkpoints/missing_phantom_weights.npz")
    assert engine.weights_status == "MISSING"

    with pytest.raises(ModelUnavailableError, match="MODEL_UNAVAILABLE"):
        engine.predict(geometry="NACA 0012", mach=0.2, reynolds=2e6, aoa_deg=4.0)


def test_deterministic_cpu_training_reproducibility(tmp_path):
    """Verifies that train_and_export_surrogate runs on pure CPU and reproduces identical weights."""
    out_dir1 = tmp_path / "run1"
    out_dir2 = tmp_path / "run2"

    res1 = train_and_export_surrogate(
        output_dir=str(out_dir1),
        export_to_checkpoints=False,
        epochs=3,
        seed=42
    )
    res2 = train_and_export_surrogate(
        output_dir=str(out_dir2),
        export_to_checkpoints=False,
        epochs=3,
        seed=42
    )

    assert res1["checksum"] is not None
    assert res2["checksum"] is not None
    assert res1["checksum"] == res2["checksum"]


def test_api_model_lifecycle_status():
    """Tests GET /api/physics/models/{model_id}/status."""
    res = client.get("/api/physics/models/MODEL-AERO-SURROGATE-V1/status")
    assert res.status_code == 200
    data = res.json()
    assert data["model_id"] == "MODEL-AERO-SURROGATE-V1"
    assert data["lifecycle_status"] == "VERIFIED_PRODUCTION"
    assert data["verification"]["valid"] is True
    assert data["training_provenance"]["device_used"].startswith("Local CPU")

    res_agn = client.get("/api/physics/models/MODEL-AEROGRAPHNET-NACA-2D/status")
    assert res_agn.status_code == 200
    data_agn = res_agn.json()
    assert data_agn["lifecycle_status"] == "UNTRAINED_SCAFFOLD"
    assert data_agn["verification"]["valid"] is False


def test_api_verify_all_checkpoints():
    """Tests POST /api/physics/models/verify-checkpoints."""
    res = client.post("/api/physics/models/verify-checkpoints")
    assert res.status_code == 200
    data = res.json()
    assert "verifications" in data
    assert "MODEL-AERO-SURROGATE-V1" in data["verifications"]
    assert data["verifications"]["MODEL-AERO-SURROGATE-V1"]["valid"] is True
