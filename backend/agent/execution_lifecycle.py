"""
AASI Phase 28: Autonomous Execution Lifecycle & Error Recovery Controller.
Connects:
EXECUTION_FAILED -> LOG INGESTION -> ERROR CLASSIFICATION -> ROOT-CAUSE HYPOTHESIS ->
REPAIR CANDIDATE -> REPAIR VALIDATION -> NEW EXECUTION PLAN.
Enforces:
- Hard maximum 3 automatic retries.
- Immutable case hashes (never overwrite the failed attempt).
- Full auditability.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.agent.diagnostics import CFDDiagnosticsEngine, DiagnosticReport, CFDErrorClass
from backend.agent.repair_engine import CFDRepairEngine, RepairOutcome, RepairCandidate
from backend.compute.queue import job_queue, JobState


class ExecutionRecoveryReport(BaseModel):
    job_id: str
    original_attempt: int
    new_attempt: int
    diagnosis: DiagnosticReport
    repair_candidate: Optional[RepairCandidate] = None
    outcome_status: str  # "RETRY_STAGED", "HUMAN_REVIEW_REQUIRED"
    new_job_state: JobState
    detail: str
    traceable_history: List[Dict[str, Any]] = Field(default_factory=list)


class AutonomousLifecycleController:
    """
    Coordinates automatic diagnosis, candidate repair generation, and non-mutating retries.
    """

    MAX_RETRIES = 3

    @classmethod
    def handle_solver_failure(
        cls,
        job_id: str,
        solver_log: str,
        current_attempt: int = 1,
        original_case_hash: Optional[str] = None,
        original_spec: Optional[Dict[str, Any]] = None,
    ) -> ExecutionRecoveryReport:
        job = job_queue.get_job(job_id)
        spec = original_spec or (job.model_dump() if job else {})
        case_hash = original_case_hash or (
            (job.case_hash or job.artifacts.get("case_hash", ""))
            if job else hashlib.sha256(job_id.encode()).hexdigest()
        ) or hashlib.sha256(job_id.encode()).hexdigest()

        # 1. ERROR CLASSIFICATION & ROOT-CAUSE HYPOTHESIS
        diagnosis = CFDDiagnosticsEngine.diagnose(solver_log=solver_log)

        # 2. REPAIR CANDIDATE PROPOSAL
        repair_outcome = CFDRepairEngine.propose_repair(
            original_spec=spec,
            original_case_hash=case_hash,
            diagnosis=diagnosis,
            current_retry_count=current_attempt - 1,
        )

        # Mark job as FAILED if not already
        if job and job.state != JobState.FAILED:
            try:
                job_queue.transition_state(job_id, JobState.FAILED, reason=f"Failure detected: {diagnosis.diagnosis}")
            except Exception as e:
                pass

        if current_attempt >= cls.MAX_RETRIES or repair_outcome.status == "REPAIR_REJECTED_BOUNDS_EXCEEDED":
            if job:
                job_queue.transition_state(
                    job_id,
                    JobState.HUMAN_REVIEW_REQUIRED,
                    reason=f"Exhausted {cls.MAX_RETRIES} retries. Diagnosed: {diagnosis.error_class.value}",
                )
            return ExecutionRecoveryReport(
                job_id=job_id,
                original_attempt=current_attempt,
                new_attempt=current_attempt,
                diagnosis=diagnosis,
                repair_candidate=None,
                outcome_status="HUMAN_REVIEW_REQUIRED",
                new_job_state=JobState.HUMAN_REVIEW_REQUIRED,
                detail=f"Automatic retry limit ({cls.MAX_RETRIES}) reached. Escalating to human review.",
                traceable_history=[
                    {"attempt": current_attempt, "error": diagnosis.error_class.value, "status": "ESCALATED"}
                ],
            )

        # 3. NON-MUTATING REPAIR VALIDATION & NEW STAGING
        candidate = repair_outcome.candidate
        new_attempt = current_attempt + 1
        if job:
            job_queue.transition_state(
                job_id,
                JobState.STAGED,
                reason=f"Repair candidate staged (attempt {new_attempt}/{cls.MAX_RETRIES}): {candidate.reason}",
            )

        return ExecutionRecoveryReport(
            job_id=job_id,
            original_attempt=current_attempt,
            new_attempt=new_attempt,
            diagnosis=diagnosis,
            repair_candidate=candidate,
            outcome_status="RETRY_STAGED",
            new_job_state=JobState.STAGED,
            detail=f"Synthesized non-mutating repair for {diagnosis.error_class.value}. New hash: {candidate.candidate_case_hash[:12]}",
            traceable_history=[
                {"attempt": current_attempt, "error": diagnosis.error_class.value, "status": "FAILED"},
                {"attempt": new_attempt, "candidate_hash": candidate.candidate_case_hash, "status": "STAGED"},
            ],
        )
