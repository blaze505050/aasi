"""
AASI Cognitive Engine: Canonical Aerospace Demonstrations (Section 22).
Implements the 4 authoritative demonstrations using authentic system physics:
Demo 1: NACA 0012 Re=6e6, alpha=6 deg (Closed-Loop Discovery & Memory Consolidation)
Demo 2: NACA 4412 alpha=20 deg (Deep Stall Safe Failure & Negative Knowledge Retention)
Demo 3: NACA 0012 alpha=0 deg (Multi-Model Contradiction & D'Alembert's Paradox)
Demo 4: Reynolds-Number Drag Scaling (Re=3e6 vs Re=6e6 Boundary Layer Transition Analysis)
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from backend.cognitive.memory import CognitiveMemoryCategory, cognitive_memory_engine
from backend.cognitive.orchestrator import AutonomyLevel, OrchestratorStoppingCondition, cognitive_orchestrator
from backend.cognitive.states import CognitiveState

logger = logging.getLogger("aasi.cognitive.demonstrations")


def run_demo_1_naca0012_re6e6_alpha6() -> Dict[str, Any]:
    """
    Demo 1: NACA 0012 Re=6e6, alpha=6 deg.
    Closed-loop scientific investigation: retrieves memory, formulates hypotheses,
    plans discriminating experiment, executes panel solver, verifies bounds, updates memory.
    """
    session = cognitive_orchestrator.create_session(
        question="Investigate lift and drag behavior of NACA 0012 at alpha=6 deg, Re=6e6",
        geometry_name="NACA 0012",
        alpha_deg=6.0,
        reynolds=6.0e6,
        mach=0.15,
        autonomy_level=AutonomyLevel.LEVEL_4,
    )
    completed = cognitive_orchestrator.run_investigation(session.session_id)
    return {
        "demo": "DEMO_1_NACA0012_RE6E6_ALPHA6",
        "session_id": completed.session_id,
        "final_state": completed.current_state.value,
        "stopping_reason": completed.stopping_reason.value if completed.stopping_reason else None,
        "assertions": {k: v.model_dump() for k, v in completed.world_model.assertions.items()},
        "winning_hypothesis": [h.title for h in completed.active_hypotheses if h.status.value == "SUPPORTED"],
        "provenance_hash": completed.world_model.provenance_hash,
    }


def run_demo_2_naca4412_alpha20_safe_failure() -> Dict[str, Any]:
    """
    Demo 2: NACA 4412 alpha=20 deg.
    Recognizes extreme post-stall extrapolation, detects divergence/failure risk,
    refuses to fabricate unverified output, records negative knowledge, halts safely.
    """
    session = cognitive_orchestrator.create_session(
        question="Determine steady aerodynamic lift of cambered NACA 4412 at alpha=20 deg",
        geometry_name="NACA 4412",
        alpha_deg=20.0,
        reynolds=3.0e6,
        mach=0.15,
        autonomy_level=AutonomyLevel.LEVEL_4,
    )
    completed = cognitive_orchestrator.run_investigation(session.session_id)
    return {
        "demo": "DEMO_2_NACA4412_ALPHA20_SAFE_FAILURE",
        "session_id": completed.session_id,
        "final_state": completed.current_state.value,
        "stopping_reason": completed.stopping_reason.value if completed.stopping_reason else None,
        "critique_verdict": completed.active_critiques[0].overall_critique_verdict if completed.active_critiques else None,
        "extrapolation_risk": completed.active_critiques[0].extrapolation_risk if completed.active_critiques else None,
        "unknowns": completed.world_model.unknowns,
        "executed_tool_count": len(completed.executed_results),
    }


def run_demo_3_naca0012_alpha0_dalembert_contradiction() -> Dict[str, Any]:
    """
    Demo 3: NACA 0012 alpha=0 deg.
    Diagnoses model-form contradiction between potential flow (CD=0) and viscous RANS (CD>0).
    Explains D'Alembert's paradox and boundary layer shear stress without calling it an error.
    """
    from backend.cognitive.contradiction import CognitiveContradictionEngine
    engine = CognitiveContradictionEngine()

    con = engine.evaluate_contradiction(
        quantity="CD",
        source_a="Potential Flow (Inviscid)",
        tier_a="ANALYTICAL",
        value_a=0.0,
        source_b="Viscous RANS (OpenFOAM simpleFoam)",
        tier_b="NUMERICAL_AUDITED",
        value_b=0.0082,
        geometry_name="NACA 0012",
        operating_state={"alpha_deg": 0.0, "reynolds": 3e6, "mach": 0.15},
    )
    return {
        "demo": "DEMO_3_DALEMBERT_CONTRADICTION",
        "contradiction_type": con.contradiction_type.value if con else None,
        "is_genuine_defect": con.is_genuine_defect if con else None,
        "physical_explanation": con.physical_explanation if con else None,
        "governing_mechanism": con.governing_mechanism if con else None,
        "action": con.recommended_resolving_action if con else None,
    }


def run_demo_4_reynolds_scaling_investigation() -> Dict[str, Any]:
    """
    Demo 4: Reynolds-number drag scaling investigation (Re=3e6 vs Re=6e6).
    Investigates skin-friction coefficient reduction via Schlichting boundary layer theory.
    """
    from backend.cognitive.tools import scientific_tool_registry
    res_3e6 = scientific_tool_registry.execute_tool(
        "discrete_vortex_panel",
        {"geometry": "NACA 0012", "alpha_deg": 0.0, "reynolds": 3.0e6, "mach": 0.15},
    )
    res_6e6 = scientific_tool_registry.execute_tool(
        "discrete_vortex_panel",
        {"geometry": "NACA 0012", "alpha_deg": 0.0, "reynolds": 6.0e6, "mach": 0.15},
    )

    cd_3e6 = res_3e6["results"]["CD"]
    cd_6e6 = res_6e6["results"]["CD"]

    delta_cd = cd_6e6 - cd_3e6
    return {
        "demo": "DEMO_4_REYNOLDS_SCALING",
        "re_baseline": 3.0e6,
        "cd_baseline": cd_3e6,
        "re_higher": 6.0e6,
        "cd_higher": cd_6e6,
        "delta_cd": round(delta_cd, 6),
        "physical_explanation": "Higher Reynolds number compresses turbulent boundary layer thickness delta/x ~ 0.37/Re^(1/5), lowering wall friction coefficient Cf.",
        "verified_trend": cd_6e6 < cd_3e6,
    }
