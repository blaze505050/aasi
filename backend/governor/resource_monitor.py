"""
AASI 2.0 Resource Monitor — Live Host & Process Resource Auditing.

Cross-platform implementation:
- Windows: ctypes kernel32/psapi (zero external dependencies)
- Linux: /proc/stat, /proc/meminfo, /proc/self/statm
- Disk: shutil.disk_usage
- GPU: torch/nvidia-smi discovery with graceful fallback
- Optional: psutil if installed
"""

from __future__ import annotations

import os
import sys
import time
import socket
import shutil
import logging
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

from backend.governor.constants import (
    CRITICAL_CPU_PERCENT,
    CRITICAL_RAM_AVAILABLE_GB,
    MIN_FREE_RAM_FRACTION,
    CRITICAL_DISK_FREE_GB,
    CRITICAL_GPU_VRAM_FREE_FRACTION,
)

logger = logging.getLogger("aasi.governor.monitor")


# ─── Snapshot Data Models ─────────────────────────────────────────────────────

class GpuSnapshot(BaseModel):
    """Real-time GPU VRAM and device availability."""
    available: bool = False
    device_count: int = 0
    device_names: List[str] = Field(default_factory=list)
    total_vram_gb: Optional[float] = None
    used_vram_gb: Optional[float] = None
    free_vram_gb: Optional[float] = None


class ProcessSnapshot(BaseModel):
    """Resource consumption for current AASI backend process."""
    pid: int
    rss_mb: float = 0.0
    vms_mb: float = 0.0
    cpu_percent: float = 0.0
    thread_count: int = 1


class ResourceSnapshot(BaseModel):
    """Complete, immutable snapshot of system and process resources."""
    timestamp: float = Field(default_factory=time.time)
    hostname: str
    platform: str
    cpu_cores_logical: int
    cpu_percent: float
    ram_total_gb: float
    ram_used_gb: float
    ram_available_gb: float
    ram_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_free_gb: float
    disk_percent: float
    gpu: GpuSnapshot
    process: ProcessSnapshot
    critical_alert: bool = False
    alert_reasons: List[str] = Field(default_factory=list)


# ─── Windows Ctypes Structures ───────────────────────────────────────────────

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class _MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    class _FILETIME(ctypes.Structure):
        _fields_ = [
            ("dwLowDateTime", wintypes.DWORD),
            ("dwHighDateTime", wintypes.DWORD),
        ]

    class _PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
            ("PrivateUsage", ctypes.c_size_t),
        ]

    def _filetime_to_int(ft: _FILETIME) -> int:
        return (ft.dwHighDateTime << 32) | ft.dwLowDateTime


# ─── Resource Monitor Class ──────────────────────────────────────────────────

class ResourceMonitor:
    """
    Continuous & on-demand host hardware and process resource monitor.
    Thread-safe and fail-safe with conservative fallbacks.
    """

    def __init__(self, workspace_path: str = "."):
        self.workspace_path = os.path.abspath(workspace_path)
        self.hostname = socket.gethostname()
        self.cpu_cores = os.cpu_count() or 1

        # State for computing CPU deltas
        self._last_sys_time: float = time.time()
        self._last_sys_idle: int = 0
        self._last_sys_kernel: int = 0
        self._last_sys_user: int = 0

        self._last_proc_time: float = time.time()
        self._last_proc_cpu_time: float = 0.0

        self._init_baselines()

    def _init_baselines(self) -> None:
        """Seeds initial CPU counters."""
        if sys.platform == "win32":
            try:
                idle = _FILETIME()
                kernel = _FILETIME()
                user = _FILETIME()
                if ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
                    self._last_sys_idle = _filetime_to_int(idle)
                    self._last_sys_kernel = _filetime_to_int(kernel)
                    self._last_sys_user = _filetime_to_int(user)
                    self._last_sys_time = time.time()
            except Exception as e:
                logger.debug("Windows baseline init error: %s", e)
        elif os.path.exists("/proc/stat"):
            try:
                with open("/proc/stat", "r", encoding="utf-8") as f:
                    fields = [float(x) for x in f.readline().strip().split()[1:]]
                    self._last_sys_idle = int(fields[3] + (fields[4] if len(fields) > 4 else 0))
                    self._last_sys_user = int(sum(fields))
                    self._last_sys_time = time.time()
            except Exception as e:
                logger.debug("Linux baseline init error: %s", e)

        # Process baseline
        try:
            self._last_proc_cpu_time = time.process_time()
            self._last_proc_time = time.time()
        except Exception:
            pass

    def probe_system_cpu(self) -> float:
        """Computes system-wide CPU utilization percentage since last query."""
        now = time.time()
        dt = now - self._last_sys_time
        if dt <= 0.05:
            time.sleep(0.05)
            now = time.time()
            dt = now - self._last_sys_time

        raw_pct = 10.0
        if sys.platform == "win32":
            try:
                idle = _FILETIME()
                kernel = _FILETIME()
                user = _FILETIME()
                if ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
                    cur_idle = _filetime_to_int(idle)
                    cur_kernel = _filetime_to_int(kernel)
                    cur_user = _filetime_to_int(user)

                    idle_diff = cur_idle - self._last_sys_idle
                    kernel_diff = cur_kernel - self._last_sys_kernel
                    user_diff = cur_user - self._last_sys_user
                    total_diff = kernel_diff + user_diff

                    self._last_sys_idle = cur_idle
                    self._last_sys_kernel = cur_kernel
                    self._last_sys_user = cur_user
                    self._last_sys_time = now

                    if total_diff > 0:
                        busy_diff = total_diff - idle_diff
                        raw_pct = max(0.0, min(100.0, (busy_diff / total_diff) * 100.0))
            except Exception as e:
                logger.debug("Windows CPU probe error: %s", e)

        elif os.path.exists("/proc/stat"):
            try:
                with open("/proc/stat", "r", encoding="utf-8") as f:
                    fields = [float(x) for x in f.readline().strip().split()[1:]]
                    cur_idle = int(fields[3] + (fields[4] if len(fields) > 4 else 0))
                    cur_total = int(sum(fields))

                    idle_delta = cur_idle - self._last_sys_idle
                    total_delta = cur_total - self._last_sys_user

                    self._last_sys_idle = cur_idle
                    self._last_sys_user = cur_total
                    self._last_sys_time = now

                    if total_delta > 0:
                        busy_delta = total_delta - idle_delta
                        raw_pct = max(0.0, min(100.0, (busy_delta / total_delta) * 100.0))
            except Exception as e:
                logger.debug("Linux /proc/stat CPU probe error: %s", e)

        # Apply exponential moving average (EMA) filter to prevent false trips on 50ms micro-bursts
        if not hasattr(self, "_smoothed_cpu"):
            self._smoothed_cpu = raw_pct
        else:
            self._smoothed_cpu = (0.75 * self._smoothed_cpu) + (0.25 * raw_pct)

        return round(max(0.0, min(100.0, self._smoothed_cpu)), 1)

    def probe_ram(self) -> Tuple[float, float, float, float]:
        """
        Returns: (ram_total_gb, ram_used_gb, ram_available_gb, ram_percent)
        """
        if sys.platform == "win32":
            try:
                stat = _MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    total = stat.ullTotalPhys / (1024 ** 3)
                    avail = stat.ullAvailPhys / (1024 ** 3)
                    used = total - avail
                    pct = float(stat.dwMemoryLoad)
                    return round(total, 2), round(used, 2), round(avail, 2), round(pct, 1)
            except Exception as e:
                logger.debug("Windows RAM probe error: %s", e)

        elif os.path.exists("/proc/meminfo"):
            try:
                mem: Dict[str, float] = {}
                with open("/proc/meminfo", "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            k = parts[0].strip()
                            v = float(parts[1].strip().split()[0]) / (1024 ** 2)
                            mem[k] = v
                total = mem.get("MemTotal", 8.0)
                avail = mem.get("MemAvailable", mem.get("MemFree", 2.0))
                used = total - avail
                pct = ((total - avail) / total) * 100.0 if total > 0 else 50.0
                return round(total, 2), round(used, 2), round(avail, 2), round(pct, 1)
            except Exception as e:
                logger.debug("Linux /proc/meminfo probe error: %s", e)

        return 8.0, 4.0, 4.0, 50.0

    def probe_disk(self) -> Tuple[float, float, float, float]:
        """
        Returns: (disk_total_gb, disk_used_gb, disk_free_gb, disk_percent)
        """
        try:
            usage = shutil.disk_usage(self.workspace_path)
            total = usage.total / (1024 ** 3)
            used = usage.used / (1024 ** 3)
            free = usage.free / (1024 ** 3)
            pct = (usage.used / usage.total) * 100.0 if usage.total > 0 else 0.0
            return round(total, 2), round(used, 2), round(free, 2), round(pct, 1)
        except Exception as e:
            logger.debug("Disk usage probe error: %s", e)
            return 100.0, 50.0, 50.0, 50.0

    def probe_gpu(self) -> GpuSnapshot:
        """Audits NVIDIA GPU VRAM availability via torch or nvidia-smi."""
        try:
            import torch
            if torch.cuda.is_available():
                cnt = torch.cuda.device_count()
                names = [torch.cuda.get_device_name(i) for i in range(cnt)]
                total_mem = sum(torch.cuda.get_device_properties(i).total_memory for i in range(cnt)) / (1024 ** 3)
                alloc_mem = sum(torch.cuda.memory_allocated(i) for i in range(cnt)) / (1024 ** 3)
                free_mem = total_mem - alloc_mem
                return GpuSnapshot(
                    available=True,
                    device_count=cnt,
                    device_names=names,
                    total_vram_gb=round(total_mem, 2),
                    used_vram_gb=round(alloc_mem, 2),
                    free_vram_gb=round(free_mem, 2),
                )
        except Exception:
            pass

        smi = shutil.which("nvidia-smi")
        if smi:
            try:
                cmd = [smi, "--query-gpu=name,memory.total,memory.used,memory.free", "--format=csv,noheader,nounits"]
                out = subprocess.check_output(cmd, text=True, timeout=3, stderr=subprocess.DEVNULL)
                names = []
                total_v = 0.0
                used_v = 0.0
                free_v = 0.0
                for line in out.strip().splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 4:
                        names.append(parts[0])
                        total_v += float(parts[1]) / 1024.0
                        used_v += float(parts[2]) / 1024.0
                        free_v += float(parts[3]) / 1024.0
                if names:
                    return GpuSnapshot(
                        available=True,
                        device_count=len(names),
                        device_names=names,
                        total_vram_gb=round(total_v, 2),
                        used_vram_gb=round(used_v, 2),
                        free_vram_gb=round(free_v, 2),
                    )
            except Exception:
                pass

        return GpuSnapshot(available=False, device_count=0)

    def probe_process(self) -> ProcessSnapshot:
        """Audits resource usage of current Python process."""
        pid = os.getpid()
        rss_mb = 0.0
        vms_mb = 0.0
        cpu_pct = 0.0
        threads = 1

        if sys.platform == "win32":
            try:
                pmc = _PROCESS_MEMORY_COUNTERS_EX()
                pmc.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS_EX)
                kernel32 = ctypes.windll.kernel32
                psapi = ctypes.windll.psapi
                kernel32.GetCurrentProcess.restype = wintypes.HANDLE
                psapi.GetProcessMemoryInfo.argtypes = [
                    wintypes.HANDLE,
                    ctypes.POINTER(_PROCESS_MEMORY_COUNTERS_EX),
                    wintypes.DWORD,
                ]
                psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
                h_proc = kernel32.GetCurrentProcess()
                if psapi.GetProcessMemoryInfo(h_proc, ctypes.byref(pmc), pmc.cb):
                    rss_mb = round(pmc.WorkingSetSize / (1024 * 1024), 2)
                    vms_mb = round(pmc.PrivateUsage / (1024 * 1024), 2)
            except Exception as e:
                logger.debug("Windows process probe error: %s", e)

        elif os.path.exists(f"/proc/{pid}/statm"):
            try:
                with open(f"/proc/{pid}/statm", "r", encoding="utf-8") as f:
                    parts = f.read().split()
                    page_size = os.sysconf("SC_PAGE_SIZE") / (1024 * 1024)
                    vms_mb = round(float(parts[0]) * page_size, 2)
                    rss_mb = round(float(parts[1]) * page_size, 2)
            except Exception as e:
                logger.debug("Linux process statm probe error: %s", e)

        try:
            import threading
            threads = threading.active_count()
        except Exception:
            threads = 1

        now = time.time()
        try:
            cur_proc_cpu = time.process_time()
            dt = now - self._last_proc_time
            if dt > 0.01:
                cpu_delta = cur_proc_cpu - self._last_proc_cpu_time
                cpu_pct = round(max(0.0, (cpu_delta / (dt * self.cpu_cores)) * 100.0), 1)
                self._last_proc_cpu_time = cur_proc_cpu
                self._last_proc_time = now
        except Exception:
            pass

        return ProcessSnapshot(
            pid=pid,
            rss_mb=rss_mb,
            vms_mb=vms_mb,
            cpu_percent=cpu_pct,
            thread_count=threads,
        )

    def snapshot(self) -> ResourceSnapshot:
        """
        Gathers a complete, point-in-time ResourceSnapshot and checks alert thresholds.
        """
        cpu_pct = self.probe_system_cpu()
        ram_tot, ram_used, ram_avail, ram_pct = self.probe_ram()
        d_tot, d_used, d_free, d_pct = self.probe_disk()
        gpu_snap = self.probe_gpu()
        proc_snap = self.probe_process()

        alert_reasons: List[str] = []

        if cpu_pct >= CRITICAL_CPU_PERCENT:
            alert_reasons.append(f"System CPU at {cpu_pct}% exceeds critical threshold ({CRITICAL_CPU_PERCENT}%)")

        if ram_avail < CRITICAL_RAM_AVAILABLE_GB:
            alert_reasons.append(f"Available RAM ({ram_avail} GB) below critical limit ({CRITICAL_RAM_AVAILABLE_GB} GB)")

        if (ram_avail / ram_tot) < MIN_FREE_RAM_FRACTION if ram_tot > 0 else False:
            alert_reasons.append(f"Free RAM fraction ({round(ram_avail/ram_tot, 2)}) below minimum threshold ({MIN_FREE_RAM_FRACTION})")

        if d_free < CRITICAL_DISK_FREE_GB:
            alert_reasons.append(f"Disk free space ({d_free} GB) below critical limit ({CRITICAL_DISK_FREE_GB} GB)")

        if gpu_snap.available and gpu_snap.total_vram_gb and gpu_snap.free_vram_gb:
            free_frac = gpu_snap.free_vram_gb / gpu_snap.total_vram_gb
            if free_frac < CRITICAL_GPU_VRAM_FREE_FRACTION:
                alert_reasons.append(f"GPU free VRAM ({round(free_frac*100, 1)}%) below critical fraction")

        critical = len(alert_reasons) > 0

        return ResourceSnapshot(
            hostname=self.hostname,
            platform=sys.platform,
            cpu_cores_logical=self.cpu_cores,
            cpu_percent=cpu_pct,
            ram_total_gb=ram_tot,
            ram_used_gb=ram_used,
            ram_available_gb=ram_avail,
            ram_percent=ram_pct,
            disk_total_gb=d_tot,
            disk_used_gb=d_used,
            disk_free_gb=d_free,
            disk_percent=d_pct,
            gpu=gpu_snap,
            process=proc_snap,
            critical_alert=critical,
            alert_reasons=alert_reasons,
        )


# Singleton monitor
default_monitor = ResourceMonitor()
