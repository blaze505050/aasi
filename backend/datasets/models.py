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
    LICENSE_CHECKED = "LICENSE_CHECKED"
    DOWNLOADED = "DOWNLOADED"
    VALIDATED = "VALIDATED"
    NORMALIZED = "NORMALIZED"
    TRAINING_READY = "TRAINING_READY"
    TRAINED = "TRAINED"
    EVALUATED = "EVALUATED"
    DEPLOYED = "DEPLOYED"


class DataSplitType(str, Enum):
    GEOMETRY_LEVEL = "GEOMETRY_LEVEL"
    CONDITION_LEVEL = "CONDITION_LEVEL"
    OOD_EXTRAPOLATION = "OOD_EXTRAPOLATION"
    RANDOM_STRATIFIED = "RANDOM_STRATIFIED"


class StorageStatus(str, Enum):
    AVAILABLE_LOCAL = "AVAILABLE_LOCAL"
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
    citation: str
    url: str
    checksum: str  # SHA-256
    size_bytes: int
    domain: str = "AERODYNAMICS"
    geometry: str
    conditions: Dict[str, Any] = Field(default_factory=dict)
    variables: List[str] = Field(default_factory=list)
    units: Dict[str, str] = Field(default_factory=dict)
    resolution: str
    solver: Optional[str] = None
    experimental_or_simulated: str  # "EXPERIMENTAL" or "SIMULATED"
    validation_status: str = "VALIDATED"
    train_test_split: Dict[str, Any] = Field(default_factory=dict)
    known_limitations: List[str] = Field(default_factory=list)
    lifecycle_stage: DatasetLifecycle = DatasetLifecycle.DISCOVERED
    storage_status: StorageStatus = StorageStatus.AVAILABLE_REMOTE_DIRECT
    local_path: Optional[str] = None
    verified_byte_hash: Optional[str] = None
    sample_subset_available: bool = False
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
