"""
AASI Phase 5 Test Suite: Full Cognitive OS & Autonomous Closed-Loop Verification.
Governing Doctrine: Absolute Anti-Fabrication Rule.

Validates:
1. Competing hypotheses generation with cryptographic Merkle-DAG linkage.
2. Quantitative hypothesis falsification and corroboration against physical evidence.
3. Adversarial scientific critic audits with prescribed epistemic repair strategies.
4. L0–L5 autonomy governance gates (L1/L2 human approval stops vs L4/L5 autonomous execution).
5. Closed-loop campaign convergence: Hypothesize -> Critique -> Execute -> Verify -> Reconcile -> Merkle Seal.
6. Autonomous Level 5 self-repair protocol for deep-stall extrapolation regimes.
7. Cognitive REST API endpoints (/hypothesize, /critique, /investigate, /session/{id}/graph).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.cognitive.hypothesis_engine import (
    CognitiveHypothesisEngine,
    CognitiveHypothesisStatus,
    StructuredHypothesis,
)
from backend.cognitive.critic import ScientificCritic
from backend.cognitive.orchestrator import (
    AutonomyLevel,
    CognitiveOrchestrator,
    OrchestratorStoppingCondition,
    cognitive_orchestrator,
)
from backend.cognitive.states import CognitiveState
from backend.science.merkle_lineage import merkle_lineage
from backend.science.epistemic_kernel import epistemic_kernel

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Competing Hypotheses & Merkle Lineage Linkage
# ---------------------------------------------------------------------------

def test_competing_hypotheses_with_merkle_provenance():
    """Verify hypothesis generation produces competing pairs linked to Merkle blocks."""
    engine = CognitiveHypothesisEngine()
    hypotheses = engine.generate_competing_hypotheses(
        question="What governs drag rise for NACA 0012 at alpha=4 deg?",
        geometry_name="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
    )

    assert len(hypotheses) >= 2
    h1, h2 = hypotheses[0], hypotheses[1]

    # Mutually competing
    assert h1.competing_with == [h2.hypothesis_id]
    assert h2.competing_with == [h1.hypothesis_id]

    # Falsification criteria
    assert len(h1.falsification_criteria) > 0
    assert h1.falsification_criteria[0].threshold_value > 0.0

    # Cryptographic Merkle Linkage
    assert h1.merkle_node_id is not None
    assert len(h1.merkle_node_id) == 64
    assert merkle_lineage.get_node(h1.merkle_node_id) is not None


# ---------------------------------------------------------------------------
# 2. Hypothesis Falsification and Corroboration
# ---------------------------------------------------------------------------

def test_hypothesis_falsification_evaluation():
    """Verify hypotheses are rejected when physical metrics trigger falsification criteria."""
    engine = CognitiveHypothesisEngine()
    hypotheses = engine.generate_competing_hypotheses(
        question="Drag breakdown of NACA 0012",
        geometry_name="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
    )
    h_attached = hypotheses[0]

    # Contradictory evidence (massive drag CD = 0.035 > threshold 0.018)
    status_bad = engine.evaluate_hypothesis_against_evidence(
        h_attached,
        evidence_results={"CL": 0.44, "CD": 0.0350},
    )
    assert status_bad == CognitiveHypothesisStatus.CONTRADICTED
    assert len(h_attached.contradicting_evidence) > 0

    # Corroborating evidence (normal attached CD = 0.0080, CL = 0.44)
    hypotheses_fresh = engine.generate_competing_hypotheses(
        question="Drag breakdown of NACA 0012",
        geometry_name="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
    )
    h_good = hypotheses_fresh[0]
    status_good = engine.evaluate_hypothesis_against_evidence(
        h_good,
        evidence_results={"CL": 0.44, "CD": 0.0075},
    )
    assert status_good == CognitiveHypothesisStatus.SUPPORTED
    assert len(h_good.supporting_evidence) > 0


# ---------------------------------------------------------------------------
# 3. Adversarial Scientific Critic & Prescribed Repairs
# ---------------------------------------------------------------------------

def test_scientific_critic_adversarial_audit_and_repairs():
    """Verify critic detects extrapolation risk and injects epistemic repair strategies."""
    critic = ScientificCritic()
    engine = CognitiveHypothesisEngine()

    hypotheses = engine.generate_competing_hypotheses(
        question="Deep stall investigation for NACA 0012",
        geometry_name="NACA 0012",
        alpha_deg=20.0,
        reynolds=3.0e6,
        mach=0.15,
    )
    h = hypotheses[0]

    critique = critic.critique_hypothesis(
        hypothesis=h,
        geometry_name="NACA 0012",
        alpha_deg=20.0,
        reynolds=3.0e6,
        mach=0.15,
    )

    assert critique.overall_critique_verdict == "HIGH_EXTRAPOLATION_RISK"
    assert critique.extrapolation_risk == "SEVERE"
    assert len(critique.vulnerabilities) > 0
    assert len(critique.suggested_repairs) > 0
    assert any("pimpleFoam" in r or "wind-tunnel" in r for r in critique.suggested_repairs)
    assert critique.merkle_node_id is not None


# ---------------------------------------------------------------------------
# 4. Autonomy Governance Gating (L1/L2 vs L4/L5)
# ---------------------------------------------------------------------------

def test_autonomy_governance_l2_stops_for_approval():
    """Verify that Autonomy Level 2 halts at planning stage awaiting human approval."""
    orchestrator = CognitiveOrchestrator()
    session = orchestrator.create_session(
        question="Evaluate NACA 0012 at alpha=2 deg",
        geometry_name="NACA 0012",
        alpha_deg=2.0,
        reynolds=3.0e6,
        mach=0.15,
        autonomy_level=AutonomyLevel.LEVEL_2,
    )

    completed = orchestrator.run_investigation(session.session_id)
    assert completed.current_state == CognitiveState.STALLED
    assert completed.stopping_reason == OrchestratorStoppingCondition.AWAITING_HUMAN_APPROVAL
    assert len(completed.candidate_experiments) > 0
    assert len(completed.executed_results) == 0  # Crucial: did not execute without signoff


# ---------------------------------------------------------------------------
# 5. Closed-Loop Campaign Level 4 Execution & Merkle Sealing
# ---------------------------------------------------------------------------

def test_closed_loop_campaign_level_4_converges():
    """Verify Level 4 goal-driven closed loop executes, verifies, and seals Merkle root."""
    orchestrator = CognitiveOrchestrator()
    session = orchestrator.create_session(
        question="Determine lift and drag of NACA 0012 at alpha=4 deg",
        geometry_name="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
        autonomy_level=AutonomyLevel.LEVEL_4,
    )

    completed = orchestrator.run_investigation(session.session_id)
    assert completed.current_state == CognitiveState.COMPLETED
    assert completed.stopping_reason == OrchestratorStoppingCondition.QUESTION_RESOLVED
    assert len(completed.executed_results) > 0
    assert completed.world_model.objective.is_resolved is True

    # Provenance hash should be Merkle root digest
    assert len(completed.world_model.provenance_hash) == 64

    # Assertions created in world model
    assertions = list(completed.world_model.assertions.values())
    assert any("Lift Coefficient" in a.property_name for a in assertions)
    assert any("Profile Drag" in a.property_name for a in assertions)

    # Hypotheses evaluated
    supported = [h for h in completed.active_hypotheses if h.status == CognitiveHypothesisStatus.SUPPORTED]
    assert len(supported) > 0


# ---------------------------------------------------------------------------
# 6. Autonomous Level 5 Self-Repair Protocol
# ---------------------------------------------------------------------------

def test_autonomous_level_5_self_repair():
    """Verify Level 5 autonomous loop executes self-repair protocol when facing stall risk."""
    orchestrator = CognitiveOrchestrator()
    session = orchestrator.create_session(
        question="Autonomous resolution of NACA 0012 deep stall at alpha=20 deg",
        geometry_name="NACA 0012",
        alpha_deg=20.0,
        reynolds=3.0e6,
        mach=0.15,
        autonomy_level=AutonomyLevel.LEVEL_5,
    )

    completed = orchestrator.run_investigation(session.session_id)
    assert completed.current_state == CognitiveState.COMPLETED
    assert completed.stopping_reason == OrchestratorStoppingCondition.QUESTION_RESOLVED
    assert completed.world_model.objective.is_resolved is True
    assert "repaired" in completed.world_model.objective.resolution_summary.lower()

    # Confirms empirical fallback used without fabricating steady CFD
    assertions = list(completed.world_model.assertions.values())
    assert any("Empirical Fallback" in a.property_name for a in assertions)


# ---------------------------------------------------------------------------
# 7. Cognitive REST API Endpoints
# ---------------------------------------------------------------------------

def test_api_cognitive_hypothesize_and_critique():
    """Verify POST /api/v1/cognitive/hypothesize and /critique endpoints."""
    # 1. Hypothesize
    res_hyp = client.post(
        "/api/v1/cognitive/hypothesize",
        json={"question": "Test question", "geometry_name": "NACA 0012", "alpha_deg": 4.0},
    )
    assert res_hyp.status_code == 200
    hyps = res_hyp.json()
    assert len(hyps) >= 2
    assert "merkle_node_id" in hyps[0]

    # 2. Critique
    res_crit = client.post(
        "/api/v1/cognitive/critique",
        json={"hypothesis": hyps[0], "geometry_name": "NACA 0012", "alpha_deg": 4.0},
    )
    assert res_crit.status_code == 200
    critique = res_crit.json()
    assert "overall_critique_verdict" in critique
    assert "merkle_node_id" in critique


def test_api_cognitive_investigate_and_graph():
    """Verify POST /api/v1/cognitive/investigate and GET /session/{id}/graph."""
    res_inv = client.post(
        "/api/v1/cognitive/investigate",
        json={"question": "Investigate NACA 0012 at alpha=2 deg", "geometry_name": "NACA 0012", "alpha_deg": 2.0},
    )
    assert res_inv.status_code == 200
    session_data = res_inv.json()["session"]
    sess_id = session_data["session_id"]

    res_graph = client.get(f"/api/v1/cognitive/session/{sess_id}/graph")
    assert res_graph.status_code == 200
    graph = res_graph.json()
    assert len(graph["nodes"]) >= 4
    assert len(graph["links"]) >= 3
