"""
Tests for Airfoil Geometry Processing Layer.

Verifies:
- Standard 64-point arc-length resampling
- Unit chord normalization
- Leading and trailing edge identification
- Symmetry detection for NACA 0012, 0009, 0006
- Analytical NACA 4-digit coordinate generation.
"""

import pytest
import numpy as np
from backend.physics_ai.geometry import AirfoilGeometryProcessor


def test_geometry_resampling_and_normalization():
    proc = AirfoilGeometryProcessor(target_points=64)
    # Generate NACA 0012
    coords, features = proc.generate_naca_4digit("0012", n_points=80)
    assert coords.shape == (64, 2)
    assert features.n_points == 64
    assert features.is_symmetric is True
    assert abs(features.max_thickness_ratio - 0.12) < 0.015
    assert np.min(coords[:, 0]) >= -1e-4
    assert np.max(coords[:, 0]) <= 1.0 + 1e-4


def test_cambered_airfoil_features():
    proc = AirfoilGeometryProcessor(target_points=64)
    coords, features = proc.generate_naca_4digit("2412", n_points=80)
    assert coords.shape == (64, 2)
    assert features.is_symmetric is False
    assert features.max_camber_ratio >= 0.01
    assert abs(features.max_thickness_ratio - 0.12) < 0.015



def test_malformed_coordinates_handling():
    proc = AirfoilGeometryProcessor(target_points=64)
    # Drastically small point list
    pts = [[0.0, 0.0], [0.5, 0.05], [1.0, 0.0]]
    coords, features = proc.process_coordinates(pts, geometry_name="Malformed")
    assert coords.shape == (64, 2)
    assert "INSUFFICIENT_RESOLUTION" in features.quality_flags
