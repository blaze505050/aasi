"""
AASI Milestone 9: Bounded Closed-Loop Scientific API Router.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Endpoints to launch, inspect, and step through the bounded autonomous
scientific investigation lifecycle across all 10 stages.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.science.closed_loop import (
    ClosedLoopReport,
    LoopStoppingReason,
    closed_loop_orchestrator,
)

router = APIRouter(prefix="/closed-loop", tags=["Closed-Loop Scientific Orchestrator"])


class LaunchClosedLoopRequest(BaseModel):
    user_question: str = Field(
        default="Investigate aerodynamic lift and drag for NACA 0012 at alpha=4.0 degrees",
        json_schema_extra={"example": "Investigate aerodynamic lift and drag for NACA 0012 at alpha=4.0 degrees"},
    )
    geometry: str = Field(default="NACA 0012", json_schema_extra={"example": "NACA 0012"})
    alpha_deg: float = Field(default=4.0, json_schema_extra={"example": 4.0})
    reynolds: float = Field(default=3.0e6, json_schema_extra={"example": 3.0e6})
    mach: float = Field(default=0.15, json_schema_extra={"example": 0.15})
    max_cycles: int = Field(default=3, ge=1, le=5, description="Strict bounded limit (max 5 cycles)")
    auto_stage_colab: bool = Field(default=True)
    simulated_execution_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional simulation results payload for automated testing of downstream verify/compare/remember stages.",
    )


@router.post("/run", response_model=ClosedLoopReport, summary="Execute Bounded Scientific Closed-Loop")
async def run_closed_loop(req: LaunchClosedLoopRequest) -> ClosedLoopReport:
    """
    Executes the 10-stage scientific investigation lifecycle:
    interpret -> hypothesize -> plan -> method -> compute -> execute/stage -> verify -> compare -> remember -> next experiment
    
    STRICT GOVERNANCE:
    - Guaranteed bounded execution (never runaway).
    - Automatically pauses or halts when stopping conditions are met
      (e.g. sufficient evidence, execution staged awaiting external run, verification failure, or max cycles).
    """
    return closed_loop_orchestrator.execute_bounded_loop(
        user_question=req.user_question,
        geometry=req.geometry,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
        max_cycles=req.max_cycles,
        auto_stage_colab=req.auto_stage_colab,
        simulated_execution_data=req.simulated_execution_data,
    )


@router.get("/sessions/{session_id}", response_model=ClosedLoopReport, summary="Get Closed-Loop Session State")
async def get_closed_loop_session(session_id: str) -> ClosedLoopReport:
    """Retrieves full investigation audit trajectory, cycle provenance, and stopping status."""
    session = closed_loop_orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Closed-loop session '{session_id}' not found.",
        )
    return session


@router.get("/stopping-criteria", response_model=Dict[str, str], summary="List Loop Stopping Criteria")
async def get_stopping_criteria() -> Dict[str, str]:
    """Returns the explicit halting conditions that bound the autonomous loop."""
    return {
        LoopStoppingReason.SUFFICIENT_EVIDENCE.value: "Target scientific question answered within required convergence tolerance.",
        LoopStoppingReason.USER_APPROVAL_REQUIRED.value: "Paused awaiting explicit researcher authorization before execution.",
        LoopStoppingReason.EXECUTION_STAGED_AWAITING_EXTERNAL.value: "Computation packaged (e.g. Colab notebook); awaiting external execution archive upload.",
        LoopStoppingReason.FAILED_VERIFICATION.value: "Numerical divergence or unphysical results (negative drag); recorded as negative evidence.",
        LoopStoppingReason.MISSING_DEPENDENCY.value: "Required solver, meshing utility, or external capability unavailable.",
        LoopStoppingReason.UNRESOLVED_UNCERTAINTY.value: "Epistemic divergence cannot be resolved without new empirical benchmarks.",
        LoopStoppingReason.MAX_CYCLES_REACHED.value: "Hard iteration ceiling reached to prevent runaway computation.",
    }
