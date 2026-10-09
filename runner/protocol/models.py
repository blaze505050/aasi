"""
AASI Runner Communication Protocol Models.
Defines typed message contracts for capabilities, registration, approval tokens,
execution requests, and structured artifact returns.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class RunnerStatus(str, Enum):
    ONLINE = "ONLINE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"


class ExecutionStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    REJECTED_SECURITY = "REJECTED_SECURITY"


class RunnerCapabilities(BaseModel):
    """Host workstation compute and solver capability profile."""
    runner_id: str
    host_name: str
    os_platform: str
    is_wsl2: bool
    python_version: str
    cpu_cores_logical: int
    cpu_cores_physical: int
    ram_total_gb: float
    ram_available_gb: float
    disk_free_gb: float
    has_cuda: bool
    cuda_device_name: Optional[str] = None
    cuda_memory_gb: Optional[float] = None
    has_mpi: bool
    mpi_version: Optional[str] = None
    openfoam_available: bool
    openfoam_version: Optional[str] = None
    supported_solvers: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RunnerRegistration(BaseModel):
    """Handshake record when Local Runner registers with the AASI Control Plane."""
    runner_id: str
    auth_token: str
    workspace_path: str
    capabilities: RunnerCapabilities
    registered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ExecutionApproval(BaseModel):
    """Cryptographic authorization record approving solver execution."""
    approval_token: str
    job_id: str
    user_approved: bool = False
    operator_identity: str = "local_operator"
    approved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    max_timeout_seconds: int = 300


class ExecutionRequest(BaseModel):
    """Structured solver invocation request. Prohibits arbitrary shell commands."""
    job_id: str
    solver_command: str
    solver_args: List[str] = Field(default_factory=list)
    case_dir_relative: str
    approval: ExecutionApproval
    timeout_seconds: int = 300
    environment_vars: Dict[str, str] = Field(default_factory=dict)


class ExecutionArtifact(BaseModel):
    """Provenance record of a file produced by solver execution."""
    relative_path: str
    file_size_bytes: int
    sha256_hash: str


class ExecutionResult(BaseModel):
    """Artifact-only structured return payload from solver execution."""
    job_id: str
    runner_id: str
    status: ExecutionStatus
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    stdout_tail: str = ""
    stderr_tail: str = ""
    artifacts: List[ExecutionArtifact] = Field(default_factory=list)
    error_message: Optional[str] = None
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
