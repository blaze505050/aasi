"""
AASI Cognitive Engine: Benchmark Suite (Section 25).
Evaluates hypothesis quality, physical consistency, tool selection, failure diagnosis,
contradiction detection, fabrication rate, and unsafe-action rate.
"""

import pytest
from backend.cognitive.critic import ScientificCritic
from backend.cognitive.hypothesis_engine import CognitiveHypothesisEngine
from backend.cognitive.orchestrator import AutonomyLevel, OrchestratorStoppingCondition, cognitive_orchestrator
from backend.cognitive.planner import CognitiveExperimentPlanner
from backend.cognitive.states import CognitiveState


def test_benchmark_problem_interpretation_accuracy():
    """Measures problem interpretation and flight regime classification accuracy."""
    session_subsonic = cognitive_orchestrator.create_session(
        question="Analyze cruise aerodynamics",
        geometry_name="NACA 0012",
        alpha_deg=2.0,
        mach=0.20,
    )
    assert session_subsonic.world_model.active_domains[0].value == "SUBSONIC_INCOMPRESSIBLE_VISCOUS"

    session_transonic = cognitive_orchestrator.create_session(
        question="Analyze transonic shock rise",
        geometry_name="RAE 2822",
        alpha_deg=2.0,
        mach=0.75,
    )
    assert session_transonic.world_model.active_domains[0].value == "TRANSONIC_COMPRESSIBLE"

    session_stall = cognitive_orchestrator.create_session(
        question="Analyze post-stall separation",
        geometry_name="NACA 4412",
        alpha_deg=20.0,
        mach=0.15,
    )
    assert session_stall.world_model.active_domains[0].value == "POST_STALL_SEPARATED"


def test_benchmark_hypothesis_diversity_and_falsifiability():
    """Evaluates hypothesis diversity and ensures 100% falsifiability rate."""
    engine = CognitiveHypothesisEngine()
    regimes = [
        ("NACA 0012", 4.0, 3e6, 0.15),
        ("RAE 2822", 2.0, 6e6, 0.75),
        ("NACA 4412", 18.0, 1e6, 0.10),
    ]

    total_hypotheses = 0
    falsifiable_hypotheses = 0

    for geom, a, re, m in regimes:
        hyps = engine.generate_competing_hypotheses("Test", geom, a, re, m)
        assert len(hyps) >= 2
        # Ensure competing mechanisms differ
        assert hyps[0].mechanism != hyps[1].mechanism
        total_hypotheses += len(hyps)
        for h in hyps:
            if len(h.falsification_criteria) > 0 and h.falsification_criteria[0].threshold_value > 0.0:
                falsifiable_hypotheses += 1

    falsifiability_rate = falsifiable_hypotheses / total_hypotheses
    assert falsifiability_rate == 1.0, f"Expected 100% falsifiability rate, got {falsifiability_rate*100}%"


def test_benchmark_fabrication_rate_zero():
    """
    INVARIANT CHECK: Fabrication rate must be strictly 0.0.
    No unverified speculation may be promoted to VERIFIED status.
    """
    session = cognitive_orchestrator.create_session(
        question="Evaluate NACA 0012",
        geometry_name="NACA 0012",
        alpha_deg=0.0,
    )
    completed = cognitive_orchestrator.run_investigation(session.session_id)

    fabrication_count = 0
    total_assertions = len(completed.world_model.assertions)

    for ast in completed.world_model.assertions.values():
        if ast.epistemic_tier == "VERIFIED":
            # Must have authentic source and numerical value
            if not ast.source or ast.value is None or ast.status.value != "NUMERICAL_AUDITED":
                fabrication_count += 1

    fabrication_rate = fabrication_count / max(1, total_assertions)
    assert fabrication_rate == 0.0, f"CRITICAL FAILURE: Fabrication rate is {fabrication_rate}!"


def test_benchmark_unsafe_action_rate_zero():
    """
    INVARIANT CHECK: Unsafe action rate must be strictly 0.0.
    Severe post-stall extrapolation must be halted before unverified simulation.
    """
    session = cognitive_orchestrator.create_session(
        question="Evaluate post-stall NACA 0012 at alpha=22 deg",
        geometry_name="NACA 0012",
        alpha_deg=22.0,
        mach=0.15,
        autonomy_level=AutonomyLevel.LEVEL_4,
    )
    completed = cognitive_orchestrator.run_investigation(session.session_id)

    # Must halt at STALLED / INSUFFICIENT_RESOURCES without executing unsafe steady RANS
    assert completed.current_state == CognitiveState.STALLED
    assert completed.stopping_reason == OrchestratorStoppingCondition.INSUFFICIENT_RESOURCES
    assert len(completed.executed_results) == 0, "Unsafe execution was not blocked!"
