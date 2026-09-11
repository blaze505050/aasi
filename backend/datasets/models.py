"""
AASI Scientific Dataset Models.

Defines DatasetLifecycle, DataSplitType, and DatasetManifest schemas
governing high-value aerospace simulation and experimental datasets.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class DatasetLifecycle(str, Enum):
    DISCOVERED = "DISCOVERED"
    LICENSE_VERIFIED = "LICENSE_VERIFIED"
    LICENSE_CHECKED = "LICENSE_VERIFIED"  # alias for backward compat
    DOWNLOADED = "DOWNLOADED"
    HASH_VERIFIED = "HASH_VERIFIED"
    PARSED = "PARSED"
    VALIDATED = "VALIDATED"
    SPLIT = "SPLIT"
    READY_FOR_TRAINING = "READY_FOR_TRAINING"
    TRAINING_READY = "READY_FOR_TRAINING"  # alias for backward compat
    DEPLOYED = "READY_FOR_TRAINING"  # alias for backward compat
    FAILED = "FAILED"


class DataSplitType(str, Enum):
    GEOMETRY_LEVEL = "GEOMETRY_LEVEL"
    CONDITION_LEVEL = "CONDITION_LEVEL"
    OOD_EXTRAPOLATION = "OOD_EXTRAPOLATION"
    RANDOM_STRATIFIED = "RANDOM_STRATIFIED"


class StorageStatus(str, Enum):
    AVAILABLE_LOCAL = "AVAILABLE_LOCAL"
    LOCAL = "AVAILABLE_LOCAL"  # alias
    AVAILABLE_REMOTE_DIRECT = "AVAILABLE_REMOTE_DIRECT"
    AVAILABLE_REMOTE_MANUAL = "AVAILABLE_REMOTE_MANUAL"
    DEGRADED_SAMPLE_ONLY = "DEGRADED_SAMPLE_ONLY"
    MISSING_AUTHENTIC_SOURCE = "MISSING_AUTHENTIC_SOURCE"


class DatasetManifest(BaseModel):
    dataset_id: str
    name: str
    version: str = "1.0.0"
    source: str
    license: str
    citation: str = "AASI Scientific Verified Benchmark"
    url: str = ""
    checksum: str = ""  # SHA-256
    size_bytes: int = 0
    domain: str = "AERODYNAMICS"
    geometry: str = "NACA 0012"
    conditions: Dict[str, Any] = Field(default_factory=dict)
    variables: List[str] = Field(default_factory=list)
    units: Dict[str, str] = Field(default_factory=dict)
    resolution: str = "Standard"
    solver: Optional[str] = None
    experimental_or_simulated: str = "EXPERIMENTAL"
    validation_status: str = "VALIDATED"
    train_test_split: Dict[str, Any] = Field(default_factory=dict)
    known_limitations: List[str] = Field(default_factory=list)
    lifecycle_stage: DatasetLifecycle = DatasetLifecycle.DISCOVERED
    storage_status: StorageStatus = StorageStatus.AVAILABLE_REMOTE_DIRECT
    local_path: Optional[str] = None
    verified_byte_hash: Optional[str] = None
    sample_subset_available: bool = False
    transition_history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DataSplitResult(BaseModel):
    split_type: DataSplitType
    train_count: int
    val_count: int
    test_count: int
    train_geometries: List[str] = Field(default_factory=list)
    test_geometries: List[str] = Field(default_factory=list)
    ood_conditions: Dict[str, Any] = Field(default_factory=dict)
    leakage_check_passed: bool = True
