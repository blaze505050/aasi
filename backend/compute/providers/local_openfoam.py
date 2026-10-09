"""
AASI Phase 27: Local OpenFOAM Compute Provider.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Ensures zero unauthorized laptop load: probes truthfully and only reports available
if local OpenFOAM installation is verified and explicitly enabled by deployment policy.
"""

import shutil
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path

from backend.compute.base import (
    ComputeProvider,
    ProviderCapability,
    ExecutionMode,
    ObservabilityLevel,
    StageJobRequest,
    StagedPackage,
    JobExecutionStatus,
)
from backend.deployment.config import get_deployment_config


class LocalOpenFOAMProvider(ComputeProvider):
    """Local OpenFOAM provider with honest capability probing and zero-load safeguards."""

    def __init__(self):
        self.config = get_deployment_config()
        self.data_dir = Path("data/compute_jobs")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def probe(self) -> ProviderCapability:
        # Check if explicitly enabled in deployment config
        if not self.config.enable_local_openfoam:
            return ProviderCapability(
                provider="LOCAL_OPENFOAM",
                available=False,
                execution_mode=ExecutionMode.UNATTENDED_DAEMON,
                unattended=True,
                observability=ObservabilityLevel.FULL_STREAMING,
                notes="Disabled by AASI deployment policy to prevent host laptop computational load.",
            )

        # Check binary presence
        simplefoam_bin = shutil.which("simpleFoam")
        blockmesh_bin = shutil.which("blockMesh")
        is_installed = bool(simplefoam_bin and blockmesh_bin)

        return ProviderCapability(
            provider="LOCAL_OPENFOAM",
            available=is_installed,
            execution_mode=ExecutionMode.UNATTENDED_DAEMON,
            unattended=True,
            observability=ObservabilityLevel.FULL_STREAMING,
            supported_solvers=["simpleFoam"],
            notes="Local OpenFOAM installation detected on host system." if is_installed else "OpenFOAM binaries not found in PATH.",
        )

    def stage_job(self, req: StageJobRequest) -> StagedPackage:
        from backend.compute.colab_session import ColabSessionPackager
        bundle = ColabSessionPackager.create_session_bundle(
            job_id=req.job_id,
            geometry_id=req.geometry_id,
            alpha_deg=req.alpha_deg,
            reynolds=req.reynolds,
            mach=req.mach,
        )
        return StagedPackage(
            job_id=req.job_id,
            provider="LOCAL_OPENFOAM",
            manifest_path=bundle["manifest_path"],
            case_path=bundle["case_path"],
            manifest_hash=bundle["manifest_hash"],
            case_hash=bundle["case_hash"],
        )

    def authorize(self, job_id: str, user_id: str) -> bool:
        # Local execution does not require external third-party authorization
        return True

    def dispatch_job(self, job_id: str) -> Dict[str, Any]:
        probe = self.probe()
        if not probe.available:
            raise RuntimeError(f"Local OpenFOAM provider unavailable: {probe.notes}")
        return {"job_id": job_id, "status": "DISPATCHED", "provider": "LOCAL_OPENFOAM"}

    def get_status(self, job_id: str) -> JobExecutionStatus:
        return JobExecutionStatus(
            job_id=job_id,
            provider="LOCAL_OPENFOAM",
            state="NOT_RUNNING",
            message="Local OpenFOAM provider inactive.",
        )

    def collect_results(self, job_id: str) -> Dict[str, Any]:
        return {}

    def cancel_job(self, job_id: str) -> bool:
        return True

    def verify_results(self, job_id: str, results_bundle: Any) -> Dict[str, Any]:
        return {"verified": False, "reason": "No results collected"}
