"""
AASI Control Plane Modular API Router: Local Runner Management.
Endpoints:
- POST /api/runner/register: Register explicitly installed Local Runner
- GET /api/runner/capabilities: Probe active runner capabilities
- POST /api/runner/heartbeat: Heartbeat & liveness probe
- POST /api/runner/jobs/execute: Execute approved job on local runner
- GET /api/runner/status: Overall runner status
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Header, Depends
from pydantic import BaseModel, Field

from runner.protocol.models import (
    RunnerCapabilities,
    RunnerRegistration,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)
from runner.agent import LocalRunnerAgent

logger = logging.getLogger("aasi.api.runner")

router = APIRouter(prefix="/runner", tags=["Local Runner"])

# In-memory registry of active local runner
_active_runner_agent: Optional[LocalRunnerAgent] = None
_active_registration: Optional[RunnerRegistration] = None
_last_heartbeat: Optional[str] = None


class HeartbeatPayload(BaseModel):
    runner_id: str
    status: str = "ONLINE"
    active_jobs: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@router.post("/register", response_model=Dict[str, Any])
async def register_local_runner(registration: RunnerRegistration) -> Dict[str, Any]:
    """Registers an explicitly installed host Local Runner with the control plane."""
    global _active_registration, _last_heartbeat
    _active_registration = registration
    _last_heartbeat = datetime.now(timezone.utc).isoformat()

    logger.info(
        "Local Runner registered: %s (OS: %s, OpenFOAM: %s, Python: %s)",
        registration.runner_id,
        registration.capabilities.os_platform,
        registration.capabilities.openfoam_version,
        registration.capabilities.python_version,
    )

    return {
        "status": "REGISTERED",
        "runner_id": registration.runner_id,
        "message": "Local runner successfully registered and ready for approved execution.",
        "registered_at": registration.registered_at,
    }


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_runner_capabilities() -> Dict[str, Any]:
    """Returns capabilities of the active Local Runner or probes local host if unmounted."""
    global _active_runner_agent, _active_registration

    if _active_registration:
        return {
            "registered": True,
            "runner_id": _active_registration.runner_id,
            "capabilities": _active_registration.capabilities.model_dump(),
            "last_heartbeat": _last_heartbeat,
        }

    # If no external runner process has connected, probe workstation capabilities
    if _active_runner_agent is None:
        _active_runner_agent = LocalRunnerAgent()

    caps = _active_runner_agent.get_capabilities()
    return {
        "registered": True,
        "runner_id": caps.runner_id,
        "capabilities": caps.model_dump(),
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/heartbeat", response_model=Dict[str, Any])
async def runner_heartbeat(payload: HeartbeatPayload) -> Dict[str, Any]:
    """Receives periodic heartbeat from connected runner."""
    global _last_heartbeat
    _last_heartbeat = datetime.now(timezone.utc).isoformat()
    return {"status": "ACK", "timestamp": _last_heartbeat}


@router.post("/jobs/execute", response_model=ExecutionResult)
async def execute_runner_job(
    request: ExecutionRequest,
    x_runner_token: Optional[str] = Header(None),
) -> ExecutionResult:
    """
    Dispatches an approved execution request to the local runner sandbox.
    Requires explicit user approval token inside request payload.
    """
    global _active_runner_agent

    # Fail closed if not approved
    if not request.approval or not request.approval.user_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Execution denied: Explicit user approval required at execution boundary.",
        )

    if _active_runner_agent is None:
        _active_runner_agent = LocalRunnerAgent()

    result = _active_runner_agent.execute_job(request)
    return result


@router.get("/status", response_model=Dict[str, Any])
async def get_runner_status() -> Dict[str, Any]:
    """Returns current Local Runner operational status."""
    is_active = (_active_registration is not None or _active_runner_agent is not None)
    return {
        "active": is_active,
        "runner_id": _active_registration.runner_id if _active_registration else (_active_runner_agent.runner_id if _active_runner_agent else None),
        "last_heartbeat": _last_heartbeat,
    }
