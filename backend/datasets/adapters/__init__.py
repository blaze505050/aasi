"""
AASI Multi-Dataset Adapters Package.
"""

from backend.datasets.adapters.base import (
    DatasetAdapter,
    DatasetCase,
    DatasetField,
    DatasetStorageState,
    StorageRequirementReport,
)
from backend.datasets.adapters.naca0012 import NACA0012DatasetAdapter
from backend.datasets.adapters.airfrans import AirfRANSDatasetAdapter

__all__ = [
    "DatasetAdapter",
    "DatasetCase",
    "DatasetField",
    "DatasetStorageState",
    "StorageRequirementReport",
    "NACA0012DatasetAdapter",
    "AirfRANSDatasetAdapter",
]
