"""
AASI Phase 27: Compute Providers API Router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.auth.models import User
from backend.auth.dependencies import get_current_user
from backend.compute.base import ProviderCapability, StageJobRequest, StagedPackage
from backend.compute.provider_manager import provider_manager
from backend.compute.queue import job_queue, JobState

router = APIRouter(prefix="/compute", tags=["Compute Infrastructure"])


class AuthorizeRequest(BaseModel):
    job_id: str


@router.get("/providers", response_model=Dict[str, ProviderCapability], summary="Probe All Compute Providers")
async def probe_providers():
    """Honest runtime probe of Local OpenFOAM, Google Colab, and Remote HPC capabilities."""
    return provider_manager.probe_all()


@router.post("/stage", response_model=StagedPackage, summary="Stage Job for Compute Backend")
async def stage_compute_job(req: StageJobRequest, user: User = Depends(get_current_user)):
    job = job_queue.get_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    provider = provider_manager.get_provider(job.provider)
    staged = provider.stage_job(req)
    job_queue.transition_state(
        req.job_id,
        JobState.STAGED,
        reason=f"Staged with {job.provider} provider.",
        artifacts={
            "manifest_path": staged.manifest_path,
            "case_path": staged.case_path,
            "notebook_path": staged.notebook_path or "",
        },
    )
    return staged


@router.post("/authorize", summary="User Authorizes Remote Compute Execution")
async def authorize_compute(req: AuthorizeRequest, user: User = Depends(get_current_user)):
    job = job_queue.get_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    provider = provider_manager.get_provider(job.provider)
    success = provider.authorize(req.job_id, user.user_id)
    dispatch_info = provider.dispatch_job(req.job_id)

    # Transition state to DISPATCHED
    job_queue.transition_state(
        req.job_id,
        JobState.DISPATCHED,
        reason=f"Operator authorization recorded for {job.provider}.",
    )
    return {
        "job_id": req.job_id,
        "authorized": success,
        "provider": job.provider,
        "dispatch_info": dispatch_info,
    }


# Milestone 2: Compute Router Endpoint
from backend.compute.router import (
    ComputeRequirements,
    ComputeRouterDecision,
    DeterministicComputeRouter,
)
from backend.compute.colab_session import ColabSessionPackager
from fastapi.responses import FileResponse
from pathlib import Path


@router.post("/route", response_model=ComputeRouterDecision, summary="Deterministic Compute Routing Policy")
async def route_compute_task(req: ComputeRequirements) -> ComputeRouterDecision:
    """
    Evaluates simulation requirements against host workstation resources
    and routes deterministically to LOCAL, COLAB, REMOTE_FUTURE, or UNAVAILABLE.
    Provides scientific explanation and order-of-magnitude regime without claiming exact runtime.
    """
    return DeterministicComputeRouter.route(req)


# Milestone 3: Colab Fallback & Reproducible Notebook Packaging Endpoints
class ColabPackageRequest(BaseModel):
    job_id: str
    geometry_id: str = "NACA 0012"
    alpha_deg: float = 4.0
    reynolds: float = 3.0e6
    mach: float = 0.15


@router.post("/colab/package", summary="Synthesize Reproducible Google Colab Execution Bundle")
async def package_colab_bundle(req: ColabPackageRequest) -> Dict[str, Any]:
    """
    Generates self-contained 1-click Colab package:
    1. job_manifest.json (and results_manifest.json)
    2. case.tar.gz (OpenFOAM 0/, constant/, system/, case_identity.json)
    3. AASI_Colab_<JOB_ID>.ipynb (and notebook.ipynb)
    Governing Rule: Absolute Anti-Fabrication Rule (status is EXECUTED, never VERIFIED).
    """
    return ColabSessionPackager.create_session_bundle(
        job_id=req.job_id,
        geometry_id=req.geometry_id,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
    )


@router.get("/jobs/{job_id}/notebook", summary="Download Colab Notebook (.ipynb)")
async def download_job_notebook(job_id: str):
    """Downloads the generated AASI_Colab_<JOB_ID>.ipynb or legacy notebook.ipynb."""
    job_dir = Path("data/compute_jobs") / job_id
    named_nb = job_dir / f"AASI_Colab_{job_id}.ipynb"
    legacy_nb = job_dir / "notebook.ipynb"

    target_nb = named_nb if named_nb.exists() else legacy_nb
    if not target_nb.exists():
        raise HTTPException(status_code=404, detail=f"No notebook found for job '{job_id}'.")

    return FileResponse(
        path=str(target_nb),
        filename=target_nb.name,
        media_type="application/x-ipynb+json",
    )


@router.get("/jobs/{job_id}/case", summary="Download OpenFOAM Case Tarball (case.tar.gz)")
async def download_job_case(job_id: str):
    """Downloads the canonical case.tar.gz for a staged simulation job."""
    job_dir = Path("data/compute_jobs") / job_id
    case_path = job_dir / "case.tar.gz"

    if not case_path.exists():
        raise HTTPException(status_code=404, detail=f"No case.tar.gz found for job '{job_id}'.")

    return FileResponse(
        path=str(case_path),
        filename="case.tar.gz",
        media_type="application/gzip",
    )

