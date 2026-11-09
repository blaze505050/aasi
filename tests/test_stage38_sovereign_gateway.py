"""
Stage 38 Verification Test Suite: Enterprise Sovereign Cloud SaaS Gateway & Token Metering
===========================================================================================
Tests:
1. Token Bucket Mathematical Refill & Capacity Clamping.
2. Token Deduction & Rate Limiting (429 handling with backoff).
3. ITAR/EAR Compliance Checking & Cryptographic Clearance Receipts.
4. FastAPI Endpoints for Stage 38.
"""

import pytest
import time
from fastapi.testclient import TestClient
from aasi_aero_fno.enterprise_sovereign_gateway import (
    EnterpriseSovereignGatewayEngine,
    TenantTier,
    ComputeTaskType,
    UserRole,
    TASK_TOKEN_COSTS,
)
from backend.main import app


def test_token_bucket_refill_and_clamping():
    engine = EnterpriseSovereignGatewayEngine()
    tenant = engine._tenants["TENANT-RESEARCH-IITB"]

    # Manually drain tokens to 10.0
    tenant.current_tokens = 10.0
    tenant.last_refill_timestamp = time.time() - 10.0  # 10 seconds ago

    # Refill rate is 5.0 tokens/sec -> 10s * 5 = 50 tokens added -> 60.0 tokens
    engine._refill_tokens(tenant, time.time())
    assert 55.0 <= tenant.current_tokens <= 65.0

    # Over-replenish: simulate 1000 seconds -> should clamp at capacity (500.0)
    tenant.last_refill_timestamp = time.time() - 1000.0
    engine._refill_tokens(tenant, time.time())
    assert tenant.current_tokens == tenant.token_capacity


def test_token_consumption_and_rate_limiting():
    engine = EnterpriseSovereignGatewayEngine()
    tenant_id = "TENANT-DEFENSE-DRDO"

    # 1. Authorize normal SciML inference (2 tokens)
    success, res = engine.consume_tokens(tenant_id, ComputeTaskType.SCIML_FNO_INFERENCE)
    assert success is True
    assert res["status"] == "CONSUMPTION_AUTHORIZED"
    assert res["tokens_deducted"] == TASK_TOKEN_COSTS[ComputeTaskType.SCIML_FNO_INFERENCE]
    assert len(res["cryptographic_receipt_sha256"]) == 64

    # 2. Artificial exhaustion: reduce tokens to 5.0 and attempt MDO (cost: 50.0)
    tenant = engine._tenants[tenant_id]
    tenant.current_tokens = 5.0

    success_mdo, res_mdo = engine.consume_tokens(tenant_id, ComputeTaskType.MDO_TOPOLOGY_OPTIMIZATION)
    assert success_mdo is False
    assert res_mdo["status"] == "RATE_LIMIT_EXCEEDED"
    assert "wait_seconds_to_refill" in res_mdo
    assert res_mdo["wait_seconds_to_refill"] > 0.0


def test_itar_export_clearance():
    engine = EnterpriseSovereignGatewayEngine()

    # Defense Prime has active ITAR clearance -> Approved
    res_defense = engine.generate_export_clearance(
        tenant_id="TENANT-DEFENSE-DRDO",
        asset_name="Hypersonic_Aero_Model.h5",
        classification="DEFENSE_ITAR_RESTRICTED",
    )
    assert res_defense["clearance_status"] == "EXPORT_APPROVED"
    assert "clearance_ticket_id" in res_defense
    assert len(res_defense["cryptographic_hash_sha256"]) == 64

    # Academic lab does NOT have ITAR clearance -> Denied
    res_academic = engine.generate_export_clearance(
        tenant_id="TENANT-RESEARCH-IITB",
        asset_name="Classified_Stealth_Coating_Data.bin",
        classification="DEFENSE_ITAR_RESTRICTED",
    )
    assert res_academic["clearance_status"] == "EXPORT_DENIED"


def test_sovereign_gateway_api_endpoints():
    client = TestClient(app)

    # 1. List tenants endpoint
    res_tenants = client.get("/api/v1/sovereign-gateway/tenants")
    assert res_tenants.status_code == 200
    tlist = res_tenants.json()["data"]["tenants"]
    assert len(tlist) >= 3

    # 2. Token consumption endpoint
    res_consume = client.post(
        "/api/v1/sovereign-gateway/consume-tokens",
        json={
            "tenant_id": "TENANT-DEFENSE-DRDO",
            "task_type_key": "SCIML_FNO_INFERENCE",
            "user_role_key": "AERODYNAMICS_SPECIALIST",
        },
    )
    assert res_consume.status_code == 200
    data_consume = res_consume.json()["data"]
    assert data_consume["status"] == "CONSUMPTION_AUTHORIZED"
    assert "cryptographic_receipt_sha256" in data_consume

    # 3. Export clearance endpoint
    res_export = client.post(
        "/api/v1/sovereign-gateway/export-clearance",
        json={
            "tenant_id": "TENANT-COMMERCIAL-BOEING",
            "asset_name": "Commercial_Wing_Polar_Table.csv",
            "classification": "COMMERCIAL_UNRESTRICTED",
        },
    )
    assert res_export.status_code == 200
    data_export = res_export.json()["data"]
    assert data_export["clearance_status"] == "EXPORT_APPROVED"
