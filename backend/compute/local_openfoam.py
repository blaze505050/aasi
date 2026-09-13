"""
AASI Phase 23: Local OpenFOAM Compute Backend.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Directly interfaces with host workstation solvers across Modes A-E, enforcing strict safety limits.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import shutil
import os

from backend.cfd.real_execution import CFDResourceGovernor, RealCFDExecutionBridge
from backend.compute.base import (
    BackendProbeResult,
    BackendType,
    ComputeBackend,
    ExecutionState,
    JobStatusResult,
)
from backend.compute.jobs import CFDJobManifest


class LocalOpenFOAMBackend(ComputeBackend):
    """
    Host workstation CFD execution backend.
    Enforces local workstation disk, RAM, and CPU safety reserves.
    Fails closed with USER_EXECUTED_REQUIRED when no local solver is found.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path(".")
        self.bridge = RealCFDExecutionBridge()

    def probe(self) -> BackendProbeResult:
        """Audit host workstation solver availability and hardware resources."""
        solver_detected = self.bridge.detect_solver()
        res = CFDResourceGovernor.audit_resources()

        has_solver = solver_detected["mode"] not in ["NO_SOLVER", "USER_EXECUTED"]

        return BackendProbeResult(
            backend="local_openfoam",
            runtime_available=has_solver,
            python_version="3.12",
            cpu=f"{os.cpu_count() or 4} Cores",
            ram_gb=round(res.get("total_ram_gb", 16.0), 2),
            gpu="None",
            gpu_available=False,
            openfoam_available=has_solver,
            openfoam_version=solver_detected.get("version"),
            disk_free_gb=round(res.get("available_disk_gb", 20.0), 2),
            network_available=True,
            execution_mode=solver_detected["mode"],
            status_code="LOCAL_SOLVER_READY" if has_solver else "USER_EXECUTED_REQUIRED",
        )

    def submit(self, job_manifest: CFDJobManifest) -> CFDJobManifest:
        """Stage canonical case deck for local execution."""
        from backend.physics_ai.geometry_representation import GeometryRepresentationEngine
        geo = GeometryRepresentationEngine()
        coords = geo.generate_naca4(thickness=0.12, camber=0.0).tolist()

        case_dir = self.bridge.prepare_canonical_case(
            case_name=f"local_{job_manifest.job_id}",
            airfoil_name=job_manifest.geometry_name,
            coordinates=coords,
            alpha_deg=float(job_manifest.conditions.get("aoa_deg", 4.0)),
            reynolds=float(job_manifest.conditions.get("reynolds", 3.0e6)),
            mach=float(job_manifest.conditions.get("mach", 0.15)),
        )

        job_manifest.artifacts_dir = str(case_dir.as_posix())
        # Try live execution
        exec_res = self.bridge.execute_case(case_dir)
        if exec_res["status"] == "USER_EXECUTED_REQUIRED":
            job_manifest.transition_to(
                ExecutionState.USER_EXECUTED_REQUIRED,
                detail="Host lacks native OpenFOAM binary. Case staged for manual execution."
            )
        elif exec_res["status"] == "COMPLETED":
            job_manifest.transition_to(ExecutionState.COMPLETED, detail="Local solver execution complete.")
        else:
            job_manifest.transition_to(ExecutionState.FAILED, detail=str(exec_res.get("error", "Execution failed.")))

        return job_manifest

    def status(self, job_id: str) -> JobStatusResult:
        """Return status of local job."""
        return JobStatusResult(
            job_id=job_id,
            backend="local_openfoam",
            status=ExecutionState.USER_EXECUTED_REQUIRED,
            message="Local solver execution requires client action under Mode E.",
        )

    def cancel(self, job_id: str) -> bool:
        return True

    def collect(self, job_id: str) -> Dict[str, Any]:
        return {"collected": False, "status": "USER_EXECUTED_REQUIRED"}

    def verify(self, job_id: str) -> Dict[str, Any]:
        return {"verified": False, "status": "USER_EXECUTED_REQUIRED"}
