"""
Tests for Physics-AI Pipeline & Checkpoint Integrity.

Verifies:
- Model forward pass and parameter counting
- Deterministic initialization via random seeds
- SHA-256 weight checksum stability
- Checkpoint saving and loading roundtrip
- Leakage-free geometry partitioning.
"""

import pytest
import numpy as np
from pathlib import Path
from backend.physics_ai.models import AeroSurrogateV1
from backend.physics_ai.normalization import FlowConditionNormalizer, AerodynamicTargetScaler
from backend.physics_ai.checkpoints import CheckpointManager
from backend.physics_ai.splits import GeometryLevelSplitter
from backend.physics_ai.dataset import AerodynamicAirfoilDataset


def test_model_forward_shape():
    model = AeroSurrogateV1(coords_points=64, seed=42)
    B = 8
    X_geom = np.random.randn(B, 64, 2).astype(np.float32)
    X_cond = np.random.randn(B, 3).astype(np.float32)
    out = model.forward(X_geom, X_cond)
    assert out.shape == (B, 3)
    assert model.count_parameters() > 10000


def test_model_determinism():
    m1 = AeroSurrogateV1(seed=123)
    m2 = AeroSurrogateV1(seed=123)
    assert m1.compute_weights_checksum() == m2.compute_weights_checksum()

    m3 = AeroSurrogateV1(seed=456)
    assert m1.compute_weights_checksum() != m3.compute_weights_checksum()


def test_checkpoint_roundtrip(tmp_path):
    ckpt_mgr = CheckpointManager(checkpoints_dir=str(tmp_path))
    model = AeroSurrogateV1(seed=42)
    norm = FlowConditionNormalizer()
    scaler = AerodynamicTargetScaler()
    metadata = {"epochs": 10, "test_loss": 0.005}

    saved_path, checksum = ckpt_mgr.save_checkpoint(
        model=model,
        condition_normalizer=norm,
        target_scaler=scaler,
        training_metadata=metadata,
        filename="test_surrogate.npz"
    )
    assert saved_path.exists()
    assert len(checksum) == 64

    # Load back and verify checksum match
    loaded_model, loaded_norm, loaded_scaler, loaded_meta, loaded_ck = ckpt_mgr.load_checkpoint(saved_path)
    assert loaded_ck == checksum
    assert loaded_model.compute_weights_checksum() == model.compute_weights_checksum()


def test_geometry_level_splits():
    ds = AerodynamicAirfoilDataset.load_from_directory("data/datasets/authentic_airfoils")
    splitter = GeometryLevelSplitter(seed=42)
    split_dict = splitter.split_samples(ds.samples)

    manifest = split_dict["manifest"]
    train_geoms = set(manifest["train_geometries"])
    test_geoms = set(manifest["test_geometries"])
    val_geoms = set(manifest["val_geometries"])
    ood_geoms = set(manifest["ood_geometries"])

    # Strict zero-leakage check: intersections must be completely empty
    assert len(train_geoms.intersection(test_geoms)) == 0
    assert len(train_geoms.intersection(val_geoms)) == 0
    assert len(test_geoms.intersection(val_geoms)) == 0
    assert len(train_geoms.intersection(ood_geoms)) == 0
