"""
API Tests for Scientific Compiler and DAG Execution endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_compiler_compile_endpoint(client):
    res = client.post(
        "/api/v1/compiler/compile",
        json={
            "source": 'INVESTIGATE "NACA0012 Alpha Test" { GEOMETRY "NACA0012" CONDITIONS { alpha: 4.0 deg } }',
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total_missions"] == 1
    dag = data["dags"][0]
    assert dag["node_count"] >= 6
    assert dag["stages_count"] >= 3
    assert len(dag["provenance_hash"]) == 64


def test_api_compiler_execute_endpoint(client):
    res = client.post(
        "/api/v1/compiler/execute",
        json={
            "source": 'INVESTIGATE "NACA0012 Run" { GEOMETRY "NACA0012" CONDITIONS { alpha: 3.0 deg } }',
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["completed_tasks"] >= 6
    assert data["failed_tasks"] == 0
    assert "t_solver_panel" in data["results"]
    assert len(data["provenance_hash"]) == 64


def test_api_compiler_compile_validation_error(client):
    res = client.post(
        "/api/v1/compiler/compile",
        json={
            "source": 'INVESTIGATE "Violation" { GEOMETRY "NACA0012" CONDITIONS { Mach: -0.5 } }',
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert "validation failed" in data["error"].lower()
