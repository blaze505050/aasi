"""
Unit and Integration Tests for AASI Certification Dossier Generator and API Endpoints.
Verifies ASME V&V 20 & NASA-STD-7009B dossier generation, HTML rendering,
physical sanity invariance, and HTTP route responses.
"""

import pytest
from fastapi.testclient import TestClient

from backend.compliance.dossier_generator import (
    CertificationDossierGenerator,
    CertificationDossierData,
)
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_dossier_generation_naca4412():
    """Verify autonomous generation of complete NASA-STD-7009B / ASME V&V 20 dossier."""
    dossier = CertificationDossierGenerator.generate_dossier(
        job_id="EXP-TEST-0042",
        geometry_name="NACA 4412",
        alpha_deg=4.0,
        reynolds=3_000_000,
        mach=0.15,
    )

    assert isinstance(dossier, CertificationDossierData)
    assert dossier.job_id == "EXP-TEST-0042"
    assert dossier.geometry.name == "NACA 4412"
    assert dossier.geometry.max_thickness_pct > 10.0
    assert len(dossier.multi_fidelity) == 4
    # All physical sanity checks should be evaluated
    assert len(dossier.physical_invariants) >= 5
    # Drag positivity check must be passed
    drag_check = next(c for c in dossier.physical_invariants if c.rule_id == "INV-01")
    assert drag_check.passed is True
    # NASA-STD-7009B scorecard must contain 8 dimensions
    assert len(dossier.nasa_cas.categories) == 8
    assert dossier.nasa_cas.composite_score_pct >= 60.0
    # Cryptographic hashes must be non-empty SHA-256 strings
    assert len(dossier.provenance.coordinate_sha256) == 64
    assert len(dossier.provenance.results_sha256) == 64


def test_dossier_html_rendering():
    """Verify publication-grade HTML output contains required sections and valid vector markup."""
    dossier = CertificationDossierGenerator.generate_dossier(
        job_id="EXP-HTML-TEST",
        geometry_name="NACA 0012",
        alpha_deg=6.0,
    )
    html = CertificationDossierGenerator.render_html(dossier)
    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "ASME V&amp;V 20-2009" in html
    assert "NASA-STD-7009B" in html
    assert "<svg" in html
    assert "window.print()" in html
    assert "Multi-Fidelity Aerodynamic Comparison Matrix" in html
    assert "Grid Convergence Index (GCI)" in html


def test_dossier_api_endpoints(client):
    """Verify GET /api/investigate/{job_id}/dossier and /dossier/json."""
    # 1. Submit a preliminary investigation
    post_res = client.post(
        "/api/investigate",
        json={"objective": "Analyze NACA 0012 at alpha = 4 deg and Re = 3e6", "preferred_provider": "LOCAL_SANDBOX"},
        headers={"X-User-Id": "test_engineer", "X-User-Role": "ADMIN"},
    )
    assert post_res.status_code == 200
    job_id = post_res.json()["job_id"]

    # 2. Query HTML dossier
    dossier_res = client.get(
        f"/api/investigate/{job_id}/dossier",
        headers={"X-User-Id": "test_engineer", "X-User-Role": "ADMIN"},
    )
    assert dossier_res.status_code == 200
    assert "text/html" in dossier_res.headers["content-type"]
    assert "ASME V&amp;V 20-2009" in dossier_res.text

    # 3. Query JSON dossier
    json_res = client.get(
        f"/api/investigate/{job_id}/dossier/json",
        headers={"X-User-Id": "test_engineer", "X-User-Role": "ADMIN"},
    )
    assert json_res.status_code == 200
    data = json_res.json()
    assert data["job_id"] == job_id
    assert "asme_vv20" in data
    assert "nasa_cas" in data
