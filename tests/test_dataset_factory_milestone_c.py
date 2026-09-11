"""
Unit and Integration Tests for Milestone C: Real Dataset Factory & Transparent Download Manager.

Validates:
- StorageStatus classification (AVAILABLE_LOCAL vs AVAILABLE_REMOTE_DIRECT / MANUAL)
- Disk space pre-flight verification and hardware quota protection
- UIUC Airfoil coordinate parser (chord normalization, thickness, camber calculation)
- NASA TMR benchmark verification case comparisons
- API endpoints: /api/datasets/storage-summary, /api/datasets/tmr-benchmarks, /api/datasets/airfoil/parse-geometry
"""

import pytest
import shutil
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.datasets.models import DatasetManifest, StorageStatus, DatasetLifecycle
from backend.datasets.catalog import DatasetCatalog
from backend.datasets.download import DownloadManager
from backend.datasets.authentic_parsers import (
    UIUCAirfoilParser,
    NASATMRParser,
    AirfoilGeometryFeatures,
)

client = TestClient(app)


def test_storage_status_classification():
    """Verifies that dataset catalog honestly separates physically local datasets from remote repositories."""
    catalog = DatasetCatalog()
    local = catalog.get_local_datasets()
    remote = catalog.get_remote_datasets()

    assert len(local) >= 3
    assert len(remote) >= 2

    local_ids = {m.dataset_id for m in local}
    assert "DATASET-AUTHENTIC-AIRFOILS-V1" in local_ids
    assert "DATASET-UIUC-COORDINATES" in local_ids

    remote_ids = {m.dataset_id for m in remote}
    assert "DATASET-AIRFRANS-1K" in remote_ids
    assert "DATASET-NASA-CRM-TRANSONIC" in remote_ids

    airfrans = catalog.get_manifest("DATASET-AIRFRANS-1K")
    assert airfrans.storage_status == StorageStatus.AVAILABLE_REMOTE_DIRECT

    crm = catalog.get_manifest("DATASET-NASA-CRM-TRANSONIC")
    assert crm.storage_status == StorageStatus.AVAILABLE_REMOTE_MANUAL


def test_download_manager_disk_space_guardrail(tmp_path):
    """Verifies that DownloadManager aborts download if host physical disk space is insufficient."""
    manager = DownloadManager(cache_dir=str(tmp_path))

    manifest = DatasetManifest(
        dataset_id="TEST-MODERATE-DATASET",
        name="Moderate Dataset",
        source="Test",
        license="CC-BY-4.0",
        citation="Test",
        url="https://example.com/data.dat",
        checksum="abcd"*16,
        size_bytes=500_000_000,  # 500 MB
        domain="AERODYNAMICS",
        geometry="NACA 0012",
        resolution="Coarse",
        experimental_or_simulated="SIMULATED",
    )

    # Mock disk_usage to return only 100 MB free (less than 500 MB + buffer)
    mock_stat = shutil._ntuple_diskusage(total=10**10, used=9.9*10**9, free=100*1024*1024)
    with patch("shutil.disk_usage", return_value=mock_stat):
        res = manager.download_dataset(manifest)
        assert res["success"] is False
        assert "Insufficient free disk space" in res["error"]


def test_download_manager_successful_verification(tmp_path):
    """Verifies that download manager sets local path, byte hash, and storage status on success."""
    manager = DownloadManager(cache_dir=str(tmp_path))

    manifest = DatasetManifest(
        dataset_id="TEST-DOWNLOAD-OK",
        name="Test Valid Download",
        source="Test",
        license="Public Domain",
        citation="Test",
        url="https://example.com/test.dat",
        checksum="mock_hash",
        size_bytes=1024,
        domain="AERODYNAMICS",
        geometry="NACA 0012",
        resolution="Coarse",
        experimental_or_simulated="EXPERIMENTAL",
    )

    mock_bytes = b"Authentic aerodynamic measurements alpha,CL,CD\n0.0,0.0,0.008\n"
    res = manager.download_dataset(manifest, mock_content=mock_bytes)

    assert res["success"] is True
    assert res["storage_status"] == StorageStatus.AVAILABLE_LOCAL.value
    assert manifest.storage_status == StorageStatus.AVAILABLE_LOCAL
    assert manifest.local_path is not None
    assert manifest.verified_byte_hash is not None
    assert manifest.lifecycle_stage == DatasetLifecycle.DOWNLOADED


def test_uiuc_airfoil_parser_symmetric():
    """Tests UIUC coordinate parser on NACA 0012 profile."""
    # Synthetic clean NACA 0012 coordinates
    coords_text = """NACA 0012
 1.0000   0.0013
 0.9500   0.0084
 0.8000   0.0262
 0.6000   0.0456
 0.4000   0.0580
 0.3000   0.0600
 0.2000   0.0574
 0.1000   0.0468
 0.0500   0.0356
 0.0000   0.0000
 0.0500  -0.0356
 0.1000  -0.0468
 0.2000  -0.0574
 0.3000  -0.0600
 0.4000  -0.0580
 0.6000  -0.0456
 0.8000  -0.0262
 0.9500  -0.0084
 1.0000  -0.0013
"""
    geom = UIUCAirfoilParser.parse_coordinate_text(coords_text, "NACA 0012")
    assert geom.airfoil_name == "NACA 0012"
    assert geom.is_symmetric is True
    # Max thickness should be approx 0.12 (0.06 upper - (-0.06) lower)
    assert 0.11 <= geom.max_thickness_ratio <= 0.13
    assert 0.25 <= geom.max_thickness_xc <= 0.35
    assert geom.max_camber_ratio < 0.005


def test_uiuc_airfoil_parser_invalid():
    """Tests error handling for degenerate or insufficient coordinates."""
    with pytest.raises(ValueError, match="Insufficient coordinate points"):
        UIUCAirfoilParser.parse_coordinate_text("1.0 0.0\n0.5 0.05\n0.0 0.0")


def test_nasa_tmr_parser_benchmarks():
    """Tests NASA TMR benchmark verification case retrieval and evaluation."""
    cases = NASATMRParser.list_benchmarks()
    assert len(cases) >= 2

    flat_plate = NASATMRParser.get_benchmark("NASA-TMR-2D-FLATPLATE")
    assert flat_plate is not None
    assert flat_plate.reynolds == 5.0e6
    assert "cf_x_0_97_SA" in flat_plate.benchmark_quantities

    # Evaluate simulated value with 1.4% error
    eval_res = NASATMRParser.evaluate_simulation_against_tmr(
        "NASA-TMR-2D-FLATPLATE",
        {"cf_x_0_97_SA": 0.00280}
    )
    assert eval_res["valid"] is True
    cf_res = eval_res["comparison"]["cf_x_0_97_SA"]
    assert cf_res["relative_difference_pct"] < 2.0
    assert cf_res["acceptable_agreement"] is True


def test_api_dataset_storage_summary():
    """Tests GET /api/datasets/storage-summary."""
    res = client.get("/api/datasets/storage-summary")
    assert res.status_code == 200
    data = res.json()
    assert "local_datasets_count" in data
    assert "remote_datasets_count" in data
    assert data["local_datasets_count"] >= 3
    assert "disk_info" in data


def test_api_dataset_tmr_benchmarks():
    """Tests GET /api/datasets/tmr-benchmarks."""
    res = client.get("/api/datasets/tmr-benchmarks")
    assert res.status_code == 200
    data = res.json()
    assert "benchmarks" in data
    assert len(data["benchmarks"]) >= 2


def test_api_airfoil_parse_geometry():
    """Tests POST /api/datasets/airfoil/parse-geometry."""
    coords_text = """NACA 0012
 1.0000   0.0013
 0.8000   0.0262
 0.5000   0.0530
 0.3000   0.0600
 0.1000   0.0468
 0.0000   0.0000
 0.1000  -0.0468
 0.3000  -0.0600
 0.5000  -0.0530
 0.8000  -0.0262
 1.0000  -0.0013
"""
    res = client.post("/api/datasets/airfoil/parse-geometry", json={"raw_coordinates": coords_text})
    assert res.status_code == 200
    data = res.json()
    assert data["airfoil_name"] == "NACA 0012"
    assert data["is_symmetric"] is True
    assert 0.11 <= data["max_thickness_ratio"] <= 0.13
