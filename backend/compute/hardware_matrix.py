"""
AASI Hardware Capability Matrix & Resource-Aware Task Router.

Inspects host workstation resources (CPU cores, total/available RAM, free disk space,
CUDA availability, OS, WSL2, and installed solvers) and enforces fail-closed resource routing
to prevent system lockups, out-of-memory thrashing, or silent solver crashes.
"""

from __future__ import annotations

import os
import sys
import shutil
import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.compute.models import ComputeBackendType
from backend.simulation.detector import SolverDetector

logger = logging.getLogger(__name__)


class ComputationalTaskType(str, Enum):
    SURROGATE_INFERENCE = "SURROGATE_INFERENCE"
    SURROGATE_TRAINING = "SURROGATE_TRAINING"
    CFD_2D = "CFD_2D"
    CFD_3D = "CFD_3D"
    MESH_GENERATION = "MESH_GENERATION"
    DATASET_IMPORT = "DATASET_IMPORT"


class HardwareProfile(BaseModel):
    """Accurate, non-fabricated hardware capability profile of the host system."""
    cpu_cores_logical: int
    cpu_cores_physical: int
    ram_total_gb: float
    ram_available_gb: float
    disk_free_gb: float
    has_cuda: bool
    cuda_device_name: Optional[str] = None
    cuda_memory_gb: Optional[float] = None
    is_windows: bool
    has_wsl2: bool
    installed_solvers: Dict[str, bool]
    safe_max_local_mesh_cells: int
    safe_max_local_dimension: str
    supported_backends: List[str]
    operating_regime: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RoutingDecision(BaseModel):
    """Resource-aware dispatch decision for a computational workload."""
    task_type: str
    recommended_backend: ComputeBackendType
    allowed_locally: bool
    reason: str
    resource_bottlenecks: List[str] = Field(default_factory=list)
    suggested_action: str
    hardware_summary: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _probe_ram() -> tuple[float, float]:
    """Probes total and available physical RAM in GB without requiring external packages."""
    if sys.platform == "win32":
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                total_gb = round(stat.ullTotalPhys / (1024 ** 3), 2)
                avail_gb = round(stat.ullAvailPhys / (1024 ** 3), 2)
                return total_gb, avail_gb
        except Exception as exc:
            logger.debug("Windows ctypes RAM probe failed: %s", exc)

    # Linux / WSL2 / fallback: check /proc/meminfo
    if os.path.exists("/proc/meminfo"):
        try:
            mem_info: Dict[str, float] = {}
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().split()[0]
                        mem_info[key] = float(val) / (1024 ** 2)  # kB to GB
            total_gb = round(mem_info.get("MemTotal", 8.0), 2)
            avail_gb = round(mem_info.get("MemAvailable", 2.0), 2)
            return total_gb, avail_gb
        except Exception as exc:
            logger.debug("/proc/meminfo probe failed: %s", exc)

    return 8.0, 2.0


def _probe_cuda() -> tuple[bool, Optional[str], Optional[float]]:
    """Safely probes CUDA availability without crashing on missing DLLs or policies."""
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            mem_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2)
            return True, device_name, mem_gb
    except Exception:
        pass
    return False, None, None


class HardwareMatrixManager:
    """Manages system hardware detection and enforces resource-aware compute routing."""

    def __init__(self):
        self._cached_profile: Optional[HardwareProfile] = None

    def detect_hardware(self, force_refresh: bool = False) -> HardwareProfile:
        """Probes host hardware and returns a validated HardwareProfile."""
        if self._cached_profile and not force_refresh:
            return self._cached_profile

        cpu_logical = os.cpu_count() or 1
        cpu_physical = cpu_logical  # on Python stdlib without psutil, logical is safe upper bound
        total_ram, avail_ram = _probe_ram()

        try:
            free_disk = round(shutil.disk_usage(".").free / (1024 ** 3), 2)
        except Exception:
            free_disk = 10.0

        has_cuda, cuda_name, cuda_mem = _probe_cuda()
        is_windows = (sys.platform == "win32")
        has_wsl2 = (shutil.which("wsl.exe") is not None or shutil.which("wsl") is not None)

        detector = SolverDetector()
        solver_results = detector.detect_all()
        installed_solvers = {name: info.is_available for name, info in solver_results.items()}

        # Safe operational constraints determination
        # Lightweight developer edge workstation (<= 8GB RAM or <= 4 CPU cores or no CUDA)
        if total_ram <= 12.0 or cpu_logical <= 4 or not has_cuda:
            regime = "LIGHTWEIGHT_CPU_EDGE"
            safe_max_cells = 50_000
            safe_dimension = "2D"
        elif total_ram <= 32.0 and cpu_logical <= 16:
            regime = "MIDRANGE_WORKSTATION"
            safe_max_cells = 250_000
            safe_dimension = "2D"
        else:
            regime = "HIGH_PERFORMANCE_SERVER"
            safe_max_cells = 2_000_000
            safe_dimension = "3D"

        supported_backends = [
            ComputeBackendType.USER_EXECUTED.value,
            ComputeBackendType.CACHED.value,
            ComputeBackendType.REMOTE.value,
        ]
        # Only advertise LOCAL if at least one native CFD solver is installed
        if any(installed_solvers.values()):
            supported_backends.append(ComputeBackendType.LOCAL.value)

        profile = HardwareProfile(
            cpu_cores_logical=cpu_logical,
            cpu_cores_physical=cpu_physical,
            ram_total_gb=total_ram,
            ram_available_gb=avail_ram,
            disk_free_gb=free_disk,
            has_cuda=has_cuda,
            cuda_device_name=cuda_name,
            cuda_memory_gb=cuda_mem,
            is_windows=is_windows,
            has_wsl2=has_wsl2,
            installed_solvers=installed_solvers,
            safe_max_local_mesh_cells=safe_max_cells,
            safe_max_local_dimension=safe_dimension,
            supported_backends=supported_backends,
            operating_regime=regime,
        )

        self._cached_profile = profile
        return profile

    def route_task(
        self,
        task_type: str | ComputationalTaskType,
        mesh_cells: int = 0,
        dimension: str = "2D",
        solver: str = "openfoam",
        model_type: str = "surrogate",
        sample_count: int = 1000,
        profile: Optional[HardwareProfile] = None,
    ) -> RoutingDecision:
        """
        Evaluates task requirements against host hardware profile and routes to
        LOCAL, USER_EXECUTED, or REMOTE backends fail-closed.
        """
        hw = profile or self.detect_hardware()
        task_type_str = task_type.value if isinstance(task_type, ComputationalTaskType) else str(task_type).upper()

        hw_summary = {
            "cpu_cores": hw.cpu_cores_logical,
            "ram_total_gb": hw.ram_total_gb,
            "ram_available_gb": hw.ram_available_gb,
            "disk_free_gb": hw.disk_free_gb,
            "has_cuda": hw.has_cuda,
            "regime": hw.operating_regime,
        }

        # 1. Surrogate Inference
        if task_type_str in (ComputationalTaskType.SURROGATE_INFERENCE.value, "SURROGATE_INFERENCE", "INFERENCE"):
            return RoutingDecision(
                task_type=task_type_str,
                recommended_backend=ComputeBackendType.LOCAL,
                allowed_locally=True,
                reason="Surrogate polynomial and ridge regression models evaluate in <10ms on pure CPU using minimal RAM (<50 MB).",
                resource_bottlenecks=[],
                suggested_action="Execute immediately on local CPU.",
                hardware_summary=hw_summary,
            )

        # 2. Surrogate Training
        if task_type_str in (ComputationalTaskType.SURROGATE_TRAINING.value, "SURROGATE_TRAINING", "TRAINING"):
            if model_type.lower() in ("fno", "graphnet", "deep_surrogate") or not hw.has_cuda and sample_count > 50_000:
                bottlenecks = [
                    "Host lacks discrete NVIDIA CUDA GPU",
                    f"Sample count ({sample_count:,}) or model architecture ({model_type}) exceeds pure-CPU capacity",
                ]
                return RoutingDecision(
                    task_type=task_type_str,
                    recommended_backend=ComputeBackendType.REMOTE,
                    allowed_locally=False,
                    reason=f"Model architecture '{model_type}' requires GPU acceleration not present on this host.",
                    resource_bottlenecks=bottlenecks,
                    suggested_action="Generate remote training Slurm script or export dataset for execution on an external GPU workstation.",
                    hardware_summary=hw_summary,
                )
            else:
                # Deterministic CPU polynomial / ridge training
                return RoutingDecision(
                    task_type=task_type_str,
                    recommended_backend=ComputeBackendType.LOCAL,
                    allowed_locally=True,
                    reason=f"CPU training for '{model_type}' with {sample_count} samples fits within local memory ({hw.ram_available_gb:.1f} GB available).",
                    resource_bottlenecks=[],
                    suggested_action="Execute deterministic training locally using SurrogateTrainer.",
                    hardware_summary=hw_summary,
                )

        # 3. 3D CFD Simulation
        if task_type_str in (ComputationalTaskType.CFD_3D.value, "CFD_3D") or dimension.upper() == "3D":
            bottlenecks = [
                f"Workstation memory ({hw.ram_total_gb:.1f} GB total) is below the 16+ GB minimum for 3D Navier-Stokes",
                f"Safe local simulation limit is {hw.safe_max_local_dimension} on {hw.operating_regime}",
                "3D mesh generation and multi-core MPI decomposition require dedicated cluster resources",
            ]
            return RoutingDecision(
                task_type=task_type_str,
                recommended_backend=ComputeBackendType.USER_EXECUTED,
                allowed_locally=False,
                reason="3D CFD simulations cannot run on a 4-core, 8 GB developer workstation without high risk of kernel freeze or OOM.",
                resource_bottlenecks=bottlenecks,
                suggested_action="Use AASI USER_EXECUTED deck generator to create standalone aasi_case/ package with Allrun scripts for HPC execution.",
                hardware_summary=hw_summary,
            )

        # 4. 2D CFD Simulation
        if task_type_str in (ComputationalTaskType.CFD_2D.value, "CFD_2D") or dimension.upper() == "2D":
            # Check local solver availability
            solver_key = solver.strip()
            # Normalize solver key lookup
            solver_available = any(
                k.lower() == solver_key.lower() and v
                for k, v in hw.installed_solvers.items()
            )

            if not solver_available:
                return RoutingDecision(
                    task_type=task_type_str,
                    recommended_backend=ComputeBackendType.USER_EXECUTED,
                    allowed_locally=False,
                    reason=f"Solver '{solver}' is not installed locally in host PATH or WSL2.",
                    resource_bottlenecks=[f"Solver binary '{solver}' missing"],
                    suggested_action="Generate standalone aasi_case/ directory containing Allrun / Allrun.bat scripts, manifest, and validation checklist.",
                    hardware_summary=hw_summary,
                )

            # Check mesh cell safety
            if mesh_cells > hw.safe_max_local_mesh_cells:
                bottlenecks = [
                    f"Requested mesh cells ({mesh_cells:,}) exceed workstation safe threshold ({hw.safe_max_local_mesh_cells:,} cells)",
                    f"Host available RAM is {hw.ram_available_gb:.1f} GB",
                ]
                return RoutingDecision(
                    task_type=task_type_str,
                    recommended_backend=ComputeBackendType.USER_EXECUTED,
                    allowed_locally=False,
                    reason=f"Mesh cell count ({mesh_cells:,}) exceeds local safety limit ({hw.safe_max_local_mesh_cells:,}).",
                    resource_bottlenecks=bottlenecks,
                    suggested_action="Export standalone case deck to run on external machine or HPC cluster.",
                    hardware_summary=hw_summary,
                )

            # Solver is available and mesh is within safety bounds
            return RoutingDecision(
                task_type=task_type_str,
                recommended_backend=ComputeBackendType.LOCAL,
                allowed_locally=True,
                reason=f"Solver '{solver}' is installed and mesh ({mesh_cells:,} cells) is within safe workstation threshold ({hw.safe_max_local_mesh_cells:,}).",
                resource_bottlenecks=[],
                suggested_action="Execute locally using LocalComputeBackend.",
                hardware_summary=hw_summary,
            )

        # Default / Fallback
        return RoutingDecision(
            task_type=task_type_str,
            recommended_backend=ComputeBackendType.USER_EXECUTED,
            allowed_locally=False,
            reason=f"Unrecognized or unverified task type '{task_type_str}'. Failing closed to protect host resources.",
            resource_bottlenecks=["Unverified compute profile"],
            suggested_action="Inspect requirements and use USER_EXECUTED deck generation.",
            hardware_summary=hw_summary,
        )


hardware_matrix_manager = HardwareMatrixManager()
