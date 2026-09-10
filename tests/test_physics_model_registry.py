"""
Tests for AASI Physics-AI Model Registry, Physical Validation, and Active Learning.
"""

import pytest
from backend.physics.model_registry import PhysicsModelRegistry
from backend.physics.training_models import RegisteredModel, TrainingConfig
from backend.physics.validation import PhysicsValidator
from backend.physics.active_learning import ActiveLearningEngine


def test_physics_model_registry_list_and_get():
    """Verifies that PhysicsModelRegistry tracks registered models with domain envelopes."""
    registry = PhysicsModelRegistry()
    models = registry.list_models()
    assert len(models) >= 2

    aerographnet = registry.get_model("MODEL-AEROGRAPHNET-NACA-2D")
    assert aerographnet is not None
    assert aerographnet.architecture == "AeroGraphNet"
    assert aerographnet.domain["mach"] == [0.1, 0.6]
    assert aerographnet.domain["aoa_deg"] == [-6.0, 12.0]
    assert "cl_rmse" in aerographnet.metrics

    fno = registry.get_model("MODEL-FNO-AIRFOIL-PRESSURE-2D")
    assert fno is not None
    assert fno.architecture == "FNO"


def test_model_registry_prevent_silent_overwrite():
    """Verifies that duplicate model IDs cannot silently overwrite existing registered models."""
    registry = PhysicsModelRegistry()
    duplicate_model = registry.get_model("MODEL-AEROGRAPHNET-NACA-2D")
    with pytest.raises(ValueError, match="Silent replacement is strictly prohibited"):
        registry.register_model(duplicate_model)


def test_physics_validator_aerodynamic_sanity():
    """Tests that PhysicsValidator checks monotonicity, symmetry, and bounds."""
    # Predictions that follow normal lift slope
    preds = [
        {"aoa": -2.0, "cl": -0.22, "cd": 0.0075},
        {"aoa": 0.0, "cl": 0.00, "cd": 0.0070},
        {"aoa": 2.0, "cl": 0.22, "cd": 0.0074},
        {"aoa": 4.0, "cl": 0.44, "cd": 0.0080},
    ]
    ground_truth = [
        {"aoa": -2.0, "cl": -0.21, "cd": 0.0074},
        {"aoa": 0.0, "cl": 0.00, "cd": 0.0071},
        {"aoa": 2.0, "cl": 0.21, "cd": 0.0073},
        {"aoa": 4.0, "cl": 0.43, "cd": 0.0079},
    ]
    report = PhysicsValidator.validate_predictions(
        model_id="TEST-MODEL-001",
        predictions=preds,
        ground_truth=ground_truth,
        is_symmetric_airfoil=True
    )
    assert report.passed is True
    assert report.monotonicity_preserved is True
    assert report.symmetry_preserved is True
    assert report.cl_rmse < 0.02


def test_physics_validator_catches_unphysical_monotonicity():
    """Tests that PhysicsValidator catches negative lift slope before stall."""
    # Defective model where lift drops between 2 and 4 deg
    defective_preds = [
        {"aoa": 0.0, "cl": 0.00, "cd": 0.007},
        {"aoa": 2.0, "cl": 0.35, "cd": 0.008},
        {"aoa": 4.0, "cl": 0.20, "cd": 0.009},  # Violation
    ]
    ground_truth = [
        {"aoa": 0.0, "cl": 0.00, "cd": 0.007},
        {"aoa": 2.0, "cl": 0.22, "cd": 0.008},
        {"aoa": 4.0, "cl": 0.44, "cd": 0.009},
    ]
    report = PhysicsValidator.validate_predictions(
        model_id="DEFECTIVE-MODEL",
        predictions=defective_preds,
        ground_truth=ground_truth
    )
    assert report.monotonicity_preserved is False
    assert any("Monotonicity violation" in f for f in report.findings)


def test_active_learning_uncertainty_candidates():
    """Tests that ActiveLearningEngine identifies high-uncertainty regions near stall and transonic onset."""
    known = [
        {"mach": 0.15, "aoa": 0.0},
        {"mach": 0.15, "aoa": 4.0},
    ]
    candidates = ActiveLearningEngine.identify_sampling_candidates(
        geometry="NACA 0012",
        existing_training_points=known,
        mach_grid=[0.15, 0.60],
        aoa_grid=[0.0, 16.0]
    )
    assert len(candidates) > 0
    top = candidates[0]
    assert top.estimated_uncertainty > 0.5
    # The point at M=0.60, AoA=16.0 should have highest uncertainty
    high_candidates = [c for c in candidates if c.mach >= 0.6 or c.aoa_deg >= 16.0]
    assert len(high_candidates) > 0
    assert high_candidates[0].sampling_priority == "HIGH"
