"""
AASI 2.0 Runtime Governor — Task Resource Estimator.
"""

from __future__ import annotations

from typing import Dict, Any
from backend.governor.resource_budget import ResourceBudget


class ResourceEstimator:
    """Estimates worst-case CPU, RAM, and wall time for aerodynamic tasks."""

    TOOL_ESTIMATES = {
        "aero_2d_solve": {"ram_gb": 0.05, "timeout_seconds": 15},
        "aero_3d_vlm": {"ram_gb": 0.08, "timeout_seconds": 20},
        "polar_sweep": {"ram_gb": 0.12, "timeout_seconds": 60},
        "uncertainty_quantify": {"ram_gb": 0.03, "timeout_seconds": 5},
        "benchmark_verify": {"ram_gb": 0.08, "timeout_seconds": 30},
        "geometry_parse": {"ram_gb": 0.04, "timeout_seconds": 10},
        "export_datcom": {"ram_gb": 0.08, "timeout_seconds": 30},
        "export_shabp": {"ram_gb": 0.08, "timeout_seconds": 30},
        "mesh_generate": {"ram_gb": 0.05, "timeout_seconds": 10},
    }

    @classmethod
    def estimate(cls, tool_name: str) -> ResourceBudget:
        est = cls.TOOL_ESTIMATES.get(tool_name, {"ram_gb": 0.25, "timeout_seconds": 120})
        return ResourceBudget(
            max_ram_gb=est["ram_gb"],
            max_timeout_seconds=est["timeout_seconds"],
        )
