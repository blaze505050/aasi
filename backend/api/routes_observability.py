"""
AASI Phase 27: Observability & Telemetry API Router.
Provides system health, Stage-10 governance status, telemetry metrics,
and structured event auditing.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional, Dict, Any
import os

from backend.auth.models import User
from backend.auth.dependencies import get_current_user, get_optional_user
from backend.observability.metrics import metrics_collector, TelemetryMetrics
from backend.observability.events import event_bus, InvestigationEvent
from backend.observability.logger import structured_logger
from backend.deployment.config import deployment_config
from backend.compute.queue import job_queue
from backend.compute.provider_manager import provider_manager

router = APIRouter(prefix="/observability", tags=["Observability & Telemetry"])


@router.get("/health", summary="System Health & Stage-10 Governance Status")
async def get_health():
    """
    Returns deployment health, Stage-10 governance status, and provider readiness.
    Under the Absolute Anti-Fabrication Rule, Stage-10 status is STAGE_10_BLOCKED
    until verified external hardware execution is confirmed.
    """
    providers = provider_manager.list_providers()
    active_jobs = len(job_queue.list_jobs(limit=1000))

    return {
        "status": "healthy",
        "stage_governance": {
            "stage_9": "STAGE_9_GRANTED",
            "stage_10": "STAGE_10_BLOCKED",
            "reason": "Stage-10 promotion requires empirical external hardware CFD execution archives.",
        },
        "dev_mode": deployment_config.dev_mode,
        "zero_laptop_load_guaranteed": True,
        "providers_registered": [p.probe().provider for p in providers],
        "active_jobs_count": active_jobs,
        "version": "27.0.0",
    }


@router.get("/metrics", response_model=TelemetryMetrics, summary="Get Telemetry Metrics Snapshot")
async def get_metrics():
    """Returns telemetry snapshot including throughput, latencies, and error rates."""
    providers = [p.probe().provider for p in provider_manager.list_providers() if p.probe().available]
    active_count = len([j for j in job_queue.list_jobs(limit=100) if j.state.value not in ["COMPLETED", "FAILED", "CANCELLED"]])
    return metrics_collector.snapshot(active_count=active_count, providers=providers)


@router.get("/events", response_model=List[InvestigationEvent], summary="Query Investigation Events")
async def get_events(
    job_id: Optional[str] = Query(None, description="Filter events by Job ID"),
    limit: int = Query(50, ge=1, le=500, description="Max number of events to return"),
):
    """Fetches in-memory or persisted investigation events."""
    events = event_bus.get_events(job_id=job_id, limit=limit)
    return events


# ─── Cryptographic Audit Log Endpoints (Item 16) ───

@router.get("/audit-log", summary="Query Cryptographic Audit Log Entries")
async def get_audit_log(
    org_id: Optional[str] = Query("default"),
    limit: int = Query(50, ge=1, le=500),
):
    """Returns append-only, SHA-256 chained transaction log entries."""
    from backend.storage.audit_log import audit_logger
    entries = audit_logger.list_entries(org_id=org_id, limit=limit)
    return {
        "org_id": org_id,
        "count": len(entries),
        "entries": entries,
    }


@router.post("/audit-log/verify", summary="Verify SHA-256 Audit Chain Integrity")
async def verify_audit_log():
    """Validates full mathematical hash chain from genesis to head block to confirm zero data tampering."""
    from backend.storage.audit_log import audit_logger
    res = audit_logger.verify_chain_integrity()
    return res
