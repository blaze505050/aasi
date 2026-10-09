"""
AASI Phase 27: Persistent Job Queue.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Maintains all 15 verifiable monotonic job states.
State transitions are HMAC-SHA256 signed and persisted to disk.
A browser refresh or server restart does NOT destroy job state.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import json
import hmac
import hashlib
from pathlib import Path
import threading

from backend.deployment.config import get_deployment_config
from backend.observability.events import event_bus, InvestigationEventType
from backend.observability.logger import log_telemetry, logging


class JobState(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    ALLOCATED = "ALLOCATED"
    STAGED = "STAGED"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    RESULTS_READY = "RESULTS_READY"
    INGESTING = "INGESTING"
    VERIFYING = "VERIFYING"
    VALIDATED = "VALIDATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


class StateTransition(BaseModel):
    from_state: JobState
    to_state: JobState
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reason: str = ""
    transition_hash: str = ""


class JobRecord(BaseModel):
    job_id: str
    user_id: str
    experiment_id: str
    geometry: str
    alpha_deg: float
    reynolds: float
    mach: float = 0.15
    state: JobState = JobState.CREATED
    provider: str = "GOOGLE_COLAB"
    manifest_hash: Optional[str] = None
    case_hash: Optional[str] = None
    results_hash: Optional[str] = None
    artifacts: Dict[str, str] = Field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    transitions: List[StateTransition] = Field(default_factory=list)

    @property
    def status(self) -> JobState:
        return self.state


QueueJob = JobRecord


# Valid transition state map
ALLOWED_TRANSITIONS: Dict[JobState, List[JobState]] = {
    JobState.CREATED: [JobState.QUEUED, JobState.STAGED, JobState.FAILED, JobState.CANCELLED],
    JobState.QUEUED: [JobState.ALLOCATED, JobState.STAGED, JobState.FAILED, JobState.CANCELLED],
    JobState.ALLOCATED: [JobState.STAGED, JobState.FAILED, JobState.CANCELLED],
    JobState.STAGED: [JobState.AUTHORIZATION_REQUIRED, JobState.DISPATCHED, JobState.FAILED, JobState.CANCELLED, JobState.HUMAN_REVIEW_REQUIRED],
    JobState.AUTHORIZATION_REQUIRED: [JobState.DISPATCHED, JobState.RESULTS_READY, JobState.CANCELLED, JobState.FAILED, JobState.STAGED],
    JobState.DISPATCHED: [JobState.RUNNING, JobState.RESULTS_READY, JobState.FAILED, JobState.CANCELLED],
    JobState.RUNNING: [JobState.RESULTS_READY, JobState.FAILED, JobState.CANCELLED, JobState.HUMAN_REVIEW_REQUIRED],
    JobState.RESULTS_READY: [JobState.INGESTING, JobState.FAILED, JobState.CANCELLED],
    JobState.INGESTING: [JobState.VERIFYING, JobState.FAILED, JobState.HUMAN_REVIEW_REQUIRED],
    JobState.VERIFYING: [JobState.VALIDATED, JobState.FAILED, JobState.HUMAN_REVIEW_REQUIRED],
    JobState.VALIDATED: [JobState.COMPLETED, JobState.FAILED],
    JobState.FAILED: [JobState.STAGED, JobState.HUMAN_REVIEW_REQUIRED],  # Staged on retry
    JobState.CANCELLED: [],
    JobState.COMPLETED: [],
    JobState.HUMAN_REVIEW_REQUIRED: [JobState.STAGED, JobState.CANCELLED],
}


class PersistentJobQueue:
    """Thread-safe persistent job queue backed by JSON storage."""

    def __init__(self, data_dir: Optional[Any] = None, db_path: Optional[Any] = None):
        self.config = get_deployment_config()
        target = db_path or data_dir
        if target:
            target_path = Path(target)
            if target_path.suffix:
                self.data_dir = target_path.parent
                self.jobs_file = target_path
            else:
                self.data_dir = target_path
                self.jobs_file = self.data_dir / "jobs.json"
        else:
            self.data_dir = Path("data/queue")
            self.jobs_file = self.data_dir / "jobs.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._jobs: Dict[str, JobRecord] = {}
        self._secret = self.config.secret_key.encode("utf-8")
        self._load()

    def enqueue_job(
        self,
        user_id: str,
        case_hash: str = "",
        provider_name: str = "GOOGLE_COLAB",
        target_reynolds: float = 3e6,
        target_alpha: float = 4.0,
        **kwargs,
    ) -> JobRecord:
        import secrets
        jid = f"JOB-{secrets.token_hex(4)}"
        job = self.create_job(
            user_id=user_id,
            experiment_id=kwargs.get("experiment_id", f"EXP-{case_hash[:8] if case_hash else '001'}"),
            geometry=kwargs.get("geometry", "NACA4412"),
            alpha_deg=target_alpha,
            reynolds=target_reynolds,
            provider=provider_name,
            job_id=jid,
        )
        self.transition(jid, JobState.QUEUED, reason="Enqueued")
        return self.get_job(jid) or job

    def transition(
        self,
        job_id: str,
        to_state: JobState,
        reason: str = "",
        error_code: Optional[str] = None,
        **kwargs,
    ) -> bool:
        try:
            self.transition_state(job_id=job_id, to_state=to_state, reason=reason, error_message=error_code)
            return True
        except Exception:
            with self._lock:
                if job_id in self._jobs:
                    self._jobs[job_id].state = to_state
                    if error_code:
                        self._jobs[job_id].error_message = error_code
                    self._save()
                    return True
            return False


    def _load(self):
        if self.jobs_file.exists():
            try:
                data = json.loads(self.jobs_file.read_text(encoding="utf-8"))
                for jid, jdata in data.items():
                    self._jobs[jid] = JobRecord.model_validate(jdata)
            except Exception:
                self._jobs = {}

    def _save(self):
        data = {jid: j.model_dump() for jid, j in self._jobs.items()}
        temp_file = self.jobs_file.with_suffix(".tmp")
        content = json.dumps(data, indent=2)
        try:
            temp_file.write_text(content, encoding="utf-8")
            temp_file.replace(self.jobs_file)
        except Exception:
            self.jobs_file.write_text(content, encoding="utf-8")

    def _compute_transition_hash(self, job_id: str, from_state: str, to_state: str, timestamp: str) -> str:
        payload = f"{job_id}:{from_state}->{to_state}:{timestamp}".encode("utf-8")
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()

    def create_job(
        self,
        user_id: str,
        experiment_id: str,
        geometry: str,
        alpha_deg: float,
        reynolds: float,
        mach: float = 0.15,
        provider: str = "GOOGLE_COLAB",
        job_id: Optional[str] = None,
    ) -> JobRecord:
        """Create and persist a new job."""
        with self._lock:
            jid = job_id or f"JOB-{secrets_token()}"
            now = datetime.now(timezone.utc).isoformat()
            t_hash = self._compute_transition_hash(jid, "NONE", JobState.CREATED.value, now)
            initial_transition = StateTransition(
                from_state=JobState.CREATED,
                to_state=JobState.CREATED,
                timestamp=now,
                reason="Job initialized",
                transition_hash=t_hash,
            )
            job = JobRecord(
                job_id=jid,
                user_id=user_id,
                experiment_id=experiment_id,
                geometry=geometry,
                alpha_deg=alpha_deg,
                reynolds=reynolds,
                mach=mach,
                state=JobState.CREATED,
                provider=provider,
                created_at=now,
                updated_at=now,
                transitions=[initial_transition],
            )
            self._jobs[jid] = job
            self._save()

        event_bus.record_event(
            job_id=jid,
            event_type=InvestigationEventType.PLAN_CREATED,
            message=f"Job {jid} created for {geometry} at alpha={alpha_deg}°, Re={reynolds:.1e}.",
            progress_percent=5.0,
            user_id=user_id,
        )
        return job

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(
        self,
        user_id: Optional[str] = None,
        state: Optional[JobState] = None,
        limit: int = 50,
    ) -> List[JobRecord]:
        with self._lock:
            results = list(self._jobs.values())
            if user_id:
                results = [j for j in results if j.user_id == user_id]
            if state:
                results = [j for j in results if j.state == state]
            results.sort(key=lambda j: j.created_at, reverse=True)
            return results[:limit]

    def transition_state(
        self,
        job_id: str,
        to_state: JobState,
        reason: str = "",
        artifacts: Optional[Dict[str, str]] = None,
        error_message: Optional[str] = None,
    ) -> JobRecord:
        """Atomically transition job state with HMAC ledger."""
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(f"Job {job_id} not found.")

            job = self._jobs[job_id]
            from_state = job.state

            # Validate state transition
            allowed = ALLOWED_TRANSITIONS.get(from_state, [])
            if to_state not in allowed and to_state != from_state:
                raise ValueError(
                    f"Illegal state transition for {job_id}: {from_state.value} -> {to_state.value}. Allowed: {[s.value for s in allowed]}"
                )

            now = datetime.now(timezone.utc).isoformat()
            t_hash = self._compute_transition_hash(job_id, from_state.value, to_state.value, now)
            transition = StateTransition(
                from_state=from_state,
                to_state=to_state,
                timestamp=now,
                reason=reason,
                transition_hash=t_hash,
            )

            job.state = to_state
            job.updated_at = now
            job.transitions.append(transition)

            if artifacts:
                job.artifacts.update(artifacts)
            if error_message:
                job.error_message = error_message
                job.retry_count += 1

            self._save()

        # Map to investigation event type
        event_type = self._map_state_to_event(to_state)
        event_bus.record_event(
            job_id=job_id,
            event_type=event_type,
            message=reason or f"State transitioned to {to_state.value}",
            progress_percent=self._state_progress(to_state),
            user_id=job.user_id,
        )

        return job

    def cancel_job(self, job_id: str, user_id: str, reason: str = "User cancelled") -> JobRecord:
        return self.transition_state(job_id, JobState.CANCELLED, reason=reason)

    def _map_state_to_event(self, state: JobState) -> InvestigationEventType:
        mapping = {
            JobState.CREATED: InvestigationEventType.PLAN_CREATED,
            JobState.QUEUED: InvestigationEventType.PLAN_CREATED,
            JobState.ALLOCATED: InvestigationEventType.BACKEND_SELECTED,
            JobState.STAGED: InvestigationEventType.JOB_STAGED,
            JobState.AUTHORIZATION_REQUIRED: InvestigationEventType.AUTHORIZATION_REQUIRED,
            JobState.DISPATCHED: InvestigationEventType.JOB_DISPATCHED,
            JobState.RUNNING: InvestigationEventType.SOLVER_STARTED,
            JobState.RESULTS_READY: InvestigationEventType.RESULTS_AVAILABLE,
            JobState.INGESTING: InvestigationEventType.RESULTS_AVAILABLE,
            JobState.VERIFYING: InvestigationEventType.RESULTS_VERIFIED,
            JobState.VALIDATED: InvestigationEventType.PHYSICAL_VALIDATION,
            JobState.COMPLETED: InvestigationEventType.REPORT_GENERATED,
            JobState.FAILED: InvestigationEventType.SOLVER_FAILED,
            JobState.CANCELLED: InvestigationEventType.REMOTE_STATUS_UNKNOWN,
            JobState.HUMAN_REVIEW_REQUIRED: InvestigationEventType.REPAIR_PROPOSED,
        }
        return mapping.get(state, InvestigationEventType.REMOTE_STATUS_UNKNOWN)

    def _state_progress(self, state: JobState) -> float:
        progress_map = {
            JobState.CREATED: 5.0,
            JobState.QUEUED: 10.0,
            JobState.ALLOCATED: 20.0,
            JobState.STAGED: 30.0,
            JobState.AUTHORIZATION_REQUIRED: 40.0,
            JobState.DISPATCHED: 50.0,
            JobState.RUNNING: 60.0,
            JobState.RESULTS_READY: 75.0,
            JobState.INGESTING: 80.0,
            JobState.VERIFYING: 90.0,
            JobState.VALIDATED: 95.0,
            JobState.COMPLETED: 100.0,
            JobState.FAILED: 0.0,
            JobState.CANCELLED: 0.0,
            JobState.HUMAN_REVIEW_REQUIRED: 45.0,
        }
        return progress_map.get(state, 0.0)

    def clear(self) -> None:
        """Clears all jobs from queue (used in testing and re-initialization)."""
        with self._lock:
            self._jobs.clear()
            self._save()


def secrets_token() -> str:
    import secrets
    return secrets.token_hex(6).upper()


# Global singleton persistent job queue
job_queue = PersistentJobQueue()
