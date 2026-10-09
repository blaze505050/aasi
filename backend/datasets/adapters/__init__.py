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
from backend.datasets.adapters.tmr2d import NASATMR2DDatasetAdapter
from backend.datasets.adapters.authentic_airfoils import AuthenticAirfoilsDatasetAdapter
from backend.datasets.adapters.universal import UniversalAerospaceDatasetAdapter


__all__ = [
    "DatasetAdapter",
    "DatasetCase",
    "DatasetField",
    "DatasetStorageState",
    "StorageRequirementReport",
    "NACA0012DatasetAdapter",
    "AirfRANSDatasetAdapter",
    "NASATMR2DDatasetAdapter",
    "AuthenticAirfoilsDatasetAdapter",
    "UniversalAerospaceDatasetAdapter",
]


