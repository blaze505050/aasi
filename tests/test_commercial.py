"""
Test Suite for AASI Commercial Architecture.
Tests Organization, Project, Plan, UsageTracker, and Commercial API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.auth.commercial import (
    Organization,
    Project,
    Plan,
    PlanTier,
    UsageEvent,
    UsageEventType,
    UsageTracker,
    get_plan,
    DEFAULT_PLANS,
)


@pytest.fixture
def client():
    return TestClient(app)


class TestCommercialModels:
    def test_organization_creation(self):
        org = Organization(name="Skunk Works Lab", owner_id="usr_chief")
        assert org.name == "Skunk Works Lab"
        assert org.slug == "skunk-works-lab"
        assert org.owner_id == "usr_chief"
        assert "usr_chief" in org.member_ids
        assert org.plan_id == "free"
        assert org.is_active is True
        assert org.org_id.startswith("ORG-")

    def test_project_creation(self):
        org = Organization(name="X-Planes", owner_id="usr_lead")
        proj = Project(org_id=org.org_id, name="X-59 Low Boom", description="Sonic boom mitigation investigation")
        assert proj.project_id.startswith("PRJ-")
        assert proj.org_id == org.org_id
        assert proj.name == "X-59 Low Boom"
        assert proj.is_active is True

    def test_plans_defined(self):
        assert "free" in DEFAULT_PLANS
        assert "professional" in DEFAULT_PLANS
        assert "team" in DEFAULT_PLANS
        assert "enterprise" in DEFAULT_PLANS

        free = get_plan("free")
        assert free.tier == PlanTier.FREE
        assert free.max_investigations_per_month == 5
        assert "panel_solver" in free.features

        pro = get_plan("professional")
        assert pro.max_investigations_per_month == 25
        assert "cfd_staging" in pro.features

        ent = get_plan("enterprise")
        assert ent.max_investigations_per_month > 1000
        assert "sso" in ent.features

    def test_usage_tracking_and_quota(self):
        import uuid
        tracker = UsageTracker()
        org_id = f"ORG-TEST-{uuid.uuid4().hex[:6]}"

        # Initially zero
        assert tracker.get_monthly_count(org_id, UsageEventType.INVESTIGATION_STARTED) == 0

        # Record events
        for _ in range(3):
            tracker.record(UsageEvent(
                org_id=org_id,
                user_id="usr_1",
                event_type=UsageEventType.INVESTIGATION_STARTED,
                quantity=1.0,
            ))

        assert tracker.get_monthly_count(org_id, UsageEventType.INVESTIGATION_STARTED) == 3

        # Quota check with free plan (max 5)
        free_plan = get_plan("free")
        assert tracker.check_quota(org_id, free_plan, UsageEventType.INVESTIGATION_STARTED) is True

        # Add 3 more events -> total 6
        for _ in range(3):
            tracker.record(UsageEvent(
                org_id=org_id,
                user_id="usr_1",
                event_type=UsageEventType.INVESTIGATION_STARTED,
                quantity=1.0,
            ))

        assert tracker.get_monthly_count(org_id, UsageEventType.INVESTIGATION_STARTED) == 6
        assert tracker.check_quota(org_id, free_plan, UsageEventType.INVESTIGATION_STARTED) is False

        # Summary
        summary = tracker.get_usage_summary(org_id)
        assert summary["investigation_started"] == 6


class TestCommercialApi:
    def test_list_plans(self, client):
        resp = client.get("/api/v1/commercial/plans")
        assert resp.status_code == 200
        data = resp.json()
        plans = data if isinstance(data, list) else data.get("plans", [])
        assert len(plans) >= 4

    def test_get_plan_details(self, client):
        resp = client.get("/api/v1/commercial/plans/professional")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"]["name"] == "Professional"
        assert data["plan"]["max_investigations_per_month"] == 25

    def test_organization_lifecycle(self, client):
        import uuid
        test_slug = f"orbital-{uuid.uuid4().hex[:6]}"
        # Create org
        payload = {
            "name": "Orbital Aero Dynamics",
            "slug": test_slug,
            "owner_id": "usr_orbit_1",
        }
        create_resp = client.post("/api/v1/commercial/organizations", json=payload)
        assert create_resp.status_code == 200
        org_data = create_resp.json()["organization"]
        org_id = org_data["org_id"]
        assert org_data["name"] == "Orbital Aero Dynamics"
        assert org_data["slug"] == test_slug

        # Duplicate slug rejected
        dup_resp = client.post("/api/v1/commercial/organizations", json=payload)
        assert dup_resp.status_code == 409

        # Get org
        get_resp = client.get(f"/api/v1/commercial/organizations/{org_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["organization"]["org_id"] == org_id

        # Create project in org
        proj_payload = {
            "org_id": org_id,
            "name": "NACA Transonic Buffeting",
            "description": "Shock-induced separation study",
        }
        proj_resp = client.post("/api/v1/commercial/projects", json=proj_payload)
        assert proj_resp.status_code == 200
        proj_id = proj_resp.json()["project"]["project_id"]

        # Get project
        get_proj_resp = client.get(f"/api/v1/commercial/projects/{proj_id}")
        assert get_proj_resp.status_code == 200
        assert get_proj_resp.json()["project"]["name"] == "NACA Transonic Buffeting"

        # List projects in org
        list_proj_resp = client.get(f"/api/v1/commercial/organizations/{org_id}/projects")
        assert list_proj_resp.status_code == 200
        assert list_proj_resp.json()["count"] >= 1

        # Check usage
        usage_resp = client.get(f"/api/v1/commercial/organizations/{org_id}/usage")
        assert usage_resp.status_code == 200
        assert "limits" in usage_resp.json()

        # Check quota
        quota_resp = client.get(f"/api/v1/commercial/organizations/{org_id}/quota-check?event_type=investigation_started")
        assert quota_resp.status_code == 200
        assert quota_resp.json()["allowed"] is True


class TestApiKeysAndSecurity:
    def test_password_complexity_enforcement(self, client):
        import uuid
        uid = uuid.uuid4().hex[:6]
        # Weak password (no uppercase or digits)
        resp = client.post("/api/v1/auth/register", json={
            "username": f"user_weak_{uid}",
            "email": f"weak_{uid}@aerotech.com",
            "password": "weak",
        })
        assert resp.status_code == 400
        assert "at least 8 characters" in resp.json()["detail"]

        # Strong password meets complexity
        resp = client.post("/api/v1/auth/register", json={
            "username": f"user_strong_{uid}",
            "email": f"strong_{uid}@aerotech.com",
            "password": "AeroSpace2026!Secure",
        })
        assert resp.status_code == 200
        assert resp.json()["username"] == f"user_strong_{uid}"

    def test_api_key_lifecycle_and_authentication(self, client):
        import uuid
        uid = uuid.uuid4().hex[:6]
        uname = f"worker_{uid}"
        pwd = "AeroSpace2026!Secure"

        # Register user
        reg_resp = client.post("/api/v1/auth/register", json={
            "username": uname,
            "email": f"{uname}@aerotech.com",
            "password": pwd,
        })
        assert reg_resp.status_code == 200

        # 1. Login to obtain session token
        login_resp = client.post("/api/v1/auth/login", json={
            "username_or_email": uname,
            "password": pwd,
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]
        session_headers = {"Authorization": f"Bearer {token}"}

        # 2. Create API key
        key_resp = client.post(
            "/api/v1/auth/api-keys",
            json={"name": "Flight Test CI/CD", "scopes": ["read", "write"]},
            headers=session_headers,
        )
        assert key_resp.status_code == 200
        raw_key = key_resp.json()["raw_secret_key"]
        key_id = key_resp.json()["api_key"]["key_id"]
        assert raw_key.startswith("aasi_sk_")

        # 3. Authenticate with X-API-Key header
        me_resp = client.get("/api/v1/auth/me", headers={"X-API-Key": raw_key})
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == uname

        # 4. Authenticate with Bearer API key
        me_bearer_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {raw_key}"})
        assert me_bearer_resp.status_code == 200
        assert me_bearer_resp.json()["username"] == uname

        # 5. List API keys
        list_resp = client.get("/api/v1/auth/api-keys", headers=session_headers)
        assert list_resp.status_code == 200
        assert any(k["key_id"] == key_id for k in list_resp.json())

        # 6. Revoke API key
        del_resp = client.delete(f"/api/v1/auth/api-keys/{key_id}", headers=session_headers)
        assert del_resp.status_code == 200

        # 7. Revoked key is rejected
        rejected_resp = client.get("/api/v1/auth/me", headers={"X-API-Key": raw_key})
        assert rejected_resp.status_code == 401

    def test_session_token_revocation_on_logout(self, client):
        import uuid
        uid = uuid.uuid4().hex[:6]
        uname = f"logout_user_{uid}"
        pwd = "AeroSpace2026!Secure"

        reg_resp = client.post("/api/v1/auth/register", json={
            "username": uname,
            "email": f"{uname}@aerotech.com",
            "password": pwd,
        })
        assert reg_resp.status_code == 200

        login_resp = client.post("/api/v1/auth/login", json={
            "username_or_email": uname,
            "password": pwd,
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verify active
        me_resp = client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200

        # Logout & revoke
        logout_resp = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_resp.status_code == 200

        # Now token is revoked
        revoked_resp = client.get("/api/v1/auth/me", headers=headers)
        assert revoked_resp.status_code == 401


class TestCommercialEnterpriseFeatures:
    def test_organization_upgrade_plan(self, client):
        # 1. Upgrade default org to enterprise
        upgrade_resp = client.post("/api/commercial/organizations/default/upgrade", json={
            "plan_id": "enterprise"
        })
        assert upgrade_resp.status_code == 200
        data = upgrade_resp.json()
        assert data["status"] == "UPGRADED"
        assert data["new_plan"]["tier"] == "enterprise"
        assert data["new_plan"]["max_investigations_per_month"] == 999_999

        # 2. Verify invalid plan rejection
        bad_resp = client.post("/api/commercial/organizations/default/upgrade", json={
            "plan_id": "ultra_invalid"
        })
        assert bad_resp.status_code == 400

    def test_issue_asme_vv20_certification_signoff(self, client):
        cert_resp = client.post("/api/commercial/certify", json={
            "job_id": "JOB-NACA0012-CRUISE",
            "geometry": "NACA 0012",
            "alpha_deg": 4.0,
            "reynolds": 3000000,
            "mach": 0.15,
            "auditor_name": "Lead Aerodynamicist"
        })
        assert cert_resp.status_code == 200
        data = cert_resp.json()
        assert "certificate_id" in data
        assert data["verification_status"] == "VERIFIED_COMPLIANT"
        assert data["standard"].startswith("ASME V&V 20")
        assert len(data["audit_checks"]) >= 4
        assert "sha256_digital_seal" in data
        assert len(data["sha256_digital_seal"]) == 64



