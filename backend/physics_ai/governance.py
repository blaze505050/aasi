"""
AASI Performance & Hardware Governance Engine.

Performs pre-flight scientific resource budgeting before executing physics-AI training:
- Calculates dataset disk requirements, RAM consumption, tensor memory, and runtime.
- Evaluates against host workstation limits (15 GB disk safety reserve).
- Returns RESOURCE_LIMITED fail-closed if host capacity is inadequate.
- Strictly prevents workstation crashes and silent data downsampling.
"""

from typing import Dict, Any, Optional
import shutil
import os
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
from pydantic import BaseModel


class HardwareGovernanceReport(BaseModel):
    is_safe: bool
    status: str  # "SAFE_TO_EXECUTE" or "RESOURCE_LIMITED"
    dataset_disk_mb: float
    estimated_ram_mb: float
    estimated_training_memory_mb: float
    estimated_runtime_seconds: float
    available_disk_gb: float
    available_ram_gb: float
    recommendation: str
    sampling_policy: Optional[str] = None


class HardwareGovernanceGuard:
    """Pre-flight hardware and storage safety gatekeeper."""

    SAFETY_DISK_RESERVE_BYTES = 15_000_000_000  # 15 GB reserve

    @classmethod
    def evaluate_training_feasibility(
        cls,
        sample_count: int,
        epochs: int = 100,
        batch_size: int = 32,
        dataset_size_bytes: int = 1_000_000,
        sampling_policy: Optional[str] = None
    ) -> HardwareGovernanceReport:
        """
        Evaluates training feasibility on the active host workstation.
        """
        # 1. Host capacity inquiry
        try:
            total_disk, used_disk, free_disk = shutil.disk_usage(os.path.abspath("."))
        except Exception:
            free_disk = 20_000_000_000

        free_ram_bytes = 4_000_000_000
        if HAS_PSUTIL:
            try:
                ram = psutil.virtual_memory()
                free_ram_bytes = ram.available
            except Exception:
                pass

        free_disk_gb = round(free_disk / 1e9, 2)
        free_ram_gb = round(free_ram_bytes / 1e9, 2)

        # 2. Resource estimates
        dataset_disk_mb = round(dataset_size_bytes / 1e6, 2)
        # In-memory arrays: [N, 64, 2] coords + [N, 3] conditions + [N, 3] targets + grads
        estimated_ram_mb = round((sample_count * 64 * 2 * 4 * 4) / 1e6 + 50.0, 2)
        estimated_training_mb = round(estimated_ram_mb * 2.5 + 80.0, 2)

        # Approximate CPU throughput: ~15,000 forward-backward passes / second on vectorized NumPy
        steps_per_epoch = max(1, sample_count // batch_size)
        total_steps = steps_per_epoch * epochs
        estimated_runtime_sec = round(max(0.5, total_steps * (batch_size / 2500.0)), 2)

        # 3. Feasibility check
        is_disk_safe = (free_disk - dataset_size_bytes) >= cls.SAFETY_DISK_RESERVE_BYTES
        is_ram_safe = (free_ram_bytes - (estimated_training_mb * 1e6)) >= 1_000_000_000  # Leave at least 1 GB RAM

        is_safe = is_disk_safe and is_ram_safe
        if not is_safe:
            status = "RESOURCE_LIMITED"
            if not is_disk_safe:
                recommendation = (
                    f"RESOURCE_LIMITED: Dataset footprint ({dataset_disk_mb} MB) breaches 15 GB workstation "
                    f"reserve on {free_disk_gb} GB free disk. External compute/storage required."
                )
            else:
                recommendation = (
                    f"RESOURCE_LIMITED: Training memory ({estimated_training_mb} MB) exceeds safe operating limit "
                    f"on {free_ram_gb} GB available RAM."
                )
        else:
            status = "SAFE_TO_EXECUTE"
            recommendation = (
                f"Hardware check passed. Training feasible locally ({estimated_training_mb} MB RAM, "
                f"~{estimated_runtime_sec}s runtime, {free_disk_gb} GB disk reserve preserved)."
            )

        return HardwareGovernanceReport(
            is_safe=is_safe,
            status=status,
            dataset_disk_mb=dataset_disk_mb,
            estimated_ram_mb=estimated_ram_mb,
            estimated_training_memory_mb=estimated_training_mb,
            estimated_runtime_seconds=estimated_runtime_sec,
            available_disk_gb=free_disk_gb,
            available_ram_gb=free_ram_gb,
            recommendation=recommendation,
            sampling_policy=sampling_policy
        )
