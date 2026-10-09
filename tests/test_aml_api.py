"""
API Tests for Aerospace Mission Language (AML) and Tool Bus endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_aml_parse_endpoint(client):
    res = client.post(
        "/api/v1/aml/parse",
        json={"source": 'INVESTIGATE "NACA0012 Alpha Sweep" { GEOMETRY "NACA0012" }'},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["statement_count"] == 1
    assert data["ast"]["statements"][0]["geometry"] == "NACA0012"


def test_api_aml_parse_syntax_error(client):
    res = client.post(
        "/api/v1/aml/parse",
        json={"source": "INVESTIGATE { unterminated block"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["error"] is not None


def test_api_aml_validate_endpoint_valid(client):
    res = client.post(
        "/api/v1/aml/validate",
        json={"source": 'INVESTIGATE "Physical Test" { GEOMETRY "NACA0012" CONDITIONS { Mach: 0.2, Re: 3000000.0, alpha: 4.0 deg } }'},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["error_count"] == 0


def test_api_aml_validate_endpoint_invalid(client):
    res = client.post(
        "/api/v1/aml/validate",
        json={"source": 'INVESTIGATE "Physical Violation" { GEOMETRY "NACA0012" CONDITIONS { Mach: -0.5, Re: -100.0 } }'},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert data["error_count"] >= 2


def test_api_aml_contracts_catalog(client):
    res = client.get("/api/v1/aml/contracts")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 4
    tool_names = [c["tool_id"] for c in data["contracts"]]
    assert "aerodynamics" in tool_names
    assert "orbit" in tool_names


def test_api_aml_contract_execution_provenance(client):
    res = client.post(
        "/api/v1/aml/contracts/execute",
        json={
            "tool_id": "aerodynamics",
            "operation": "airfoil_polar",
            "parameters": {
                "geometry": "NACA0012",
                "alpha_deg": 5.0,
                "reynolds": 1000000.0,
                "mach": 0.15,
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["provenance_hash"] != ""
    assert "cl" in data["output"]


def test_api_aml_autonomy_levels(client):
    res = client.get("/api/v1/aml/autonomy-levels")
    assert res.status_code == 200
    data = res.json()
    assert len(data["levels"]) == 6
    assert data["levels"][0]["level"] == "L0_ADVISORY"
    assert data["levels"][5]["level"] == "L5_AUTONOMOUS"
    assert "default_envelope" in data
