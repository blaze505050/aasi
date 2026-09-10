"""
AASI Compute Backend Models.

Defines execution backends, simulation requests, job descriptors,
and artifact ingestion payloads.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ComputeBackendType(str, Enum):
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"
    USER_EXECUTED = "USER_EXECUTED"
    CACHED = "CACHED"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    AWAITING_USER_UPLOAD = "AWAITING_USER_UPLOAD"


class ComputeRequest(BaseModel):
    case_id: str
    geometry: str = "NACA 0012"
    solver: str = "openfoam"
    backend: ComputeBackendType = ComputeBackendType.USER_EXECUTED
    mach: float = 0.15
    reynolds: float = 3000000.0
    aoa_deg: float = 4.0
    turbulence_model: str = "k-omega SST"
    mesh_parameters: Dict[str, Any] = Field(default_factory=lambda: {"cells": 125000, "y_plus": 0.85})
    additional_settings: Dict[str, Any] = Field(default_factory=dict)


class GeneratedCaseDeck(BaseModel):
    case_id: str
    geometry: str
    solver: str
    case_directory: str
    readme_path: str
    manifest_path: str
    validation_checklist_path: str
    script_paths: List[str]
    file_hashes: Dict[str, str]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UploadedArtifactPayload(BaseModel):
    case_id: str
    solver: str = "openfoam"
    file_name: str
    file_content: str  # text log or base64
    conditions: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestionResult(BaseModel):
    case_id: str
    status: str
    solver: str
    converged: bool
    iterations: int = 0
    residuals: Dict[str, float] = Field(default_factory=dict)
    coefficients: Dict[str, float] = Field(default_factory=dict)
    provenance_hash: str
    validation_status: str
    validation_notes: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

