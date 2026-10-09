"""
AASI Milestone 5: Experiment Planner API Router.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Candidate experiment generation with question, changed parameters, method,
expected information, cost estimate, dependencies, and rationale.
Explicitly refuses to claim mathematical optimality.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.science.planner import (
    CandidateExperiment,
    CandidateStatus,
    experiment_planner,
)
from backend.compute.colab_session import ColabSessionPackager

router = APIRouter(prefix="/planner", tags=["Experiment Planner"])


class GenerateCandidatesRequest(BaseModel):
    geometry: str = Field(default="NACA 0012", json_schema_extra={"example": "NACA 0012"})
    alpha_deg: Optional[float] = Field(default=None)
    current_alpha_deg: Optional[float] = Field(default=None)
    reynolds: float = Field(default=3.0e6, json_schema_extra={"example": 3.0e6})
    mach: float = Field(default=0.15, json_schema_extra={"example": 0.15})
    has_verified_cfd: bool = Field(default=False)

    @property
    def effective_alpha(self) -> float:
        if self.alpha_deg is not None:
            return float(self.alpha_deg)
        if self.current_alpha_deg is not None:
            return float(self.current_alpha_deg)
        return 4.0


class StageCandidateRequest(BaseModel):
    destination: str = Field(default="COLAB", json_schema_extra={"example": "COLAB"})
    override_job_id: Optional[str] = Field(default=None)


@router.post("/generate", summary="Generate Ranked Candidate Experiments (Workspace alias)")
async def generate_candidates_alias(req: GenerateCandidatesRequest) -> Dict[str, Any]:
    """Compatibility endpoint returning {'candidates': [...]} for InvestigationWorkspace."""
    candidates = experiment_planner.generate_candidates(
        geometry=req.geometry,
        alpha_deg=req.effective_alpha,
        reynolds=req.reynolds,
        mach=req.mach,
        has_verified_cfd=req.has_verified_cfd,
    )
    return {"candidates": [c.to_presentation_dict() for c in candidates]}


@router.post("/candidates", response_model=List[Dict[str, Any]], summary="Generate Ranked Candidate Experiments")
async def generate_candidate_experiments(req: GenerateCandidatesRequest) -> List[Dict[str, Any]]:
    """
    Generates candidate experiments ranked by transparent multi-criteria heuristic:
    S = clamp(0.35*D + 0.30*R + 0.25*U - 0.15*C, 0.0, 1.0).
    Every experiment contains question, parameters, method, expected information, cost, dependencies, reason.
    DOES NOT claim mathematical optimality.
    """
    candidates = experiment_planner.generate_candidates(
        geometry=req.geometry,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
        has_verified_cfd=req.has_verified_cfd,
    )
    return [c.to_presentation_dict() for c in candidates]


@router.get("/candidates", response_model=List[Dict[str, Any]], summary="List Cached Candidate Experiments")
async def list_candidate_experiments() -> List[Dict[str, Any]]:
    """Lists currently proposed candidate experiments ordered by transparent heuristic score."""
    candidates = experiment_planner.list_candidates()
    return [c.to_presentation_dict() for c in candidates]


@router.get("/candidates/{experiment_id}", response_model=Dict[str, Any], summary="Get Candidate Experiment by ID")
async def get_candidate_experiment(experiment_id: str) -> Dict[str, Any]:
    """Retrieves full candidate experiment specification and score breakdown."""
    candidate = experiment_planner.get_candidate(experiment_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Candidate experiment '{experiment_id}' not found.")
    return candidate.to_presentation_dict()


@router.post("/candidates/{experiment_id}/stage", response_model=Dict[str, Any], summary="Stage Candidate Experiment for Execution")
async def stage_candidate_experiment(experiment_id: str, req: StageCandidateRequest) -> Dict[str, Any]:
    """
    Stages a candidate experiment for execution by synthesizing a reproducible execution bundle.
    Transitions status from CANDIDATE to STAGED.
    """
    candidate = experiment_planner.get_candidate(experiment_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Candidate experiment '{experiment_id}' not found.")

    job_id = req.override_job_id or f"JOB-{candidate.experiment_id}"
    geom = candidate.geometry_id or "NACA 0012"
    alpha = float(candidate.changed_parameters.get("alpha_deg", 4.0))
    reynolds = float(candidate.changed_parameters.get("reynolds", 3.0e6))
    mach = float(candidate.changed_parameters.get("mach", 0.15))

    bundle = ColabSessionPackager.create_session_bundle(
        job_id=job_id,
        geometry_id=geom,
        alpha_deg=alpha,
        reynolds=reynolds,
        mach=mach,
    )
    candidate.status = CandidateStatus.STAGED

    return {
        "experiment_id": candidate.experiment_id,
        "job_id": job_id,
        "status": candidate.status.value,
        "destination": req.destination,
        "bundle": bundle,
        "message": f"Candidate {candidate.experiment_id} staged as job {job_id} ({geom} alpha={alpha}° Re={reynolds:.1e}).",
    }
