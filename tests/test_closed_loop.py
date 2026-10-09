"""
Unit and Integration Tests for Milestone 9: Bounded Closed-Loop Scientific Orchestrator.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Section 10 of MVP Backlog & Prompt 10:
- All 10 scientific lifecycle stages: interpret -> hypothesize -> plan -> method -> compute -> execute/stage -> verify -> compare -> remember -> next experiment
- Loop bounding and halting rules:
  1. EXECUTION_STAGED_AWAITING_EXTERNAL (never fabricates external execution)
  2. FAILED_VERIFICATION (negative evidence recorded, loop halted)
  3. SUFFICIENT_EVIDENCE (convergence reached, loop completed)
  4. MAX_CYCLES_REACHED (strict bounding against runaway iteration)
- Cryptographic provenance and Merkle hashes.
- REST API routes in backend/api/routes_closed_loop.py.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.science.closed_loop import (
    ClosedLoopOrchestrator,
    ClosedLoopReport,
    LoopStoppingReason,
    closed_loop_orchestrator,
)
from backend.science.memory import scientific_memory


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Full 10-Stage Progression & Convergence
# ---------------------------------------------------------------------------

def test_full_10_stage_progression_converged():
    """
    Executes a complete 10-stage scientific cycle with verified simulated execution data
    matching surrogate within tolerance -> halts on SUFFICIENT_EVIDENCE.
    """
    orchestrator = ClosedLoopOrchestrator()
    # Provide authentic simulated execution data matching realistic NACA 0012 values
    sim_data = {"CL": 0.441, "CD": 0.0084, "CM": -0.005, "converged": True}

    report = orchestrator.execute_bounded_loop(
        user_question="Investigate lift and drag for NACA 0012 at alpha=4.0 deg",
        geometry="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
        max_cycles=3,
        simulated_execution_data=sim_data,
    )

    assert report.total_cycles_completed == 1
    assert report.is_loop_bounded is True
    assert report.stopping_reason == LoopStoppingReason.SUFFICIENT_EVIDENCE
    assert report.final_status == "COMPLETED"
    assert len(report.provenance_hash) == 64

    # Verify all 10 stages are present in the cycle record
    cycle = report.cycles[0]
    assert cycle.step_1_interpret["target_geometry"] == "NACA 0012"
    assert len(cycle.step_2_hypothesize) > 0
    assert len(cycle.step_3_plan) > 0
    assert "OpenFOAM" in cycle.step_4_method
    assert "destination" in cycle.step_5_compute
    assert cycle.step_6_execute_stage["status"] == "EXECUTED"
    assert cycle.step_7_verify["verification_status"] == "VERIFIED"
    assert cycle.step_8_compare["quantity"] == "CL"
    assert cycle.step_9_remember is not None
    assert cycle.step_10_next_experiment["decision"] == "CONVERGED"


# ---------------------------------------------------------------------------
# 2. Strict Halting on Staged Execution (Anti-Fabrication)
# ---------------------------------------------------------------------------

def test_loop_pauses_when_execution_staged_on_colab():
    """
    CRITICAL RULE: When computation is routed to Colab and external execution results
    have not been uploaded yet, the loop MUST pause with EXECUTION_STAGED_AWAITING_EXTERNAL.
    It must NEVER fabricate numerical CFD results.
    """
    orchestrator = ClosedLoopOrchestrator()
    report = orchestrator.execute_bounded_loop(
        user_question="Investigate lift for NACA 0012",
        geometry="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
        max_cycles=3,
        simulated_execution_data=None,  # No simulated execution -> MUST PAUSE
    )

    assert report.total_cycles_completed == 1
    assert report.stopping_reason == LoopStoppingReason.EXECUTION_STAGED_AWAITING_EXTERNAL
    assert "PAUSED" in report.final_status

    cycle = report.cycles[0]
    assert cycle.step_6_execute_stage["status"] == "STAGED"
    assert cycle.step_6_execute_stage["is_executed"] is False
    assert cycle.step_6_execute_stage["is_verified"] is False
    # Verification and downstream comparison were NOT executed
    assert cycle.step_7_verify is None
    assert cycle.step_8_compare is None


# ---------------------------------------------------------------------------
# 3. Halting on Verification Failure (Negative Evidence Preservation)
# ---------------------------------------------------------------------------

def test_loop_halts_on_verification_failure_and_records_negative_evidence():
    """
    When solver diverged or produced negative drag, verification MUST fail,
    the loop halts on FAILED_VERIFICATION, and negative evidence is committed to memory.
    """
    orchestrator = ClosedLoopOrchestrator()
    # Unphysical negative drag: CD = -0.0050 (violates second law / dissipation)
    unphysical_data = {"CL": 0.441, "CD": -0.0050, "converged": False}

    report = orchestrator.execute_bounded_loop(
        user_question="Test unphysical case",
        geometry="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
        simulated_execution_data=unphysical_data,
    )

    assert report.stopping_reason == LoopStoppingReason.FAILED_VERIFICATION
    assert "PAUSED_FAILED_VERIFICATION" in report.final_status

    cycle = report.cycles[0]
    assert cycle.step_7_verify["verification_status"] == "FAILED"
    assert cycle.step_7_verify["drag_positive"] is False

    # Negative evidence must be committed into memory
    mem_id = cycle.step_9_remember
    assert mem_id is not None
    mem_entry = scientific_memory.get_entry(mem_id)
    assert mem_entry is not None
    assert mem_entry.entry_type.value == "FAILED_INVESTIGATION"


# ---------------------------------------------------------------------------
# 4. Strict Hard Iteration Limit (Bounded Loop Guard)
# ---------------------------------------------------------------------------

def test_hard_iteration_limit_enforced():
    """
    Verify that loop never executes beyond max_cycles (capped at 5).
    """
    orchestrator = ClosedLoopOrchestrator()
    # Artificially force divergence between CFD and surrogate so it proposes next experiment
    divergent_data = {"CL": 0.850, "CD": 0.020, "converged": True}

    report = orchestrator.execute_bounded_loop(
        user_question="Iterative sweep",
        geometry="NACA 0012",
        alpha_deg=0.0,
        reynolds=3.0e6,
        mach=0.15,
        max_cycles=2,  # Bounded to 2 cycles
        simulated_execution_data=divergent_data,
    )

    assert report.total_cycles_completed == 2
    assert report.stopping_reason == LoopStoppingReason.MAX_CYCLES_REACHED
    assert "HALTED_MAX_CYCLES_REACHED" in report.final_status


# ---------------------------------------------------------------------------
# 5. REST API Routes
# ---------------------------------------------------------------------------

def test_api_closed_loop_stopping_criteria(client):
    """GET /api/closed-loop/stopping-criteria returns all halting conditions."""
    resp = client.get("/api/closed-loop/stopping-criteria")
    assert resp.status_code == 200
    criteria = resp.json()
    assert "SUFFICIENT_EVIDENCE" in criteria
    assert "USER_APPROVAL_REQUIRED" in criteria
    assert "MAX_CYCLES_REACHED" in criteria


def test_api_closed_loop_run_staged(client):
    """POST /api/closed-loop/run pauses on external staging when no results provided."""
    payload = {
        "user_question": "Investigate NACA 0012 at alpha=4 deg",
        "geometry": "NACA 0012",
        "alpha_deg": 4.0,
        "reynolds": 3000000.0,
        "mach": 0.15,
        "max_cycles": 2,
    }
    resp = client.post("/api/closed-loop/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"].startswith("LOOP-")
    assert data["is_loop_bounded"] is True
    assert data["stopping_reason"] == "EXECUTION_STAGED_AWAITING_EXTERNAL"

    # Test GET /api/closed-loop/sessions/{id}
    session_resp = client.get(f"/api/closed-loop/sessions/{data['session_id']}")
    assert session_resp.status_code == 200
    session_data = session_resp.json()
    assert session_data["provenance_hash"] == data["provenance_hash"]


def test_api_closed_loop_run_converged(client):
    """POST /api/closed-loop/run with authentic execution data completes cycle."""
    payload = {
        "user_question": "Investigate NACA 0012 at alpha=4 deg",
        "geometry": "NACA 0012",
        "alpha_deg": 4.0,
        "reynolds": 3000000.0,
        "mach": 0.15,
        "max_cycles": 2,
        "simulated_execution_data": {
            "CL": 0.441,
            "CD": 0.0084,
            "CM": -0.005,
            "converged": True,
        },
    }
    resp = client.post("/api/closed-loop/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["final_status"] == "COMPLETED"
    assert data["stopping_reason"] == "SUFFICIENT_EVIDENCE"
    assert len(data["cycles"]) == 1
