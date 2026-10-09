"""
AASI Phase 27: Resource Governance & Multitenant Isolation.
Enforces concurrency limits, archive size bounds, execution timeouts, and rate limits.
Never exposes another user's CFD jobs.
"""

from typing import Dict, Optional
import time
from collections import defaultdict
from fastapi import HTTPException, status
from backend.auth.models import User, UserQuota
from backend.deployment.config import get_deployment_config


class GovernanceEngine:
    """Enforces computational quotas, multitenant job ownership, and request rate limiting."""

    def __init__(self):
        self.config = get_deployment_config()
        self._user_quotas: Dict[str, UserQuota] = {}
        self._rate_limit_windows: Dict[str, list] = defaultdict(list)
        self._active_jobs: Dict[str, str] = {}  # job_id -> user_id

    def reset(self) -> None:
        """Reset all active quotas and jobs (for test isolation)."""
        self._user_quotas.clear()
        self._rate_limit_windows.clear()
        self._active_jobs.clear()

    def get_quota(self, user_id: str) -> UserQuota:
        if user_id not in self._user_quotas:
            self._user_quotas[user_id] = UserQuota(
                user_id=user_id,
                max_concurrent_jobs=self.config.max_concurrent_jobs_per_user,
                max_archive_size_mb=self.config.max_archive_size_bytes // (1024 * 1024),
                rate_limit_per_minute=self.config.rate_limit_per_minute,
            )
        return self._user_quotas[user_id]

    def check_job_submission_allowed(self, user_id: str) -> bool:
        """Verify user has not exceeded concurrent job ceiling."""
        quota = self.get_quota(user_id)
        # Only count jobs that are actively executing numerical computations on server
        from backend.compute.queue import job_queue
        to_remove = []
        active_running = 0
        for jid, uid in self._active_jobs.items():
            if uid == user_id:
                job = job_queue.get_job(jid)
                if not job or job.status.value not in ("RUNNING", "COMPUTING"):
                    to_remove.append(jid)
                else:
                    active_running += 1
        for jid in to_remove:
            self._active_jobs.pop(jid, None)

        if active_running >= quota.max_concurrent_jobs:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Resource quota exceeded: Maximum concurrent running jobs ({quota.max_concurrent_jobs}) reached.",
            )
        return True

    def register_active_job(self, job_id: str, user_id: str):
        self._active_jobs[job_id] = user_id
        quota = self.get_quota(user_id)
        quota.active_jobs_count = sum(1 for uid in self._active_jobs.values() if uid == user_id)

    def release_job(self, job_id: str):
        if job_id in self._active_jobs:
            user_id = self._active_jobs.pop(job_id)
            quota = self.get_quota(user_id)
            quota.active_jobs_count = sum(1 for uid in self._active_jobs.values() if uid == user_id)

    def check_archive_size_allowed(self, size_bytes: int):
        if size_bytes > self.config.max_archive_size_bytes:
            max_mb = self.config.max_archive_size_bytes // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archive exceeds maximum allowed size ({max_mb} MB).",
            )

    def check_rate_limit(self, identifier: str) -> bool:
        """Sliding window rate limit check."""
        now = time.time()
        window = self._rate_limit_windows[identifier]
        # Prune timestamps older than 60s
        self._rate_limit_windows[identifier] = [ts for ts in window if now - ts < 60.0]
        if len(self._rate_limit_windows[identifier]) >= self.config.rate_limit_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Request rate limit exceeded. Please wait before retrying.",
            )
        self._rate_limit_windows[identifier].append(now)
        return True

    def can_start_job(self, user_id: str) -> bool:
        quota = self.get_quota(user_id)
        current_active = sum(1 for uid in self._active_jobs.values() if uid == user_id)
        return current_active < quota.max_concurrent_jobs

    def increment_active_job(self, user_id: str):
        import secrets
        jid = f"tmp_job_{secrets.token_hex(4)}"
        self.register_active_job(jid, user_id)

    def decrement_active_job(self, user_id: str):
        for jid, uid in list(self._active_jobs.items()):
            if uid == user_id:
                self.release_job(jid)
                break

    def get_active_jobs(self, user_id: str) -> int:
        return sum(1 for uid in self._active_jobs.values() if uid == user_id)

    def verify_job_ownership(self, job_user_id: str, requesting_user_id: str, user_role: str):
        """Ensure users cannot access or cancel jobs owned by others, unless ADMIN."""
        if user_role == "ADMIN":
            return True
        if job_user_id != requesting_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access or modify this compute job.",
            )
        return True



# Global singleton governance engine
governance_engine = GovernanceEngine()
