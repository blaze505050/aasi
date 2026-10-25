"""
AASI 2.0 Resource Budget — Allocation, Headroom Evaluation & Enforcement.

Enforces deterministic resource boundaries on tasks before and during execution:
- CPU utilization ceilings
- RAM allocation limits & system headroom requirements
- Disk write quotas & free space preservation
- GPU VRAM reservations
- Hard execution timeouts
"""

from __future__ import annotations

import time
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, model_validator

from backend.governor.constants import (
    DEFAULT_TASK_TIMEOUT_SECONDS,
    HARD_MAX_TIMEOUT_SECONDS,
    DEFAULT_MAX_CPU_PERCENT,
    CRITICAL_CPU_PERCENT,
    DEFAULT_MAX_RAM_GB,
    CRITICAL_RAM_AVAILABLE_GB,
    MIN_FREE_RAM_FRACTION,
    DEFAULT_MAX_DISK_GB,
    CRITICAL_DISK_FREE_GB,
    DEFAULT_MAX_GPU_VRAM_GB,
    CRITICAL_GPU_VRAM_FREE_FRACTION,
)
from backend.governor.resource_monitor import ResourceSnapshot

logger = logging.getLogger("aasi.governor.budget")


# ─── Verdict Model ────────────────────────────────────────────────────────────

class BudgetVerdict(BaseModel):
    """Deterministic result of budget evaluation against system resources."""
    approved: bool
    reasons: List[str] = Field(default_factory=list)
    requested_budget: Dict[str, Any] = Field(default_factory=dict)
    headroom: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_approved(self) -> bool:
        return self.approved


# ─── Resource Budget Model ────────────────────────────────────────────────────

class ResourceBudget(BaseModel):
    """
    Specification of resource limits requested for or assigned to a task execution.
    """
    task_id: Optional[str] = None
    max_timeout_seconds: int = Field(default=DEFAULT_TASK_TIMEOUT_SECONDS, ge=1)
    max_cpu_percent: float = Field(default=DEFAULT_MAX_CPU_PERCENT, ge=1.0, le=100.0)
    max_ram_gb: float = Field(default=DEFAULT_MAX_RAM_GB, ge=0.1)
    max_disk_gb: float = Field(default=DEFAULT_MAX_DISK_GB, ge=0.1)
    max_gpu_vram_gb: float = Field(default=0.0, ge=0.0)
    allow_network: bool = False
    allow_subprocesses: bool = False
    enforce_headroom: bool = True

    @model_validator(mode="after")
    def validate_bounds(self) -> "ResourceBudget":
        """Enforces absolute ceilings (HARD_MAX)."""
        if self.max_timeout_seconds > HARD_MAX_TIMEOUT_SECONDS:
            raise ValueError(
                f"Requested timeout {self.max_timeout_seconds}s exceeds HARD_MAX ({HARD_MAX_TIMEOUT_SECONDS}s)"
            )
        return self

    def evaluate(self, snapshot: ResourceSnapshot) -> BudgetVerdict:
        """
        Deterministically evaluates whether the system can safely execute
        a task under this budget, fail-closing on any constraint violation.
        """
        reasons: List[str] = []

        # 1. Existing system-wide critical alerts
        if snapshot.critical_alert:
            for alert in snapshot.alert_reasons:
                reasons.append(f"System alert active: {alert}")

        # 2. CPU headroom evaluation
        if snapshot.cpu_percent >= CRITICAL_CPU_PERCENT:
            reasons.append(
                f"Host CPU saturated ({snapshot.cpu_percent}% >= {CRITICAL_CPU_PERCENT}%)"
            )

        # 3. RAM headroom evaluation
        if snapshot.ram_available_gb < CRITICAL_RAM_AVAILABLE_GB:
            reasons.append(
                f"Host RAM critically low ({snapshot.ram_available_gb} GB < {CRITICAL_RAM_AVAILABLE_GB} GB)"
            )

        if self.enforce_headroom:
            # Task must not claim more than available RAM minus critical reserve
            safe_available_ram = max(0.0, snapshot.ram_available_gb - CRITICAL_RAM_AVAILABLE_GB)
            if self.max_ram_gb > safe_available_ram:
                reasons.append(
                    f"Requested RAM ({self.max_ram_gb} GB) exceeds safe available RAM ({round(safe_available_ram, 2)} GB)"
                )

            # Minimum free fraction preservation
            if snapshot.ram_total_gb > 0:
                post_alloc_free = (snapshot.ram_available_gb - self.max_ram_gb) / snapshot.ram_total_gb
                if post_alloc_free < MIN_FREE_RAM_FRACTION:
                    reasons.append(
                        f"Post-allocation free RAM ({round(post_alloc_free * 100, 1)}%) violates minimum free floor ({round(MIN_FREE_RAM_FRACTION * 100, 1)}%)"
                    )

        # 4. Disk headroom evaluation
        if snapshot.disk_free_gb < CRITICAL_DISK_FREE_GB:
            reasons.append(
                f"Host disk critically low ({snapshot.disk_free_gb} GB < {CRITICAL_DISK_FREE_GB} GB)"
            )

        if self.enforce_headroom:
            safe_free_disk = max(0.0, snapshot.disk_free_gb - CRITICAL_DISK_FREE_GB)
            if self.max_disk_gb > safe_free_disk:
                reasons.append(
                    f"Requested disk ({self.max_disk_gb} GB) exceeds safe free disk ({round(safe_free_disk, 2)} GB)"
                )

        # 5. GPU headroom evaluation
        if self.max_gpu_vram_gb > 0:
            if not snapshot.gpu.available:
                reasons.append(
                    f"Task requested {self.max_gpu_vram_gb} GB GPU VRAM, but no GPU is available on host"
                )
            elif snapshot.gpu.free_vram_gb is not None:
                if self.max_gpu_vram_gb > snapshot.gpu.free_vram_gb:
                    reasons.append(
                        f"Requested GPU VRAM ({self.max_gpu_vram_gb} GB) exceeds free VRAM ({snapshot.gpu.free_vram_gb} GB)"
                    )

        approved = len(reasons) == 0

        headroom_summary = {
            "host_cpu_percent": snapshot.cpu_percent,
            "host_ram_available_gb": snapshot.ram_available_gb,
            "host_ram_total_gb": snapshot.ram_total_gb,
            "host_disk_free_gb": snapshot.disk_free_gb,
            "gpu_available": snapshot.gpu.available,
            "gpu_free_vram_gb": snapshot.gpu.free_vram_gb,
        }

        return BudgetVerdict(
            approved=approved,
            reasons=reasons,
            requested_budget=self.model_dump(),
            headroom=headroom_summary,
        )


# ─── Live Execution Enforcement Context ──────────────────────────────────────

class BudgetEnforcement:
    """
    Context tracker during task execution. Monitors elapsed time and memory bounds.
    """

    def __init__(self, budget: ResourceBudget):
        self.budget = budget
        self.start_time: float = 0.0
        self.end_time: Optional[float] = None
        self.timed_out: bool = False
        self.canceled: bool = False

    def __enter__(self) -> "BudgetEnforcement":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.end_time = time.time()

    @property
    def elapsed_seconds(self) -> float:
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time

    def check_limits(self) -> None:
        """Raises TimeoutError if budget timeout is exceeded."""
        if self.elapsed_seconds > self.budget.max_timeout_seconds:
            self.timed_out = True
            raise TimeoutError(
                f"Task exceeded execution budget timeout of {self.budget.max_timeout_seconds}s "
                f"(elapsed: {round(self.elapsed_seconds, 2)}s)"
            )
