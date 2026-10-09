"""
AASI Host Capability Detector.
Audits workstation resources (CPU, RAM, disk, CUDA, MPI, Python, OpenFOAM binaries)
and packages them into a verifiable RunnerCapabilities structure.
"""

from __future__ import annotations

import os
import sys
import shutil
import socket
import logging
import subprocess
from typing import Dict, List, Optional, Tuple

from runner.protocol.models import RunnerCapabilities

logger = logging.getLogger("aasi.runner.detector")


def probe_ram_gb() -> Tuple[float, float]:
    """Probes total and available physical RAM in GB."""
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
                total = round(stat.ullTotalPhys / (1024 ** 3), 2)
                avail = round(stat.ullAvailPhys / (1024 ** 3), 2)
                return total, avail
        except Exception as exc:
            logger.debug("Windows ctypes RAM probe failed: %s", exc)

    if os.path.exists("/proc/meminfo"):
        try:
            mem_info: Dict[str, float] = {}
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().split()[0]
                        mem_info[key] = float(val) / (1024 ** 2)
            total = round(mem_info.get("MemTotal", 8.0), 2)
            avail = round(mem_info.get("MemAvailable", 2.0), 2)
            return total, avail
        except Exception as exc:
            logger.debug("/proc/meminfo probe failed: %s", exc)

    return 8.0, 2.0


def probe_cuda() -> Tuple[bool, Optional[str], Optional[float]]:
    """Probes CUDA availability, device name, and memory."""
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            mem = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2)
            return True, name, mem
    except Exception:
        pass

    # Fallback to nvcc check
    nvcc = shutil.which("nvcc")
    if nvcc:
        return True, "NVIDIA CUDA (nvcc detected)", None

    return False, None, None


def probe_mpi() -> Tuple[bool, Optional[str]]:
    """Probes MPI runtime availability."""
    for exe in ["mpirun", "mpiexec"]:
        path = shutil.which(exe)
        if path:
            try:
                out = subprocess.check_output([exe, "--version"], text=True, timeout=5, stderr=subprocess.STDOUT)
                first_line = out.strip().splitlines()[0] if out else "MPI runtime"
                return True, first_line
            except Exception:
                return True, "MPI runtime detected"
    return False, None


def probe_openfoam() -> Tuple[bool, Optional[str], List[str]]:
    """
    Probes OpenFOAM solvers in host PATH or via WSL2.
    Returns: (is_available, version_string, supported_solvers_list)
    """
    solvers = ["simpleFoam", "pimpleFoam", "rhoSimpleFoam", "blockMesh", "checkMesh", "foamToVTK"]
    found_solvers: List[str] = []

    for s in solvers:
        if shutil.which(s):
            found_solvers.append(s)

    version_str: Optional[str] = None
    if found_solvers:
        try:
            cmd = [found_solvers[0], "-help"]
            out = subprocess.check_output(cmd, text=True, timeout=5, stderr=subprocess.STDOUT)
            for line in out.splitlines():
                if "Version:" in line or "OpenFOAM" in line:
                    version_str = line.strip()
                    break
        except Exception:
            version_str = "OpenFOAM native binary"
        return True, version_str or "OpenFOAM", found_solvers

    # Check via WSL2 if on Windows
    if sys.platform == "win32" and shutil.which("wsl"):
        try:
            res = subprocess.run(["wsl", "which", "simpleFoam"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                found_solvers.append("simpleFoam")
                for s in solvers[1:]:
                    r = subprocess.run(["wsl", "which", s], capture_output=True, text=True, timeout=3)
                    if r.returncode == 0:
                        found_solvers.append(s)
                return True, "OpenFOAM (WSL2)", found_solvers
        except Exception:
            pass

    return False, None, []


class HostCapabilityDetector:
    """Executes capability probes and constructs a RunnerCapabilities object."""

    @classmethod
    def detect(cls, runner_id: Optional[str] = None) -> RunnerCapabilities:
        hostname = socket.gethostname()
        rid = runner_id or f"RUNNER-{hostname}-{os.getpid()}"

        total_ram, avail_ram = probe_ram_gb()
        has_cuda, cuda_name, cuda_mem = probe_cuda()
        has_mpi, mpi_ver = probe_mpi()
        has_of, of_ver, supported_solvers = probe_openfoam()

        try:
            disk_free = round(shutil.disk_usage(".").free / (1024 ** 3), 2)
        except Exception:
            disk_free = 10.0

        is_wsl2 = False
        if sys.platform != "win32":
            is_wsl2 = os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop") or "microsoft" in os.uname().release.lower()
        else:
            is_wsl2 = (shutil.which("wsl") is not None)

        cpu_logical = os.cpu_count() or 1

        return RunnerCapabilities(
            runner_id=rid,
            host_name=hostname,
            os_platform=sys.platform,
            is_wsl2=is_wsl2,
            python_version=sys.version.split()[0],
            cpu_cores_logical=cpu_logical,
            cpu_cores_physical=cpu_logical,
            ram_total_gb=total_ram,
            ram_available_gb=avail_ram,
            disk_free_gb=disk_free,
            has_cuda=has_cuda,
            cuda_device_name=cuda_name,
            cuda_memory_gb=cuda_mem,
            has_mpi=has_mpi,
            mpi_version=mpi_ver,
            openfoam_available=has_of,
            openfoam_version=of_ver,
            supported_solvers=supported_solvers,
        )
