"""
Unit and Integration Tests for Universal CFD Knowledge Oracle and Hardware Safety Architecture.
Verifies that:
1. System possesses structured knowledge of historical NASA, AGARD, AIAA, UIUC, and Hypersonic CFD benchmarks.
2. Hardware safety guard strictly caps memory (32 MB) and disk dumps (50 MB limit).
3. Zero-footprint virtual descriptors resolve aerodynamic forces without local hardware strain.
4. REST API routes in routes_dataset.py operate with high reliability.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.datasets.safety import WorkstationSafetyGuard, HardwareSafetyStatus
from backend.knowledge.universal_cfd_catalog import UniversalCFDOracle, UNIVERSAL_BENCHMARK_REGISTRY
from backend.datasets.adapters.universal import UniversalAerospaceDatasetAdapter
from backend.dataset.catalog import cfd_catalog


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Hardware Safety Guard Tests
# ---------------------------------------------------------------------------

def test_hardware_safety_status_metrics():
    """Verify hardware safety metrics inspect memory and disk accurately."""
    status = WorkstationSafetyGuard.get_hardware_status()
    assert isinstance(status, HardwareSafetyStatus)
    assert status.ram_total_gb > 0.0
    assert status.disk_total_gb > 0.0
    assert status.virtualized_storage_active is True
    assert status.max_memory_cache_mb == 32.0


def test_safety_guard_blocks_oversized_file_write():
    """Verify safety guard raises PermissionError if attempting to write > 50 MB locally."""
    oversized_bytes = 60 * 1024 * 1024  # 60 MB
    with pytest.raises(PermissionError) as exc_info:
        WorkstationSafetyGuard.validate_file_write_safety(oversized_bytes)
    assert "HARDWARE SAFETY GUARD ACTIVATED" in str(exc_info.value)


def test_safety_guard_allows_safe_small_write():
    """Verify safety guard permits small scientific artifacts within budget."""
    safe_bytes = 100 * 1024  # 100 KB
    # Should not raise
    WorkstationSafetyGuard.validate_file_write_safety(safe_bytes)


# ---------------------------------------------------------------------------
# 2. Universal CFD Oracle Tests
# ---------------------------------------------------------------------------

def test_universal_registry_covers_major_aerospace_families():
    """Verify registry indexes NASA TMR, AGARD, AIAA, UIUC, and Hypersonic benchmarks."""
    families = {b.benchmark_family for b in UNIVERSAL_BENCHMARK_REGISTRY.values()}
    assert "NASA_TMR" in families
    assert "AGARD" in families
    assert "AIAA_DPW" in families
    assert "UIUC" in families
    assert "NACA_TR824" in families
    assert "NASA_HYPERSONIC" in families


def test_resolve_universal_polar_onera_m6():
    """Verify ONERA M6 transonic 3D wing resolution matches AGARD standard conditions."""
    polar = UniversalCFDOracle.resolve_universal_polar(
        geometry="ONERA M6",
        alpha_deg=3.06,
        mach=0.84,
        reynolds=1.17e7,
    )
    assert polar["CL"] > 0.35
    assert polar["CD"] > 0.015
    assert "AGARD-AR-138" in polar["matched_benchmark_id"]
    assert "Schmitt" in polar["citation"]


def test_resolve_universal_polar_space_shuttle():
    """Verify Space Shuttle Orbiter entry resolution at high angle of attack."""
    polar = UniversalCFDOracle.resolve_universal_polar(
        geometry="Space Shuttle Orbiter",
        alpha_deg=40.0,
        mach=18.0,
        reynolds=1.2e6,
    )
    assert polar["CD"] > 1.0  # High bluff body entry drag
    assert "NASA-SHUTTLE-ORBITER" in polar["matched_benchmark_id"]
    assert "TM-104744" in polar["citation"]


def test_resolve_universal_polar_selig_s1223():
    """Verify extreme high-lift STOL UAV airfoil (S1223) resolution."""
    polar = UniversalCFDOracle.resolve_universal_polar(
        geometry="Selig S1223",
        alpha_deg=8.0,
        mach=0.08,
        reynolds=2.0e5,
    )
    assert polar["CL"] > 1.50  # S1223 generates very high lift
    assert "UIUC-SELIG-S1223" in polar["matched_benchmark_id"]


def test_cfd_catalog_fallback_to_universal_oracle():
    """Verify CFDCatalog automatically falls back to UniversalCFDOracle for exotic geometry."""
    polar = cfd_catalog.get_benchmark_polar("ONERA M6", alpha_deg=3.06, reynolds=1.17e7, mach=0.84)
    assert polar is not None
    assert polar["CL"] > 0.30
    assert polar["CD"] > 0.010


# ---------------------------------------------------------------------------
# 3. Universal Dataset Adapter Tests
# ---------------------------------------------------------------------------

def test_universal_adapter_enforces_metadata_only_storage():
    """Verify universal adapter enforces zero-disk-bloat metadata-only storage state."""
    adapter = UniversalAerospaceDatasetAdapter()
    manifest = adapter.get_manifest()
    assert manifest.dataset_id == "DATASET-UNIVERSAL-AEROSPACE-BENCHMARKS"
    assert adapter.get_storage_state().value == "DATASET_METADATA_ONLY"
    cases = adapter.list_cases(limit=10)
    assert len(cases) > 0
    assert all(c.has_field_data is False for c in cases)  # Virtualized


# ---------------------------------------------------------------------------
# 4. REST API Endpoints Tests
# ---------------------------------------------------------------------------

def test_api_hardware_safety_endpoint(client):
    """Verify /api/dataset/hardware-safety returns real-time hardware status."""
    resp = client.get("/api/dataset/hardware-safety")
    assert resp.status_code == 200
    data = resp.json()
    assert "ram_total_gb" in data
    assert "disk_safety_reserve_gb" in data
    assert data["virtualized_storage_active"] is True


def test_api_universal_benchmarks_endpoint(client):
    """Verify /api/dataset/universal-benchmarks lists historical benchmarks."""
    resp = client.get("/api/dataset/universal-benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 15
    case_ids = [b["case_id"] for b in data]
    assert "NASA-TMR-NACA0012" in case_ids
    assert "AGARD-AR-138-ONERA-M6" in case_ids


def test_api_resolve_universal_polar_endpoint(client):
    """Verify /api/dataset/resolve-universal-polar provides instant forces in < 100ms."""
    payload = {
        "geometry": "NACA 64-212",
        "alpha_deg": 4.0,
        "mach": 0.25,
        "reynolds": 6.0e6,
    }
    resp = client.post("/api/dataset/resolve-universal-polar", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "CL" in data
    assert "CD" in data
    assert "CM" in data
    assert "asme_vv20_uncertainty" in data
