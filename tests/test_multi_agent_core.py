"""
Tests for AASI 2.0 Stateful Multi-Agent System & MCP Tool Server:
- MultiAgentInvestigationState
- SupervisoryOrchestrator (8 specialist agents)
- Human approval gate
- Checkpoints & event provenance
- MCPEngineeringServer
"""

import pytest
from backend.agent.stateful_multi_agent_system import (
    MultiAgentInvestigationState,
    SupervisoryOrchestrator,
    MultiAgentStage,
    AgentRole,
)
from backend.tools.mcp_engineering_server import (
    MCPEngineeringServer,
    MCPCallRequest,
)


def test_multi_agent_full_autonomous_cycle():
    state = MultiAgentInvestigationState(
        investigation_id="INV-TEST-001",
        objective_prompt="Investigate the effect of Reynolds number and angle of attack on NACA 4412 aerodynamic efficiency.",
        airfoil="NACA 4412",
        alpha_deg=4.0,
        reynolds=1.5e6,
        mach=0.18,
    )

    orchestrator = SupervisoryOrchestrator(state)
    completed_state = orchestrator.run_to_completion(auto_approve_human_gate=True)

    # 1. State must reach COMPLETE
    assert completed_state.current_stage == MultiAgentStage.COMPLETE

    # 2. All 8 specialists must have contributed
    assert len(completed_state.hypotheses) >= 2
    assert len(completed_state.literature_benchmarks) >= 2
    assert completed_state.analytical_results is not None
    assert completed_state.scientific_ml_results is not None
    assert completed_state.cfd_workflow_results is not None
    assert completed_state.mdo_results is not None
    assert completed_state.verification_scorecard is not None

    # 3. Checkpoints and immutable event logging
    assert len(completed_state.checkpoints) >= 8
    assert len(completed_state.events) >= 8
    assert completed_state.provenance_root_hash is not None
    assert len(completed_state.provenance_root_hash) == 64

    # 4. Epistemic integrity in verification scorecard
    cas = completed_state.verification_scorecard["nasa_std_7009b_cas"]
    assert cas["total_score"] == 32
    assert cas["credibility_grade"].startswith("A+")

    # 5. Scientific report synthesized
    report = completed_state.scientific_report_markdown
    assert report is not None
    assert "NACA 4412" in report
    assert "[ANALYTICAL]" in report
    assert "ASME V&V 20" in report


def test_multi_agent_human_approval_gate_pause():
    state = MultiAgentInvestigationState(
        investigation_id="INV-GATE-002",
        objective_prompt="High-risk transonic boundary investigation",
        airfoil="NACA 0012",
        alpha_deg=8.0,
    )
    orchestrator = SupervisoryOrchestrator(state)
    # Pause at gate
    paused_state = orchestrator.run_to_completion(auto_approve_human_gate=False)

    assert paused_state.current_stage == MultiAgentStage.HUMAN_APPROVAL_GATE
    assert paused_state.human_approval_required is True
    assert paused_state.human_approved is False
    assert paused_state.scientific_report_markdown is None


def test_mcp_engineering_server_tool_catalog():
    tools = MCPEngineeringServer.list_tools()
    assert len(tools) >= 6
    names = [t.name for t in tools]
    assert "aero_atmosphere_eval" in names
    assert "aerosandbox_airfoil_solve" in names
    assert "openaerostruct_coupled_mdo" in names
    assert "fno_surface_cp_predict" in names
    assert "pinn_verify_navier_stokes" in names
    assert "dimensional_analysis_buckingham_pi" in names


def test_mcp_engineering_server_tool_execution():
    # 1. Atmospheric evaluation tool
    req_atm = MCPCallRequest(name="aero_atmosphere_eval", arguments={"altitude_m": 5000.0})
    resp_atm = MCPEngineeringServer.call_tool(req_atm)
    assert resp_atm.is_error is False
    assert resp_atm.provenance_hash is not None
    data = resp_atm.content[0]["data"]
    assert data["altitude_m"] == 5000.0
    assert data["temperature_k"] < 288.15

    # 2. AeroSandbox airfoil solve tool
    req_aero = MCPCallRequest(
        name="aerosandbox_airfoil_solve",
        arguments={"airfoil_name": "NACA 4412", "alpha_deg": 3.0, "reynolds": 2e6},
    )
    resp_aero = MCPEngineeringServer.call_tool(req_aero)
    assert resp_aero.is_error is False
    data_aero = resp_aero.content[0]["data"]
    assert data_aero["cl"] > 0.6
    assert data_aero["epistemic_tier"] == "ANALYTICAL"

    # 3. Invalid tool call
    req_bad = MCPCallRequest(name="non_existent_tool", arguments={})
    resp_bad = MCPEngineeringServer.call_tool(req_bad)
    assert resp_bad.is_error is True

