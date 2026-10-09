"""
AASI Phase 27 Auth Package.
Provides authentication, authorization, governance, and commercial entity models.
"""

from backend.auth.models import User, UserRole, SessionToken, UserProfile, UserQuota
from backend.auth.security import security_manager, SecurityManager
from backend.auth.governance import governance_engine, GovernanceEngine
from backend.auth.dependencies import get_current_user, get_optional_user
from backend.auth.commercial import (
    Organization,
    Project,
    Plan,
    PlanTier,
    UsageEvent,
    UsageEventType,
    UsageTracker,
    usage_tracker,
    get_plan,
    DEFAULT_PLANS,
)

__all__ = [
    "User",
    "UserRole",
    "SessionToken",
    "UserProfile",
    "UserQuota",
    "security_manager",
    "SecurityManager",
    "governance_engine",
    "GovernanceEngine",
    "get_current_user",
    "get_optional_user",
    # Commercial models
    "Organization",
    "Project",
    "Plan",
    "PlanTier",
    "UsageEvent",
    "UsageEventType",
    "UsageTracker",
    "usage_tracker",
    "get_plan",
    "DEFAULT_PLANS",
]

