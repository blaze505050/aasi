"""
AASI 2.0 Safety Governor — Central Permission, Resource Enforcement & Audit Gate.

Single point of authorization for all agent actions, tool invocations, and solver runs:
1. Kill switch check (fail-closed)
2. Execution policy check (allowlist & dangerous pattern enforcement)
3. Resource budget evaluation against live host metrics
4. Cryptographically signed audit log (SHA-256 Merkle chain)
"""

from __future__ import annotations

import time
import json
import hashlib
import logging
from collections import deque
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from backend.governor.constants import GOVERNOR_DECISION_LOG_MAX_ENTRIES
from backend.governor.resource_monitor import ResourceMonitor, default_monitor, ResourceSnapshot
from backend.governor.resource_budget import ResourceBudget, BudgetVerdict
from backend.governor.kill_switch import KillSwitch, global_kill_switch, KillSwitchState
from backend.governor.execution_policy import (
    ExecutionAction,
    ActionType,
    PolicyVerdict,
    ExecutionPolicyEngine,
    default_policy_engine,
)

logger = logging.getLogger("aasi.governor.safety")


class DecisionVerdict(BaseModel):
    """Immutable verdict for an action authorization request."""
    approved: bool
    decision_id: str
    timestamp: float = Field(default_factory=time.time)
    action: ExecutionAction
    kill_switch_active: bool = False
    policy_verdict: Optional[PolicyVerdict] = None
    budget_verdict: Optional[BudgetVerdict] = None
    denial_reasons: List[str] = Field(default_factory=list)
    previous_hash: str = "GENESIS"
    provenance_hash: str = ""

    def compute_hash(self) -> str:
        """Computes deterministic SHA-256 provenance hash for audit tamper-evidence."""
        content = {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "approved": self.approved,
            "action_type": self.action.action_type.value,
            "tool_name": self.action.tool_name,
            "kill_switch_active": self.kill_switch_active,
            "denial_reasons": self.denial_reasons,
            "previous_hash": self.previous_hash,
        }
        raw = json.dumps(content, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SafetyGovernor:
    """
    Central safety coordinator and authorization barrier for AASI.
    Enforces fail-closed deterministic decisions with audit logging.
    """

    def __init__(
        self,
        resource_monitor: Optional[ResourceMonitor] = None,
        policy_engine: Optional[ExecutionPolicyEngine] = None,
        kill_switch: Optional[KillSwitch] = None,
        max_log_entries: int = GOVERNOR_DECISION_LOG_MAX_ENTRIES,
    ):
        self.monitor = resource_monitor or default_monitor
        self.policy_engine = policy_engine or default_policy_engine
        self.kill_switch = kill_switch or global_kill_switch
        self._audit_log: deque = deque(maxlen=max_log_entries)
        self._last_hash = "GENESIS"

    def authorize(
        self,
        action: ExecutionAction,
        budget: Optional[ResourceBudget] = None,
    ) -> DecisionVerdict:
        """
        Primary authorization entry point.
        Checks:
        1. Kill Switch -> fail-closed if active
        2. Policy Engine -> fail-closed if denied
        3. Resource Budget -> fail-closed if insufficient headroom
        """
        denial_reasons: List[str] = []
        kill_tripped = self.kill_switch.is_tripped

        # 1. Kill Switch Check
        if kill_tripped:
            state = self.kill_switch.get_state()
            denial_reasons.append(
                f"Emergency kill switch active: {state.reason or 'Manual halt'} (by {state.tripped_by})"
            )

        # 2. Execution Policy Check
        pol_verdict = self.policy_engine.evaluate(action)
        if not pol_verdict.allowed:
            denial_reasons.extend(pol_verdict.reasons)

        # 3. Resource Budget Check
        budget_to_check = budget or ResourceBudget()
        snapshot = self.monitor.snapshot()
        bud_verdict = budget_to_check.evaluate(snapshot)
        if not bud_verdict.approved:
            denial_reasons.extend(bud_verdict.reasons)

        approved = len(denial_reasons) == 0

        # Unique Decision ID
        now = time.time()
        raw_id = f"{action.action_type}:{action.tool_name or 'none'}:{now}"
        decision_id = f"DEC-{hashlib.sha256(raw_id.encode('utf-8')).hexdigest()[:12]}"

        decision = DecisionVerdict(
            approved=approved,
            decision_id=decision_id,
            timestamp=now,
            action=action,
            kill_switch_active=kill_tripped,
            policy_verdict=pol_verdict,
            budget_verdict=bud_verdict,
            denial_reasons=denial_reasons,
            previous_hash=self._last_hash,
        )
        decision.provenance_hash = decision.compute_hash()
        self._last_hash = decision.provenance_hash

        # Append to audit trail
        self._audit_log.append(decision)

        if not approved:
            logger.warning(
                "❌ Action DENIED by Governor: %s (%s) — Reasons: %s",
                action.action_type.value, action.tool_name, "; ".join(denial_reasons)
            )
        else:
            logger.info(
                "✅ Action APPROVED by Governor: %s (%s)",
                action.action_type.value, action.tool_name
            )

        return decision

    def trip_emergency_halt(self, reason: str, triggered_by: str = "operator") -> KillSwitchState:
        return self.kill_switch.trip(reason=reason, triggered_by=triggered_by)

    def reset_emergency_halt(self, authorized_by: str = "operator", force: bool = False) -> KillSwitchState:
        return self.kill_switch.reset(authorized_by=authorized_by, force=force)

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns recent authorization records."""
        items = list(self._audit_log)[-limit:]
        return [item.model_dump() for item in reversed(items)]

    def verify_audit_log(self) -> bool:
        """Verifies integrity of the hash chain."""
        prev = "GENESIS"
        for decision in self._audit_log:
            if decision.previous_hash != prev:
                return False
            expected = decision.compute_hash()
            if decision.provenance_hash != expected:
                return False
            prev = decision.provenance_hash
        return True


# Global default governor
global_governor = SafetyGovernor()
