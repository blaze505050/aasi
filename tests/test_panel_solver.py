"""
Unit and physical benchmark tests for the AASI Discrete Vortex Panel Solver.
"""

import math
import pytest
import numpy as np

from backend.physics.panel_solver import (
    AerodynamicPanelSolver,
    generate_naca4_coordinates,
    calculate_airfoil_aerodynamics,
)
from backend.tools.registry import tool_registry


def test_naca_coordinate_generation():
    coords = generate_naca4_coordinates("0012", 100)
    assert coords.ndim == 2
    assert coords.shape[1] == 2
    # Check leading edge (min x close to 0) and trailing edge (max x close to 1)
    assert np.min(coords[:, 0]) <= 0.01
    assert np.max(coords[:, 0]) >= 0.99
    # Symmetric airfoil should have symmetric y bounds
    assert abs(np.max(coords[:, 1]) + np.min(coords[:, 1])) < 0.01


def test_panel_solver_symmetric_lift_slope():
    solver = AerodynamicPanelSolver()
    solver.set_naca("0012")

    res_0 = solver.solve(alpha_deg=0.0)
    res_4 = solver.solve(alpha_deg=4.0)
    res_8 = solver.solve(alpha_deg=8.0)

    # Symmetric profile at alpha=0 must have zero lift
    assert abs(res_0["CL"]) < 1e-4

    # Monotonic lift increase
    assert res_4["CL"] > res_0["CL"]
    assert res_8["CL"] > res_4["CL"]

    # Theoretical lift slope for thin airfoil is 2*pi per radian (~0.11 per degree)
    # With 12% thickness correction: ~0.115 - 0.122 per degree
    lift_slope_per_deg = (res_8["CL"] - res_0["CL"]) / 8.0
    assert 0.10 <= lift_slope_per_deg <= 0.13


def test_cambered_airfoil_positive_zero_alpha_lift():
    solver = AerodynamicPanelSolver()
    solver.set_naca("4412")

    res_0 = solver.solve(alpha_deg=0.0)
    # NACA 4412 has 4% camber -> CL at alpha=0 is ~0.45 - 0.55 in experimental data
    assert res_0["CL"] > 0.40
    assert res_0["CM"] < 0.0  # Cambered airfoils have negative pitching moment at alpha=0


def test_viscous_drag_physical_bounds():
    solver = AerodynamicPanelSolver()
    solver.set_naca("0012")

    res = solver.solve(alpha_deg=4.0, reynolds=3e6)
    # Profile drag for NACA 0012 at Re=3e6 is typically 0.007 - 0.012
    assert 0.006 <= res["CD"] <= 0.015

    # Higher Reynolds number should have lower skin friction
    res_high_re = solver.solve(alpha_deg=4.0, reynolds=1e7)
    assert res_high_re["CD"] < res["CD"]


def test_compressibility_scaling():
    solver = AerodynamicPanelSolver()
    solver.set_naca("0012")

    res_subsonic = solver.solve(alpha_deg=4.0, mach=0.1)
    res_compressible = solver.solve(alpha_deg=4.0, mach=0.5)

    # Karman-Tsien/Prandtl-Glauert increases lift with Mach number (1/sqrt(1-M^2))
    assert res_compressible["CL"] > res_subsonic["CL"]


def test_tool_registry_aerodynamics_execution():
    res = tool_registry.execute(
        "aerodynamics",
        "airfoil_polar",
        geometry="NACA 0012",
        alpha_deg=4.0,
        reynolds=3000000.0,
        mach=0.15,
    )
    assert res["tool"] == "aerodynamics"
    assert "CL" in res["results"]
    assert "CD" in res["results"]
    assert res["results"]["CL"] > 0.4
    assert res["results"]["CD"] > 0.005
