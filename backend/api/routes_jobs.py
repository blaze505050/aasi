"""
AASI Phase 27: Persistent Job Queue & Event Streaming API Router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json
import asyncio

from backend.auth.models import User
from backend.auth.dependencies import get_current_user, get_optional_user
from backend.auth.governance import governance_engine
from backend.compute.queue import job_queue, JobRecord, JobState
from backend.observability.events import event_bus, InvestigationEvent

router = APIRouter(prefix="/jobs", tags=["Compute Jobs & Queue"])


@router.get("", response_model=List[JobRecord], summary="List User Compute Jobs")
async def list_jobs(
    state: Optional[JobState] = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
):
    # Filter by user unless admin
    target_uid = None if user.role.value == "ADMIN" else user.user_id
    return job_queue.list_jobs(user_id=target_uid, state=state, limit=limit)


@router.get("/{job_id}", response_model=JobRecord, summary="Get Compute Job Details")
async def get_job(job_id: str, user: User = Depends(get_current_user)):
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Compute job not found.")
    governance_engine.verify_job_ownership(job.user_id, user.user_id, user.role.value)
    return job


@router.get("/{job_id}/events", summary="Server-Sent Events (SSE) Real-Time Progress Stream")
async def stream_job_events(job_id: str, token: Optional[str] = None):
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Compute job not found.")

    async def event_generator():
        async for evt in event_bus.subscribe(job_id):
            data_str = json.dumps(evt.model_dump())
            yield f"data: {data_str}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{job_id}/cancel", response_model=JobRecord, summary="Cancel Active Compute Job")
async def cancel_job(job_id: str, user: User = Depends(get_current_user)):
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Compute job not found.")
    governance_engine.verify_job_ownership(job.user_id, user.user_id, user.role.value)
    cancelled = job_queue.cancel_job(job_id, user.user_id)
    governance_engine.release_job(job_id)
    return cancelled
