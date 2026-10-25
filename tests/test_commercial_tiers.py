"""
Tests for Phase 15 & 16: Commercial Tiers and Tenant Security Boundaries.
"""

from pathlib import Path
import pytest
from backend.compliance.commercial_tiers import (
    CommercialTier,
    CommercialTierEnforcer,
    TenantContext,
    UserRole,
    commercial_enforcer,
)


def test_researcher_tier_tool_boundaries():
    ctx = TenantContext(
        org_id="ORG-ACADEMIC",
        user_id="USR-STUDENT",
        tier=CommercialTier.RESEARCHER,
        role=UserRole.RESEARCHER,
    )
    # Allowed on Researcher tier
    assert commercial_enforcer.is_tool_allowed(ctx, "aero_2d_solve") is True
    assert commercial_enforcer.is_tool_allowed(ctx, "polar_sweep") is True
    assert commercial_enforcer.is_tool_allowed(ctx, "browser_research") is True

    # Blocked on Researcher tier (requires Engineering)
    assert commercial_enforcer.is_tool_allowed(ctx, "export_datcom") is False
    assert commercial_enforcer.is_tool_allowed(ctx, "mesh_generate") is False
    assert commercial_enforcer.is_tool_allowed(ctx, "rocket_trajectory") is False


def test_engineering_tier_tool_boundaries():
    ctx = TenantContext(
        org_id="ORG-AEROCORP",
        user_id="USR-AERO-LEAD",
        tier=CommercialTier.ENGINEERING,
        role=UserRole.ENGINEER,
    )
    assert commercial_enforcer.is_tool_allowed(ctx, "aero_2d_solve") is True
    assert commercial_enforcer.is_tool_allowed(ctx, "rocket_trajectory") is True
    assert commercial_enforcer.is_tool_allowed(ctx, "mdao_evaluate") is True
    assert commercial_enforcer.is_tool_allowed(ctx, "su2_case_setup") is True
    assert commercial_enforcer.is_tool_allowed(ctx, "export_datcom") is True


def test_enterprise_tier_unrestricted():
    ctx = TenantContext(
        org_id="ORG-DEFENSE-PRIME",
        user_id="USR-CHIEF-SCIENTIST",
        tier=CommercialTier.ENTERPRISE,
        role=UserRole.ADMIN,
    )
    assert commercial_enforcer.is_tool_allowed(ctx, "rocket_trajectory") is True
    assert commercial_enforcer.is_tool_allowed(ctx, "custom_hypersonic_solver") is True


def test_quota_exhaustion():
    ctx = TenantContext(
        org_id="ORG-FREE",
        user_id="USR-GUEST",
        tier=CommercialTier.RESEARCHER,
        daily_jobs_executed=20,
    )
    allowed, reason = commercial_enforcer.check_quota(ctx)
    assert allowed is False
    assert "Daily job quota exceeded" in reason

    # Engineering tier has higher quota
    ctx.tier = CommercialTier.ENGINEERING
    allowed, reason = commercial_enforcer.check_quota(ctx)
    assert allowed is True
    assert reason is None


def test_tenant_path_traversal_rejection(tmp_path):
    ctx = TenantContext(
        org_id="ORG-TEST",
        user_id="USR-TEST",
        tier=CommercialTier.ENGINEERING,
    )
    ws = tmp_path / "workspace"
    ws.mkdir()

    valid_file = str(ws / "case_01" / "mesh.geo")
    assert commercial_enforcer.validate_tenant_path_isolation(ctx, valid_file, ws) is True

    # Traversal attempts
    assert commercial_enforcer.validate_tenant_path_isolation(ctx, "../../../etc/passwd", ws) is False
    assert commercial_enforcer.validate_tenant_path_isolation(ctx, "..\\..\\Windows\\System32", ws) is False
