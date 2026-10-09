"""
AASI Phase 27 & Phase 23: Compute Backend Abstraction.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Universal provider interface: probe, stage_job, authorize, dispatch_job,
get_status, collect_results, cancel_job, verify_results.
Maintains full backwards compatibility with Phase 23-26 architecture.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# ============================================================================
# Phase 23 Legacy / Foundation Enums & Models
# ============================================================================

class BackendType(str, Enum):
    """Supported computational backends (Phase 23 compatibility)."""
    LOCAL = "LOCAL"
    COLAB = "COLAB"
    REMOTE_HPC = "REMOTE_HPC"
    USER_EXECUTED = "USER_EXECUTED"
    CACHED = "CACHED"


class ExecutionState(str, Enum):
    """
    Monotonic, verifiable execution states for CFD computation.
    Only genuine solver execution may produce REAL_EXECUTED.
    """
    NOT_CONFIGURED = "NOT_CONFIGURED"
    BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
    QUEUED = "QUEUED"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    PHYSICS_VALIDATION_FAILED = "PHYSICS_VALIDATION_FAILED"
    REPRODUCIBILITY_FAILED = "REPRODUCIBILITY_FAILED"
    REAL_EXECUTED = "REAL_EXECUTED"
    USER_EXECUTED_REQUIRED = "USER_EXECUTED_REQUIRED"
    COLAB_USER_EXECUTED_REQUIRED = "COLAB_USER_EXECUTED_REQUIRED"
    RESULTS_IMPORTED = "RESULTS_IMPORTED"


class BackendProbeResult(BaseModel):
    """Runtime reality measurements for a compute backend."""
    backend: str
    runtime_available: bool
    python_version: str
    cpu: str
    ram_gb: float
    gpu: str = "None"
    gpu_available: bool = False
    openfoam_available: bool = False
    openfoam_version: Optional[str] = None
    disk_free_gb: float
    network_available: bool = True
    execution_mode: str
    status_code: str
    measured_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobStatusResult(BaseModel):
    """Status query response for an active or completed job."""
    job_id: str
    backend: str
    status: ExecutionState
    progress_percent: float = 0.0
    elapsed_seconds: float = 0.0
    message: str = ""
    exit_code: Optional[int] = None
    artifacts_ready: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ComputeBackend(ABC):
    """
    Universal contract for CFD execution backends (Local, Colab, Remote HPC).
    The scientific discovery engine interacts through this interface.
    """

    @abstractmethod
    def probe(self) -> BackendProbeResult:
        """Measure real-time environment status, hardware, and solver availability."""
        pass

    @abstractmethod
    def submit(self, job_manifest: Any) -> Any:
        """Stage, package, and submit a compute job for execution."""
        pass

    @abstractmethod
    def status(self, job_id: str) -> JobStatusResult:
        """Poll the current execution status of a submitted job."""
        pass

    @abstractmethod
    def cancel(self, job_id: str) -> bool:
        """Terminate a running or queued job cleanly."""
        pass

    @abstractmethod
    def collect(self, job_id: str) -> Dict[str, Any]:
        """Collect and parse raw solver outputs, logs, forces, and spatial flowfields."""
        pass

    @abstractmethod
    def verify(self, job_id: str) -> Dict[str, Any]:
        """Independently audit cryptographic checksums and physical conservation laws."""
        pass


# ============================================================================
# Phase 27 Enhanced Remote Compute Fabric Models
# ============================================================================

class ProviderType(str, Enum):
    LOCAL_OPENFOAM = "LOCAL_OPENFOAM"
    COLAB = "COLAB"
    REMOTE_HPC = "REMOTE_HPC"
    USER_AUTHORIZED = "USER_AUTHORIZED"


class ExecutionMode(str, Enum):
    UNATTENDED_DAEMON = "UNATTENDED_DAEMON"
    USER_AUTHORIZED = "USER_AUTHORIZED"
    BATCH_SCHEDULER = "BATCH_SCHEDULER"
    MANUAL_IMPORT = "MANUAL_IMPORT"


class ObservabilityLevel(str, Enum):
    FULL_STREAMING = "FULL_STREAMING"
    POLLING_MILESTONES = "POLLING_MILESTONES"
    LIMITED = "LIMITED"
    NONE = "NONE"


class ProviderCapability(BaseModel):
    provider: str
    available: bool
    execution_mode: ExecutionMode
    unattended: bool
    observability: ObservabilityLevel
    verification: str = "REQUIRED"
    supported_solvers: List[str] = Field(default_factory=lambda: ["simpleFoam"])
    estimated_setup_time_sec: int = 60
    notes: str = ""


class StageJobRequest(BaseModel):
    job_id: str
    user_id: str
    geometry_id: str
    alpha_deg: float
    reynolds: float
    mach: float = 0.15
    mesh_cells_target: int = 50_000
    solver: str = "simpleFoam"


class StagedPackage(BaseModel):
    job_id: str
    provider: str
    manifest_path: str
    case_path: str
    notebook_path: Optional[str] = None
    script_path: Optional[str] = None
    authorization_url: Optional[str] = None
    manifest_hash: str
    case_hash: str
    staged_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobExecutionStatus(BaseModel):
    job_id: str
    provider: str
    state: str
    progress_percent: float = 0.0
    message: str = ""
    observability_state: str = "CONFIRMED"  # or "REMOTE_STATUS_UNKNOWN"
    artifacts_ready: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ComputeProvider(ABC):
    """
    Standardized provider abstraction for AASI remote and local compute.
    The scientific orchestrator interacts through this interface.
    """

    @abstractmethod
    def probe(self) -> ProviderCapability:
        """Measure real-time environment status, hardware, and solver availability."""
        pass

    @abstractmethod
    def stage_job(self, req: StageJobRequest) -> StagedPackage:
        """Synthesize simulation deck, manifest, and execution bundle."""
        pass

    @abstractmethod
    def authorize(self, job_id: str, user_id: str) -> bool:
        """Record operator authorization for compute dispatch."""
        pass

    @abstractmethod
    def dispatch_job(self, job_id: str) -> Dict[str, Any]:
        """Dispatch job or provide execution link."""
        pass

    @abstractmethod
    def get_status(self, job_id: str) -> JobExecutionStatus:
        """Poll verifiable execution state. Never fake RUNNING without evidence."""
        pass

    @abstractmethod
    def collect_results(self, job_id: str) -> Dict[str, Any]:
        """Retrieve output archive, logs, and force polars."""
        pass

    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """Terminate active compute execution."""
        pass

    @abstractmethod
    def verify_results(self, job_id: str, results_bundle: Any) -> Dict[str, Any]:
        """Cryptographically and physically audit returned results."""
        pass
