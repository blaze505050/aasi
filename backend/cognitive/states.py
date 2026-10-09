"""
AASI Cognitive Engine: Cognitive States and Finite State Machine.
Defines explicit operational states governing the scientific investigation lifecycle.
No fake animations; all states reflect verifiable backend processing.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

logger = logging.getLogger("aasi.cognitive.states")


class CognitiveState(str, Enum):
    """
    Explicit operational states of the AASI Cognitive Engine.
    Strictly governed by the 17-state investigation lifecycle.
    """
    IDLE = "IDLE"
    UNDERSTANDING = "UNDERSTANDING"
    MODELING = "MODELING"
    RETRIEVING = "RETRIEVING"
    HYPOTHESIZING = "HYPOTHESIZING"
    CRITIQUING = "CRITIQUING"
    PLANNING = "PLANNING"
    SELECTING_TOOL = "SELECTING_TOOL"
    AWAITING_EXECUTION = "AWAITING_EXECUTION"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECONCILING = "RECONCILING"
    LEARNING = "LEARNING"
    DECIDING = "DECIDING"
    STALLED = "STALLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Formal State Transition Matrix: Defines valid transitions to prevent illegal skips
VALID_TRANSITIONS: Dict[CognitiveState, Set[CognitiveState]] = {
    CognitiveState.IDLE: {
        CognitiveState.UNDERSTANDING,
    },
    CognitiveState.UNDERSTANDING: {
        CognitiveState.MODELING,
        CognitiveState.RETRIEVING,
        CognitiveState.STALLED,
        CognitiveState.FAILED,
    },
    CognitiveState.MODELING: {
        CognitiveState.RETRIEVING,
        CognitiveState.HYPOTHESIZING,
        CognitiveState.STALLED,
        CognitiveState.FAILED,
    },
    CognitiveState.RETRIEVING: {
        CognitiveState.HYPOTHESIZING,
        CognitiveState.PLANNING,
        CognitiveState.STALLED,
        CognitiveState.FAILED,
    },
    CognitiveState.HYPOTHESIZING: {
        CognitiveState.CRITIQUING,
        CognitiveState.STALLED,
        CognitiveState.FAILED,
    },
    CognitiveState.CRITIQUING: {
        CognitiveState.PLANNING,
        CognitiveState.HYPOTHESIZING,  # Loop back if all hypotheses refuted/invalid
        CognitiveState.DECIDING,       # If prior evidence immediately answers the critique
        CognitiveState.STALLED,
        CognitiveState.FAILED,
    },
    CognitiveState.PLANNING: {
        CognitiveState.SELECTING_TOOL,
        CognitiveState.STALLED,
        CognitiveState.FAILED,
    },
    CognitiveState.SELECTING_TOOL: {
        CognitiveState.AWAITING_EXECUTION,
        CognitiveState.EXECUTING,
        CognitiveState.STALLED,
        CognitiveState.FAILED,
    },
    CognitiveState.AWAITING_EXECUTION: {
        CognitiveState.EXECUTING,
        CognitiveState.STALLED,
        CognitiveState.FAILED,
    },
    CognitiveState.EXECUTING: {
        CognitiveState.VERIFYING,
        CognitiveState.FAILED,
    },
    CognitiveState.VERIFYING: {
        CognitiveState.RECONCILING,
        CognitiveState.FAILED,        # Physical violation or audit divergence
        CognitiveState.STALLED,
    },
    CognitiveState.RECONCILING: {
        CognitiveState.LEARNING,
        CognitiveState.PLANNING,      # Re-plan if discrepancy triggers secondary investigation
        CognitiveState.STALLED,
        CognitiveState.FAILED,
    },
    CognitiveState.LEARNING: {
        CognitiveState.DECIDING,
        CognitiveState.STALLED,
        CognitiveState.FAILED,
    },
    CognitiveState.DECIDING: {
        CognitiveState.COMPLETED,
        CognitiveState.UNDERSTANDING, # Next iteration of research loop
        CognitiveState.PLANNING,      # Next experiment
        CognitiveState.STALLED,
        CognitiveState.FAILED,
    },
    CognitiveState.STALLED: {
        CognitiveState.IDLE,
        CognitiveState.UNDERSTANDING,
        CognitiveState.PLANNING,
    },
    CognitiveState.COMPLETED: {
        CognitiveState.IDLE,
    },
    CognitiveState.FAILED: {
        CognitiveState.IDLE,
    },
}


class CognitiveTransitionRecord(BaseModel):
    """Immutable audit entry for a cognitive state change."""
    transition_id: str
    from_state: CognitiveState
    to_state: CognitiveState
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trigger: str = Field(..., description="Action or event causing transition")
    rationale: str = Field(..., description="Machine-readable rationale explaining the transition")


class CognitiveStateMachine:
    """Manages explicit cognitive transitions with integrity enforcement."""

    def __init__(self, initial_state: CognitiveState = CognitiveState.IDLE):
        self._current_state = initial_state
        self._history: List[CognitiveTransitionRecord] = []

    @property
    def current_state(self) -> CognitiveState:
        return self._current_state

    @property
    def history(self) -> List[CognitiveTransitionRecord]:
        return list(self._history)

    def transition_to(
        self,
        new_state: CognitiveState,
        trigger: str,
        rationale: str,
        force: bool = False,
    ) -> CognitiveTransitionRecord:
        """
        Transitions to a new state if permitted by the transition matrix.
        Raises ValueError on illegal state jumps unless explicitly forced.
        """
        valid_next = VALID_TRANSITIONS.get(self._current_state, set())
        if not force and new_state not in valid_next and new_state != self._current_state:
            raise ValueError(
                f"ILLEGAL COGNITIVE TRANSITION: Cannot jump from {self._current_state.value} to {new_state.value}. "
                f"Permitted next states: {[s.value for s in valid_next]}."
            )

        import uuid
        record = CognitiveTransitionRecord(
            transition_id=f"TR-{uuid.uuid4().hex[:8].upper()}",
            from_state=self._current_state,
            to_state=new_state,
            trigger=trigger,
            rationale=rationale,
        )
        self._history.append(record)
        prev = self._current_state
        self._current_state = new_state
        logger.info("Cognitive transition: %s -> %s [Trigger: %s]", prev.value, new_state.value, trigger)
        return record
