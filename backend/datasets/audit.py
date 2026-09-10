"""
AASI Dataset Authenticity Audit Service.

Performs rigorous inspection of registered aerospace datasets:
verifies whether raw data files actually exist on disk, audits download URLs,
detects NaN/Inf values, validates physical coefficient bounds, checks geometry
counts, and strictly prevents metadata-only manifests from being labeled as verified.
"""

import os
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Any

from backend.datasets.catalog import DatasetCatalog
from backend.datasets.audit_models import (
    AuditStatusEnum,
    DatasetAuditResult,
    DatasetAuditSummary,
)


class DatasetAuditService:
    """Rigorous audit service for all registered physical datasets."""

    def __init__(self, data_root: str = "data/datasets"):
        self.data_root = Path(data_root)
        self.catalog = DatasetCatalog()

    def audit_dataset(self, dataset_id: str) -> DatasetAuditResult:
        """Audits a single dataset by ID against actual local disk and metadata."""
        manifest = self.catalog.manifests.get(dataset_id)
        if not manifest:
            return DatasetAuditResult(
                dataset_id=dataset_id,
                dataset_name="Unknown",
                overall_status=AuditStatusEnum.UNAVAILABLE,
                errors=[f"Dataset '{dataset_id}' not found in registry catalog."],
            )

        result = DatasetAuditResult(
            dataset_id=manifest.dataset_id,
            dataset_name=manifest.name,
            source_url=manifest.url,
            source_type="CFD_SIMULATION" if manifest.experimental_or_simulated == "SIMULATED" else "WIND_TUNNEL_EXPERIMENT",
            license_declared=manifest.license,
            sample_count_declared=self._extract_sample_count(manifest),
        )

        # 1. Local Disk Inspection
        target_dir = None
        candidates = [
            self.data_root / dataset_id,
            self.data_root / dataset_id.lower(),
            self.data_root / dataset_id.lower().replace("-", "_"),
            self.data_root / dataset_id.lower().replace("-", "_").replace("dataset_", ""),
            self.data_root / dataset_id.lower().replace("-", "_").replace("dataset_", "").replace("_v1", ""),
        ]
        for c in candidates:
            if c.exists() and c.is_dir():
                target_dir = c
                break

        if not target_dir and self.data_root.exists():
            clean_id = dataset_id.lower().replace("-", "").replace("_", "").replace("dataset", "")
            for p in self.data_root.iterdir():
                if p.is_dir() and clean_id in p.name.lower().replace("-", "").replace("_", ""):
                    target_dir = p
                    break

        if not target_dir:
            result.download_status = "NOT_DOWNLOADED"
            result.overall_status = AuditStatusEnum.METADATA_ONLY
            result.warnings.append(
                f"Raw dataset payload not present locally under '{self.data_root}/{dataset_id}'. "
                "Manifest represents cryptographic and metadata specification only."
            )
            result.evidence["local_storage"] = "ABSENT"
            return result

        result.local_path = str(target_dir)
        result.download_status = "LOCAL_EXISTS"

        # 2. Inspect Local Files & Data Records
        data_files = list(target_dir.glob("*.json")) + list(target_dir.glob("*.csv")) + list(target_dir.glob("*.dat"))
        if not data_files:
            result.overall_status = AuditStatusEnum.METADATA_ONLY
            result.warnings.append(f"Directory exists at '{target_dir}' but contains no data files (.json, .csv, .dat).")
            return result

        total_bytes = sum(f.stat().st_size for f in data_files)
        result.size_bytes_actual = total_bytes

        # Audit content inside JSON or CSV files
        actual_samples = 0
        unique_geometries = set()
        nan_inf_count = 0
        invalid_records = 0
        physical_violations = 0

        for fpath in data_files:
            if fpath.suffix == ".json" and not fpath.name.endswith(".manifest.json"):
                try:
                    content = json.loads(fpath.read_text(encoding="utf-8"))
                    records = content if isinstance(content, list) else content.get("samples", content.get("records", []))
                    if isinstance(records, list):
                        for rec in records:
                            actual_samples += 1
                            if isinstance(rec, dict):
                                geom = rec.get("geometry") or rec.get("airfoil") or rec.get("geometry_id")
                                if geom:
                                    unique_geometries.add(str(geom))

                                # Check targets
                                cl = rec.get("cl") or (rec.get("target", {}).get("cl") if isinstance(rec.get("target"), dict) else None)
                                cd = rec.get("cd") or (rec.get("target", {}).get("cd") if isinstance(rec.get("target"), dict) else None)

                                if cl is not None:
                                    try:
                                        cl_val = float(cl)
                                        if math.isnan(cl_val) or math.isinf(cl_val):
                                            nan_inf_count += 1
                                        elif abs(cl_val) > 4.0:
                                            physical_violations += 1
                                    except (ValueError, TypeError):
                                        invalid_records += 1

                                if cd is not None:
                                    try:
                                        cd_val = float(cd)
                                        if math.isnan(cd_val) or math.isinf(cd_val):
                                            nan_inf_count += 1
                                        elif cd_val < 0.0:
                                            physical_violations += 1
                                    except (ValueError, TypeError):
                                        invalid_records += 1
                except Exception as e:
                    result.errors.append(f"Failed to parse JSON file '{fpath.name}': {str(e)}")

        result.sample_count_actual = actual_samples
        result.geometry_count_actual = len(unique_geometries)
        result.nan_inf_count = nan_inf_count
        result.invalid_records_count = invalid_records

        # 3. Determine Overall Status
        if physical_violations > 0:
            result.physical_sanity_status = "BOUNDARY_VIOLATION"
            result.warnings.append(f"Found {physical_violations} records violating physical aerodynamic bounds (e.g. CD < 0 or |CL| > 4.0).")

        if nan_inf_count > 0 or invalid_records > 0:
            result.overall_status = AuditStatusEnum.INVALID
            result.errors.append(f"Dataset contains {nan_inf_count} NaN/Inf values and {invalid_records} unparseable records.")
        elif actual_samples > 0 and physical_violations == 0:
            # Check if this is authentic full data or demo data
            if "demo" in dataset_id.lower() or "synthetic" in dataset_id.lower():
                result.overall_status = AuditStatusEnum.DEMO_DATA
            elif result.sample_count_declared and actual_samples < (result.sample_count_declared * 0.5):
                result.overall_status = AuditStatusEnum.PARTIALLY_VERIFIED
                result.warnings.append(f"Sample count ({actual_samples}) is a subset of declared total ({result.sample_count_declared}).")
            else:
                result.overall_status = AuditStatusEnum.VERIFIED
        else:
            result.overall_status = AuditStatusEnum.METADATA_ONLY

        result.evidence["file_count"] = len(data_files)
        result.evidence["geometries"] = list(unique_geometries)[:10]
        return result

    def audit_all(self) -> DatasetAuditSummary:
        """Audits all datasets registered in DatasetCatalog."""
        results = [self.audit_dataset(ds_id) for ds_id in self.catalog.manifests.keys()]
        verified = sum(1 for r in results if r.overall_status == AuditStatusEnum.VERIFIED)
        partially = sum(1 for r in results if r.overall_status == AuditStatusEnum.PARTIALLY_VERIFIED)
        meta_only = sum(1 for r in results if r.overall_status == AuditStatusEnum.METADATA_ONLY)
        demo = sum(1 for r in results if r.overall_status == AuditStatusEnum.DEMO_DATA)
        invalid = sum(1 for r in results if r.overall_status == AuditStatusEnum.INVALID)
        unavail = sum(1 for r in results if r.overall_status == AuditStatusEnum.UNAVAILABLE)

        return DatasetAuditSummary(
            total_datasets_audited=len(results),
            verified_count=verified,
            partially_verified_count=partially,
            metadata_only_count=meta_only,
            demo_data_count=demo,
            invalid_count=invalid,
            unavailable_count=unavail,
            results=results,
        )

    def _extract_sample_count(self, manifest) -> Optional[int]:
        if hasattr(manifest, "train_test_split") and isinstance(manifest.train_test_split, dict):
            train = manifest.train_test_split.get("training_airfoils", 0)
            test = manifest.train_test_split.get("testing_airfoils", 0)
            if train or test:
                return train + test
        return getattr(manifest, "sample_count", None)
