"""
AASI Phase 23: Compute Fabric Manager.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Coordinates backend discovery, deterministic selection policies, preflight gating,
and job lifecycle progression across PLAN, PREPARE, DISPATCH, EXECUTE, INGEST, VALIDATE, PROMOTE.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib
import json

from backend.compute.base import (
    BackendProbeResult,
    BackendType,
    ComputeBackend,
    ExecutionState,
    JobStatusResult,
)
from backend.compute.colab import ColabBackend
from backend.compute.jobs import CFDJobManifest
from backend.compute.local_openfoam import LocalOpenFOAMBackend
from backend.compute.remote_hpc import FutureRemoteHPCBackend


class ComputeFabricManager:
    """
    Central orchestration authority for all computational backends.
    Enforces scientific governance, explicit authorization, and fail-closed safety.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path(".")
        self.backends: Dict[BackendType, ComputeBackend] = {
            BackendType.LOCAL: LocalOpenFOAMBackend(workspace_root=self.workspace_root),
            BackendType.COLAB: ColabBackend(workspace_root=self.workspace_root),
            BackendType.REMOTE_HPC: FutureRemoteHPCBackend(),
        }

    def probe_all_backends(self) -> Dict[str, BackendProbeResult]:
        """Probes all registered computational backends for live status."""
        return {
            btype.value: backend.probe()
            for btype, backend in self.backends.items()
        }

    def select_backend_policy(self, force_backend: Optional[BackendType] = None) -> BackendType:
        """
        Deterministic backend selection hierarchy:
        1. If local OpenFOAM is installed and ready -> LOCAL
        2. Else if Colab execution bundle framework is ready -> COLAB
        3. Else if Remote HPC endpoint is configured -> REMOTE_HPC
        4. Else -> USER_EXECUTED fallback
        """
        if force_backend and force_backend in self.backends:
            return force_backend

        local_probe = self.backends[BackendType.LOCAL].probe()
        if local_probe.openfoam_available:
            return BackendType.LOCAL

        colab_probe = self.backends[BackendType.COLAB].probe()
        if colab_probe.runtime_available:
            return BackendType.COLAB

        hpc_probe = self.backends[BackendType.REMOTE_HPC].probe()
        if hpc_probe.runtime_available:
            return BackendType.REMOTE_HPC

        return BackendType.USER_EXECUTED

    def plan_job(
        self,
        experiment_id: str,
        geometry_name: str,
        alpha_deg: float = 4.0,
        reynolds: float = 3.0e6,
        mach: float = 0.15,
        target_backend: Optional[BackendType] = None,
    ) -> CFDJobManifest:
        """
        Stage 1: PLAN.
        Creates an immutable job manifest with pre-allocated job ID and core hashes.
        """
        job_id = f"JOB-P23-{geometry_name.replace(' ', '')}-AOA{int(alpha_deg)}"
        geom_hash = hashlib.sha256(geometry_name.encode("utf-8")).hexdigest()
        case_hash = hashlib.sha256(f"{job_id}:{alpha_deg}:{reynolds}:{mach}".encode("utf-8")).hexdigest()

        selected_backend = target_backend or self.select_backend_policy()

        manifest = CFDJobManifest(
            job_id=job_id,
            experiment_id=experiment_id,
            geometry_name=geometry_name,
            geometry_hash=geom_hash,
            case_hash=case_hash,
            solver="simpleFoam",
            backend=selected_backend,
            conditions={
                "aoa_deg": alpha_deg,
                "reynolds": reynolds,
                "mach": mach,
            },
            status=ExecutionState.QUEUED,
        )
        manifest.transition_to(ExecutionState.QUEUED, detail="Job planned and queued in fabric manager.")
        return manifest

    def prepare_job(self, manifest: CFDJobManifest) -> CFDJobManifest:
        """
        Stage 2: PREPARE.
        Packages case deck and builds reproducible execution bundle.
        """
        backend = self.backends.get(manifest.backend)
        if not backend:
            manifest.transition_to(ExecutionState.FAILED, detail=f"Backend {manifest.backend} not registered.")
            return manifest

        manifest = backend.submit(manifest)
        return manifest

    def dispatch_job(self, job_id: str, backend_type: Optional[BackendType] = None) -> JobStatusResult:
        """
        Stage 3: DISPATCH.
        Confirms bundle dispatch to the selected compute backend.
        """
        btype = backend_type or BackendType.COLAB
        backend = self.backends.get(btype)
        if not backend:
            return JobStatusResult(
                job_id=job_id,
                backend=btype.value,
                status=ExecutionState.FAILED,
                message=f"Unknown backend {btype}",
            )
        return backend.status(job_id)

    def ingest_and_validate(self, job_id: str, backend_type: Optional[BackendType] = None) -> Dict[str, Any]:
        """
        Stages 4-6: INGEST, VALIDATE & AUDIT.
        Collects raw outputs, executes Physical Validation Gate, and verifies Merkle DAG.
        """
        btype = backend_type or BackendType.COLAB
        backend = self.backends.get(btype)
        if not backend:
            return {"success": False, "status": ExecutionState.FAILED.value, "error": "Backend unavailable"}

        verify_result = backend.verify(job_id)
        return verify_result
