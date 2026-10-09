"""
AASI Phase 27: Telemetry Metrics Collector.
Collects queue throughput, execution durations, verification error rates, and API latencies.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import time
from collections import defaultdict


class TelemetryMetrics(BaseModel):
    total_inquiries: int = 0
    total_jobs_queued: int = 0
    total_jobs_completed: int = 0
    total_jobs_failed: int = 0
    active_jobs_count: int = 0
    avg_cfd_duration_seconds: float = 0.0
    verification_success_rate: float = 100.0
    errors_by_type: Dict[str, int] = Field(default_factory=dict)
    active_providers: List[str] = Field(default_factory=list)


class MetricsCollector:
    def __init__(self):
        self._total_inquiries = 0
        self._jobs_queued = 0
        self._jobs_completed = 0
        self._jobs_failed = 0
        self._durations: List[float] = []
        self._verifications_passed = 0
        self._verifications_failed = 0
        self._errors: Dict[str, int] = defaultdict(int)

    def record_inquiry(self):
        self._total_inquiries += 1

    def record_job_queued(self):
        self._jobs_queued += 1

    def record_job_completed(self, duration_seconds: float):
        self._jobs_completed += 1
        self._durations.append(duration_seconds)

    def record_job_failed(self, error_type: str):
        self._jobs_failed += 1
        self._errors[error_type] += 1

    def record_verification(self, success: bool):
        if success:
            self._verifications_passed += 1
        else:
            self._verifications_failed += 1

    def record_api_latency(self, endpoint: str, latency_ms: float):
        self._total_inquiries += 1

    def record_job_execution(self, provider: str, duration_sec: float, success: bool = True):
        if success:
            self.record_job_completed(duration_sec)
        else:
            self.record_job_failed("EXECUTION_ERROR")
        if not hasattr(self, "_provider_jobs"):
            self._provider_jobs = defaultdict(int)
        self._provider_jobs[provider.lower()] += 1

    def get_summary(self) -> Dict[str, Any]:
        p_jobs = getattr(self, "_provider_jobs", defaultdict(int))
        return {
            "total_api_requests": self._total_inquiries,
            "jobs_by_provider": dict(p_jobs),
            "jobs_completed": self._jobs_completed,
            "jobs_failed": self._jobs_failed,
        }

    def snapshot(self, active_count: int = 0, providers: Optional[List[str]] = None) -> TelemetryMetrics:
        avg_dur = sum(self._durations) / len(self._durations) if self._durations else 0.0
        total_v = self._verifications_passed + self._verifications_failed
        v_rate = (self._verifications_passed / total_v * 100.0) if total_v > 0 else 100.0

        return TelemetryMetrics(
            total_inquiries=self._total_inquiries,
            total_jobs_queued=self._jobs_queued,
            total_jobs_completed=self._jobs_completed,
            total_jobs_failed=self._jobs_failed,
            active_jobs_count=active_count,
            avg_cfd_duration_seconds=round(avg_dur, 2),
            verification_success_rate=round(v_rate, 2),
            errors_by_type=dict(self._errors),
            active_providers=providers or ["GOOGLE_COLAB", "REMOTE_HPC", "LOCAL_OPENFOAM"],
        )


metrics_collector = MetricsCollector()

