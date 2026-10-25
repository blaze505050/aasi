"""
AASI 2.0 Commercial Tier Architecture & Multi-Tenant Access Control.
Governing Doctrine: Strict Least-Privilege & Absolute Anti-Fabrication Rule.

Product Tiers:
- AASI Researcher (Free / Academic verification, 2D/3D analytical solvers, read-only memory)
- AASI Engineering (RocketPy, OpenMDAO, SU2 staging, full exporters, 4 concurrent jobs)
- AASI Enterprise (Colab/Remote HPC dispatch, custom solvers, private tenant isolation)
- AASI Platform/API (Headless REST/gRPC API, HMAC key authentication, automated pipelines)
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field


class CommercialTier(str, Enum):
    RESEARCHER = "RESEARCHER"
    ENGINEERING = "ENGINEERING"
    ENTERPRISE = "ENTERPRISE"
    PLATFORM_API = "PLATFORM_API"


class UserRole(str, Enum):
    VIEWER = "VIEWER"
    RESEARCHER = "RESEARCHER"
    ENGINEER = "ENGINEER"
    ADMIN = "ADMIN"


# Tool Permissibility Matrix per Commercial Tier
TIER_TOOL_PERMISSIONS: Dict[CommercialTier, Set[str]] = {
    CommercialTier.RESEARCHER: {
        "aero_2d_solve",
        "aero_3d_vlm",
        "polar_sweep",
        "uncertainty_quantify",
        "benchmark_verify",
        "geometry_parse",
        "browser_research",
    },
    CommercialTier.ENGINEERING: {
        "aero_2d_solve",
        "aero_3d_vlm",
        "polar_sweep",
        "uncertainty_quantify",
        "benchmark_verify",
        "geometry_parse",
        "export_datcom",
        "export_shabp",
        "mesh_generate",
        "rocket_trajectory",
        "mdao_evaluate",
        "su2_case_setup",
        "browser_research",
    },
    CommercialTier.ENTERPRISE: {
        # All tools permitted
        "*"
    },
    CommercialTier.PLATFORM_API: {
        "*"
    },
}

# Resource and Quota Envelope per Commercial Tier
TIER_QUOTAS: Dict[CommercialTier, Dict[str, Any]] = {
    CommercialTier.RESEARCHER: {
        "max_daily_jobs": 20,
        "max_concurrent_jobs": 1,
        "max_memory_mb": 100.0,
        "max_wall_time_sec": 30.0,
        "private_tenant_isolation": False,
    },
    CommercialTier.ENGINEERING: {
        "max_daily_jobs": 200,
        "max_concurrent_jobs": 4,
        "max_memory_mb": 350.0,
        "max_wall_time_sec": 120.0,
        "private_tenant_isolation": True,
    },
    CommercialTier.ENTERPRISE: {
        "max_daily_jobs": 10000,
        "max_concurrent_jobs": 32,
        "max_memory_mb": 2048.0,
        "max_wall_time_sec": 3600.0,
        "private_tenant_isolation": True,
    },
    CommercialTier.PLATFORM_API: {
        "max_daily_jobs": 50000,
        "max_concurrent_jobs": 64,
        "max_memory_mb": 2048.0,
        "max_wall_time_sec": 1800.0,
        "private_tenant_isolation": True,
    },
}


class TenantContext(BaseModel):
    """Execution context binding user, organization, tier, and quotas."""
    org_id: str = Field(..., description="Organization identifier")
    user_id: str = Field(..., description="User identifier")
    tier: CommercialTier = Field(default=CommercialTier.RESEARCHER)
    role: UserRole = Field(default=UserRole.RESEARCHER)
    daily_jobs_executed: int = Field(default=0)
    monthly_tokens_consumed: int = Field(default=0)
    is_active: bool = Field(default=True)


class CommercialTierEnforcer:
    """
    Evaluates tier entitlements, quotas, tool permissions, and multi-tenant security boundaries.
    """

    def is_tool_allowed(self, context: TenantContext, tool_name: str) -> bool:
        """Verifies if the tenant tier permits the requested tool."""
        allowed_tools = TIER_TOOL_PERMISSIONS.get(context.tier, set())
        if "*" in allowed_tools:
            return True
        return tool_name in allowed_tools

    def check_quota(self, context: TenantContext) -> Tuple[bool, Optional[str]]:
        """Verifies whether the tenant is within their daily job quota."""
        if not context.is_active:
            return False, "Tenant account is suspended or inactive."

        limits = TIER_QUOTAS.get(context.tier, TIER_QUOTAS[CommercialTier.RESEARCHER])
        max_daily = limits["max_daily_jobs"]

        if context.daily_jobs_executed >= max_daily:
            return False, f"Daily job quota exceeded ({context.daily_jobs_executed}/{max_daily}). Upgrade to Engineering or Enterprise for higher volume."

        return True, None

    def validate_tenant_path_isolation(self, context: TenantContext, requested_path: str, workspace_root: Path) -> bool:
        """
        Guarantees that a tenant can only access files within their assigned organization workspace.
        Rejects directory traversal (../, ..\\) and absolute paths outside the tenant space.
        """
        # Resolve path
        norm_path = os.path.normpath(requested_path)
        if ".." in norm_path.split(os.sep):
            return False

        try:
            req_p = Path(requested_path).resolve()
            ws_p = workspace_root.resolve()
            # If Enterprise/Engineering with tenant isolation, must remain in tenant subfolder or workspace root
            if not str(req_p).startswith(str(ws_p)):
                return False
            return True
        except Exception:
            return False

    def record_job_execution(self, context: TenantContext) -> None:
        """Increments usage counter upon successful dispatch."""
        context.daily_jobs_executed += 1


# Global tier enforcer singleton
commercial_enforcer = CommercialTierEnforcer()
