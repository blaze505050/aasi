"""
AASI 2.0 Agent Task Harness API Router.

Exposes:
1. POST /agent/task — Submit research query through the fail-closed autonomous loop
2. GET /agent/tools — Discover registered scientific tools and contracts
3. POST /agent/tools/dispatch — Directly dispatch a registered tool under Safety Governor control
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.governor import ResourceBudget
from backend.harness import (
    global_task_harness,
    global_tool_bus,
    HarnessTaskResult,
    ToolResult,
)

logger = logging.getLogger("aasi.api.agent")

router = APIRouter(prefix="/agent", tags=["AASI 2.0 Agent Harness"])


class AgentTaskRequest(BaseModel):
    """User or system research query to the agent harness."""
    question: str = Field(..., description="Engineering or scientific inquiry")
    max_timeout_seconds: Optional[int] = Field(default=300, ge=1, le=3600)
    max_ram_gb: Optional[float] = Field(default=0.25, ge=0.05)


class ToolDispatchRequest(BaseModel):
    """Direct invocation of a registered tool via ToolBus."""
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    max_timeout_seconds: Optional[int] = Field(default=120)


@router.post(
    "/task",
    response_model=HarnessTaskResult,
    summary="Execute Scientific Inquiry Task",
)
async def execute_agent_task(payload: AgentTaskRequest) -> HarnessTaskResult:
    """
    Submits a research question to the AASI Agent Harness.
    Executes through QUESTION → PLAN → VALIDATE → EXECUTE → VERIFY → RECONCILE → LEARN → DECIDE.
    Fail-closed and verified against physical invariants.
    """
    budget = ResourceBudget(
        max_timeout_seconds=payload.max_timeout_seconds or 300,
        max_ram_gb=payload.max_ram_gb or 0.25,
    )
    result = global_task_harness.run(
        question=payload.question,
        budget=budget,
    )
    return result


@router.get(
    "/tools",
    summary="Catalog of Registered Tools",
)
async def list_registered_tools() -> List[Dict[str, Any]]:
    """Returns the public catalog of all tools registered on the ToolBus."""
    return global_tool_bus.list_tools()


@router.post(
    "/tools/dispatch",
    response_model=ToolResult,
    summary="Direct Tool Dispatch",
)
async def dispatch_tool(payload: ToolDispatchRequest) -> ToolResult:
    """Directly dispatches a registered scientific tool under governor control."""
    budget = ResourceBudget(max_timeout_seconds=payload.max_timeout_seconds or 120)
    return global_tool_bus.dispatch(
        tool_name=payload.tool_name,
        parameters=payload.parameters,
        budget=budget,
    )
