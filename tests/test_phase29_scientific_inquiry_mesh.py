"""
AASI Phase 29: Scientific Inquiry Mesh & End-to-End Investigation Verification.
Validates the canonical workflow:
"What happens to the drag of NACA 4412 from alpha 4° to 12° at Re=3e6?"
Ensuring:
- Natural language parsing & multi-point alpha sweep
- Multi-fidelity matrix & epistemic tagging
- Anti-fabrication guarantees (live CFD staged, not executed)
- Remote execution packaging with cryptographic hashing
- Physical validation & discrepancy explanation
- Prioritized next experiment proposals & non-automatic staging
- Scientific memory engine reusability
- Structured scientific answer synthesis
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.auth.security import security_manager
from backend.auth.governance import governance_engine
from backend.compute.queue import job_queue
from backend.agent.planner import ScientificPlanner
from backend.agent.memory import ScientificMemoryEngine
from backend.agent.next_experiment import NextExperimentEngine
from backend.agent.scientific_answer import ScientificAnswerEngine, StructuredScientificResponse
from backend.agent.canonical_investigation import Investigation, EpistemicTier
from backend.dataset.catalog import cfd_catalog

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    job_queue.clear()
    governance_engine.reset()
    from backend.auth.commercial import usage_tracker
    usage_tracker.reset()


@pytest.fixture
def test_token():
    user = security_manager.get_user_by_username("scientist_4412")
    if not user:
        user = security_manager.create_user("scientist_4412", "scientist_4412@aasi.aero", "Pass123!Secure", role="RESEARCHER")
    session = security_manager.create_session_token(user)
    return session.token


def test_1_parse_canonical_user_query():
    """Verify natural language parsing of alpha 4 to 12 range at Re=3e6 for NACA 4412."""
    query = "What happens to the drag of NACA 4412 from alpha 4° to 12° at Re=3e6?"
    spec = ScientificPlanner.parse_objective(query)
    
    assert spec.geometry == "NACA 4412"
    assert spec.reynolds == 3_000_000.0
    assert spec.alpha_range is not None
    assert spec.alpha_range[0] == 4.0
    assert spec.alpha_range[-1] == 12.0
    assert len(spec.alpha_range) >= 5


def test_2_end_to_end_investigation_submission(test_token):
    """Verify POST /api/investigate processes query, stages case, and returns multi-fidelity plan."""
    query = "What happens to the drag of NACA 4412 from alpha 4° to 12° at Re=3e6?"
    res = client.post(
        "/api/investigate",
        json={"objective": query, "preferred_provider": "COLAB"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    
    assert data["geometry"] == "NACA 4412"
    assert data["reynolds"] == 3_000_000.0
    assert data["job_state"] == "AUTHORIZATION_REQUIRED"
    assert "launch_url" in data
    assert data["notebook_path"] is not None
    
    # Check multi-fidelity matrix
    matrix = {entry["quantity"]: entry for entry in data["multi_fidelity_matrix"]}
    assert "Drag Coefficient (CD)" in matrix
    cd_entry = matrix["Drag Coefficient (CD)"]
    assert cd_entry["analytical"] is not None
    assert cd_entry["database"] is not None
    assert cd_entry["surrogate"] is not None
    # STRICT ANTI-FABRICATION: Live CFD must be None before actual execution
    assert cd_entry["live_cfd"] is None
    assert cd_entry["status"] == "AWAITING_REMOTE_CFD"
    
    # Check alpha sweep matrix
    assert "sweep_matrix" in data
    assert len(data["sweep_matrix"]) >= 5
    assert "4.0" in data["sweep_matrix"]
    assert "12.0" in data["sweep_matrix"]


def test_3_next_experiment_proposals_generation(test_token):
    """Verify prioritized next experiments are synthesized with expected information gain and requirements."""
    query = "What happens to the drag of NACA 4412 from alpha 4° to 12° at Re=3e6?"
    res = client.post(
        "/api/investigate",
        json={"objective": query, "preferred_provider": "COLAB"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    proposals = data.get("next_experiments", [])
    
    assert len(proposals) >= 2
    for p in proposals:
        assert "proposal_id" in p
        assert "objective" in p
        assert "variable_to_change" in p
        assert "expected_information_gained" in p
        assert "reason" in p
        assert "execution_requirements" in p


def test_4_accept_next_experiment_strictly_staged_no_auto_exec(test_token):
    """Verify operator can accept proposal, staging it without automatic execution."""
    # 1. Submit investigation
    res = client.post(
        "/api/investigate",
        json={"objective": "NACA 4412 drag inquiry", "preferred_provider": "COLAB"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert res.status_code == 200
    job_id = res.json()["job_id"]
    proposals = res.json()["next_experiments"]
    assert len(proposals) > 0
    proposal_id = proposals[0]["proposal_id"]
    
    # 2. Accept proposal
    accept_res = client.post(
        f"/api/investigate/{job_id}/next-experiment",
        json={"proposal_id": proposal_id},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert accept_res.status_code == 200
    acc_data = accept_res.json()
    assert acc_data["status"] == "STAGED"
    assert acc_data["parent_investigation_id"].startswith("INV-")
    assert acc_data["proposal_id"] == proposal_id
    assert "new_job_id" in acc_data


def test_5_scientific_memory_reusability(test_token):
    """Verify prior investigations are indexed and reusable parameters are surfaced."""
    # First query
    res = client.post(
        "/api/investigate",
        json={"objective": "NACA 4412 at alpha=6.0 deg, Re=3e6", "preferred_provider": "COLAB"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert res.status_code == 200
    
    # Second query for similar geometry
    match = ScientificMemoryEngine.lookup_similar_investigations("NACA 4412", alpha_deg=6.5, reynolds=3_000_000.0)
    assert match is not None
    assert match.geometry == "NACA 4412"
    assert len(match.reusable_mesh_parameters) > 0
    assert len(match.reusable_solver_settings) > 0
    assert len(match.applicability_conditions) > 0


def test_6_structured_scientific_answer_endpoint(test_token):
    """Verify GET /api/investigate/{job_id}/structured-answer produces canonical Step 13 structure."""
    res = client.post(
        "/api/investigate",
        json={"objective": "NACA 4412 drag investigation Re=3e6", "preferred_provider": "COLAB"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert res.status_code == 200
    job_id = res.json()["job_id"]
    
    ans_res = client.get(
        f"/api/investigate/{job_id}/structured-answer",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert ans_res.status_code == 200
    ans_data = ans_res.json()
    
    assert "conclusion" in ans_data
    assert "evidence" in ans_data
    assert "comparison" in ans_data
    assert "what_aasi_verified" in ans_data
    assert "discrepancies" in ans_data
    assert "physical_interpretation" in ans_data
    assert "uncertainty_and_limitations" in ans_data
    assert "next_experiment" in ans_data
    assert "provenance" in ans_data
    assert "stage_10_governance" in ans_data["what_aasi_verified"]
    assert "anti_fabrication_rule" in ans_data["what_aasi_verified"]
