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
    # Official 11-stage acquisition contract:
    DISCOVERED = "DISCOVERED"
    LICENSE_VERIFIED = "LICENSE_VERIFIED"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    DOWNLOAD_REQUESTED = "DOWNLOAD_REQUESTED"
    DOWNLOADED = "DOWNLOADED"
    HASH_VERIFIED = "HASH_VERIFIED"
    PARSED = "PARSED"
    SCHEMA_VALIDATED = "SCHEMA_VALIDATED"
    PHYSICS_VALIDATED = "PHYSICS_VALIDATED"
    SPLIT_VALIDATED = "SPLIT_VALIDATED"
    READY_FOR_TRAINING = "READY_FOR_TRAINING"
    FAILED = "FAILED"

    # Backward compatibility aliases
    LICENSE_CHECKED = "LICENSE_VERIFIED"
    VALIDATED = "PHYSICS_VALIDATED"
    SPLIT = "SPLIT_VALIDATED"
    TRAINING_READY = "READY_FOR_TRAINING"
    DEPLOYED = "READY_FOR_TRAINING"


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
    REMOTE_DATASET_AVAILABLE = "REMOTE_DATASET_AVAILABLE"
    LOCAL_DATASET_NOT_ACQUIRED = "LOCAL_DATASET_NOT_ACQUIRED"
    DEGRADED_SAMPLE_ONLY = "DEGRADED_SAMPLE_ONLY"
    MISSING_AUTHENTIC_SOURCE = "MISSING_AUTHENTIC_SOURCE"


class AcquisitionTransition(BaseModel):
    """Immutable transition record in the 11-stage dataset acquisition contract."""
    transition_id: str
    dataset_id: str
    from_stage: DatasetLifecycle
    to_stage: DatasetLifecycle
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor: str = "AASI_ACQUISITION_ENGINE"
    gate_checks_passed: Dict[str, bool] = Field(default_factory=dict)
    provenance_hash: str = ""
    notes: str = ""


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
