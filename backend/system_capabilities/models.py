"""
AASI 2.0 System Capabilities — Structured Data Models.

Defines typed schemas for workstation discovery, resource sampling,
and capability reporting.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from backend.governor.resource_monitor import GpuSnapshot, ProcessSnapshot, ResourceSnapshot


class HostPlatformInfo(BaseModel):
    hostname: str
    os_name: str
    os_version: str
    architecture: str
    python_version: str
    node_version: Optional[str] = None
    git_version: Optional[str] = None
    is_wsl: bool = False
    wsl_distributions: List[str] = Field(default_factory=list)


class CpuCapabilities(BaseModel):
    logical_cores: int
    physical_cores: int
    model_name: Optional[str] = None
    current_utilization_pct: float = 0.0


class MemoryCapabilities(BaseModel):
    total_ram_gb: float
    available_ram_gb: float
    used_ram_gb: float
    load_percent: float


class StorageCapabilities(BaseModel):
    workspace_disk_total_gb: float
    workspace_disk_free_gb: float
    workspace_disk_used_gb: float
    free_percent: float


class SolverAvailability(BaseModel):
    has_openfoam: bool = False
    openfoam_version: Optional[str] = None
    openfoam_location: Optional[str] = None  # NATIVE, WSL, NONE
    supported_solvers: List[str] = Field(default_factory=list)
    has_cuda: bool = False
    cuda_device_name: Optional[str] = None
    cuda_vram_gb: Optional[float] = None
    has_mpi: bool = False
    mpi_runtime: Optional[str] = None


class SystemCapabilityReport(BaseModel):
    """Authoritative, immutable report of host hardware and software capabilities."""
    timestamp_utc: float = Field(default_factory=time.time)
    platform: HostPlatformInfo
    cpu: CpuCapabilities
    memory: MemoryCapabilities
    storage: StorageCapabilities
    gpu: GpuSnapshot
    solvers: SolverAvailability
    process: ProcessSnapshot
    confidence_level: float = 1.0
    detection_limitations: List[str] = Field(default_factory=list)
