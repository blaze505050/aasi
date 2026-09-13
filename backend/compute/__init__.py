"""
AASI Compute Module.
Phase 23: Remote Compute Fabric & Execution Backends.
"""

from backend.compute.models import (
    ComputeBackendType,
    ExecutionStatus,
    ComputeRequest,
    GeneratedCaseDeck,
    UploadedArtifactPayload,
    IngestionResult,
)
from backend.compute.registry import ComputeBackendRegistry
from backend.compute.user_provided import UserProvidedCaseGenerator
from backend.compute.artifacts import ArtifactIngestionService
from backend.compute.hardware_matrix import (
    HardwareProfile,
    RoutingDecision,
    ComputationalTaskType,
    HardwareMatrixManager,
    hardware_matrix_manager,
)

# Phase 23 Remote Compute Fabric
from backend.compute.base import (
    BackendType,
    ExecutionState,
    ComputeBackend,
    BackendProbeResult,
    JobStatusResult,
)
from backend.compute.jobs import (
    CFDJobManifest,
    CFDJobEvent,
)
from backend.compute.colab import ColabBackend
from backend.compute.local_openfoam import LocalOpenFOAMBackend
from backend.compute.remote_hpc import FutureRemoteHPCBackend
from backend.compute.manager import ComputeFabricManager

__all__ = [
    # Legacy Phase 5/6 models
    "ComputeBackendType",
    "ExecutionStatus",
    "ComputeRequest",
    "GeneratedCaseDeck",
    "UploadedArtifactPayload",
    "IngestionResult",
    "ComputeBackendRegistry",
    "UserProvidedCaseGenerator",
    "ArtifactIngestionService",
    "HardwareProfile",
    "RoutingDecision",
    "ComputationalTaskType",
    "HardwareMatrixManager",
    "hardware_matrix_manager",
    # Phase 23 Compute Fabric
    "BackendType",
    "ExecutionState",
    "ComputeBackend",
    "BackendProbeResult",
    "JobStatusResult",
    "CFDJobManifest",
    "CFDJobEvent",
    "ColabBackend",
    "LocalOpenFOAMBackend",
    "FutureRemoteHPCBackend",
    "ComputeFabricManager",
]
