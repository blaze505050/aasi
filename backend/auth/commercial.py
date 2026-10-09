"""
AASI Commercial Models: Organization, Project, Plan, and Usage Tracking.
Provides the commercial entity hierarchy required for a paid platform.

Entity Hierarchy:
    ORGANIZATION
    └── PROJECTS
        └── INVESTIGATIONS
            └── EXPERIMENTS → EVIDENCE → ARTIFACTS

Billing:
    Plan → Entitlement → UsageEvent → Quota enforcement
"""

import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ────────────────────────────────────────────────────────────────
# Organization
# ────────────────────────────────────────────────────────────────

class Organization(BaseModel):
    """Top-level commercial entity. All investigations, memory, and billing belong to an organization."""
    org_id: str = Field(default_factory=lambda: f"ORG-{secrets.token_hex(6).upper()}")
    name: str
    slug: str = Field(default="", description="URL-safe unique identifier (e.g. 'acme-aero')")
    owner_id: str = Field(default="usr_default", description="User ID of the organization owner")
    member_ids: List[str] = Field(default_factory=list, description="User IDs of all members")
    plan_id: str = Field(default="free", description="Active plan identifier")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    settings: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

    def model_post_init(self, __context: Any) -> None:
        if not self.slug and self.name:
            import re
            cleaned = re.sub(r'[^a-zA-Z0-9]+', '-', self.name.lower()).strip('-')
            self.slug = cleaned or f"org-{self.org_id.lower()}"
        if not self.member_ids and self.owner_id:
            self.member_ids = [self.owner_id]


# ────────────────────────────────────────────────────────────────
# Project
# ────────────────────────────────────────────────────────────────

class Project(BaseModel):
    """Groups investigations within an organization."""
    project_id: str = Field(default_factory=lambda: f"PRJ-{secrets.token_hex(6).upper()}")
    org_id: str = Field(..., description="Parent organization ID")
    name: str
    description: str = ""
    member_ids: List[str] = Field(default_factory=list, description="User IDs with project access")
    investigation_ids: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True


# ────────────────────────────────────────────────────────────────
# Plan & Entitlement
# ────────────────────────────────────────────────────────────────

class PlanTier(str, Enum):
    """Pricing tier identifiers."""
    FREE = "free"
    PROFESSIONAL = "professional"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class Plan(BaseModel):
    """Defines entitlements for a pricing tier."""
    plan_id: str
    name: str
    tier: PlanTier
    max_investigations_per_month: int = 5
    max_experiments_per_investigation: int = 3
    max_ai_tokens_per_month: int = 50_000
    max_memory_entries: int = 100
    max_storage_bytes: int = 500 * 1024 * 1024  # 500 MB
    max_members: int = 1
    features: List[str] = Field(default_factory=list)
    is_active: bool = True


# Default plan definitions
DEFAULT_PLANS: Dict[str, Plan] = {
    "free": Plan(
        plan_id="free",
        name="Free / Research",
        tier=PlanTier.FREE,
        max_investigations_per_month=5,
        max_experiments_per_investigation=3,
        max_ai_tokens_per_month=50_000,
        max_memory_entries=100,
        max_storage_bytes=500 * 1024 * 1024,
        max_members=1,
        features=["panel_solver", "analytical", "basic_export"],
    ),
    "professional": Plan(
        plan_id="professional",
        name="Professional",
        tier=PlanTier.PROFESSIONAL,
        max_investigations_per_month=25,
        max_experiments_per_investigation=10,
        max_ai_tokens_per_month=500_000,
        max_memory_entries=1_000,
        max_storage_bytes=5 * 1024 * 1024 * 1024,
        max_members=1,
        features=[
            "panel_solver", "analytical", "cfd_staging", "xfoil",
            "private_memory", "all_exports", "api_access",
        ],
    ),
    "team": Plan(
        plan_id="team",
        name="Team",
        tier=PlanTier.TEAM,
        max_investigations_per_month=100,
        max_experiments_per_investigation=25,
        max_ai_tokens_per_month=2_000_000,
        max_memory_entries=10_000,
        max_storage_bytes=25 * 1024 * 1024 * 1024,
        max_members=5,
        features=[
            "panel_solver", "analytical", "cfd_staging", "xfoil",
            "private_memory", "shared_memory", "all_exports", "api_access",
            "projects", "rbac", "collaboration",
        ],
    ),
    "enterprise": Plan(
        plan_id="enterprise",
        name="Enterprise",
        tier=PlanTier.ENTERPRISE,
        max_investigations_per_month=999_999,
        max_experiments_per_investigation=999,
        max_ai_tokens_per_month=999_999_999,
        max_memory_entries=999_999,
        max_storage_bytes=1024 * 1024 * 1024 * 1024,  # 1 TB
        max_members=999,
        features=[
            "panel_solver", "analytical", "cfd_staging", "xfoil",
            "private_memory", "shared_memory", "all_exports", "api_access",
            "projects", "rbac", "collaboration", "sso", "audit_logs",
            "private_deployment", "custom_integrations", "sla",
        ],
    ),
}


def get_plan(plan_id: str) -> Plan:
    """Retrieve plan by ID. Returns free plan as fallback."""
    return DEFAULT_PLANS.get(plan_id, DEFAULT_PLANS["free"])


# ────────────────────────────────────────────────────────────────
# Usage Tracking
# ────────────────────────────────────────────────────────────────

class UsageEventType(str, Enum):
    """Types of billable or trackable usage events."""
    INVESTIGATION_STARTED = "investigation_started"
    EXPERIMENT_RUN = "experiment_run"
    AI_INFERENCE = "ai_inference"
    STORAGE_USED = "storage_used"
    MEMORY_STORED = "memory_stored"
    EXPORT_GENERATED = "export_generated"
    TOOL_EXECUTION = "tool_execution"
    COMPUTE_JOB_SUBMITTED = "compute_job_submitted"


class UsageEvent(BaseModel):
    """Atomic usage event for metering and billing."""
    event_id: str = Field(default_factory=lambda: f"EVT-{secrets.token_hex(6).upper()}")
    org_id: str
    user_id: str
    project_id: Optional[str] = None
    investigation_id: Optional[str] = None
    event_type: UsageEventType
    quantity: float = 1.0
    unit: str = "count"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ────────────────────────────────────────────────────────────────
# Usage Tracker (in-memory for now; persistent backend later)
# ────────────────────────────────────────────────────────────────

class UsageTracker:
    """Tracks usage events per organization for quota enforcement and billing (backed by SQLite)."""

    def __init__(self):
        self._events: List[UsageEvent] = []

    def record(self, event: UsageEvent) -> None:
        """Record a usage event into persistent storage and local cache."""
        self._events.append(event)
        try:
            from backend.storage.commercial_db import commercial_db
            commercial_db.record_usage_event(event)
        except Exception:
            pass

    def get_monthly_count(self, org_id: str, event_type: UsageEventType) -> int:
        """Get count of events of a specific type in the current calendar month."""
        try:
            from backend.storage.commercial_db import commercial_db
            return commercial_db.get_monthly_count(org_id, event_type)
        except Exception:
            pass
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count = 0
        for evt in self._events:
            if evt.org_id != org_id or evt.event_type != event_type:
                continue
            try:
                evt_time = datetime.fromisoformat(evt.timestamp)
                if evt_time >= month_start:
                    count += int(evt.quantity)
            except (ValueError, TypeError):
                continue
        return count

    def check_quota(self, org_id: str, plan: Plan, event_type: UsageEventType) -> bool:
        """Check if organization is within quota for the given event type."""
        current = self.get_monthly_count(org_id, event_type)
        limits = {
            UsageEventType.INVESTIGATION_STARTED: plan.max_investigations_per_month,
            UsageEventType.AI_INFERENCE: plan.max_ai_tokens_per_month,
            UsageEventType.MEMORY_STORED: plan.max_memory_entries,
        }
        limit = limits.get(event_type)
        if limit is None:
            return True  # No limit defined for this event type
        return current < limit

    def get_usage_summary(self, org_id: str) -> Dict[str, int]:
        """Get usage summary for an organization in the current month."""
        try:
            from backend.storage.commercial_db import commercial_db
            return commercial_db.get_usage_summary(org_id)
        except Exception:
            pass
        summary: Dict[str, int] = {}
        for evt_type in UsageEventType:
            count = self.get_monthly_count(org_id, evt_type)
            if count > 0:
                summary[evt_type.value] = count
        return summary

    def get_all_events(self, org_id: str) -> List[UsageEvent]:
        """Get all events for an organization."""
        return [e for e in self._events if e.org_id == org_id]

    def reset(self) -> None:
        """Reset all in-memory and persistent usage events."""
        self._events.clear()
        try:
            from backend.storage.commercial_db import commercial_db
            commercial_db.clear_usage_events()
        except Exception:
            pass


# Global singleton
usage_tracker = UsageTracker()
