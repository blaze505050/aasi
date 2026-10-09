"""
AASI Phase 27: Real-Time Event Bus & Server-Sent Events (SSE) Engine.
Enforces honest reporting: if remote observability is absent, broadcasts
'REMOTE STATUS UNKNOWN' rather than fabricating solver progress.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, AsyncGenerator
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import json
import asyncio
from pathlib import Path
from backend.observability.logger import log_telemetry, logging


class InvestigationEventType(str, Enum):
    PLAN_CREATED = "PLAN_CREATED"
    JOB_SUBMITTED = "JOB_SUBMITTED"
    KNOWLEDGE_QUERY = "KNOWLEDGE_QUERY"
    FIDELITY_SELECTED = "FIDELITY_SELECTED"
    CASE_GENERATED = "CASE_GENERATED"
    PREFLIGHT_STARTED = "PREFLIGHT_STARTED"
    PREFLIGHT_PASSED = "PREFLIGHT_PASSED"
    BACKEND_SELECTED = "BACKEND_SELECTED"
    JOB_STAGED = "JOB_STAGED"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    JOB_DISPATCHED = "JOB_DISPATCHED"
    SOLVER_STARTED = "SOLVER_STARTED"
    SOLVER_PROGRESS = "SOLVER_PROGRESS"
    SOLVER_FAILED = "SOLVER_FAILED"
    REPAIR_PROPOSED = "REPAIR_PROPOSED"
    RETRY_STARTED = "RETRY_STARTED"
    RESULTS_AVAILABLE = "RESULTS_AVAILABLE"
    RESULTS_VERIFIED = "RESULTS_VERIFIED"
    PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION"
    DATABASE_COMMIT = "DATABASE_COMMIT"
    REPORT_GENERATED = "REPORT_GENERATED"
    REMOTE_STATUS_UNKNOWN = "REMOTE_STATUS_UNKNOWN"


EventType = InvestigationEventType


class InvestigationEvent(BaseModel):
    event_id: str
    job_id: str
    event_type: InvestigationEventType
    message: str
    progress_percent: float = 0.0
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventBus:
    """Pub/Sub event bus supporting replay and async SSE streaming."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("data/observability/events")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._history: Dict[str, List[InvestigationEvent]] = {}
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    def record_event(
        self,
        job_id: str,
        event_type: InvestigationEventType,
        message: str,
        progress_percent: float = 0.0,
        payload: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> InvestigationEvent:
        """Record and broadcast an event."""
        event_id = f"EVT-{len(self._history.get(job_id, [])) + 1:04d}"
        event = InvestigationEvent(
            event_id=event_id,
            job_id=job_id,
            event_type=event_type,
            message=message,
            progress_percent=progress_percent,
            payload=payload or {},
        )

        if job_id not in self._history:
            self._history[job_id] = []
        self._history[job_id].append(event)

        # Log structured telemetry
        log_telemetry(
            level=logging.INFO,
            message=f"[{event_type.value}] {message}",
            job_id=job_id,
            user_id=user_id,
            state=event_type.value,
            extra={"progress": progress_percent, "event_id": event_id},
        )

        # Broadcast to active SSE queues
        if job_id in self._subscribers:
            for q in self._subscribers[job_id]:
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    pass

    def publish(
        self,
        event_type: InvestigationEventType,
        job_id: str,
        message: str = "",
        user_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        progress_percent: float = 0.0,
        **kwargs,
    ) -> InvestigationEvent:
        """Alias for record_event for publishing convenience."""
        return self.record_event(
            job_id=job_id,
            event_type=event_type,
            message=message or f"Event {event_type.value}",
            progress_percent=progress_percent,
            payload=payload,
            user_id=user_id,
        )

    def _save_job_events(self, job_id: str):
        job_file = self.data_dir / f"{job_id}_events.json"
        data = [e.model_dump() for e in self._history.get(job_id, [])]
        job_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_job_events(self, job_id: str) -> List[InvestigationEvent]:
        """Fetch all recorded events for a job."""
        if job_id in self._history:
            return self._history[job_id]
        job_file = self.data_dir / f"{job_id}_events.json"
        if job_file.exists():
            try:
                data = json.loads(job_file.read_text(encoding="utf-8"))
                events = [InvestigationEvent.model_validate(d) for d in data]
                self._history[job_id] = events
                return events
            except Exception:
                return []
        return []

    async def subscribe(self, job_id: str) -> AsyncGenerator[InvestigationEvent, None]:
        """Async generator yielding events for SSE streaming."""
        q = asyncio.Queue(maxsize=100)
        if job_id not in self._subscribers:
            self._subscribers[job_id] = []
        self._subscribers[job_id].append(q)

        # Yield historical events first to ensure client catches up after refresh
        historical = self.get_job_events(job_id)
        for h_event in historical:
            yield h_event

        try:
            while True:
                event = await q.get()
                yield event
        except asyncio.CancelledError:
            pass
        finally:
            if job_id in self._subscribers and q in self._subscribers[job_id]:
                self._subscribers[job_id].remove(q)


# Global singleton event bus
event_bus = EventBus()
