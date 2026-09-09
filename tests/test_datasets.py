"""Tests for Phase 3 Physical Dataset Registry, CFD Data Schema, and Physics AI interfaces."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.knowledge.dataset_registry import DatasetRegistry
from backend.knowledge.models import CFDClassification, CFDDataModel, Dataset, Provenance
from backend.physics.models import (
    AeroGraphNetModel,
    DoMINOModel,
    FNOModel,
    GNNModel,
    MeshGraphNetModel,
    PINNModel,
    PINOModel,
    PhysicsModelType,
    PhysicsNeMoModel,
)

client = TestClient(app)


class TestCFDDataModelAndClassification:
    """Test CFD physics data schema and classification."""

    def test_cfd_metadata_schema_validation(self):
        cfd = CFDDataModel(
            geometry="NACA 0012",
            mesh="Structured C-grid, 250k cells, y+ < 1",
            solver="OpenFOAM v2312",
            governing_equations="2D Steady Incompressible RANS",
            mach=0.3,
            reynolds=500000.0,
            aoa_deg=8.0,
            turbulence_model="Spalart-Allmaras",
            convergence_criteria="Residuals < 1e-6",
            cl=0.815,
            cd=0.0145,
            cm=-0.0028,
            classification=CFDClassification.REFERENCE_CFD,
        )
        assert cfd.geometry == "NACA 0012"
        assert cfd.mach == 0.3
        assert cfd.reynolds == 500000.0
        assert cfd.cl == 0.815
        assert cfd.classification == CFDClassification.REFERENCE_CFD

    def test_cfd_classifications_are_distinct(self):
        classifications = [c.value for c in CFDClassification]
        assert "REFERENCE_CFD" in classifications
        assert "NEW_CFD" in classifications
        assert "ML_SURROGATE" in classifications
        assert len(classifications) == 3


class TestDatasetRegistryAndConditionSearch:
    """Test physical dataset registration and condition-based search."""

    def test_dataset_registry_registration_and_retrieval(self):
        reg = DatasetRegistry()
        ds = Dataset(
            dataset_id="TEST-EXP-001",
            name="NACA 0012 Test",
            source="NASA Langley",
            geometry="NACA 0012",
            conditions={"Mach": 0.3, "Reynolds": 500000.0},
            citation="NASA TN-D-628",
            checksum="test-checksum-123",
            data_points=[
                {"aoa": 0.0, "cl": 0.000, "cd": 0.0080},
                {"aoa": 8.0, "cl": 0.820, "cd": 0.0142},
            ],
        )
        reg.register(ds)
        assert reg.get("TEST-EXP-001") is not None
        assert len(reg.list_datasets()) == 1

    def test_exact_condition_search_match(self):
        reg = DatasetRegistry()
        ds = Dataset(
            dataset_id="EXP-NACA0012",
            name="NACA 0012 Wind Tunnel",
            source="NASA Langley",
            geometry="NACA 0012",
            conditions={"Mach": 0.3, "Reynolds": 500000.0},
            citation="NASA TN-D-628",
            checksum="chk-456",
            uncertainty={"cd": 0.0005, "cl": 0.015},
            data_points=[
                {"aoa": 4.0, "cl": 0.412, "cd": 0.0096},
                {"aoa": 8.0, "cl": 0.820, "cd": 0.0142},
            ],
        )
        reg.register(ds)

        matches = reg.query_conditions(
            geometry="NACA 0012",
            mach=0.3,
            reynolds=500000.0,
            aoa_deg=8.0,
        )
        assert len(matches) == 1
        matched_pts = matches[0]["matched_points"]
        assert len(matched_pts) == 1
        assert matched_pts[0]["cd"] == 0.0142
        assert matched_pts[0]["cl"] == 0.820

    def test_out_of_envelope_condition_returns_no_match(self):
        reg = DatasetRegistry()
        ds = Dataset(
            dataset_id="EXP-NACA0012",
            name="NACA 0012 Wind Tunnel",
            source="NASA",
            geometry="NACA 0012",
            conditions={"Mach": 0.3, "Reynolds": 500000.0},
            citation="NASA TN-D-628",
            checksum="chk-789",
            data_points=[{"aoa": 8.0, "cl": 0.820, "cd": 0.0142}],
        )
        reg.register(ds)

        # Query hypersonic Mach 6.0 condition for subsonic low-speed dataset
        matches = reg.query_conditions(
            geometry="NACA 0012",
            mach=6.0,
            reynolds=500000.0,
            aoa_deg=8.0,
        )
        # Must return empty list rather than fabricating a number
        assert len(matches) == 0


class TestPhysicsAISurrogateInterfaces:
    """Test Phase 4 physics surrogate model interfaces."""

    def test_physics_model_stubs_raise_not_implemented(self):
        models = [
            PINNModel(),
            PINOModel(),
            FNOModel(),
            GNNModel(),
            DoMINOModel(),
            MeshGraphNetModel(),
            AeroGraphNetModel(),
            PhysicsNeMoModel(),
        ]
        for m in models:
            assert m.metadata.status == "PLANNED_PHASE_4"
            with pytest.raises(NotImplementedError) as exc_info:
                m.predict({"Mach": 0.3})
            assert "Phase 4" in str(exc_info.value)


class TestDatasetAPIEndpoints:
    """Test Dataset API endpoints."""

    def test_api_datasets_list(self):
        res = client.get("/api/knowledge/datasets")
        assert res.status_code == 200
        data = res.json()
        assert "datasets" in data
        assert len(data["datasets"]) >= 2

    def test_api_dataset_detail(self):
        res = client.get("/api/knowledge/datasets/AASI-EXP-AERO-NACA0012-M03-RE5E5")
        assert res.status_code == 200
        ds = res.json()
        assert ds["geometry"] == "NACA 0012"
        assert ds["is_experimental"] is True
        assert len(ds["data_points"]) >= 7

    def test_api_dataset_condition_query(self):
        res = client.post(
            "/api/knowledge/datasets/query",
            json={
                "geometry": "NACA 0012",
                "mach": 0.3,
                "reynolds": 500000.0,
                "aoa_deg": 8.0,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["match_count"] >= 1
        first_match = data["matches"][0]
        assert first_match["matched_points"][0]["cd"] == 0.0142
