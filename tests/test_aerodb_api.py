"""
API Integration Tests for Aerodynamic Database (Aero DB) Routes.
Verifies POST /api/aerodb/generate, GET /api/aerodb/{id}, and format exports.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_aerodb_generate_and_retrieve(client):
    """Test generating an Aero DB via POST and retrieving via GET."""
    payload = {
        "geometry": "NACA 0012",
        "alpha_min": -2.0,
        "alpha_max": 6.0,
        "alpha_step": 2.0,
        "reynolds_list": [3_000_000.0],
        "mach_list": [0.15],
    }

    # 1. Generate
    res = client.post(
        "/api/aerodb/generate",
        json=payload,
        headers={"X-User-Id": "chief_aero", "X-User-Role": "ADMIN"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "db_id" in data
    assert data["geometry_name"] == "NACA 0012"
    assert len(data["polars"]) == 1
    db_id = data["db_id"]

    # 2. Retrieve by ID
    get_res = client.get(
        f"/api/aerodb/{db_id}",
        headers={"X-User-Id": "chief_aero", "X-User-Role": "ADMIN"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["db_id"] == db_id

    # 3. Export DATCOM
    datcom_res = client.get(
        f"/api/aerodb/{db_id}/export?format=datcom",
        headers={"X-User-Id": "chief_aero", "X-User-Role": "ADMIN"},
    )
    assert datcom_res.status_code == 200
    assert "$FLTCON" in datcom_res.text
    assert "attachment" in datcom_res.headers.get("content-disposition", "")

    # 4. Export CSV
    csv_res = client.get(
        f"/api/aerodb/{db_id}/export?format=csv",
        headers={"X-User-Id": "chief_aero", "X-User-Role": "ADMIN"},
    )
    assert csv_res.status_code == 200
    assert "alpha_deg" in csv_res.text
    assert "text/csv" in csv_res.headers.get("content-type", "")

    # 5. Export S/HABP
    shabp_res = client.get(
        f"/api/aerodb/{db_id}/export?format=shabp",
        headers={"X-User-Id": "chief_aero", "X-User-Role": "ADMIN"},
    )
    assert shabp_res.status_code == 200
    assert "$TABLE" in shabp_res.text
