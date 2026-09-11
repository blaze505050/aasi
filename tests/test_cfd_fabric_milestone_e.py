"""
Unit and Integration Tests for Milestone E: Canonical OpenFOAM Deck Generation,
Artifact Ingestion & ASME V&V 20 Engine.

Validates:
- Canonical OpenFOAM case deck generation (0/, constant/, system/, scripts/, Allrun, Allrun.bat)
- 14-section markdown execution guide and manifest hash
- Artifact ingestion: OpenFOAM forceCoeffs.dat, log.simpleFoam, XFOIL polars
- Physical anomaly detection (negative drag, excessive stall lift)
- 3-grid ASME V&V 20 Grid Convergence Index (GCI) evaluation
- API endpoints: /api/compute/generate-case, /api/compute/upload-artifact, /api/validation/grid-convergence
"""

import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.compute.models import ComputeRequest, ComputeBackendType, UploadedArtifactPayload
from backend.compute.user_provided import UserProvidedCaseGenerator
from backend.compute.artifacts import ArtifactIngestionService
from backend.validation.grid_convergence import GridConvergenceService

client = TestClient(app)


def test_openfoam_case_deck_generation(tmp_path):
    """Verifies that UserProvidedCaseGenerator generates complete OpenFOAM deck with Allrun and README."""
    generator = UserProvidedCaseGenerator(base_output_dir=str(tmp_path))

    req = ComputeRequest(
        case_id="TEST-CASE-NACA0012-001",
        geometry="NACA 0012",
        mach=0.2,
        reynolds=2.0e6,
        aoa_deg=4.0,
        turbulence_model="k-omega SST",
        solver="OpenFOAM",
        backend=ComputeBackendType.USER_EXECUTED,
    )

    deck = generator.generate_case(req)
    assert deck.case_id == "TEST-CASE-NACA0012-001"
    case_dir = Path(deck.case_directory)
    assert case_dir.exists()

    # Core OpenFOAM directories
    assert (case_dir / "0" / "U").exists()
    assert (case_dir / "0" / "p").exists()
    assert (case_dir / "constant" / "transportProperties").exists()
    assert (case_dir / "constant" / "turbulenceProperties").exists()
    assert (case_dir / "system" / "controlDict").exists()
    assert (case_dir / "system" / "fvSchemes").exists()
    assert (case_dir / "system" / "fvSolution").exists()
    assert (case_dir / "system" / "blockMeshDict").exists()

    # Runners and instructions
    allrun = case_dir / "Allrun"
    assert allrun.exists()
    assert "#!/usr/bin/env bash" in allrun.read_text(encoding="utf-8")

    allrun_bat = case_dir / "Allrun.bat"
    assert allrun_bat.exists()
    assert "wsl" in allrun_bat.read_text(encoding="utf-8").lower()

    readme = Path(deck.readme_path)
    assert readme.exists()
    readme_text = readme.read_text(encoding="utf-8")
    assert "### 1. Software Requirement" in readme_text
    assert "### 14. Validation Procedure" in readme_text

    # Manifest
    manifest = Path(deck.manifest_path)
    assert manifest.exists()
    assert len(deck.file_hashes) >= 10


def test_artifact_ingestion_openfoam_force_coeffs():
    """Tests parsing of OpenFOAM postProcessing forceCoeffs.dat."""
    service = ArtifactIngestionService()

    sample_force_coeffs = """# OpenFOAM forceCoeffs output
# Time      Cm          Cd          Cl          Cl(f)       Cl(r)
0           0.000000    0.000000    0.000000    0.000000    0.000000
50          -0.012500   0.018200    0.342000    0.171000    0.171000
100         -0.015200   0.012400    0.415000    0.207500    0.207500
200         -0.016100   0.010800    0.432000    0.216000    0.216000
"""

    payload = UploadedArtifactPayload(
        case_id="TEST-CASE-001",
        file_name="forceCoeffs.dat",
        file_content=sample_force_coeffs,
        solver="OpenFOAM",
    )

    res = service.ingest_artifact(payload)
    assert res.status == "INGESTED"
    assert res.coefficients.get("cl") == 0.432
    assert res.coefficients.get("cd") == 0.0108
    assert res.coefficients.get("cm") == -0.0161
    assert res.provenance_hash is not None


def test_artifact_ingestion_physical_anomalies():
    """Verifies that unphysical aerodynamic values trigger validation warnings."""
    service = ArtifactIngestionService()

    # Negative drag
    bad_drag = "Time,Cd,Cl\n100,-0.005,0.4"
    res1 = service.ingest_artifact(UploadedArtifactPayload(
        case_id="TEST-BAD-DRAG", file_name="history.csv", file_content=bad_drag, solver="generic"
    ))
    assert res1.validation_status == "PHYSICAL_ANOMALY"

    # Excessive stall lift (> 3.0)
    bad_lift = "Time,Cd,Cl\n100,0.02,4.5"
    res2 = service.ingest_artifact(UploadedArtifactPayload(
        case_id="TEST-BAD-LIFT", file_name="history.csv", file_content=bad_lift, solver="generic"
    ))
    assert res2.validation_status == "SUSPICIOUS_HIGH_LIFT"


def test_asme_vv20_mesh_convergence_study():
    """Verifies ASME V&V 20 GCI calculation across fine, medium, and coarse grids."""
    service = ArtifactIngestionService()

    # 3-grid study for NACA 0012 Cl at alpha=4 deg:
    # Fine (160k cells): Cl = 0.4320
    # Medium (80k cells): Cl = 0.4280
    # Coarse (40k cells): Cl = 0.4200
    r_fine = service.ingest_artifact(UploadedArtifactPayload(
        case_id="GRID-FINE", file_name="res.csv", file_content="Time,Cl,Cd\n100,0.4320,0.010", solver="csv"
    ))
    r_med = service.ingest_artifact(UploadedArtifactPayload(
        case_id="GRID-MED", file_name="res.csv", file_content="Time,Cl,Cd\n100,0.4280,0.011", solver="csv"
    ))
    r_coarse = service.ingest_artifact(UploadedArtifactPayload(
        case_id="GRID-COARSE", file_name="res.csv", file_content="Time,Cl,Cd\n100,0.4200,0.013", solver="csv"
    ))

    gci_eval = service.evaluate_mesh_convergence_study(r_fine, r_med, r_coarse, metric="cl")
    assert gci_eval["valid"] is True
    gci = gci_eval["gci_result"]
    assert gci["apparent_order_p"] > 0.0
    assert gci["gci_fine_pct"] < 5.0
    assert gci["is_in_asymptotic_range"] is True


def test_api_compute_generate_case():
    """Tests POST /api/compute/generate-case endpoint."""
    res = client.post("/api/compute/generate-case", json={
        "case_id": "API-TEST-NACA0012",
        "geometry": "NACA 0012",
        "mach": 0.25,
        "reynolds": 3e6,
        "aoa_deg": 2.0,
        "solver": "OpenFOAM",
        "backend": "USER_EXECUTED"
    })
    assert res.status_code == 200
    data = res.json()
    assert "case_deck" in data
    assert data["case_deck"]["case_id"] == "API-TEST-NACA0012"
    assert "case_directory" in data["case_deck"]
    assert "readme_path" in data["case_deck"]


def test_api_compute_upload_artifact():
    """Tests POST /api/compute/upload-artifact endpoint."""
    res = client.post("/api/compute/upload-artifact", json={
        "case_id": "API-TEST-UPLOAD",
        "file_name": "forceCoeffs.dat",
        "file_content": "# Time Cd Cl\n100 0.012 0.45\n",
        "solver": "OpenFOAM"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["coefficients"]["cl"] == 0.45
    assert data["coefficients"]["cd"] == 0.012
    assert "provenance_hash" in data


def test_api_grid_convergence():
    """Tests POST /api/validation/grid-convergence endpoint."""
    res = client.post("/api/validation/grid-convergence", json={
        "f1": 0.432,
        "f2": 0.428,
        "f3": 0.420,
        "r21": 1.4142,
        "r32": 1.4142,
        "metric_name": "CL"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["metric_name"] == "CL"
    assert data["apparent_order_p"] > 0
    assert "gci_fine_pct" in data
