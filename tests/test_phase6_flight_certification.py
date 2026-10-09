"""
Phase 6 Integration Tests: Formal Flight Certification, Production Hardening & Merkle Proofs.
Governing Standards: ASME V&V 20-2009 and NASA-STD-7009B.
Governing Doctrine: Absolute Anti-Fabrication Rule.
"""

import io
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.compliance.dossier_generator import (
    CertificationDossierGenerator,
    CertificationDossierData,
    dossier_registry,
)
from backend.science.merkle_lineage import merkle_lineage, MerkleNodeType
from backend.science.epistemic_kernel import epistemic_kernel
from backend.cognitive.orchestrator import CognitiveOrchestrator, AutonomyLevel

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. ASME V&V 20 Richardson Extrapolation & GCI Study
# ---------------------------------------------------------------------------

def test_asme_vv20_richardson_extrapolation_dossier():
    """Validates genuine ASME V&V 20 3-grid convergence calculation in certification dossier."""
    job_id = f"TEST-ASME-{uuid.uuid4().hex[:6].upper()}"
    dossier = CertificationDossierGenerator.generate_dossier(
        job_id=job_id,
        geometry_name="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
    )

    assert isinstance(dossier, CertificationDossierData)
    assert dossier.job_id == job_id
    assert dossier.dossier_id.startswith("DOSSIER-")
    assert dossier.geometry.name == "NACA 0012"
    assert dossier.geometry.max_thickness_pct > 0.0

    # ASME V&V 20 Verification Report validation
    asme = dossier.asme_vv20
    assert asme.gci_fine_pct > 0.0
    assert asme.gci_fine_pct < 10.0  # Converged fine mesh uncertainty within bounds
    assert asme.observed_order_p > 0.0  # Asymptotic convergence order
    assert asme.safety_factor == 1.25  # Standard ASME safety factor Fs
    assert asme.numerical_uncertainty_plus_minus > 0.0
    assert asme.richardson_extrapolated > 0.0  # Converged Richardson extrapolation CL


# ---------------------------------------------------------------------------
# 2. NASA-STD-7009B Credibility Assessment Scale (CAS)
# ---------------------------------------------------------------------------

def test_nasa_std_7009b_cas_scorecard():
    """Validates 8-category NASA-STD-7009B CAS credibility scoring."""
    job_id = f"TEST-NASA-{uuid.uuid4().hex[:6].upper()}"
    dossier = CertificationDossierGenerator.generate_dossier(
        job_id=job_id,
        geometry_name="NACA 4412",
        alpha_deg=6.0,
        reynolds=3.0e6,
        mach=0.15,
    )

    cas = dossier.nasa_cas
    assert len(cas.categories) == 8
    assert cas.composite_score_pct >= 60.0
    assert cas.credibility_tier in ["HIGH", "MODERATE"]

    # Verify key dimensions
    dim_names = [c.dimension_name for c in cas.categories]
    assert "Development Verification" in dim_names
    assert "Execution Verification" in dim_names
    assert "Results Uncertainty" in dim_names
    assert "M&S Management" in dim_names

    for cat in cas.categories:
        assert 0 <= cat.score <= 4
        assert len(cat.evidence_summary) > 10


# ---------------------------------------------------------------------------
# 3. Cryptographic Merkle Lineage Sealing
# ---------------------------------------------------------------------------

def test_merkle_dag_lineage_sealing_on_certification():
    """Validates that dossier generation seals an immutable Merkle audit node and updates root."""
    job_id = f"TEST-MERKLE-{uuid.uuid4().hex[:6].upper()}"
    dossier = CertificationDossierGenerator.generate_dossier(
        job_id=job_id,
        geometry_name="NACA 0012",
        alpha_deg=2.0,
        reynolds=3.0e6,
        mach=0.15,
    )

    # Merkle node recorded in global DAG
    nodes = merkle_lineage.get_investigation_nodes(job_id)
    assert len(nodes) >= 1

    audit_node = next((n for n in nodes if n.node_type == MerkleNodeType.AUDIT_CHECKPOINT), None)
    assert audit_node is not None
    assert audit_node.code_digest != ""
    assert audit_node.metrics_digest != ""
    assert audit_node.metadata.get("classification") == "AIRWORTHINESS_DOSSIER"

    # Root hash is deterministic 64-char hex
    assert len(dossier.provenance.merkle_root_hash) == 64
    assert dossier.provenance.epistemic_trust_tier == "VERIFIED_CFD"


# ---------------------------------------------------------------------------
# 4. Epistemic Kernel Auto-Indexing
# ---------------------------------------------------------------------------

def test_epistemic_kernel_indexing_on_certification():
    """Validates that certified results are automatically indexed into the Epistemic Kernel."""
    job_id = f"TEST-EPI-{uuid.uuid4().hex[:6].upper()}"
    dossier = CertificationDossierGenerator.generate_dossier(
        job_id=job_id,
        geometry_name="NACA 0012",
        alpha_deg=5.0,
        reynolds=3.0e6,
        mach=0.15,
    )

    rec = epistemic_kernel.get_record(f"EPI-{job_id}")
    assert rec is not None
    assert rec.geometry == "NACA 0012"
    assert "CL" in rec.results
    assert rec.provenance_hash != ""


# ---------------------------------------------------------------------------
# 5. REST API: Generate & List Certification Dossiers
# ---------------------------------------------------------------------------

def test_routes_certification_generate_and_list():
    """Tests POST /api/v1/certification/generate and GET /api/v1/certification/list."""
    job_id = f"CERT-API-{uuid.uuid4().hex[:6].upper()}"
    res = client.post(
        "/api/v1/certification/generate",
        json={
            "job_id": job_id,
            "geometry_name": "NACA 0012",
            "alpha_deg": 4.0,
            "reynolds": 3.0e6,
            "mach": 0.15,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["job_id"] == job_id
    assert "dossier_id" in data
    dossier_id = data["dossier_id"]

    # Retrieve by ID
    res_get = client.get(f"/api/v1/certification/{dossier_id}")
    assert res_get.status_code == 200
    assert res_get.json()["dossier_id"] == dossier_id

    # List
    res_list = client.get("/api/v1/certification/list")
    assert res_list.status_code == 200
    summaries = res_list.json()
    assert len(summaries) >= 1
    assert any(s["dossier_id"] == dossier_id for s in summaries)


# ---------------------------------------------------------------------------
# 6. REST API: HTML & PDF Rendering
# ---------------------------------------------------------------------------

def test_routes_certification_html_and_pdf_rendering():
    """Tests GET /api/v1/certification/{id}/html and /pdf."""
    job_id = f"CERT-DOC-{uuid.uuid4().hex[:6].upper()}"
    res = client.post(
        "/api/v1/certification/generate",
        json={
            "job_id": job_id,
            "geometry_name": "NACA 4412",
            "alpha_deg": 4.0,
            "reynolds": 3.0e6,
            "mach": 0.15,
        },
    )
    assert res.status_code == 200
    dossier_id = res.json()["dossier_id"]

    # 1. HTML Rendering
    res_html = client.get(f"/api/v1/certification/{dossier_id}/html")
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    assert "ASME V&amp;V 20-2009" in res_html.text or "ASME V&V 20" in res_html.text
    assert "<svg" in res_html.text  # Engineering airfoil cross section rendered

    # 2. PDF Rendering
    res_pdf = client.get(f"/api/v1/certification/{dossier_id}/pdf")
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.headers["content-type"]
    assert len(res_pdf.content) > 1000  # Genuine binary PDF produced


# ---------------------------------------------------------------------------
# 7. REST API: Cryptographic Merkle Proof
# ---------------------------------------------------------------------------

def test_routes_certification_merkle_proof():
    """Tests GET /api/v1/certification/{id}/merkle-proof."""
    job_id = f"CERT-PRF-{uuid.uuid4().hex[:6].upper()}"
    res = client.post(
        "/api/v1/certification/generate",
        json={
            "job_id": job_id,
            "geometry_name": "NACA 0012",
            "alpha_deg": 2.0,
        },
    )
    assert res.status_code == 200
    dossier_id = res.json()["dossier_id"]

    res_proof = client.get(f"/api/v1/certification/{dossier_id}/merkle-proof")
    assert res_proof.status_code == 200
    proof = res_proof.json()
    assert proof["is_valid"] is True
    assert len(proof["merkle_root_hash"]) == 64
    assert proof["node_count"] >= 1
    assert "Cryptographic lineage cryptographically verified" in proof["verification_statement"]


# ---------------------------------------------------------------------------
# 8. Production Hardening: System Health & Readiness
# ---------------------------------------------------------------------------

def test_production_system_health_and_readiness():
    """Tests GET /api/v1/system/health, /readiness, and /telemetry."""
    # 1. Health
    res_h = client.get("/api/v1/system/health")
    assert res_h.status_code == 200
    health = res_h.json()
    assert health["status"] == "HEALTHY"
    assert health["uptime_seconds"] >= 0.0
    assert "epistemic_kernel" in health
    assert "merkle_lineage" in health
    assert health["solvers_ready"]["hess_smith_panel_solver"] is True
    assert health["solvers_ready"]["asme_vv20_gci_engine"] is True

    # 2. Readiness
    res_r = client.get("/api/v1/system/readiness")
    assert res_r.status_code == 200
    ready = res_r.json()
    assert ready["ready"] is True
    assert ready["status"] == "ALL_SYSTEMS_OPERATIONAL"

    # 3. Telemetry
    res_t = client.get("/api/v1/system/telemetry")
    assert res_t.status_code == 200
    telemetry = res_t.json()
    assert telemetry["anti_fabrication_rule"] == "ACTIVE_STRICT"
    assert telemetry["total_merkle_blocks"] >= 0


# ---------------------------------------------------------------------------
# 9. End-to-End Flight Certification Lifecycle
# ---------------------------------------------------------------------------

def test_end_to_end_closed_loop_flight_certification():
    """
    End-to-end integration:
    Cognitive investigation -> Closed loop solve -> Formal flight certification -> Merkle verification.
    """
    orchestrator = CognitiveOrchestrator()
    session = orchestrator.create_session(
        question="Certify NACA 0012 pre-stall aerodynamics at alpha=4 deg",
        geometry_name="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
        autonomy_level=AutonomyLevel.LEVEL_4,
    )

    # 1. Execute cognitive loop
    completed = orchestrator.run_investigation(session.session_id)
    assert completed.world_model.objective.is_resolved is True

    # 2. Issue formal flight certification on the completed session
    res_cert = client.post(
        "/api/v1/certification/generate",
        json={
            "job_id": completed.session_id,
            "geometry_name": completed.world_model.geometry.name,
            "alpha_deg": completed.world_model.operating_state.alpha_deg,
            "reynolds": completed.world_model.operating_state.reynolds,
            "mach": completed.world_model.operating_state.mach,
        },
    )
    assert res_cert.status_code == 200
    dossier_data = res_cert.json()
    assert dossier_data["job_id"] == completed.session_id
    assert dossier_data["is_flight_envelope_cleared"] is True

    # 3. Merkle proof binds both cognitive hypotheses, solver execution, and certification seal
    res_proof = client.get(f"/api/v1/certification/{dossier_data['dossier_id']}/merkle-proof")
    assert res_proof.status_code == 200
    proof = res_proof.json()
    assert proof["is_valid"] is True
    assert proof["node_count"] >= 2  # Hypotheses + Audit Seal
