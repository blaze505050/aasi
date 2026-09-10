"""
Tests for Phase 5 REST API Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_sources_list():
    """Tests GET /api/sources."""
    res = client.get("/api/sources")
    assert res.status_code == 200
    data = res.json()
    assert "sources" in data
    assert len(data["sources"]) >= 10


def test_api_sources_detail():
    """Tests GET /api/sources/NASA_NTRS."""
    res = client.get("/api/sources/NASA_NTRS")
    assert res.status_code == 200
    data = res.json()
    assert data["organization"] == "NASA"
    assert data["public_access"] is True


def test_api_sources_nasa_search():
    """Tests GET /api/sources/nasa/search."""
    res = client.get("/api/sources/nasa/search?q=NACA")
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) > 0


def test_api_sources_isro_search():
    """Tests GET /api/sources/isro/search."""
    res = client.get("/api/sources/isro/search?q=Chandrayaan")
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) > 0


def test_api_current_info():
    """Tests GET /api/current-info."""
    res = client.get("/api/current-info")
    assert res.status_code == 200
    data = res.json()
    assert "events" in data
    assert len(data["events"]) >= 3
    assert data["events"][0]["label"] == "CURRENT_INFORMATION"


def test_api_dataset_catalog():
    """Tests GET /api/datasets/catalog."""
    res = client.get("/api/datasets/catalog")
    assert res.status_code == 200
    data = res.json()
    assert "datasets" in data
    assert len(data["datasets"]) >= 3


def test_api_compute_generate_case():
    """Tests POST /api/compute/generate-case."""
    payload = {
        "case_id": "API-TEST-CASE-GEN",
        "geometry": "NACA 0012",
        "mach": 0.15,
        "reynolds": 3000000.0,
        "aoa_deg": 4.0,
        "backend": "USER_EXECUTED"
    }
    res = client.post("/api/compute/generate-case", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "AWAITING_USER_UPLOAD"
    assert "case_deck" in data
    assert "readme_path" in data["case_deck"]


def test_api_compute_upload_artifact():
    """Tests POST /api/compute/upload-artifact."""
    payload = {
        "case_id": "API-TEST-CASE-GEN",
        "solver": "openfoam",
        "file_name": "coefficient.dat",
        "file_content": "1000  0.00762  0.4410  -0.0123"
    }
    res = client.post("/api/compute/upload-artifact", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "INGESTED"
    assert data["coefficients"]["cd"] == pytest.approx(0.00762, abs=1e-5)


def test_api_physics_models():
    """Tests GET /api/physics/models."""
    res = client.get("/api/physics/models")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    assert len(data["models"]) >= 2


def test_api_physics_active_learning():
    """Tests POST /api/physics/active-learning."""
    res = client.post("/api/physics/active-learning", json={"geometry": "NACA 0012", "reynolds": 3e6})
    assert res.status_code == 200
    data = res.json()
    assert "candidates" in data
    assert len(data["candidates"]) > 0


def test_api_graph_entities_and_neighbors():
    """Tests GET /api/graph/entities and /api/graph/neighbors."""
    res = client.get("/api/graph/entities?q=NACA")
    assert res.status_code == 200
    data = res.json()
    assert len(data["entities"]) > 0

    res_n = client.get("/api/graph/neighbors/AF-NACA0012")
    assert res_n.status_code == 200
    data_n = res_n.json()
    assert len(data_n["neighbors"]) > 0
