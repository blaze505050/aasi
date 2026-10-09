"""
AASI Milestone 4: Scientific Hypothesis Engine Test Suite.
Tests:
- Verification of all 6 mandatory fields (statement, evidence basis, assumptions, prediction, candidate test, status)
- Strict Anti-Fabrication Rule: Hypotheses must NEVER be represented as established facts
- Cryptographic provenance hashing and tamper resistance
- Epistemic lifecycle progression (PROPOSED -> TESTING -> SUPPORTED / REFUTED / INCONCLUSIVE)
- Aerodynamic discrepancy hypothesis generation
- FastAPI control plane endpoints
- Investigation graph integration
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.science.hypotheses import (
    ScientificHypothesis,
    HypothesisStatus,
    HypothesisEngine,
)
from backend.main import app


# ---------------------------------------------------------------------------
# Test 1: All 6 Mandatory Fields Present in Hypothesis
# ---------------------------------------------------------------------------
def test_hypothesis_model_contains_all_six_required_fields():
    """Milestone 4 requirement: statement, evidence basis, assumptions, prediction, candidate test, status."""
    hyp = ScientificHypothesis(
        hypothesis_id="HYP-TEST-001",
        title="Boundary Layer Separation Drag Rise",
        statement="Adverse pressure gradient causes upper-surface separation above alpha = 12 deg, inducing rapid pressure drag rise.",
        evidence_basis=[
            "Abbott & von Doenhoff Report 824 shows non-linear drag rise onset at alpha ~ 12 deg.",
            "Navier-Stokes momentum deficit indicates boundary layer detachment.",
        ],
        assumptions=[
            "Chord Reynolds number Re = 3.0e6",
            "Incompressible Mach = 0.15",
            "Smooth surface without trip strips",
        ],
        prediction="Wall shear stress tau_w drops to zero and CD increases by >30% between alpha=10 deg and alpha=14 deg.",
        candidate_test="Run OpenFOAM simpleFoam AoA sweep [10, 12, 14] deg and monitor upper surface wall shear distribution.",
        status=HypothesisStatus.PROPOSED,
        domain="aerodynamics",
        geometry_id="NACA 0012",
    )

    # 1. Check all 6 core fields
    assert hyp.statement.startswith("Adverse pressure gradient")
    assert len(hyp.evidence_basis) == 2
    assert len(hyp.assumptions) == 3
    assert "tau_w drops to zero" in hyp.prediction
    assert "simpleFoam AoA sweep" in hyp.candidate_test
    assert hyp.status == HypothesisStatus.PROPOSED

    # 2. Check metadata fields
    assert hyp.hypothesis_id == "HYP-TEST-001"
    assert hyp.domain == "aerodynamics"
    assert hyp.geometry_id == "NACA 0012"


# ---------------------------------------------------------------------------
# Test 2: CRITICAL RULE — Hypotheses Must NEVER Be Represented as Facts
# ---------------------------------------------------------------------------
def test_hypothesis_never_represented_as_established_fact():
    """
    CRITICAL SCIENTIFIC INTEGRITY RULE:
    Hypotheses are conjectures and can NEVER be declared established facts.
    Attempting to set is_established_fact = True must be rejected.
    """
    hyp = ScientificHypothesis(
        title="Test Conjecture",
        statement="Compressibility effects begin at Mach > 0.3.",
        evidence_basis=["Prandtl-Glauert compressibility rule"],
        assumptions=["Subsonic flow"],
        prediction="Lift slope increases by factor 1/sqrt(1 - M^2).",
        candidate_test="Sweep Mach [0.1, 0.2, 0.3, 0.4] in OpenFOAM.",
    )

    # 1. Must default to False
    assert hyp.is_established_fact is False
    assert "NEVER be treated as an established physical fact" in hyp.epistemic_warning

    # 2. Rejects attempt to set as True
    with pytest.raises(ValueError, match="CRITICAL EPISTEMIC VIOLATION"):
        ScientificHypothesis(
            title="Invalid Fact Claim",
            statement="Drag is always 0.01.",
            evidence_basis=["None"],
            assumptions=["None"],
            prediction="None",
            candidate_test="None",
            is_established_fact=True,
        )

    # 3. Presentation dictionary preserves disclaimer
    p_dict = hyp.to_presentation_dict()
    assert p_dict["is_established_fact"] is False
    assert "epistemic_warning" in p_dict


# ---------------------------------------------------------------------------
# Test 3: Provenance Hashing and Tamper Resistance
# ---------------------------------------------------------------------------
def test_hypothesis_provenance_hashing():
    """Verifies that cryptographic hash seals hypothesis parameters deterministically."""
    hyp1 = ScientificHypothesis(
        hypothesis_id="HYP-HASH-001",
        title="Decambering",
        statement="Viscous boundary layer decambering reduces lift.",
        evidence_basis=["Thin airfoil theory"],
        assumptions=["Re=3e6"],
        prediction="dCL/da = 5.9/rad vs 6.28/rad",
        candidate_test="AoA sweep in simpleFoam",
    )
    hash1 = hyp1.compute_provenance_hash()
    assert len(hash1) == 64

    # Identical content yields identical hash
    hyp2 = ScientificHypothesis(
        hypothesis_id="HYP-HASH-001",
        title="Decambering",
        statement="Viscous boundary layer decambering reduces lift.",
        evidence_basis=["Thin airfoil theory"],
        assumptions=["Re=3e6"],
        prediction="dCL/da = 5.9/rad vs 6.28/rad",
        candidate_test="AoA sweep in simpleFoam",
    )
    assert hyp2.compute_provenance_hash() == hash1

    # Modified prediction yields different hash
    hyp3 = ScientificHypothesis(
        hypothesis_id="HYP-HASH-001",
        title="Decambering",
        statement="Viscous boundary layer decambering reduces lift.",
        evidence_basis=["Thin airfoil theory"],
        assumptions=["Re=3e6"],
        prediction="dCL/da = 5.5/rad vs 6.28/rad",  # modified
        candidate_test="AoA sweep in simpleFoam",
    )
    assert hyp3.compute_provenance_hash() != hash1


# ---------------------------------------------------------------------------
# Test 4: Engine Formulation and Disk Persistence
# ---------------------------------------------------------------------------
def test_engine_formulate_and_persistence(tmp_path):
    """Verifies HypothesisEngine registers and persists hypothesis objects to disk."""
    engine = HypothesisEngine(workspace_root=tmp_path)

    hyp = engine.formulate(
        title="Leading-Edge Suction Peak Collapse",
        statement="At alpha > 14 deg, leading-edge suction peak collapses due to laminar separation bubble bursting.",
        evidence_basis=["Abbott & von Doenhoff Cp distribution catalogs"],
        assumptions=["Re = 6.0e6", "Mach = 0.15"],
        prediction="Minimum pressure coefficient Cp_min increases from -4.5 to -1.2 across stall.",
        candidate_test="Extract surface Cp profile in OpenFOAM simpleFoam at alpha=14 and alpha=16 deg.",
        domain="aerodynamics",
        geometry_id="NACA 4412",
        confidence=0.85,
    )

    assert hyp.hypothesis_id.startswith("HYP-")
    assert hyp.status == HypothesisStatus.PROPOSED
    assert hyp.provenance_hash != ""

    # Check persistence on disk
    persisted_file = tmp_path / "data" / "hypotheses" / f"{hyp.hypothesis_id}.json"
    assert persisted_file.exists()

    # Reload into fresh engine
    reloaded_engine = HypothesisEngine(workspace_root=tmp_path)
    loaded_hyp = reloaded_engine.get_hypothesis(hyp.hypothesis_id)
    assert loaded_hyp is not None
    assert loaded_hyp.statement == hyp.statement
    assert loaded_hyp.prediction == hyp.prediction
    assert loaded_hyp.is_established_fact is False


# ---------------------------------------------------------------------------
# Test 5: Epistemic Status Lifecycle (PROPOSED -> TESTING -> SUPPORTED)
# ---------------------------------------------------------------------------
def test_hypothesis_status_lifecycle_supported(tmp_path):
    """
    Tests progression to SUPPORTED when candidate test matches prediction.
    Even when SUPPORTED, is_established_fact MUST REMAIN False.
    """
    engine = HypothesisEngine(workspace_root=tmp_path)

    hyp = engine.formulate(
        title="Trailing Edge Separation Progression",
        statement="Separation starts at trailing edge and moves forward as alpha increases.",
        evidence_basis=["Boundary-layer momentum equation"],
        assumptions=["Re = 3e6"],
        prediction="Separation location x_sep/c moves from 0.95 to 0.70 between 8 and 12 deg.",
        candidate_test="Run simpleFoam at alpha=[8, 10, 12] deg and record x_sep.",
    )

    # 1. Move to TESTING
    hyp = engine.update_status(hyp.hypothesis_id, HypothesisStatus.TESTING, test_job_id="JOB-CFD-001")
    assert hyp.status == HypothesisStatus.TESTING
    assert hyp.test_evidence["job_id"] == "JOB-CFD-001"

    # 2. Test results confirm prediction -> SUPPORTED
    hyp = engine.update_status(
        hyp.hypothesis_id,
        HypothesisStatus.SUPPORTED,
        evidence_summary="Verified simpleFoam run confirmed x_sep/c moved from 0.94 to 0.68.",
        measured_values={"x_sep_8deg": 0.94, "x_sep_12deg": 0.68},
    )
    assert hyp.status == HypothesisStatus.SUPPORTED
    assert "x_sep_8deg" in hyp.test_evidence["measured_values"]

    # CRITICAL: Supported hypotheses are STILL NOT established facts!
    assert hyp.is_established_fact is False
    assert hyp.to_presentation_dict()["is_established_fact"] is False


# ---------------------------------------------------------------------------
# Test 6: Epistemic Status Lifecycle (PROPOSED -> REFUTED)
# ---------------------------------------------------------------------------
def test_hypothesis_status_lifecycle_refuted(tmp_path):
    """Tests progression to REFUTED when candidate test contradicts prediction."""
    engine = HypothesisEngine(workspace_root=tmp_path)

    hyp = engine.formulate(
        title="Incorrect Zero Drag Hypothesis",
        statement="Drag coefficient remains zero at high Reynolds numbers.",
        evidence_basis=["Inviscid Euler model"],
        assumptions=["Inviscid limit"],
        prediction="CD will be 0.0000 at Re = 1e8.",
        candidate_test="Execute simpleFoam at Re=1e8.",
    )

    hyp = engine.update_status(
        hyp.hypothesis_id,
        HypothesisStatus.REFUTED,
        evidence_summary="Verified CFD run measured CD = 0.0055 > 0 due to turbulent skin friction.",
        measured_values={"CD": 0.0055},
    )
    assert hyp.status == HypothesisStatus.REFUTED
    assert hyp.is_established_fact is False


# ---------------------------------------------------------------------------
# Test 7: Aerodynamic Discrepancy Hypothesis Generation
# ---------------------------------------------------------------------------
def test_discrepancy_hypotheses_generation(tmp_path):
    """
    Verifies that the engine formulates structured hypotheses for multi-source discrepancies:
    - Analytical vs CFD (drag: viscous deficit, lift: decambering)
    - Live CFD vs Neural Surrogate (spatial kernel smoothing)
    - Live CFD vs Wind Tunnel Database (RANS turbulence closure)
    """
    engine = HypothesisEngine(workspace_root=tmp_path)

    # 1. Analytical vs CFD (CD discrepancy)
    cd_hyps = engine.generate_for_discrepancy(
        quantity="CD",
        geometry="NACA 0012",
        alpha_deg=4.0,
        reynolds=3e6,
        mach=0.15,
        src_a="ANALYTICAL",
        val_a=0.0075,
        src_b="LIVE_CFD",
        val_b=0.0125,
        abs_diff=0.0050,
    )
    assert len(cd_hyps) >= 1
    h_drag = cd_hyps[0]
    assert "Viscous Boundary Layer" in h_drag.title
    assert "d'Alembert" in h_drag.evidence_basis[0]
    assert "simpleFoam" in h_drag.candidate_test
    assert h_drag.is_established_fact is False

    # 2. Analytical vs CFD (CL discrepancy)
    cl_hyps = engine.generate_for_discrepancy(
        quantity="CL",
        geometry="NACA 2412",
        alpha_deg=6.0,
        reynolds=3e6,
        mach=0.15,
        src_a="ANALYTICAL",
        val_a=0.88,
        src_b="LIVE_CFD",
        val_b=0.82,
        abs_diff=0.06,
    )
    assert len(cl_hyps) >= 1
    assert "Decambering" in cl_hyps[0].title

    # 3. Live CFD vs Neural Surrogate
    surr_hyps = engine.generate_for_discrepancy(
        quantity="CD",
        geometry="NACA 0012",
        alpha_deg=10.0,
        reynolds=3e6,
        mach=0.15,
        src_a="LIVE_CFD",
        val_a=0.025,
        src_b="SURROGATE",
        val_b=0.021,
        abs_diff=0.004,
    )
    assert len(surr_hyps) >= 1
    assert "Surrogate" in surr_hyps[0].title

    # 4. Live CFD vs Wind Tunnel Database
    db_hyps = engine.generate_for_discrepancy(
        quantity="CD",
        geometry="NACA 0012",
        alpha_deg=0.0,
        reynolds=6e6,
        mach=0.15,
        src_a="LIVE_CFD",
        val_a=0.0062,
        src_b="DATABASE_REAL",
        val_b=0.0058,
        abs_diff=0.0004,
    )
    assert len(db_hyps) >= 1
    assert "Turbulence Closure" in db_hyps[0].title


# ---------------------------------------------------------------------------
# Test 8: FastAPI Hypotheses Endpoints
# ---------------------------------------------------------------------------
def test_hypotheses_fastapi_endpoints():
    """Tests the /api/hypotheses REST endpoints."""
    client = TestClient(app)

    # 1. Formulate via POST /api/hypotheses
    post_payload = {
        "title": "Shock Wave Boundary Layer Interaction",
        "statement": "Transonic buffet onset occurs when shock-induced separation bubble fails to reattach.",
        "evidence_basis": ["Delery transonic shock-boundary layer experiments (1985)"],
        "assumptions": ["Transonic Mach = 0.75", "Re = 5.0e6"],
        "prediction": "Pressure recovery downstream of shock shows plateaus and rms surface pressure spikes > 5x.",
        "candidate_test": "Execute rhoSimpleFoam or pimpleFoam with kOmegaSST at Mach 0.75.",
        "domain": "aerodynamics",
        "geometry_id": "RAE 2822",
        "confidence": 0.90,
    }
    resp = client.post("/api/hypotheses", json=post_payload)
    assert resp.status_code == 200
    data = resp.json()
    hid = data["hypothesis_id"]
    assert hid.startswith("HYP-")
    assert data["status"] == "PROPOSED"
    assert data["is_established_fact"] is False
    assert "provenance_hash" in data

    # 2. Retrieve via GET /api/hypotheses/{id}
    get_resp = client.get(f"/api/hypotheses/{hid}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Shock Wave Boundary Layer Interaction"
    assert get_resp.json()["is_established_fact"] is False

    # 3. List via GET /api/hypotheses
    list_resp = client.get("/api/hypotheses?domain=aerodynamics")
    assert list_resp.status_code == 200
    assert any(h["hypothesis_id"] == hid for h in list_resp.json())

    # 4. Evaluate via POST /api/hypotheses/{id}/evaluate
    eval_payload = {
        "status": "SUPPORTED",
        "evidence_summary": "Simulated buffet onset verified in rhoSimpleFoam with shock stall at Mach 0.76.",
        "test_job_id": "JOB-TRANSONIC-BUFFET-001",
        "measured_values": {"buffet_onset_mach": 0.76, "unsteady_rms_cp": 0.18},
    }
    eval_resp = client.post(f"/api/hypotheses/{hid}/evaluate", json=eval_payload)
    assert eval_resp.status_code == 200
    updated_data = eval_resp.json()
    assert updated_data["status"] == "SUPPORTED"
    assert updated_data["is_established_fact"] is False
    assert updated_data["test_evidence"]["job_id"] == "JOB-TRANSONIC-BUFFET-001"


# ---------------------------------------------------------------------------
# Test 9: Investigation Graph Integration & Anti-Fabrication Warnings
# ---------------------------------------------------------------------------
def test_investigation_graph_hypothesis_nodes():
    """Verifies that InvestigationGraph includes structured hypotheses marked as non-facts."""
    from backend.agent.canonical_investigation import Investigation, OperatingConditions
    from backend.agent.investigation_graph import InvestigationGraph, InquiryNodeType

    hyp = ScientificHypothesis(
        hypothesis_id="HYP-GRAPH-001",
        title="Separation Delay via Camber",
        statement="Positive camber delays upper surface stall by shifting suction peak rearward.",
        evidence_basis=["NACA Report 824"],
        assumptions=["Re = 3e6"],
        prediction="NACA 4412 will stall at alpha = 16 deg vs NACA 0012 stall at alpha = 14 deg.",
        candidate_test="Compare simpleFoam stall envelopes.",
        status=HypothesisStatus.PROPOSED,
    )

    inv = Investigation(
        investigation_id="INV-HYP-TEST-001",
        user_request="Investigate stall mechanism differences between symmetric and cambered sections.",
        scientific_intent="Identify stall angle shift mechanism",
        geometry="NACA 4412",
        operating_conditions=OperatingConditions(alpha_deg=14.0, reynolds=3e6),
        hypotheses=[hyp],
    )

    graph = InvestigationGraph.build_from_investigation(inv)
    hyp_nodes = [n for n in graph.nodes if n.node_type == InquiryNodeType.HYPOTHESIS]
    assert len(hyp_nodes) >= 1

    found_structured = False
    for n in hyp_nodes:
        if "Separation Delay via Camber" in n.title:
            found_structured = True
            assert "NOT ESTABLISHED FACT" in n.content
            assert "Prediction:" in n.content
            assert "Candidate Test:" in n.content
    assert found_structured, "Expected structured hypothesis node in inquiry graph."
