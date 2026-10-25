"""
AASI 2.0 Runtime Governor — Human-in-the-Loop Approval Policy.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ApprovalRequest(BaseModel):
    request_id: str
    action_type: str
    description: str
    requested_resources: Dict[str, Any] = Field(default_factory=dict)
    reasons_for_approval: List[str] = Field(default_factory=list)
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED
    decided_by: Optional[str] = None


class ApprovalPolicy:
    """Evaluates whether an action requires explicit operator escalation."""

    @classmethod
    def requires_approval(
        cls,
        action_type: str,
        ram_gb: float = 0.0,
        modifies_production_code: bool = False,
    ) -> bool:
        if action_type in ("SYSTEM_COMMAND", "NETWORK_REQUEST"):
            return True
        if ram_gb > 1.0:
            return True
        if modifies_production_code:
            return True
        return False
