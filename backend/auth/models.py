"""
AASI Phase 27: Authentication & User Governance Models.
Defines user accounts, session tokens, roles, and resource quota models.
Zero plaintext passwords stored.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class UserRole(str, Enum):
    RESEARCHER = "RESEARCHER"
    OPERATOR = "OPERATOR"
    AUDITOR = "AUDITOR"
    ADMIN = "ADMIN"


class User(BaseModel):
    user_id: str
    username: str
    email: str
    password_hash: str
    salt: str
    role: UserRole = UserRole.RESEARCHER
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None


class UserProfile(BaseModel):
    user_id: str
    username: str
    email: str
    role: UserRole
    created_at: str


class SessionToken(BaseModel):
    token: str
    user_id: str
    username: str
    role: UserRole
    expires_at: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserQuota(BaseModel):
    user_id: str
    max_concurrent_jobs: int = 2
    active_jobs_count: int = 0
    max_archive_size_mb: int = 100
    daily_cfd_hours_allowed: float = 5.0
    daily_cfd_hours_used: float = 0.0
    rate_limit_per_minute: int = 60


class ApiKey(BaseModel):
    key_id: str
    key_hash: str
    name: str
    user_id: str
    org_id: Optional[str] = None
    prefix: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_used_at: Optional[str] = None
    is_active: bool = True
    scopes: List[str] = Field(default_factory=lambda: ["read", "write", "investigate"])

