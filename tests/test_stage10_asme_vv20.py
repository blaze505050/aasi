"""
Unit and integration tests for AASI Stage 10: Automated ASME V&V 20-2009 & NASA-STD-7009B CAS Engine.
Verifies 3-grid Richardson extrapolation, Roache GCI fine/medium, asymptotic range ratio,
NASA-STD-7009B 8-factor matrix, Merkle root lineage, and API routes.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure package roots are on sys.path
_repo_root = Path(__file__).resolve().parent.parent
_fno_pkg = _repo_root / "aasi-aero-fno"
for p in [str(_repo_root), str(_fno_pkg)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from aasi_aero_fno.asme_vv20_engine import (
    AsmeCertificationEngine,
    RichardsonExtrapolationMetrics,
    FlightCertificationDossier,
    ASME_VV20_BENCHMARKS,
)
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_richardson_extrapolation_asymptotic_convergence():
    """Verifies 3-grid Richardson extrapolation on quadratic refinement."""
    # Synthetic 2nd order convergence: f(h) = 0.80 + 0.02 * h^2
    # h1 = 1.0 -> f1 = 0.820
    # h2 = 1.414 -> f2 = 0.840
    # h3 = 2.0 -> f3 = 0.880
    metrics = AsmeCertificationEngine.evaluate_richardson_extrapolation(
        f1_fine=0.820,
        f2_medium=0.840,
        f3_coarse=0.880,
        h1_fine=1.0,
        h2_medium=1.414,
        h3_coarse=2.0,
        theoretical_order=2.0,
    )
    assert isinstance(metrics, RichardsonExtrapolationMetrics)
    assert metrics.convergence_type == "Monotonic Convergence"
    assert abs(metrics.order_of_accuracy_p - 2.0) < 0.25
    assert metrics.gci_fine_pct < 4.0
    assert metrics.is_in_asymptotic_range is True
    assert abs(metrics.apparent_value_f_extrapolated - 0.80) < 0.01


def test_flight_certification_dossier_generation():
    """Verifies generation of complete NASA-STD-7009B & ASME V&V 20 flight dossier."""
    dossier = AsmeCertificationEngine.generate_flight_certification_dossier(
        aircraft_mission="ISRO RLV Re-entry Flare Clearance",
        target_metric="Maximum Normal Force Coefficient C_N",
        f1_fine=1.245,
        f2_medium=1.232,
        f3_coarse=1.205,
    )
    assert isinstance(dossier, FlightCertificationDossier)
    assert dossier.dossier_id.startswith("AASI-ASME-VV20-")
    assert dossier.nasa_cas_score_composite >= 3.5
    assert "Flight Clearance Approved" in dossier.nasa_cas_rating
    assert len(dossier.nasa_cas_dimensions) == 8
    # Merkle root hash length
    assert len(dossier.merkle_root_hash) == 64
    assert len(dossier.audit_trail_hashes) == 5


def test_asme_vv20_benchmarks_catalog():
    """Verifies NASA TMR Flat Plate and CRM benchmarks."""
    assert "nasa_tmr_flat_plate_gci" in ASME_VV20_BENCHMARKS
    assert "nasa_crm_wing_transonic_gci" in ASME_VV20_BENCHMARKS
    crm = ASME_VV20_BENCHMARKS["nasa_crm_wing_transonic_gci"]
    assert crm["gci_fine_pct"] <= 0.50
    assert crm["asymptotic_range"] >= 0.95


def test_api_asme_vv20_generate_dossier(client):
    """Verifies POST /api/aero/asme-vv20/generate-dossier returns 200 with flight release."""
    resp = client.post(
        "/api/aero/asme-vv20/generate-dossier",
        json={
            "aircraft_mission": "Gaganyaan Abort Aerodynamic Clearance",
            "target_metric": "Static Pitching Moment Stability Derivative C_m,alpha",
            "f1_fine": -0.0452,
            "f2_medium": -0.0441,
            "f3_coarse": -0.0418,
            "h1_fine": 1.0,
            "h2_medium": 1.414,
            "h3_coarse": 2.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["stage"] == 10
    payload = data["data"]
    assert payload["aircraft_mission"] == "Gaganyaan Abort Aerodynamic Clearance"
    assert "merkle_root_hash" in payload
    assert len(payload["merkle_root_hash"]) == 64


def test_api_asme_vv20_benchmarks(client):
    """Verifies GET /api/aero/asme-vv20/benchmarks returns 200 with benchmarks."""
    resp = client.get("/api/aero/asme-vv20/benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["stage"] == 10
    assert "nasa_tmr_flat_plate_gci" in data["benchmarks"]
