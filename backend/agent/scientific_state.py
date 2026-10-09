"""
AASI Scientific State Machine and Explicit Provenance Definitions.
Enforces the Absolute Anti-Fabrication Rule across all computational tiers.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ProvenanceState(str, Enum):
    """Explicit epistemic origin of every scientific number."""
    SURROGATE = "SURROGATE"             # Machine learning / neural operator inference
    ANALYTICAL = "ANALYTICAL"           # Closed-form potential flow / thin airfoil theory
    DATABASE_REAL = "DATABASE_REAL"     # Pre-existing verified physical CFD / experimental archive
    LIVE_CFD = "LIVE_CFD"               # Genuinely executed numerical solver (simpleFoam)
    EXPERIMENTAL = "EXPERIMENTAL"       # Verified physical wind tunnel data (NACA reports)
    UNVERIFIED = "UNVERIFIED"           # Result awaiting validation / integrity checks
    FAILED = "FAILED"                   # Simulation or validation failed


class EpistemicTier(str, Enum):
    """Epistemic classification tiers for calculations and results."""
    DATABASE_REAL = "DATABASE_REAL"
    LIVE_CFD = "LIVE_CFD"
    SURROGATE = "SURROGATE"
    ANALYTICAL = "ANALYTICAL"
    USER_PROVIDED = "USER_PROVIDED"
    DERIVED = "DERIVED"
    SYNTHETIC = "SYNTHETIC"
    ESTIMATED = "ESTIMATED"
    UNVERIFIED = "UNVERIFIED"
    NOT_EXECUTED = "NOT_EXECUTED"
    STAGED_ONLY = "STAGED_ONLY"


class CFDResultState(str, Enum):
    """Strict CFD result progression state machine."""
    PLANNED = "PLANNED"
    CASE_GENERATED = "CASE_GENERATED"
    PREFLIGHT_PASSED = "PREFLIGHT_PASSED"
    BUNDLE_READY = "BUNDLE_READY"
    EXECUTION_REQUESTED = "EXECUTION_REQUESTED"
    EXECUTING = "EXECUTING"
    RAW_RESULTS_RECEIVED = "RAW_RESULTS_RECEIVED"
    INTEGRITY_VERIFIED = "INTEGRITY_VERIFIED"
    PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION"
    SCIENTIFIC_VALIDATION = "SCIENTIFIC_VALIDATION"
    DATABASE_COMMITTED = "DATABASE_COMMITTED"
    FAILED = "FAILED"


class ColabExecutionState(str, Enum):
    """Strict Google Colab state disambiguation. Never collapsed."""
    COLAB_BUNDLE_READY = "COLAB_BUNDLE_READY"       # Notebook and case.tar.gz staged
    COLAB_EXECUTED = "COLAB_EXECUTED"               # External cloud run claimed
    RESULTS_IMPORTED = "RESULTS_IMPORTED"           # Tarball uploaded into AASI
    RESULTS_VERIFIED = "RESULTS_VERIFIED"           # Residuals & force digests verified
    EXECUTION_UNVERIFIED = "EXECUTION_UNVERIFIED"   # When execution cannot be proven


class StateTransitionRecord(BaseModel):
    """Cryptographic record of a single state transition."""
    from_state: CFDResultState
    to_state: CFDResultState
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trigger: str
    provenance_hash: Optional[str] = None
    detail: Optional[str] = None


class ScientificStateMachine:
    """
    Validates and controls state transitions for CFD results.
    Enforces that failed states can never transition into success states
    and transitions follow strict order.
    """

    ALLOWED_TRANSITIONS = {
        CFDResultState.PLANNED: [CFDResultState.CASE_GENERATED, CFDResultState.FAILED],
        CFDResultState.CASE_GENERATED: [CFDResultState.PREFLIGHT_PASSED, CFDResultState.FAILED],
        CFDResultState.PREFLIGHT_PASSED: [CFDResultState.BUNDLE_READY, CFDResultState.EXECUTION_REQUESTED, CFDResultState.FAILED],
        CFDResultState.BUNDLE_READY: [CFDResultState.EXECUTION_REQUESTED, CFDResultState.FAILED],
        CFDResultState.EXECUTION_REQUESTED: [CFDResultState.EXECUTING, CFDResultState.FAILED],
        CFDResultState.EXECUTING: [CFDResultState.RAW_RESULTS_RECEIVED, CFDResultState.FAILED],
        CFDResultState.RAW_RESULTS_RECEIVED: [CFDResultState.INTEGRITY_VERIFIED, CFDResultState.FAILED],
        CFDResultState.INTEGRITY_VERIFIED: [CFDResultState.PHYSICAL_VALIDATION, CFDResultState.FAILED],
        CFDResultState.PHYSICAL_VALIDATION: [CFDResultState.SCIENTIFIC_VALIDATION, CFDResultState.FAILED],
        CFDResultState.SCIENTIFIC_VALIDATION: [CFDResultState.DATABASE_COMMITTED, CFDResultState.FAILED],
        CFDResultState.DATABASE_COMMITTED: [],
        CFDResultState.FAILED: [CFDResultState.PLANNED],  # Only retry via new planned configuration
    }

    def __init__(self, initial_state: CFDResultState = CFDResultState.PLANNED):
        self.current_state = initial_state
        self.history: List[StateTransitionRecord] = []

    def can_transition_to(self, new_state: CFDResultState) -> bool:
        allowed = self.ALLOWED_TRANSITIONS.get(self.current_state, [])
        return new_state in allowed

    def transition(
        self,
        new_state: CFDResultState,
        trigger: str,
        provenance_hash: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> StateTransitionRecord:
        if not self.can_transition_to(new_state):
            raise ValueError(
                f"Illegal state transition from {self.current_state.value} to {new_state.value}. "
                f"Allowed transitions: {[s.value for s in self.ALLOWED_TRANSITIONS.get(self.current_state, [])]}"
            )

        record = StateTransitionRecord(
            from_state=self.current_state,
            to_state=new_state,
            trigger=trigger,
            provenance_hash=provenance_hash,
            detail=detail,
        )
        self.history.append(record)
        self.current_state = new_state
        return record

    def fail(self, reason: str, provenance_hash: Optional[str] = None) -> StateTransitionRecord:
        """Transitions immediately to FAILED with reason."""
        return self.transition(
            CFDResultState.FAILED,
            trigger="FAILURE_TRIGGERED",
            provenance_hash=provenance_hash,
            detail=reason,
        )
