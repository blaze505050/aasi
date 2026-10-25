"""
AASI 2.0 System Capabilities — Runtime Budget Policy.
"""

from __future__ import annotations

from typing import Dict, Any, Tuple, Optional
from backend.governor.resource_budget import ResourceBudget, BudgetVerdict
from backend.governor.resource_monitor import default_monitor


class BudgetPolicyManager:
    """Manages allocation policies and headroom calculations for task execution."""

    @classmethod
    def evaluate_task_budget(cls, budget: ResourceBudget) -> BudgetVerdict:
        snap = default_monitor.snapshot()
        return budget.evaluate(snap)

    @classmethod
    def get_default_budget(cls, task_id: Optional[str] = None) -> ResourceBudget:
        return ResourceBudget(task_id=task_id)
