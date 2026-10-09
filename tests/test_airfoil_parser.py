"""
Unit and Integration Tests for AASI Airfoil Parser & Geometry Engine.
Verifies parsing of Selig, Lednicer, CSV, and analytical NACA profiles,
geometric normalization, coordinate de-rotation, and curvature re-paneling.
"""

import numpy as np
import pytest
from backend.physics.airfoil_parser import (
    AirfoilCoordinateParser,
    AirfoilGeometry,
    AirfoilParseError,
)


def test_naca4_analytical_synthesis():
    """Verify NACA 4-digit analytical generator produces correct geometry and metrics."""
    geom = AirfoilCoordinateParser.generate_naca4("NACA 4412", num_points=120)
    assert isinstance(geom, AirfoilGeometry)
    assert geom.name == "NACA 4412"
    assert abs(geom.point_count - 120) <= 2
    # NACA 4412: max thickness is 12% chord, max camber is 4% chord
    assert pytest.approx(geom.max_thickness, abs=0.015) == 0.12
    assert pytest.approx(geom.max_camber, abs=0.015) == 0.04
    assert geom.leading_edge_radius > 0
    # Coordinates must start and end near trailing edge (x=1.0)
    assert pytest.approx(geom.coordinates[0, 0], abs=0.05) == 1.0
    assert pytest.approx(geom.coordinates[-1, 0], abs=0.05) == 1.0


def test_parse_selig_format():
    """Verify standard Selig format (TE upper -> LE -> TE lower loop) parsing."""
    selig_data = """NACA 0012 Test Profile
1.000000  0.001260
0.950000  0.014780
0.800000  0.045620
0.500000  0.060000
0.200000  0.045620
0.050000  0.023240
0.000000  0.000000
0.050000 -0.023240
0.200000 -0.045620
0.500000 -0.060000
0.800000 -0.045620
0.950000 -0.014780
1.000000 -0.001260
"""
    geom = AirfoilCoordinateParser.parse_text(selig_data)
    assert "NACA 0012" in geom.name
    assert geom.point_count >= 50
    # Symmetric airfoil should have nearly zero camber
    assert geom.max_camber < 0.01
    assert pytest.approx(geom.max_thickness, abs=0.02) == 0.12


def test_parse_lednicer_format():
    """Verify Lednicer format (header with counts, upper section, lower section) parsing."""
    lednicer_data = """CLARK Y AIRFOIL
6. 6.
0.000000  0.000000
0.100000  0.065000
0.300000  0.117000
0.500000  0.110000
0.750000  0.070000
1.000000  0.001000

0.000000  0.000000
0.100000 -0.035000
0.300000 -0.040000
0.500000 -0.038000
0.750000 -0.025000
1.000000 -0.001000
"""
    geom = AirfoilCoordinateParser.parse_text(lednicer_data)
    assert "CLARK Y" in geom.name
    assert geom.point_count >= 50
    assert geom.max_thickness > 0.10
    assert geom.max_camber > 0.02


def test_parse_csv_format():
    """Verify comma-separated coordinate table parsing."""
    csv_data = """x,y
1.0, 0.002
0.8, 0.04
0.5, 0.06
0.2, 0.04
0.0, 0.0
0.2, -0.04
0.5, -0.06
0.8, -0.04
1.0, -0.002
"""
    geom = AirfoilCoordinateParser.parse_text(csv_data, default_name="Custom_CSV_Foil")
    assert geom.name == "Custom_CSV_Foil"
    assert geom.point_count >= 50
    assert geom.max_thickness > 0.05


def test_invalid_airfoil_handling():
    """Verify corrupted or empty coordinate text raises informative AirfoilParseError."""
    with pytest.raises(AirfoilParseError):
        AirfoilCoordinateParser.parse_text("")

    with pytest.raises(AirfoilParseError):
        AirfoilCoordinateParser.parse_text("Only two lines\n0.0 0.0\n")

    with pytest.raises(AirfoilParseError):
        AirfoilCoordinateParser.parse_text("Word only\nNo numbers\nHere at all\nLine 4\nLine 5\nLine 6\n")
