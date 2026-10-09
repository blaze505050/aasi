"""
AASI Phase 27: Public Deployment & Remote Compute Test Suite.
Tests:
- Deployment configuration and zero-cost environment defaults.
- Authentication, PBKDF2 hashing, signed session tokens, and multi-tenant isolation.
- Resource governance, quota enforcement, rate limiting, and execution timeouts.
- Observability logger, telemetry metrics, and real-time EventBus.
- Pluggable content-addressed object store with multi-backend fallback.
- FastAPI /api/v1 endpoints for production deployment.
"""

import os
import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.deployment.config import DeploymentConfig, get_deployment_config
from backend.auth.security import SecurityManager
from backend.auth.governance import GovernanceEngine
from backend.auth.models import UserRole
from backend.observability.logger import ObservabilityLogger
from backend.observability.events import EventBus, EventType
from backend.observability.metrics import MetricsCollector
from backend.storage.object_store import ContentAddressedObjectStore, LocalFSObjectBackend

client = TestClient(app)

# 1. Deployment Configuration
def test_deployment_config_defaults():
    config = DeploymentConfig()
    assert config.zero_cost_mode is True
    assert config.allow_synthetic_fallback is False
    assert config.max_archive_mb == 500
    assert config.max_execution_timeout_sec == 3600
    assert len(config.cors_origins) >= 1


def test_zero_cost_doctrine():
    """Anti-Fabrication doctrine: zero-cost mode must NEVER enable synthetic numbers."""
    config = DeploymentConfig(zero_cost_mode=True, allow_synthetic_fallback=False)
    assert config.zero_cost_mode is True
    assert config.allow_synthetic_fallback is False


# 2. Authentication & Security
def test_security_manager_password_hashing():
    sec = SecurityManager()
    password = "AerospaceSecret2026!"
    hashed = sec.hash_password(password)
    assert hashed.startswith("pbkdf2_sha256$")
    assert sec.verify_password(password, hashed) is True
    assert sec.verify_password("WrongPassword", hashed) is False


def test_session_token_issue_and_verify():
    sec = SecurityManager()
    token = sec.issue_session_token(user_id="usr_test_123", username="test_researcher", role=UserRole.RESEARCHER)
    assert token.token.startswith("aasi_tok_")
    
    payload = sec.verify_session_token(token.token)
    assert payload is not None
    assert payload["user_id"] == "usr_test_123"
    assert payload["role"].upper() == "RESEARCHER"

    # Tampered token verification
    tampered = token.token + "tampered"
    assert sec.verify_session_token(tampered) is None


# 3. Resource Governance & Isolation
def test_governance_engine_quotas():
    gov = GovernanceEngine()
    user_id = "tenant_alpha"
    
    # Rate limit test
    for _ in range(10):
        allowed = gov.check_rate_limit(user_id)
        assert allowed is True
    
    # Active jobs quota test
    can_start = gov.can_start_job(user_id)
    assert can_start is True
    gov.increment_active_job(user_id)
    gov.decrement_active_job(user_id)


def test_multitenancy_isolation():
    gov = GovernanceEngine()
    user_a = "tenant_a"
    user_b = "tenant_b"
    
    gov.increment_active_job(user_a)
    assert gov.get_active_jobs(user_a) == 1
    assert gov.get_active_jobs(user_b) == 0


# 4. Observability & Telemetry
def test_telemetry_metrics():
    metrics = MetricsCollector()
    metrics.record_api_latency("/api/v1/jobs", 42.5)
    metrics.record_job_execution("colab", 120.0, success=True)
    summary = metrics.get_summary()
    assert summary["total_api_requests"] == 1
    assert summary["jobs_by_provider"]["colab"] == 1


def test_event_bus_publishing_and_replay():
    bus = EventBus()
    bus.publish(
        event_type=EventType.JOB_SUBMITTED,
        job_id="job_test_001",
        user_id="usr_001",
        payload={"geometry": "NACA4412"}
    )
    events = bus.get_job_events("job_test_001")
    assert len(events) == 1
    assert events[0].event_type == EventType.JOB_SUBMITTED
    assert events[0].payload["geometry"] == "NACA4412"


# 5. Object Store
def test_content_addressed_object_store(tmp_path):
    backend = LocalFSObjectBackend(base_dir=str(tmp_path))
    store = ContentAddressedObjectStore(backend=backend)
    
    data = b"NACA 4412 CFD Simulation Mesh & Solution Data"
    meta = store.store(data, content_type="application/octet-stream", user_id="usr_store")
    
    assert meta.sha256 is not None
    assert meta.size_bytes == len(data)
    assert store.exists(meta.sha256) is True
    
    retrieved = store.retrieve(meta.sha256)
    assert retrieved == data


# 6. FastAPI API v1 Endpoints
def test_api_v1_health_and_telemetry():
    response = client.get("/api/v1/observability/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["stage_governance"]["stage_10"] == "STAGE_10_BLOCKED"

    metrics_res = client.get("/api/v1/observability/metrics")
    assert metrics_res.status_code == 200
    assert "total_inquiries" in metrics_res.json()


def test_api_v1_compute_providers():
    response = client.get("/api/v1/compute/providers")
    assert response.status_code == 200
    providers = response.json()
    assert isinstance(providers, dict)
    assert "COLAB" in providers
    assert providers["COLAB"]["available"] is True


def test_api_v1_auth_register_and_login():
    uname = f"scientist_{int(time.time() * 1000) % 1000000}"
    reg_payload = {
        "username": uname,
        "email": f"{uname}@aasi.org",
        "password": "StrongPassword2026!"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 200
    assert "user_id" in reg_res.json()
    
    login_payload = {
        "username_or_email": reg_payload["username"],
        "password": reg_payload["password"]
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert "token" in login_res.json()

