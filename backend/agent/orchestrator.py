"""
AASI Phase 26 Production Execution Orchestrator.
Enforces the formal 17-state machine for autonomous scientific experimentation:
RECEIVED -> PLANNED -> KNOWLEDGE_SEARCH -> FIDELITY_DECISION -> CASE_GENERATED ->
PREFLIGHT -> BACKEND_SELECTED -> JOB_STAGED -> USER_AUTHORIZATION_REQUIRED ->
REMOTE_EXECUTING -> RESULTS_AVAILABLE -> INGESTING -> VERIFYING ->
SCIENTIFIC_VALIDATION -> KNOWLEDGE_COMMIT -> REPORT_GENERATED -> COMPLETE
Failure states: FAILED_PREFLIGHT, FAILED_EXECUTION, FAILED_VERIFICATION, HUMAN_REVIEW_REQUIRED.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import hashlib
import json


class OrchestratorState(str, Enum):
    RECEIVED = "RECEIVED"
    PLANNED = "PLANNED"
    KNOWLEDGE_SEARCH = "KNOWLEDGE_SEARCH"
    FIDELITY_DECISION = "FIDELITY_DECISION"
    CASE_GENERATED = "CASE_GENERATED"
    PREFLIGHT = "PREFLIGHT"
    BACKEND_SELECTED = "BACKEND_SELECTED"
    JOB_STAGED = "JOB_STAGED"
    USER_AUTHORIZATION_REQUIRED = "USER_AUTHORIZATION_REQUIRED"
    REMOTE_EXECUTING = "REMOTE_EXECUTING"
    RESULTS_AVAILABLE = "RESULTS_AVAILABLE"
    INGESTING = "INGESTING"
    VERIFYING = "VERIFYING"
    SCIENTIFIC_VALIDATION = "SCIENTIFIC_VALIDATION"
    KNOWLEDGE_COMMIT = "KNOWLEDGE_COMMIT"
    REPORT_GENERATED = "REPORT_GENERATED"
    COMPLETE = "COMPLETE"

    # Explicit failure states
    FAILED_PREFLIGHT = "FAILED_PREFLIGHT"
    FAILED_EXECUTION = "FAILED_EXECUTION"
    FAILED_VERIFICATION = "FAILED_VERIFICATION"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


class OrchestratorTransition(BaseModel):
    """Cryptographic audit record of a state transition."""
    from_state: OrchestratorState
    to_state: OrchestratorState
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trigger: str
    detail: Optional[str] = None
    transition_hash: str


class OrchestratorSession(BaseModel):
    """Full session state persisted across execution milestones."""
    session_id: str
    objective: str
    current_state: OrchestratorState = OrchestratorState.RECEIVED
    geometry: Optional[str] = None
    alpha_deg: Optional[float] = None
    reynolds: Optional[float] = None
    mach: Optional[float] = None
    backend: Optional[str] = None
    job_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    history: List[OrchestratorTransition] = Field(default_factory=list)
    artifacts: Dict[str, str] = Field(default_factory=dict)
    data_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class ProductionOrchestrator:
    """
    Manages deterministic state progression with auditability and fail-closed rules.
    """

    ALLOWED_TRANSITIONS = {
        OrchestratorState.RECEIVED: [
            OrchestratorState.PLANNED,
            OrchestratorState.HUMAN_REVIEW_REQUIRED,
        ],
        OrchestratorState.PLANNED: [
            OrchestratorState.KNOWLEDGE_SEARCH,
            OrchestratorState.HUMAN_REVIEW_REQUIRED,
        ],
        OrchestratorState.KNOWLEDGE_SEARCH: [
            OrchestratorState.FIDELITY_DECISION,
            OrchestratorState.HUMAN_REVIEW_REQUIRED,
        ],
        OrchestratorState.FIDELITY_DECISION: [
            OrchestratorState.CASE_GENERATED,
            OrchestratorState.REPORT_GENERATED,  # If surrogate/database alone is sufficient
            OrchestratorState.HUMAN_REVIEW_REQUIRED,
        ],
        OrchestratorState.CASE_GENERATED: [
            OrchestratorState.PREFLIGHT,
            OrchestratorState.FAILED_PREFLIGHT,
        ],
        OrchestratorState.PREFLIGHT: [
            OrchestratorState.BACKEND_SELECTED,
            OrchestratorState.FAILED_PREFLIGHT,
        ],
        OrchestratorState.BACKEND_SELECTED: [
            OrchestratorState.JOB_STAGED,
            OrchestratorState.USER_AUTHORIZATION_REQUIRED,
            OrchestratorState.FAILED_PREFLIGHT,
        ],
        OrchestratorState.JOB_STAGED: [
            OrchestratorState.USER_AUTHORIZATION_REQUIRED,
            OrchestratorState.REMOTE_EXECUTING,
            OrchestratorState.FAILED_EXECUTION,
        ],
        OrchestratorState.USER_AUTHORIZATION_REQUIRED: [
            OrchestratorState.REMOTE_EXECUTING,
            OrchestratorState.RESULTS_AVAILABLE,
            OrchestratorState.FAILED_EXECUTION,
            OrchestratorState.HUMAN_REVIEW_REQUIRED,
        ],
        OrchestratorState.REMOTE_EXECUTING: [
            OrchestratorState.RESULTS_AVAILABLE,
            OrchestratorState.FAILED_EXECUTION,
        ],
        OrchestratorState.RESULTS_AVAILABLE: [
            OrchestratorState.INGESTING,
            OrchestratorState.FAILED_VERIFICATION,
        ],
        OrchestratorState.INGESTING: [
            OrchestratorState.VERIFYING,
            OrchestratorState.FAILED_VERIFICATION,
        ],
        OrchestratorState.VERIFYING: [
            OrchestratorState.SCIENTIFIC_VALIDATION,
            OrchestratorState.FAILED_VERIFICATION,
        ],
        OrchestratorState.SCIENTIFIC_VALIDATION: [
            OrchestratorState.KNOWLEDGE_COMMIT,
            OrchestratorState.REPORT_GENERATED,
            OrchestratorState.FAILED_VERIFICATION,
        ],
        OrchestratorState.KNOWLEDGE_COMMIT: [
            OrchestratorState.REPORT_GENERATED,
            OrchestratorState.HUMAN_REVIEW_REQUIRED,
        ],
        OrchestratorState.REPORT_GENERATED: [
            OrchestratorState.COMPLETE,
        ],
        OrchestratorState.COMPLETE: [],
        # Failure recoveries (can transition to next attempt or human review)
        OrchestratorState.FAILED_PREFLIGHT: [
            OrchestratorState.PLANNED,
            OrchestratorState.HUMAN_REVIEW_REQUIRED,
        ],
        OrchestratorState.FAILED_EXECUTION: [
            OrchestratorState.PLANNED,
            OrchestratorState.HUMAN_REVIEW_REQUIRED,
        ],
        OrchestratorState.FAILED_VERIFICATION: [
            OrchestratorState.PLANNED,
            OrchestratorState.HUMAN_REVIEW_REQUIRED,
        ],
        OrchestratorState.HUMAN_REVIEW_REQUIRED: [
            OrchestratorState.PLANNED,  # If human unblocks
        ],
    }

    def __init__(self, session_id: str, objective: str):
        self.session = OrchestratorSession(session_id=session_id, objective=objective)

    def transition_to(
        self,
        new_state: OrchestratorState,
        trigger: str,
        detail: Optional[str] = None,
        artifacts_to_add: Optional[Dict[str, str]] = None,
    ) -> OrchestratorTransition:
        """
        Transitions session to new_state if legally allowed by state graph.
        Computes SHA-256 digest of transition.
        """
        current = self.session.current_state
        allowed = self.ALLOWED_TRANSITIONS.get(current, [])
        if new_state not in allowed:
            raise ValueError(
                f"Illegal state transition from '{current.value}' to '{new_state.value}'. "
                f"Allowed transitions: {[s.value for s in allowed]}"
            )

        # Compute transition digest
        canonical = f"{self.session.session_id}:{current.value}->{new_state.value}:{trigger}:{datetime.now(timezone.utc).isoformat()}"
        t_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        transition = OrchestratorTransition(
            from_state=current,
            to_state=new_state,
            trigger=trigger,
            detail=detail,
            transition_hash=t_hash,
        )

        self.session.history.append(transition)
        self.session.current_state = new_state

        if artifacts_to_add:
            self.session.artifacts.update(artifacts_to_add)

        if new_state == OrchestratorState.COMPLETE:
            self.session.completed_at = datetime.now(timezone.utc).isoformat()

        return transition

    def fail_with(self, failure_state: OrchestratorState, reason: str) -> OrchestratorTransition:
        """Transitions immediately to one of the formal failure states."""
        if failure_state not in [
            OrchestratorState.FAILED_PREFLIGHT,
            OrchestratorState.FAILED_EXECUTION,
            OrchestratorState.FAILED_VERIFICATION,
            OrchestratorState.HUMAN_REVIEW_REQUIRED,
        ]:
            raise ValueError(f"Invalid failure state: {failure_state}")

        return self.transition_to(failure_state, trigger="FAILURE_ENCOUNTERED", detail=reason)

    def record_retry(self, reason: str) -> bool:
        """
        Increments retry count. If max_retries exceeded, transitions to HUMAN_REVIEW_REQUIRED.
        Returns True if retry allowed, False if retries exhausted.
        """
        self.session.retry_count += 1
        if self.session.retry_count > self.session.max_retries:
            self.fail_with(
                OrchestratorState.HUMAN_REVIEW_REQUIRED,
                f"Automatic retry limit ({self.session.max_retries}) exhausted. Reason: {reason}",
            )
            return False
        return True
