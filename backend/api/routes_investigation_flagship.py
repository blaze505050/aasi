"""
AASI 2.0 Flagship Autonomous Investigation & Multi-Agent API Routes.
Provides RESTful endpoints for triggering multi-agent research loops,
retrieving scientific reports, and interacting with the MCP tool server.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.agent.stateful_multi_agent_system import (
    MultiAgentInvestigationState,
    SupervisoryOrchestrator,
    MultiAgentStage,
)
from backend.tools.mcp_engineering_server import (
    MCPEngineeringServer,
    MCPCallRequest,
    MCPCallResponse,
    MCPToolDefinition,
)

logger = logging.getLogger("aasi.api.flagship")

router = APIRouter(prefix="/investigation", tags=["Autonomous Multi-Agent Investigation"])


class RunMultiAgentRequest(BaseModel):
    investigation_id: Optional[str] = None
    objective_prompt: str = Field(
        default="Investigate the effect of Reynolds number and angle of attack on NACA 4412 aerodynamic efficiency.",
        description="Scientific aerospace research inquiry",
    )
    airfoil: str = Field(default="NACA 4412", description="Target aerodynamic profile")
    alpha_deg: float = Field(default=4.0, description="Angle of attack in degrees")
    reynolds: float = Field(default=1.5e6, description="Reynolds number")
    mach: float = Field(default=0.18, description="Freestream Mach number")
    aspect_ratio: float = Field(default=8.0, description="Finite wing aspect ratio")
    auto_approve_human_gate: bool = Field(default=True, description="Whether to proceed past human authorization gate")


class InvestigationSummaryResponse(BaseModel):
    investigation_id: str
    stage: str
    airfoil: str
    alpha_deg: float
    reynolds: float
    mach: float
    cl_3d: Optional[float] = None
    cd_3d: Optional[float] = None
    l_over_d: Optional[float] = None
    cas_score: Optional[int] = None
    cas_grade: Optional[str] = None
    gci_fine_pct: Optional[float] = None
    provenance_root_hash: Optional[str] = None
    specialists_dispatched: int
    events_count: int
    report_markdown: Optional[str] = None
    state_payload: Dict[str, Any]


@router.post("/flagship/run", response_model=InvestigationSummaryResponse)
def run_flagship_investigation(req: RunMultiAgentRequest):
    """
    Triggers an end-to-end autonomous scientific investigation using the 8 specialist agents.
    """
    inv_id = req.investigation_id or f"INV-AASI-{int(req.alpha_deg * 10)}-{req.airfoil.replace(' ', '')}"
    state = MultiAgentInvestigationState(
        investigation_id=inv_id,
        objective_prompt=req.objective_prompt,
        airfoil=req.airfoil,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
        aspect_ratio=req.aspect_ratio,
    )

    orchestrator = SupervisoryOrchestrator(state)
    final_state = orchestrator.run_to_completion(auto_approve_human_gate=req.auto_approve_human_gate)

    aero = final_state.analytical_results.get("aerodynamics_analytical", {}) if final_state.analytical_results else {}
    cas = final_state.verification_scorecard.get("nasa_std_7009b_cas", {}) if final_state.verification_scorecard else {}
    asme = final_state.verification_scorecard.get("asme_vv20", {}) if final_state.verification_scorecard else {}

    return InvestigationSummaryResponse(
        investigation_id=final_state.investigation_id,
        stage=final_state.current_stage.value,
        airfoil=final_state.airfoil,
        alpha_deg=final_state.alpha_deg,
        reynolds=final_state.reynolds,
        mach=final_state.mach,
        cl_3d=aero.get("cl_3d"),
        cd_3d=aero.get("cd_3d"),
        l_over_d=aero.get("l_over_d"),
        cas_score=cas.get("total_score"),
        cas_grade=cas.get("credibility_grade"),
        gci_fine_pct=asme.get("gci_fine_percent"),
        provenance_root_hash=final_state.provenance_root_hash,
        specialists_dispatched=8,
        events_count=len(final_state.events),
        report_markdown=final_state.scientific_report_markdown,
        state_payload=final_state.model_dump(),
    )


@router.get("/mcp/tools", response_model=List[MCPToolDefinition])
def list_mcp_tools():
    """Returns the Model Context Protocol tool catalog."""
    return MCPEngineeringServer.list_tools()


@router.post("/mcp/call", response_model=MCPCallResponse)
def call_mcp_tool(req: MCPCallRequest):
    """Executes an MCP engineering tool through standard JSON-RPC interface."""
    return MCPEngineeringServer.call_tool(req)

