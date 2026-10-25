"""
AASI 2.0 System Capabilities — Live Resource Sampler.
"""

from __future__ import annotations

from typing import Dict, Any
from backend.governor.resource_monitor import default_monitor, ResourceSnapshot


class ResourceSampler:
    """Provides high-frequency and scheduled sampling of workstation resources."""

    @classmethod
    def sample_live(cls) -> ResourceSnapshot:
        return default_monitor.snapshot()

    @classmethod
    def sample_dict(cls) -> Dict[str, Any]:
        return default_monitor.snapshot().model_dump()
