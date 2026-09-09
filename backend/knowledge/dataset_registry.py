"""Dataset registry providing structured catalogs and condition-based search for aerodynamic, CFD, and flight data."""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List, Optional, Tuple
from .models import CFDClassification, CFDDataModel, Dataset, Provenance, ScientificObjectType


class DatasetRegistry:
    """Registry managing physical aerospace datasets, CFD benchmarks, and experimental measurements."""

    def __init__(self):
        self._datasets: Dict[str, Dataset] = {}

    def register(self, dataset: Dataset):
        """Register a dataset into the registry."""
        self._datasets[dataset.dataset_id] = dataset

    def get(self, dataset_id: str) -> Optional[Dataset]:
        """Retrieve dataset by ID."""
        return self._datasets.get(dataset_id)

    def list_datasets(
        self, domain: Optional[str] = None, geometry: Optional[str] = None
    ) -> List[Dataset]:
        """List datasets with optional filtering by physical domain or geometry."""
        results = list(self._datasets.values())
        if domain:
            results = [d for d in results if d.physical_domain.lower() == domain.lower()]
        if geometry:
            results = [d for d in results if geometry.lower() in d.geometry.lower()]
        return results

    def query_conditions(
        self,
        geometry: str,
        mach: Optional[float] = None,
        reynolds: Optional[float] = None,
        aoa_deg: Optional[float] = None,
        domain: str = "aerodynamics",
        tolerance_mach: float = 0.05,
        tolerance_reynolds_rel: float = 0.25,
        tolerance_aoa: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Search registered datasets for data points or benchmarks matching physical conditions.

        Returns matching entries with exact data point values, uncertainty bounds, and provenance.
        Never fabricates values outside of registered experimental or simulation data.
        """
        matches: List[Dict[str, Any]] = []

        for d_id, ds in self._datasets.items():
            if domain and ds.physical_domain.lower() != domain.lower():
                continue

            # Geometry check (e.g. NACA 0012)
            clean_geo = geometry.lower().replace(" ", "").replace("-", "")
            ds_geo = ds.geometry.lower().replace(" ", "").replace("-", "")
            if clean_geo not in ds_geo and ds_geo not in clean_geo:
                continue

            # Check macro conditions of the dataset
            conds = ds.conditions or {}
            ds_mach = conds.get("Mach") or conds.get("mach")
            ds_re = conds.get("Reynolds") or conds.get("reynolds")

            if mach is not None and ds_mach is not None:
                if abs(float(ds_mach) - float(mach)) > tolerance_mach:
                    continue

            if reynolds is not None and ds_re is not None:
                rel_diff = abs(float(ds_re) - float(reynolds)) / float(reynolds)
                if rel_diff > tolerance_reynolds_rel:
                    continue

            # Search data_points table if available
            matched_points: List[Dict[str, Any]] = []
            for pt in ds.data_points:
                pt_aoa = pt["aoa"] if "aoa" in pt else (pt["alpha"] if "alpha" in pt else pt.get("aoa_deg"))
                pt_mach = pt["mach"] if "mach" in pt else ds_mach
                pt_re = pt["reynolds"] if "reynolds" in pt else ds_re

                aoa_match = True
                if aoa_deg is not None and pt_aoa is not None:
                    if abs(float(pt_aoa) - float(aoa_deg)) > tolerance_aoa:
                        aoa_match = False

                mach_match = True
                if mach is not None and pt_mach is not None:
                    if abs(float(pt_mach) - float(mach)) > tolerance_mach:
                        mach_match = False

                re_match = True
                if reynolds is not None and pt_re is not None:
                    if abs(float(pt_re) - float(reynolds)) / float(reynolds) > tolerance_reynolds_rel:
                        re_match = False

                if aoa_match and mach_match and re_match:
                    matched_points.append(pt)

            if matched_points:
                matches.append({
                    "dataset_id": ds.dataset_id,
                    "dataset_name": ds.name,
                    "geometry": ds.geometry,
                    "source": ds.source,
                    "is_experimental": ds.is_experimental,
                    "validation_status": ds.validation_status,
                    "citation": ds.citation,
                    "conditions": ds.conditions,
                    "uncertainty": ds.uncertainty,
                    "matched_points": matched_points,
                    "checksum": ds.checksum,
                })
            elif aoa_deg is None and (mach is not None or reynolds is not None):
                # Dataset conditions match overall, even if specific aoa wasn't queried
                matches.append({
                    "dataset_id": ds.dataset_id,
                    "dataset_name": ds.name,
                    "geometry": ds.geometry,
                    "source": ds.source,
                    "is_experimental": ds.is_experimental,
                    "validation_status": ds.validation_status,
                    "citation": ds.citation,
                    "conditions": ds.conditions,
                    "uncertainty": ds.uncertainty,
                    "matched_points": ds.data_points[:5],
                    "checksum": ds.checksum,
                })

        return matches
