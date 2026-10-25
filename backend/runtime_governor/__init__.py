"""
AASI 2.0 Runtime Safety Governor Package (Phase 3).
"""

from backend.governor.safety_governor import SafetyGovernor, global_governor, DecisionVerdict
from backend.governor.kill_switch import KillSwitch, global_kill_switch, KillSwitchActiveError
from backend.governor.execution_policy import (
    ExecutionAction,
    ActionType,
    PolicyVerdict,
    ExecutionPolicyEngine,
    default_policy_engine,
)
from backend.governor.resource_budget import ResourceBudget, BudgetVerdict, BudgetEnforcement
from backend.governor.resource_monitor import ResourceMonitor, default_monitor, ResourceSnapshot

__all__ = [
    "SafetyGovernor",
    "global_governor",
    "DecisionVerdict",
    "KillSwitch",
    "global_kill_switch",
    "KillSwitchActiveError",
    "ExecutionAction",
    "ActionType",
    "PolicyVerdict",
    "ExecutionPolicyEngine",
    "default_policy_engine",
    "ResourceBudget",
    "BudgetVerdict",
    "BudgetEnforcement",
    "ResourceMonitor",
    "default_monitor",
    "ResourceSnapshot",
]
