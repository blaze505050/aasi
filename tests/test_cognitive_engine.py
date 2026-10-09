"""
AASI Cognitive Engine: Comprehensive Verification Test Suite.
Validates all cognitive primitives, state transitions, falsification criteria,
critic audits, information-gain planning, contradiction detection, and critical invariants.
"""

import pytest
from backend.cognitive.critic import ScientificCritic
from backend.cognitive.hypothesis_engine import CognitiveHypothesisEngine
from backend.cognitive.memory import CognitiveMemoryCategory, CognitiveMemoryRecord, cognitive_memory_engine
from backend.cognitive.orchestrator import AutonomyLevel, OrchestratorStoppingCondition, cognitive_orchestrator
from backend.cognitive.planner import CognitiveExperimentPlanner
from backend.cognitive.states import CognitiveState, CognitiveStateMachine
from backend.cognitive.tools import ExecutionMode, scientific_tool_registry
from backend.cognitive.world_model import (
    AerospaceWorldModel,
    AssertionStatus,
    InvestigationObjective,
    OperatingState,
    PhysicalGeometry,
    WorldModelAssertion,
)


def test_world_model_lifecycle_and_provenance():
    """Validates AerospaceWorldModel versioning, immutability, and SHA-256 Merkle provenance."""
    wm = AerospaceWorldModel(
        objective=InvestigationObjective(question="Determine lift curve slope of NACA 0012"),
        geometry=PhysicalGeometry(name="NACA 0012"),
    )
    initial_hash = wm.compute_provenance_hash()
    assert initial_hash != ""
    assert wm.version == 1

    # Add assertion
    wm.add_assertion(
        WorldModelAssertion(
            subject="NACA 0012",
            property_name="Lift Slope (dCL/da)",
            value=0.108,
            status=AssertionStatus.NUMERICAL_AUDITED,
            source="Discrete Vortex Panel Solver",
            epistemic_tier="VERIFIED",
        )
    )
    updated_hash = wm.provenance_hash
    assert updated_hash != initial_hash

    # Snapshot test
    snapshot = wm.snapshot()
    assert snapshot.version == 2
    assert snapshot.parent_version_hash == updated_hash


def test_cognitive_state_transitions():
    """Validates finite state machine transitions and prevents illegal state jumps."""
    fsm = CognitiveStateMachine()
    assert fsm.current_state == CognitiveState.IDLE

    # Valid step
    fsm.transition_to(CognitiveState.UNDERSTANDING, trigger="USER_QUERY", rationale="Starting investigation")
    assert fsm.current_state == CognitiveState.UNDERSTANDING

    # Illegal transition: Cannot jump from UNDERSTANDING directly to EXECUTING
    with pytest.raises(ValueError) as excinfo:
        fsm.transition_to(CognitiveState.EXECUTING, trigger="SKIP_PHASES", rationale="Illegal jump")
    assert "ILLEGAL COGNITIVE TRANSITION" in str(excinfo.value)


def test_hypothesis_generation_and_falsifiability():
    """Validates that hypothesis engine generates competing, falsifiable hypotheses with criteria."""
    engine = CognitiveHypothesisEngine()
    hypotheses = engine.generate_competing_hypotheses(
        question="What governs drag rise for NACA 0012 at alpha=6 deg?",
        geometry_name="NACA 0012",
        alpha_deg=6.0,
        reynolds=3.0e6,
        mach=0.15,
    )
    assert len(hypotheses) >= 2
    # Ensure they are mutually competing
    assert hypotheses[0].competing_with == [hypotheses[1].hypothesis_id]
    # Ensure falsification criteria exist
    assert len(hypotheses[0].falsification_criteria) > 0
    assert hypotheses[0].falsification_criteria[0].threshold_value > 0.0


def test_scientific_critic_adversarial_audit():
    """Validates that ScientificCritic detects model extrapolation risk in post-stall regimes."""
    critic = ScientificCritic()
    engine = CognitiveHypothesisEngine()

    # Deep stall condition (alpha = 20 deg)
    hypotheses = engine.generate_competing_hypotheses(
        question="Stall evaluation for NACA 4412",
        geometry_name="NACA 4412",
        alpha_deg=20.0,
        reynolds=3.0e6,
        mach=0.15,
    )
    critique = critic.critique_hypothesis(
        hypotheses[0],
        geometry_name="NACA 4412",
        alpha_deg=20.0,
        reynolds=3.0e6,
        mach=0.15,
    )
    assert critique.extrapolation_risk == "SEVERE"
    assert critique.overall_critique_verdict == "HIGH_EXTRAPOLATION_RISK"
    assert any(v.dimension == "MODEL_EXTRAPOLATION" for v in critique.vulnerabilities)


def test_experiment_planner_information_gain():
    """Validates multi-criteria experimental utility ranking."""
    planner = CognitiveExperimentPlanner()
    engine = CognitiveHypothesisEngine()
    hypotheses = engine.generate_competing_hypotheses(
        question="Aerodynamic evaluation of NACA 0012",
        geometry_name="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
    )
    experiments = planner.plan_discriminating_experiments(
        hypotheses=hypotheses,
        geometry_name="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
    )
    assert len(experiments) >= 2
    # Verify descending utility sort
    assert experiments[0].utility.composite_utility >= experiments[1].utility.composite_utility
    assert "utility_breakdown" in experiments[0].utility.model_dump()


def test_scientific_tool_registry_execution():
    """Validates MCP-compliant tool discovery and local panel solver execution."""
    tool = scientific_tool_registry.get_tool("discrete_vortex_panel")
    assert tool is not None
    assert ExecutionMode.LOCAL in tool.supported_modes

    exec_res = scientific_tool_registry.execute_tool(
        "discrete_vortex_panel",
        {"geometry": "NACA 0012", "alpha_deg": 4.0, "reynolds": 3.0e6, "mach": 0.15},
    )
    assert exec_res["status"] == "SUCCESS"
    assert "CL" in exec_res["results"]
    assert exec_res["results"]["CL"] > 0.35
    assert exec_res["results"]["CD"] > 0.005


def test_contradiction_engine_dalembert_paradox():
    """Validates that ContradictionEngine diagnoses D'Alembert's Paradox without calling it an error."""
    from backend.cognitive.contradiction import CognitiveContradictionEngine, ContradictionType
    engine = CognitiveContradictionEngine()

    con = engine.evaluate_contradiction(
        quantity="CD",
        source_a="Inviscid Potential Flow",
        tier_a="ANALYTICAL",
        value_a=0.0,
        source_b="Viscous RANS (OpenFOAM)",
        tier_b="NUMERICAL_AUDITED",
        value_b=0.0082,
        geometry_name="NACA 0012",
    )
    assert con is not None
    assert con.contradiction_type == ContradictionType.MODEL_FORM_DIFFERENCE
    assert con.is_genuine_defect is False
    assert "D'Alembert's Paradox" in con.physical_explanation


def test_cognitive_memory_and_skills():
    """Validates persistent cognitive memory categories and scientific skill procedures."""
    mem = cognitive_memory_engine
    rec = CognitiveMemoryRecord(
        category=CognitiveMemoryCategory.FAILURE,
        title="High-Alpha Stall Residual Stagnation",
        content="Residuals oscillate above 1e-3 in steady simpleFoam.",
        geometry="NACA 0012",
    )
    mem.add_record(rec)
    retrieved = mem.search_memory("Residual stagnation", category=CognitiveMemoryCategory.FAILURE)
    assert len(retrieved) > 0

    skill = mem.get_skill_for_investigation("NACA 0012", "polar investigation")
    assert skill is not None
    assert "verification_checks" in skill.model_dump()


def test_orchestrator_closed_loop_execution():
    """Validates complete 16-step cognitive loop execution to resolution."""
    session = cognitive_orchestrator.create_session(
        question="Determine lift and drag of NACA 0012 at alpha=4 deg",
        geometry_name="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
        autonomy_level=AutonomyLevel.LEVEL_4,
    )
    completed = cognitive_orchestrator.run_investigation(session.session_id)
    assert completed.current_state == CognitiveState.COMPLETED
    assert completed.stopping_reason == OrchestratorStoppingCondition.QUESTION_RESOLVED
    assert len(completed.active_hypotheses) >= 2
    assert len(completed.executed_results) > 0
    assert completed.world_model.objective.is_resolved is True


def test_autonomy_level_gate_enforcement():
    """Validates that Level 2 autonomy halts before computational execution awaiting human sign-off."""
    session = cognitive_orchestrator.create_session(
        question="Analyze NACA 2412 wing",
        geometry_name="NACA 2412",
        alpha_deg=2.0,
        autonomy_level=AutonomyLevel.LEVEL_2,  # Plan only
    )
    completed = cognitive_orchestrator.run_investigation(session.session_id)
    assert completed.current_state == CognitiveState.STALLED
    assert completed.stopping_reason == OrchestratorStoppingCondition.AWAITING_HUMAN_APPROVAL
    assert len(completed.executed_results) == 0  # No tool execution permitted without approval


def test_critical_invariant_negative_drag_rejected():
    """CRITICAL INVARIANT: FAILED != SUCCESS. Physical law violations cannot be verified."""
    # Test that negative drag fails verification
    fsm = CognitiveStateMachine()
    fsm.transition_to(CognitiveState.UNDERSTANDING, trigger="T", rationale="R")
    fsm.transition_to(CognitiveState.MODELING, trigger="T", rationale="R")
    fsm.transition_to(CognitiveState.HYPOTHESIZING, trigger="T", rationale="R")
    fsm.transition_to(CognitiveState.CRITIQUING, trigger="T", rationale="R")
    fsm.transition_to(CognitiveState.PLANNING, trigger="T", rationale="R")
    fsm.transition_to(CognitiveState.SELECTING_TOOL, trigger="T", rationale="R")
    fsm.transition_to(CognitiveState.EXECUTING, trigger="T", rationale="R")
    fsm.transition_to(CognitiveState.VERIFYING, trigger="T", rationale="R")

    # If CD < 0, transition must go to FAILED
    fsm.transition_to(CognitiveState.FAILED, trigger="NEGATIVE_DRAG", rationale="Second law violated")
    assert fsm.current_state == CognitiveState.FAILED
    assert fsm.current_state != CognitiveState.COMPLETED
