"""
Tests for Phase 6 FastAPI Endpoints.

Verifies:
- POST /api/physics/aerodynamics/predict
- POST /api/physics/aerodynamics/polar
- GET /api/physics/aerodynamics/model-status
- GET /api/physics/audit/datasets
- POST /api/validation/grid-convergence
- GET /api/validation/grid-convergence/benchmarks
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_predict_aerodynamics():
    response = client.post(
        "/api/physics/aerodynamics/predict",
        json={"geometry": "naca0012", "mach": 0.2, "reynolds": 2.0e6, "aoa_deg": 4.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert "cl" in data
    assert "cd" in data
    assert "cm" in data
    assert data["cd"] > 0.0
    assert data["domain_status"] == "IN_DOMAIN"
    assert data["uncertainty"]["confidence_level"] == "HIGH"


def test_api_polar_sweep():
    response = client.post(
        "/api/physics/aerodynamics/polar",
        json={"geometry": "naca0012", "mach": 0.2, "reynolds": 2.0e6, "aoa_start": -2.0, "aoa_end": 6.0, "aoa_step": 2.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["points"]) == 5
    assert data["sweep_validation"]["is_sweep_valid"] is True


def test_api_surrogate_model_status():
    response = client.get("/api/physics/aerodynamics/model-status")
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "AERO_SURROGATE_V1"
    assert len(data["sha256_checksum"]) == 64
    assert data["parameters"] > 10000


def test_api_audit_datasets():
    response = client.get("/api/physics/audit/datasets")
    assert response.status_code == 200
    data = response.json()
    assert data["verified_count"] >= 1
    assert data["metadata_only_count"] >= 3


def test_api_grid_convergence():
    response = client.post(
        "/api/validation/grid-convergence",
        json={
            "f1": 0.4285,
            "f2": 0.4210,
            "f3": 0.4070,
            "r21": 1.4142,
            "r32": 1.4142,
            "safety_factor": 1.25,
            "metric_name": "CL"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["apparent_order_p"] > 1.0
    assert data["gci_fine_pct"] > 0.0


def test_api_grid_convergence_benchmarks():
    response = client.get("/api/validation/grid-convergence/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert "lift_analysis" in data
    assert "drag_analysis" in data
