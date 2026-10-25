"""
AASI 2.0 System Capabilities — Formatted Markdown & Structured Report Exporter.
"""

from __future__ import annotations

from typing import Dict, Any
from backend.system_capabilities.discovery import SystemCapabilityDiscoverer
from backend.system_capabilities.models import SystemCapabilityReport


class CapabilityReportGenerator:
    """Generates structured JSON and formatted markdown capability reports."""

    @classmethod
    def generate_report(cls) -> SystemCapabilityReport:
        return SystemCapabilityDiscoverer.generate_report()

    @classmethod
    def generate_markdown(cls) -> str:
        rep = cls.generate_report()
        lines = [
            f"# AASI Workstation Capability Report",
            f"**Host**: {rep.platform.hostname} ({rep.platform.os_name} {rep.platform.architecture})",
            f"**Python**: {rep.platform.python_version} | **WSL**: {rep.platform.is_wsl}",
            f"",
            f"### Compute Resources",
            f"- **CPU**: {rep.cpu.logical_cores} logical cores ({rep.cpu.physical_cores} physical)",
            f"- **RAM**: {rep.memory.total_ram_gb} GB total, {rep.memory.available_ram_gb} GB available ({rep.memory.load_percent}% load)",
            f"- **Disk**: {rep.storage.workspace_disk_free_gb} GB free / {rep.storage.workspace_disk_total_gb} GB total",
            f"- **GPU**: {rep.gpu.device_names[0] if rep.gpu.available and rep.gpu.device_names else 'None (CPU fallback)'}",
            f"",
            f"### Scientific Solvers",
            f"- **OpenFOAM**: {'Available (' + (rep.solvers.openfoam_location or '') + ')' if rep.solvers.has_openfoam else 'Not in PATH'}",
            f"- **CUDA**: {'Available' if rep.solvers.has_cuda else 'Not Detected'}",
            f"- **MPI**: {'Available' if rep.solvers.has_mpi else 'Not Detected'}",
        ]
        return "\n".join(lines)
