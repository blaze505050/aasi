"""
AASI Compute Backend Registry.

Manages registration and dispatch across LOCAL, REMOTE, USER_EXECUTED, and CACHED backends.
"""

from typing import Dict, Any
from backend.compute.models import ComputeBackendType, ComputeRequest, ExecutionStatus
from backend.compute.local import LocalComputeBackend
from backend.compute.remote import RemoteComputeBackend
from backend.compute.user_provided import UserProvidedCaseGenerator
from backend.compute.artifacts import ArtifactIngestionService


class ComputeBackendRegistry:
    """Central registry routing simulation requests to the requested backend."""

    def __init__(self):
        self.local_backend = LocalComputeBackend()
        self.remote_backend = RemoteComputeBackend()
        self.user_generator = UserProvidedCaseGenerator()
        self.artifact_service = ArtifactIngestionService()

    def dispatch(self, request: ComputeRequest) -> Dict[str, Any]:
        """Dispatches request according to specified backend."""
        if request.backend == ComputeBackendType.USER_EXECUTED:
            case_deck = self.user_generator.generate_case(request)
            return {
                "backend": ComputeBackendType.USER_EXECUTED.value,
                "status": ExecutionStatus.AWAITING_USER_UPLOAD.value,
                "case_deck": case_deck.model_dump(),
                "instructions": "Standalone case directory generated. Execute with ./scripts/run.sh and upload log files back to AASI."
            }

        elif request.backend == ComputeBackendType.LOCAL:
            return self.local_backend.execute(request)

        elif request.backend == ComputeBackendType.REMOTE:
            # Generate case first, then provide Slurm script
            case_deck = self.user_generator.generate_case(request)
            slurm_script = self.remote_backend.generate_slurm_job_script(request)
            ssh_cmd = self.remote_backend.generate_ssh_dispatch_command(request)
            return {
                "backend": ComputeBackendType.REMOTE.value,
                "status": "READY_FOR_REMOTE_DISPATCH",
                "case_deck": case_deck.model_dump(),
                "slurm_script": slurm_script,
                "ssh_command": ssh_cmd
            }

        elif request.backend == ComputeBackendType.CACHED:
            return {
                "backend": ComputeBackendType.CACHED.value,
                "status": ExecutionStatus.COMPLETED.value,
                "message": "Using cached simulation benchmark result."
            }

        else:
            return {
                "status": ExecutionStatus.FAILED.value,
                "error": f"Unsupported compute backend: {request.backend}"
            }
