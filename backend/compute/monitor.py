"""
AASI Phase 26 Remote Execution State Monitor.
Tracks granular execution milestones and provides coarse fallbacks when unobservable.
Exposes endpoints: GET /api/execution/{job_id}, /events, /artifacts.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from pathlib import Path
import json


class ExecutionMilestone(str, Enum):
    QUEUED = "QUEUED"
    STARTING = "STARTING"
    ENVIRONMENT_CHECK = "ENVIRONMENT_CHECK"
    OPENFOAM_SETUP = "OPENFOAM_SETUP"
    CASE_TRANSFER = "CASE_TRANSFER"
    MESHING = "MESHING"
    MESH_VALIDATION = "MESH_VALIDATION"
    SOLVER_RUNNING = "SOLVER_RUNNING"
    CONVERGENCE_CHECK = "CONVERGENCE_CHECK"
    PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION"
    PACKAGING = "PACKAGING"
    RESULTS_READY = "RESULTS_READY"
    RESULTS_IMPORTED = "RESULTS_IMPORTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class CoarseState(str, Enum):
    UNKNOWN = "UNKNOWN"
    USER_ACTION_REQUIRED = "USER_ACTION_REQUIRED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExecutionEvent(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    milestone: ExecutionMilestone
    description: str
    progress_pct: int = 0
    details: Optional[Dict[str, Any]] = None


class JobExecutionRecord(BaseModel):
    job_id: str
    backend: str
    coarse_state: CoarseState = CoarseState.USER_ACTION_REQUIRED
    current_milestone: ExecutionMilestone = ExecutionMilestone.QUEUED
    progress_pct: int = 0
    events: List[ExecutionEvent] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RemoteExecutionMonitor:
    """
    In-memory and file-backed execution state monitor.
    """

    _registry: Dict[str, JobExecutionRecord] = {}

    @classmethod
    def register_job(cls, job_id: str, backend: str = "GOOGLE_COLAB", artifacts: Optional[List[str]] = None) -> JobExecutionRecord:
        record = JobExecutionRecord(
            job_id=job_id,
            backend=backend,
            coarse_state=CoarseState.USER_ACTION_REQUIRED,
            current_milestone=ExecutionMilestone.QUEUED,
            progress_pct=5,
            artifacts=artifacts or [],
        )
        record.events.append(
            ExecutionEvent(
                milestone=ExecutionMilestone.QUEUED,
                description=f"Job {job_id} queued on backend {backend}. Ready for user authorization.",
                progress_pct=5,
            )
        )
        cls._registry[job_id] = record
        return record

    @classmethod
    def record_event(
        cls,
        job_id: str,
        milestone: ExecutionMilestone,
        description: str,
        progress_pct: int,
        details: Optional[Dict[str, Any]] = None,
        coarse_state: Optional[CoarseState] = None,
    ) -> ExecutionEvent:
        if job_id not in cls._registry:
            cls.register_job(job_id)

        rec = cls._registry[job_id]
        rec.current_milestone = milestone
        rec.progress_pct = progress_pct
        rec.updated_at = datetime.now(timezone.utc).isoformat()

        if coarse_state:
            rec.coarse_state = coarse_state
        elif milestone == ExecutionMilestone.FAILED:
            rec.coarse_state = CoarseState.FAILED
        elif milestone == ExecutionMilestone.VERIFIED:
            rec.coarse_state = CoarseState.COMPLETED
        elif milestone in [ExecutionMilestone.MESHING, ExecutionMilestone.SOLVER_RUNNING]:
            rec.coarse_state = CoarseState.RUNNING

        event = ExecutionEvent(
            milestone=milestone,
            description=description,
            progress_pct=progress_pct,
            details=details,
        )
        rec.events.append(event)
        return event

    @classmethod
    def get_job_status(cls, job_id: str) -> Optional[JobExecutionRecord]:
        return cls._registry.get(job_id)

    @classmethod
    def get_events(cls, job_id: str) -> List[ExecutionEvent]:
        rec = cls._registry.get(job_id)
        return rec.events if rec else []

    @classmethod
    def get_artifacts(cls, job_id: str) -> List[str]:
        rec = cls._registry.get(job_id)
        if not rec:
            # Check disk for artifacts in data/compute_jobs/<job_id>
            job_path = Path("data/compute_jobs") / job_id
            if job_path.exists():
                return [f.name for f in job_path.glob("*")]
            return []
        return rec.artifacts
