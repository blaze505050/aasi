"""
API Tests for Phase 3 Evidence Reconciliation & Multi-Fidelity Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_evaluate_fidelity_attached(client):
    res = client.post(
        "/api/v1/evidence/evaluate-fidelity",
        json={
            "geometry": "NACA0012",
            "alpha_deg": 4.0,
            "mach": 0.15,
            "reynolds": 3000000.0,
            "requested_fidelity": "MULTI_FIDELITY",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["governing_regime"] == "INCOMPRESSIBLE_ATTACHED"
    assert data["requires_live_cfd"] is False
    assert "Discrete Vortex Panel" in data["recommended_solver"]


def test_api_evaluate_fidelity_transonic_escalation(client):
    res = client.post(
        "/api/v1/evidence/evaluate-fidelity",
        json={
            "geometry": "NACA0012",
            "alpha_deg": 2.0,
            "mach": 0.82,  # Transonic Mach number
            "reynolds": 6500000.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["governing_regime"] == "TRANSONIC_SHOCK"
    assert data["selected_tier"] == "LIVE_CFD"
    assert data["requires_live_cfd"] is True
    assert "OpenFOAM" in data["recommended_solver"]


def test_api_reconcile_investigation(client):
    res = client.post(
        "/api/v1/evidence/reconcile-investigation",
        json={
            "geometry": "NACA0012",
            "panel_results": {"CL": 0.485, "CD": 0.0075},
            "aerodb_results": {"cl": 0.44, "cd": 0.0062, "source": "Abbott 1945 Archive"},
            "benchmark_results": {"reference_cl": 0.44, "reference_cd": 0.0062, "uncertainty_pct": 2.5},
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["geometry"] == "NACA0012"
    assert data["items_count"] >= 4
    assert data["physical_consensus_valid"] is True
    assert data["consensus_cl"] is not None
    assert len(data["provenance_hash"]) == 64
