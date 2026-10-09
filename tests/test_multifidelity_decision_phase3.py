"""
Comprehensive test suite for Phase 3 Multi-Fidelity Decision Engine & Physical Regime Escalation.
"""

import pytest
from backend.science.multifidelity_bridge import (
    MultiFidelityDecisionEngine,
    AerodynamicRegime,
    MultiFidelityDecision,
)
from backend.agent.canonical_investigation import EpistemicTier
from backend.agent.investigation_lifecycle import AutonomyLevel
from backend.scientific_compiler import compile_aml, ScientificTaskType
from backend.scientific_runtime import execute_dag
from backend.scientific_language import parse_aml


def test_classify_aerodynamic_regimes():
    engine = MultiFidelityDecisionEngine()
    
    # Incompressible attached
    assert engine.classify_regime(mach=0.15, alpha_deg=4.0) == AerodynamicRegime.INCOMPRESSIBLE_ATTACHED
    # Subsonic compressible
    assert engine.classify_regime(mach=0.45, alpha_deg=3.0) == AerodynamicRegime.COMPRESSIBLE_SUBSONIC
    # Transonic shock
    assert engine.classify_regime(mach=0.75, alpha_deg=2.0) == AerodynamicRegime.TRANSONIC_SHOCK
    # Supersonic
    assert engine.classify_regime(mach=1.5, alpha_deg=0.0) == AerodynamicRegime.SUPERSONIC
    # High-alpha stall
    assert engine.classify_regime(mach=0.2, alpha_deg=16.0) == AerodynamicRegime.HIGH_ALPHA_STALL


def test_fidelity_decision_attached_flow():
    engine = MultiFidelityDecisionEngine()
    decision = engine.evaluate_fidelity(
        geometry="NACA0012",
        alpha_deg=4.0,
        mach=0.15,
        reynolds=3e6,
        requested_fidelity="MULTI_FIDELITY",
    )
    assert isinstance(decision, MultiFidelityDecision)
    assert decision.governing_regime == AerodynamicRegime.INCOMPRESSIBLE_ATTACHED
    assert decision.requires_live_cfd is False
    assert "Discrete Vortex Panel" in decision.recommended_solver


def test_fidelity_escalation_transonic_regime():
    engine = MultiFidelityDecisionEngine()
    decision = engine.evaluate_fidelity(
        geometry="NACA0012",
        alpha_deg=2.5,
        mach=0.78,  # Transonic Mach number
        reynolds=6.5e6,
        requested_fidelity="MULTI_FIDELITY",
        autonomy_level=AutonomyLevel.L3_BOUNDED,
    )
    # Must escalate to LIVE_CFD due to transonic shock waves
    assert decision.governing_regime == AerodynamicRegime.TRANSONIC_SHOCK
    assert decision.selected_tier == EpistemicTier.LIVE_CFD
    assert decision.requires_live_cfd is True
    assert "OpenFOAM" in decision.recommended_solver
    assert "Navier-Stokes required" in decision.escalation_reason


def test_fidelity_escalation_gated_by_autonomy():
    engine = MultiFidelityDecisionEngine()
    # In L0_ADVISORY mode, CFD escalation requires human approval
    decision = engine.evaluate_fidelity(
        geometry="NACA0012",
        alpha_deg=16.0,  # Deep stall
        mach=0.15,
        reynolds=3e6,
        autonomy_level=AutonomyLevel.L0_ADVISORY,
    )
    assert decision.requires_live_cfd is True
    assert decision.requires_human_approval is True


def test_dag_execution_with_rans_solver():
    # Verify openfoam rans handler executes within DAG runtime
    aml = """
    INVESTIGATE "NACA0012 RANS Staging" {
        GEOMETRY "NACA0012"
        CONDITIONS { alpha: 4.0 deg, Mach: 0.15, Re: 3000000.0 }
        FIDELITY LIVE_CFD
    }
    """
    dag = compile_aml(parse_aml(aml))[0]
    # Replace panel solver with SOLVER_CFD_RANS to test RANS execution
    dag.nodes["t_solver_panel"].task_type = ScientificTaskType.SOLVER_CFD_RANS
    dag.nodes["t_solver_panel"].epistemic_tier = EpistemicTier.LIVE_CFD

    report = execute_dag(dag)
    assert report.success is True
    rans_out = report.task_results["t_solver_panel"]
    assert rans_out["solver"] == "OpenFOAM simpleFoam (k-omega SST)"
    assert rans_out["case_hash"] != ""
    assert "CL" in rans_out["results"]
    assert rans_out["results"]["CL"] > 0.0
