"""
AASI 2.0 System Capabilities — Host Discovery Engine.

Performs safe, read-only discovery of workstation hardware, runtimes, and solvers.
Never elevates privileges, never mutates system configuration, and never runs stress tests.
"""

from __future__ import annotations

import os
import sys
import shutil
import socket
import platform
import subprocess
import logging
from typing import Optional, List, Tuple

from runner.detector.capabilities import probe_ram_gb, probe_cuda, probe_mpi, probe_openfoam
from backend.governor.resource_monitor import default_monitor
from backend.system_capabilities.models import (
    HostPlatformInfo,
    CpuCapabilities,
    MemoryCapabilities,
    StorageCapabilities,
    SolverAvailability,
    SystemCapabilityReport,
)

logger = logging.getLogger("aasi.capabilities.discovery")


class SystemCapabilityDiscoverer:
    """Discovers host hardware and software environment safely."""

    @classmethod
    def probe_platform(cls) -> HostPlatformInfo:
        hostname = socket.gethostname()
        py_ver = sys.version.split()[0]
        arch = platform.machine()
        os_name = sys.platform
        os_ver = platform.version()

        # Node check
        node_ver = None
        if shutil.which("node"):
            try:
                out = subprocess.check_output(["node", "--version"], text=True, timeout=2, stderr=subprocess.DEVNULL)
                node_ver = out.strip()
            except Exception:
                pass

        # Git check
        git_ver = None
        if shutil.which("git"):
            try:
                out = subprocess.check_output(["git", "--version"], text=True, timeout=2, stderr=subprocess.DEVNULL)
                git_ver = out.strip()
            except Exception:
                pass

        # WSL check
        is_wsl = False
        wsl_distros: List[str] = []
        if sys.platform == "win32" and shutil.which("wsl"):
            is_wsl = True
            try:
                out = subprocess.check_output(["wsl", "-l", "-q"], text=True, timeout=3, stderr=subprocess.DEVNULL)
                wsl_distros = [line.strip().replace("\x00", "") for line in out.splitlines() if line.strip()]
            except Exception:
                pass

        return HostPlatformInfo(
            hostname=hostname,
            os_name=os_name,
            os_version=os_ver,
            architecture=arch,
            python_version=py_ver,
            node_version=node_ver,
            git_version=git_ver,
            is_wsl=is_wsl,
            wsl_distributions=wsl_distros,
        )

    @classmethod
    def probe_cpu(cls) -> CpuCapabilities:
        logical = os.cpu_count() or 1
        util_pct = default_monitor.probe_system_cpu()
        model_name = platform.processor() or "Generic x86_64"
        return CpuCapabilities(
            logical_cores=logical,
            physical_cores=max(1, logical // 2) if sys.platform == "win32" else logical,
            model_name=model_name,
            current_utilization_pct=util_pct,
        )

    @classmethod
    def probe_memory(cls) -> MemoryCapabilities:
        total, used, avail, pct = default_monitor.probe_ram()
        return MemoryCapabilities(
            total_ram_gb=total,
            available_ram_gb=avail,
            used_ram_gb=used,
            load_percent=pct,
        )

    @classmethod
    def probe_storage(cls, workspace_path: str = ".") -> StorageCapabilities:
        total, used, free, pct = default_monitor.probe_disk()
        free_pct = round(100.0 - pct, 1)
        return StorageCapabilities(
            workspace_disk_total_gb=total,
            workspace_disk_free_gb=free,
            workspace_disk_used_gb=used,
            free_percent=free_pct,
        )

    @classmethod
    def probe_solvers(cls) -> SolverAvailability:
        has_of, of_ver, of_solvers = probe_openfoam()
        has_cuda, cuda_name, cuda_mem = probe_cuda()
        has_mpi, mpi_ver = probe_mpi()

        location = "NONE"
        if has_of:
            location = "WSL" if "WSL" in (of_ver or "") else "NATIVE"

        return SolverAvailability(
            has_openfoam=has_of,
            openfoam_version=of_ver,
            openfoam_location=location,
            supported_solvers=of_solvers,
            has_cuda=has_cuda,
            cuda_device_name=cuda_name,
            cuda_vram_gb=cuda_mem,
            has_mpi=has_mpi,
            mpi_runtime=mpi_ver,
        )

    @classmethod
    def generate_report(cls, workspace_path: str = ".") -> SystemCapabilityReport:
        platform_info = cls.probe_platform()
        cpu = cls.probe_cpu()
        memory = cls.probe_memory()
        storage = cls.probe_storage(workspace_path)
        solvers = cls.probe_solvers()
        gpu = default_monitor.probe_gpu()
        process = default_monitor.probe_process()

        limitations = []
        if not solvers.has_cuda:
            limitations.append("NVIDIA CUDA GPU not detected; GPU-accelerated neural operators must use CPU fallback.")
        if not solvers.has_openfoam:
            limitations.append("Native OpenFOAM solver not in PATH; CFD cases must be staged for WSL or Colab.")
        if memory.available_ram_gb < 1.0:
            limitations.append(f"Low available RAM ({memory.available_ram_gb} GB); memory budget strictly capped at 250 MB.")

        return SystemCapabilityReport(
            platform=platform_info,
            cpu=cpu,
            memory=memory,
            storage=storage,
            gpu=gpu,
            solvers=solvers,
            process=process,
            confidence_level=0.98,
            detection_limitations=limitations,
        )
