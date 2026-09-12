"""
AASI Multi-Dataset Abstraction Layer.

Defines the core abstract interfaces, storage states, case schemas,
and disk safety reporting required for multi-dataset CFD benchmarking.
"""

from __future__ import annotations

import shutil
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.datasets.models import DatasetManifest, DatasetLifecycle, StorageStatus


class DatasetStorageState(str, Enum):
    """Reflects local workstation storage status for CFD datasets."""
    DATASET_METADATA_ONLY = "DATASET_METADATA_ONLY"
    DATASET_PARTIAL = "DATASET_PARTIAL"
    DATASET_FULL = "DATASET_FULL"
    RESOURCE_LIMITED = "RESOURCE_LIMITED"


class DatasetField(BaseModel):
    """Metadata for a physical field or target in a dataset."""
    field_name: str
    field_type: str = "SCALAR"  # SCALAR, VECTOR_2D, VECTOR_3D, TENSOR
    units: str
    is_input: bool = True
    is_surface_field: bool = False
    min_physical_bound: Optional[float] = None
    max_physical_bound: Optional[float] = None
    description: str = ""


class DatasetCase(BaseModel):
    """Standardized representation of a single CFD simulation or experiment case."""
    case_id: str
    dataset_id: str
    geometry_name: str
    reynolds: float
    mach: float
    aoa_deg: float
    cl: Optional[float] = None
    cd: Optional[float] = None
    cm: Optional[float] = None
    has_field_data: bool = False
    node_count: Optional[int] = None
    provenance_hash: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class StorageRequirementReport(BaseModel):
    """Storage feasibility analysis against workstation capacity."""
    dataset_id: str
    storage_state: DatasetStorageState
    estimated_compressed_bytes: int
    estimated_uncompressed_bytes: int
    available_disk_bytes: int
    safety_threshold_bytes: int = 15_000_000_000  # Leave at least 15 GB free
    is_safe_for_download: bool
    recommendation: str


class DatasetAdapter(ABC):
    """Abstract base class for aerodynamic dataset adapters."""

    @abstractmethod
    def get_dataset_id(self) -> str:
        """Unique identifier of the dataset (e.g. 'DATASET-AIRFRANS-1K')."""
        pass

    @abstractmethod
    def get_manifest(self) -> DatasetManifest:
        """Returns standard DatasetManifest."""
        pass

    @abstractmethod
    def get_storage_state(self) -> DatasetStorageState:
        """Returns current storage state (DATASET_METADATA_ONLY, DATASET_PARTIAL, etc.)."""
        pass

    @abstractmethod
    def get_fields(self) -> List[DatasetField]:
        """Returns declared input and output physical fields."""
        pass

    @abstractmethod
    def list_cases(self, limit: int = 100, offset: int = 0) -> List[DatasetCase]:
        """Lists metadata for available or indexed cases."""
        pass

    @abstractmethod
    def get_case(self, case_id: str) -> Optional[DatasetCase]:
        """Retrieves a specific case by ID."""
        pass

    @abstractmethod
    def get_available_splits(self) -> Dict[str, List[str]]:
        """Returns map of split_name -> list of case_ids."""
        pass

    def check_storage_safety(self, path: str = ".") -> StorageRequirementReport:
        """Evaluates whether downloading full dataset would compromise host disk."""
        manifest = self.get_manifest()
        compressed_bytes = manifest.size_bytes
        uncompressed_bytes = int(compressed_bytes * 1.75)  # typical CFD zip expansion ratio
        
        try:
            total, used, free = shutil.disk_usage(os.path.abspath(path))
        except Exception:
            free = 20_000_000_000  # Fallback default 20 GB
            
        safety_threshold = 15_000_000_000  # 15 GB reserve required
        is_safe = (free - uncompressed_bytes) > safety_threshold
        
        if not is_safe:
            state = DatasetStorageState.RESOURCE_LIMITED
            recommendation = (
                f"Full dataset ({uncompressed_bytes / 1e9:.1f} GB uncompressed) exceeds safety reserve "
                f"on {free / 1e9:.1f} GB available disk. Enforcing {DatasetStorageState.RESOURCE_LIMITED.value} / "
                f"{DatasetStorageState.DATASET_METADATA_ONLY.value}."
            )
        else:
            state = DatasetStorageState.DATASET_METADATA_ONLY
            recommendation = "Storage check passed. Sufficient capacity for full dataset ingestion."

        return StorageRequirementReport(
            dataset_id=self.get_dataset_id(),
            storage_state=state,
            estimated_compressed_bytes=compressed_bytes,
            estimated_uncompressed_bytes=uncompressed_bytes,
            available_disk_bytes=free,
            safety_threshold_bytes=safety_threshold,
            is_safe_for_download=is_safe,
            recommendation=recommendation
        )
