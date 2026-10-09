"""
AASI Phase 26 Orchestrator Test Suite.
Verifies the formal 17-state execution machine, legal transitions,
rejection of illegal shortcuts, failure handling, and retry limits.
"""

import pytest
from backend.agent.orchestrator import (
    ProductionOrchestrator,
    OrchestratorState,
    OrchestratorTransition,
)


def test_orchestrator_initial_state():
    orch = ProductionOrchestrator(session_id="SESS-TEST-001", objective="Analyze NACA 4412")
    assert orch.session.current_state == OrchestratorState.RECEIVED
    assert orch.session.retry_count == 0
    assert len(orch.session.history) == 0


def test_orchestrator_full_happy_path_transitions():
    """Verify progression through all sequential states to COMPLETE."""
    orch = ProductionOrchestrator(session_id="SESS-TEST-002", objective="Analyze NACA 4412 at alpha=6")

    # Sequential walk
    states = [
        (OrchestratorState.PLANNED, "NLP_PARSED"),
        (OrchestratorState.KNOWLEDGE_SEARCH, "QUERY_CATALOG"),
        (OrchestratorState.FIDELITY_DECISION, "EVAL_UNCERTAINTY"),
        (OrchestratorState.CASE_GENERATED, "GENERATE_OPENFOAM"),
        (OrchestratorState.PREFLIGHT, "AUDIT_MESH"),
        (OrchestratorState.BACKEND_SELECTED, "SELECT_COLAB"),
        (OrchestratorState.JOB_STAGED, "PACKAGE_TARBALL"),
        (OrchestratorState.USER_AUTHORIZATION_REQUIRED, "PROMPT_USER"),
        (OrchestratorState.REMOTE_EXECUTING, "COLAB_STARTED"),
        (OrchestratorState.RESULTS_AVAILABLE, "RESULTS_UPLOADED"),
        (OrchestratorState.INGESTING, "EXTRACT_ARCHIVE"),
        (OrchestratorState.VERIFYING, "AUDIT_HASHES"),
        (OrchestratorState.SCIENTIFIC_VALIDATION, "CHECK_PHYSICS"),
        (OrchestratorState.KNOWLEDGE_COMMIT, "REGISTER_RECORD"),
        (OrchestratorState.REPORT_GENERATED, "COMPILE_REPORT"),
        (OrchestratorState.COMPLETE, "FINISHED"),
    ]

    for state, trigger in states:
        t = orch.transition_to(state, trigger=trigger)
        assert orch.session.current_state == state
        assert t.to_state == state
        assert len(t.transition_hash) == 64

    assert orch.session.current_state == OrchestratorState.COMPLETE
    assert orch.session.completed_at is not None
    assert len(orch.session.history) == 16


def test_orchestrator_rejects_illegal_transitions():
    """Fail-closed: illegal skips must raise ValueError."""
    orch = ProductionOrchestrator(session_id="SESS-TEST-003", objective="Analyze NACA 0012")

    with pytest.raises(ValueError, match="Illegal state transition"):
        # Skipping directly from RECEIVED to COMPLETE
        orch.transition_to(OrchestratorState.COMPLETE, trigger="SKIP_ALL")

    with pytest.raises(ValueError, match="Illegal state transition"):
        # Skipping directly from RECEIVED to REMOTE_EXECUTING
        orch.transition_to(OrchestratorState.REMOTE_EXECUTING, trigger="SKIP_PLANNING")


def test_orchestrator_failure_states():
    """Verify transitions into formal failure states."""
    orch = ProductionOrchestrator(session_id="SESS-TEST-004", objective="Analyze NACA 6409")
    orch.transition_to(OrchestratorState.PLANNED, trigger="PLAN_OK")
    orch.transition_to(OrchestratorState.KNOWLEDGE_SEARCH, trigger="SEARCH_OK")
    orch.transition_to(OrchestratorState.FIDELITY_DECISION, trigger="DECIDE_OK")
    orch.transition_to(OrchestratorState.CASE_GENERATED, trigger="CASE_OK")
    orch.transition_to(OrchestratorState.PREFLIGHT, trigger="RUN_PREFLIGHT")

    # Fail during preflight
    orch.fail_with(OrchestratorState.FAILED_PREFLIGHT, reason="Severe non-orthogonality in mesh")
    assert orch.session.current_state == OrchestratorState.FAILED_PREFLIGHT
    assert "non-orthogonality" in orch.session.history[-1].detail


def test_orchestrator_retry_exhaustion():
    """Verify exceeding 3 retries transitions to HUMAN_REVIEW_REQUIRED."""
    orch = ProductionOrchestrator(session_id="SESS-TEST-005", objective="Stress test retries")

    assert orch.record_retry("Attempt 1") is True
    assert orch.record_retry("Attempt 2") is True
    assert orch.record_retry("Attempt 3") is True
    # 4th retry exceeds MAX_RETRIES (3)
    assert orch.record_retry("Attempt 4") is False

    assert orch.session.current_state == OrchestratorState.HUMAN_REVIEW_REQUIRED
    assert orch.session.retry_count == 4
