"""
AASI 2.0 Task State Machine & Provenance Trace Models.

Enforces deterministic transitions through the standard AASI cognitive cycle:
QUESTION → PLAN → VALIDATE → EXECUTE_OR_STAGE → VERIFY → RECONCILE → LEARN → DECIDE → COMPLETE
"""

from __future__ import annotations

import time
import json
import hashlib
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from backend.tools.contracts import EpistemicTier


class TaskState(str, Enum):
    QUESTION = "QUESTION"
    PLANNING = "PLANNING"
    VALIDATING = "VALIDATING"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECONCILING = "RECONCILING"
    LEARNING = "LEARNING"
    DECIDING = "DECIDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    HALTED = "HALTED"


class TaskStep(BaseModel):
    """Discrete, cryptographically-hashed step in task execution history."""
    step_index: int
    state: TaskState
    action_name: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    epistemic_tier: Optional[EpistemicTier] = None
    success: bool = True
    error: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)
    provenance_hash: str = ""

    def compute_hash(self, prev_hash: str = "GENESIS") -> str:
        payload = {
            "step_index": self.step_index,
            "state": self.state.value,
            "action_name": self.action_name,
            "inputs": self.inputs,
            "output": self.output,
            "success": self.success,
            "prev_hash": prev_hash,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


class TaskResult(BaseModel):
    """Final, auditable result of a task execution with complete evidence trail."""
    task_id: str
    question: str
    final_state: TaskState
    success: bool
    answer: str
    evidence_record: Dict[str, Any] = Field(default_factory=dict)
    steps: List[TaskStep] = Field(default_factory=list)
    provenance_chain_hash: str = ""
    duration_seconds: float = 0.0
    start_time: float
    end_time: float
