"""
Integration test verifying authentic physics evaluation in /api/investigate.
Confirms panel solver and trained neural surrogate outputs without artificial multipliers.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_investigate_naca0012_real_physics():
    payload = {
        "objective": "Analyze the lift, drag and pitching moment of NACA 0012 at Re = 3e6 and alpha = 4°.",
        "preferred_provider": "COLAB",
    }
    response = client.post("/api/investigate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "investigation_id" in data
    assert "multi_fidelity_matrix" in data

    matrix = {entry["quantity"]: entry for entry in data["multi_fidelity_matrix"]}
    assert "Lift Coefficient (CL)" in matrix
    assert "Drag Coefficient (CD)" in matrix
    assert "Pitching Moment (CM)" in matrix

    # Analytical CL for NACA 0012 at alpha=4° calculated via discrete vortex panel method:
    # dCL/da ~ 2*pi*(1+0.77*0.12) -> CL ~ 0.48
    cl_analytical = matrix["Lift Coefficient (CL)"]["analytical"]
    assert cl_analytical is not None
    assert 0.45 <= cl_analytical <= 0.52

    # Surrogate CL for NACA 0012 at alpha=4° from trained AeroSurrogateV1 weights
    cl_surrogate = matrix["Lift Coefficient (CL)"]["surrogate"]
    assert cl_surrogate is not None
    assert 0.38 <= cl_surrogate <= 0.50

    # Ensure it's not the old faked calculation:
    # Old calculation was: round(2 * 3.14159 * (4 * 3.14159 / 180 + 0.07), 4) = 0.8784
    # which was unphysical for NACA 0012 at 4 degrees
    assert cl_analytical < 0.70

    # Viscous profile drag for NACA 0012 at Re=3e6 must be within physical envelope
    cd_analytical = matrix["Drag Coefficient (CD)"]["analytical"]
    assert cd_analytical is not None
    assert 0.007 <= cd_analytical <= 0.015


def test_investigate_naca4412_camber_effect():
    payload = {
        "objective": "Analyze aerodynamic polars of cambered profile NACA 4412 at alpha = 0° and Re = 3e6.",
        "preferred_provider": "COLAB",
    }
    response = client.post("/api/investigate", json=payload)
    assert response.status_code == 200

    data = response.json()
    matrix = {entry["quantity"]: entry for entry in data["multi_fidelity_matrix"]}

    # Cambered profile at zero angle of attack must have positive lift
    cl_analytical = matrix["Lift Coefficient (CL)"]["analytical"]
    assert cl_analytical is not None
    assert cl_analytical > 0.40
