"""
AASI Phase 1A: Formal Investigation Lifecycle & Autonomy Governance Engine.
Defines formal autonomy levels (L0-L5), strict governance envelopes,
and deterministic lifecycle progression with cryptographic auditability.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone
import hashlib
from pydantic import BaseModel, Field


class AutonomyLevel(str, Enum):
    """
    Standard Aerospace Autonomy Levels (L0-L5) for scientific operations.
    Enforces that high-consequence calculations cannot execute without required authorization.
    """
    L0_ADVISORY = "L0_ADVISORY"                 # Manual recommendations only; human executes all steps
    L1_ASSISTED = "L1_ASSISTED"                 # Automated parameter filling/plan synthesis; human confirms each action
    L2_AUTOMATED = "L2_AUTOMATED"               # Deterministic pipeline execution without dynamic branching
    L3_BOUNDED = "L3_BOUNDED"                   # Autonomous within predefined parameter/cost envelope; auto-retries
    L4_GOAL_DRIVEN = "L4_GOAL_DRIVEN"           # Formulates hypotheses, executes multi-fidelity loops until uncertainty met
    L5_AUTONOMOUS = "L5_AUTONOMOUS"             # Full open-ended aerospace discovery with self-directed experimental planning


class LifecycleStage(str, Enum):
    """
    Formal epistemic progression stages of a scientific investigation.
    """
    DRAFT = "DRAFT"
    FORMULATED = "FORMULATED"
    STAGED = "STAGED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    SYNTHESIZING = "SYNTHESIZING"
    CONCLUDED = "CONCLUDED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    HUMAN_INTERVENTION_REQUIRED = "HUMAN_INTERVENTION_REQUIRED"


class AutonomyEnvelope(BaseModel):
    """
    Bounding envelope defining permitted actions, resource budgets, and mandatory approval gates.
    """
    level: AutonomyLevel = AutonomyLevel.L3_BOUNDED
    max_compute_seconds: float = Field(default=3600.0, ge=1.0)
    max_iterations: int = Field(default=10, ge=1)
    max_retries_per_step: int = Field(default=3, ge=0)
    max_uncertainty_threshold: float = Field(default=0.05, ge=0.0)
    allowed_fidelity_tiers: List[str] = Field(
        default_factory=lambda: ["ANALYTICAL", "PANEL", "SURROGATE", "DATABASE_REAL", "LIVE_CFD"]
    )
    require_human_approval_for: List[str] = Field(
        default_factory=lambda: ["CLOUD_DISPATCH", "MESH_CELLS_EXCEEDING_1M", "LIVE_CFD_HIGH_ORDER"]
    )
    cost_budget_usd: float = Field(default=10.0, ge=0.0)


class LifecycleEvent(BaseModel):
    """
    Cryptographically verifiable record of an investigation state transition.
    """
    event_id: str
    investigation_id: str
    from_stage: LifecycleStage
    to_stage: LifecycleStage
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trigger: str
    actor: str = "AASI_RUNTIME"
    autonomy_level: AutonomyLevel
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance_hash: str = ""


class InvestigationLifecycleManager:
    """
    State machine and policy engine governing investigation progress.
    Guarantees deterministic progression and enforces Autonomy Envelope boundaries.
    """

    ALLOWED_TRANSITIONS: Dict[LifecycleStage, Set[LifecycleStage]] = {
        LifecycleStage.DRAFT: {LifecycleStage.FORMULATED, LifecycleStage.ABORTED},
        LifecycleStage.FORMULATED: {
            LifecycleStage.STAGED,
            LifecycleStage.HUMAN_INTERVENTION_REQUIRED,
            LifecycleStage.ABORTED,
            LifecycleStage.FAILED,
        },
        LifecycleStage.STAGED: {
            LifecycleStage.EXECUTING,
            LifecycleStage.HUMAN_INTERVENTION_REQUIRED,
            LifecycleStage.ABORTED,
            LifecycleStage.FAILED,
        },
        LifecycleStage.EXECUTING: {
            LifecycleStage.VERIFYING,
            LifecycleStage.HUMAN_INTERVENTION_REQUIRED,
            LifecycleStage.FAILED,
            LifecycleStage.ABORTED,
        },
        LifecycleStage.VERIFYING: {
            LifecycleStage.SYNTHESIZING,
            LifecycleStage.EXECUTING,  # Iterative loop or refinement
            LifecycleStage.HUMAN_INTERVENTION_REQUIRED,
            LifecycleStage.FAILED,
        },
        LifecycleStage.SYNTHESIZING: {
            LifecycleStage.CONCLUDED,
            LifecycleStage.STAGED,    # Multi-fidelity next experiment
            LifecycleStage.HUMAN_INTERVENTION_REQUIRED,
            LifecycleStage.FAILED,
        },
        LifecycleStage.HUMAN_INTERVENTION_REQUIRED: {
            LifecycleStage.FORMULATED,
            LifecycleStage.STAGED,
            LifecycleStage.EXECUTING,
            LifecycleStage.VERIFYING,
            LifecycleStage.SYNTHESIZING,
            LifecycleStage.ABORTED,
        },
        LifecycleStage.CONCLUDED: set(),
        LifecycleStage.FAILED: {LifecycleStage.FORMULATED},  # Can be re-formulated
        LifecycleStage.ABORTED: set(),
    }

    def __init__(
        self,
        investigation_id: str,
        envelope: Optional[AutonomyEnvelope] = None,
        initial_stage: LifecycleStage = LifecycleStage.DRAFT,
    ):
        self.investigation_id = investigation_id
        self.envelope = envelope or AutonomyEnvelope()
        self.current_stage = initial_stage
        self.history: List[LifecycleEvent] = []
        self.consumed_compute_seconds: float = 0.0
        self.iteration_count: int = 0
        self.accumulated_cost_usd: float = 0.0

    def can_transition_to(self, target: LifecycleStage) -> bool:
        """Checks structural transition validity."""
        allowed = self.ALLOWED_TRANSITIONS.get(self.current_stage, set())
        return target in allowed

    def requires_human_approval(self, action_tag: str) -> bool:
        """
        Determines whether an action must be gated by human authorization
        based on current Autonomy Level and the Autonomy Envelope.
        """
        if self.envelope.level == AutonomyLevel.L0_ADVISORY:
            return True
        if self.envelope.level == AutonomyLevel.L1_ASSISTED:
            # L1 requires confirmation on any transition beyond FORMULATED
            return True
        if action_tag in self.envelope.require_human_approval_for:
            return True
        return False

    def check_envelope_compliance(self) -> Optional[str]:
        """
        Returns violation description if bounds are exceeded, otherwise None.
        """
        if self.consumed_compute_seconds > self.envelope.max_compute_seconds:
            return f"Exceeded maximum compute budget ({self.consumed_compute_seconds:.1f}s > {self.envelope.max_compute_seconds:.1f}s)"
        if self.iteration_count > self.envelope.max_iterations:
            return f"Exceeded maximum iteration count ({self.iteration_count} > {self.envelope.max_iterations})"
        if self.accumulated_cost_usd > self.envelope.cost_budget_usd:
            return f"Exceeded cost budget (${self.accumulated_cost_usd:.2f} > ${self.envelope.cost_budget_usd:.2f})"
        return None

    def transition(
        self,
        to_stage: LifecycleStage,
        trigger: str,
        actor: str = "AASI_RUNTIME",
        action_tag: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LifecycleEvent:
        """
        Executes a controlled state transition, enforcing policy and envelope rules.
        """
        meta = metadata or {}
        # 1. Structural transition check
        if not self.can_transition_to(to_stage):
            raise ValueError(
                f"Illegal transition: {self.current_stage.value} -> {to_stage.value}. "
                f"Allowed from {self.current_stage.value}: {[s.value for s in self.ALLOWED_TRANSITIONS.get(self.current_stage, set())]}"
            )

        # 2. Envelope boundary check (unless aborting or failing)
        if to_stage not in (LifecycleStage.ABORTED, LifecycleStage.FAILED):
            violation = self.check_envelope_compliance()
            if violation:
                to_stage = LifecycleStage.HUMAN_INTERVENTION_REQUIRED
                trigger = f"ENVELOPE_BREACH: {violation}"
                meta["envelope_breach"] = violation

        # 3. Human gating check
        if action_tag and self.requires_human_approval(action_tag):
            if actor != "HUMAN_OPERATOR" and to_stage != LifecycleStage.HUMAN_INTERVENTION_REQUIRED:
                to_stage = LifecycleStage.HUMAN_INTERVENTION_REQUIRED
                trigger = f"GATED_ACTION: {action_tag} requires operator approval under {self.envelope.level.value}"
                meta["approval_required_for"] = action_tag

        # 4. Generate verifiable event record
        event_id = f"EVT-{self.investigation_id}-{len(self.history) + 1:04d}"
        now = datetime.now(timezone.utc).isoformat()
        prev_hash = self.history[-1].provenance_hash if self.history else "ROOT_INVESTIGATION"

        payload = f"{event_id}|{self.investigation_id}|{self.current_stage.value}|{to_stage.value}|{trigger}|{now}|{prev_hash}"
        event_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        event = LifecycleEvent(
            event_id=event_id,
            investigation_id=self.investigation_id,
            from_stage=self.current_stage,
            to_stage=to_stage,
            timestamp=now,
            trigger=trigger,
            actor=actor,
            autonomy_level=self.envelope.level,
            metadata=meta,
            provenance_hash=event_hash,
        )

        self.history.append(event)
        self.current_stage = to_stage

        if to_stage in (LifecycleStage.STAGED, LifecycleStage.EXECUTING):
            self.iteration_count += 1

        return event

    def record_resource_usage(self, compute_seconds: float, cost_usd: float = 0.0) -> None:
        """Accrues compute time and cost."""
        self.consumed_compute_seconds += compute_seconds
        self.accumulated_cost_usd += cost_usd
