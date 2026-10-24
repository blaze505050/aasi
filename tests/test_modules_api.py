"""
Integration tests for AASI Problem Modules and Benchmark Registry REST API.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_api_list_modules(client):
    """Verify GET /api/modules returns catalog of registered modules."""
    response = client.get("/api/modules")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_modules"] >= 2
    module_ids = [m["module_id"] for m in data["modules"]]
    assert "airfoil_2d_panel" in module_ids
    assert "aero_3d_vlm" in module_ids


def test_api_get_module_detail(client):
    """Verify GET /api/modules/{id} returns module specification and benchmarks."""
    response = client.get("/api/modules/aero_3d_vlm")
    assert response.status_code == 200
    data = response.json()
    assert data["module_id"] == "aero_3d_vlm"
    assert data["problem_id"] == 1
    assert data["tier"] == 1
    assert "L1_REDUCED_ORDER" in data["supported_fidelities"]
    assert len(data["benchmarks"]) >= 3


def test_api_solve_vlm_module(client):
    """Verify POST /api/modules/aero_3d_vlm/solve returns deterministic results with evidence."""
    payload = {
        "fidelity": "L1_REDUCED_ORDER",
        "inputs": {
            "span": 2.3926,
            "root_chord": 0.8059,
            "tip_chord": 0.4529,
            "sweep_le_deg": 30.0,
            "alpha_deg": 3.06,
            "mach": 0.20,
        },
    }
    response = client.post("/api/modules/aero_3d_vlm/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["module_id"] == "aero_3d_vlm"
    assert "CL" in data["outputs"]
    assert "CDi" in data["outputs"]
    assert "evidence" in data
    assert len(data["evidence"]["provenance_hash"]) == 64


def test_api_module_uncertainty(client):
    """Verify POST /api/modules/airfoil_2d_panel/uncertainty returns GUM 95% intervals."""
    inputs = {"airfoil": "NACA 0012", "alpha_deg": 6.0}
    response = client.post("/api/modules/airfoil_2d_panel/uncertainty", json=inputs)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "QUANTIFIED"
    assert data["coverage_factor_k"] == 1.96
    assert "cl_uncertainty_u95" in data


def test_api_run_continuous_validation(client):
    """Verify POST /api/modules/benchmarks/run-all executes full platform validation."""
    response = client.post("/api/modules/benchmarks/run-all")
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "ALL_BENCHMARKS_PASSED"
    assert data["total_failed"] == 0
    assert data["total_benchmark_cases"] >= 7
    assert len(data["provenance_hash"]) == 64
