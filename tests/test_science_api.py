"""Tests for Phase 4 Science and Simulation REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestScienceAPIEndpoints:
    """Test all new scientific resolution and simulation endpoints."""

    def test_api_science_resolve_exact_match(self):
        res = client.post(
            "/api/science/resolve",
            json={"query": "What is the drag coefficient of NACA 0012 at Mach 0.3, Re 500k and AoA 8 deg?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert "LEVEL 2" in data["resolution_level"]
        assert data["primary_result"]["value"] == pytest.approx(0.0142, abs=1e-4)
        assert data["primary_result"]["quantity"] == "CD"
        assert "trace" in data

    def test_api_science_resolve_missing_parameters(self):
        res = client.post(
            "/api/science/resolve",
            json={"query": "What is the drag coefficient of NACA 0012?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "CLARIFICATION_NEEDED"
        assert "missing_conditions" in data
        assert len(data["missing_conditions"]) >= 3

    def test_api_science_normalize(self):
        res = client.post(
            "/api/science/normalize",
            json={"query": "NACA 0012 at Mach 0.3, Re=500000 and 8 deg angle of attack"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["geometry"] == "NACA 0012"
        assert data["mach"] == 0.3
        assert data["reynolds"] == 500000.0
        assert data["aoa_deg"] == 8.0
        assert data["flow_regime"] == "subsonic"

    def test_api_datasets_experimental(self):
        res = client.get("/api/datasets/experimental")
        assert res.status_code == 200
        data = res.json()
        assert "experimental_datasets" in data
        assert len(data["experimental_datasets"]) >= 1
        first = data["experimental_datasets"][0]
        assert "geometry" in first
        assert "facility" in first
        assert "uncertainty" in first

    def test_api_datasets_cfd(self):
        res = client.get("/api/datasets/cfd")
        assert res.status_code == 200
        data = res.json()
        assert "cfd_records" in data
        assert len(data["cfd_records"]) >= 1
        first = data["cfd_records"][0]
        assert "solver" in first
        assert "cell_count" in first
        assert "turbulence_model" in first

    def test_api_surrogates(self):
        res = client.get("/api/surrogates")
        assert res.status_code == 200
        data = res.json()
        assert "surrogates" in data
        assert len(data["surrogates"]) >= 1
        first = data["surrogates"][0]
        assert "model_id" in first
        assert "input_domain" in first

    def test_api_solvers(self):
        res = client.get("/api/solvers")
        assert res.status_code == 200
        data = res.json()
        assert "solvers" in data
        solver_names = [s["solver_name"] for s in data["solvers"]]
        assert "OpenFOAM" in solver_names
        assert "SU2" in solver_names
        assert "XFOIL" in solver_names
        assert "XFLR5" in solver_names

    def test_api_simulation_dry_run(self):
        res = client.post(
            "/api/simulations",
            json={
                "case_id": "API-TEST-NACA0012",
                "solver": "OpenFOAM",
                "geometry": "NACA 0012",
                "mach": 0.3,
                "reynolds": 500000.0,
                "aoa_deg": 8.0,
                "turbulence_model": "k-omega SST",
                "mesh_cells": 16384,
                "run_mode": "DRY_RUN",
                "max_iterations": 1000,
                "convergence_tolerance": 1e-6,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["result_status"] == "DRY_RUN_VERIFIED"
        assert data["solver"] == "OpenFOAM"
        assert data["experiment_id"] == "EXP-API-TEST-NACA0012"
        assert "input_checksum" in data
