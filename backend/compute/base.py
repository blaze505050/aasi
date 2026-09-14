"""
AASI Phase 23: Compute Backend Abstraction.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Defines the standard ComputeBackend interface and monotonic execution states.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class BackendType(str, Enum):
    """Supported computational backends."""
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
    The scientific discovery engine interacts exclusively through this interface.
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
