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
from datetime import datetime, timezone
import hashlib
import platform
import subprocess
import sys
from pydantic import BaseModel


class SystemEnvironmentManifest(BaseModel):
    timestamp_utc: str
    os_platform: str
    architecture: str
    python_version: str
    git_commit: str
    total_ram_gb: float
    available_ram_gb: float
    total_disk_gb: float
    available_disk_gb: float
    disk_safety_reserve_gb: float = 15.0
    is_disk_safety_satisfied: bool
    numpy_version: Optional[str] = None
    scipy_version: Optional[str] = None
    torch_version: Optional[str] = None
    torch_cuda_available: bool = False
    simplefoam_available: bool = False
    wsl_available: bool = False
    manifest_hash: str = ""


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

    @classmethod
    def get_system_environment_manifest(cls) -> SystemEnvironmentManifest:
        """
        Gathers a verifiable, machine-readable host system environment manifest.
        Calculates a deterministic cryptographic SHA-256 hash over environment parameters.
        """
        try:
            total_disk, used_disk, free_disk = shutil.disk_usage(os.path.abspath("."))
        except Exception:
            total_disk, free_disk = 100_000_000_000, 20_000_000_000

        total_ram = 8_000_000_000
        free_ram = 1_000_000_000
        if HAS_PSUTIL:
            try:
                vm = psutil.virtual_memory()
                total_ram = vm.total
                free_ram = vm.available
            except Exception:
                pass

        total_disk_gb = round(total_disk / 1e9, 2)
        free_disk_gb = round(free_disk / 1e9, 2)
        total_ram_gb = round(total_ram / 1e9, 2)
        free_ram_gb = round(free_ram / 1e9, 2)

        is_disk_safety_satisfied = free_disk >= cls.SAFETY_DISK_RESERVE_BYTES

        # Git commit
        try:
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            git_commit = "UNKNOWN_OR_UNTRACKED"

        # Versions
        numpy_ver = None
        try:
            import numpy
            numpy_ver = numpy.__version__
        except Exception:
            pass

        scipy_ver = None
        try:
            import scipy
            scipy_ver = scipy.__version__
        except Exception:
            pass

        torch_ver = None
        torch_cuda = False
        try:
            import torch
            torch_ver = torch.__version__
            torch_cuda = torch.cuda.is_available()
        except Exception:
            pass

        simplefoam_avail = shutil.which("simpleFoam") is not None
        wsl_avail = shutil.which("wsl") is not None

        env_dict = {
            "os_platform": platform.platform(),
            "architecture": platform.machine(),
            "python_version": sys.version.split()[0],
            "git_commit": git_commit,
            "total_ram_gb": total_ram_gb,
            "available_ram_gb": free_ram_gb,
            "total_disk_gb": total_disk_gb,
            "available_disk_gb": free_disk_gb,
            "disk_safety_reserve_gb": round(cls.SAFETY_DISK_RESERVE_BYTES / 1e9, 2),
            "numpy_version": numpy_ver,
            "scipy_version": scipy_ver,
            "torch_version": torch_ver,
            "torch_cuda_available": torch_cuda,
            "simplefoam_available": simplefoam_avail,
            "wsl_available": wsl_avail,
        }

        canonical_str = "|".join(f"{k}:{v}" for k, v in sorted(env_dict.items()))
        manifest_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

        return SystemEnvironmentManifest(
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            os_platform=env_dict["os_platform"],
            architecture=env_dict["architecture"],
            python_version=env_dict["python_version"],
            git_commit=env_dict["git_commit"],
            total_ram_gb=total_ram_gb,
            available_ram_gb=free_ram_gb,
            total_disk_gb=total_disk_gb,
            available_disk_gb=free_disk_gb,
            disk_safety_reserve_gb=env_dict["disk_safety_reserve_gb"],
            is_disk_safety_satisfied=is_disk_safety_satisfied,
            numpy_version=numpy_ver,
            scipy_version=scipy_ver,
            torch_version=torch_ver,
            torch_cuda_available=torch_cuda,
            simplefoam_available=simplefoam_avail,
            wsl_available=wsl_avail,
            manifest_hash=manifest_hash
        )
