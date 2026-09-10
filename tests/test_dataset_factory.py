"""
Tests for AASI Scientific Dataset Factory and Leakage-Free Data Splitting.
"""

import os
import pytest
from backend.datasets.catalog import DatasetCatalog
from backend.datasets.split import GeometryLevelSplitter, OODSplitter
from backend.datasets.download import DownloadManager
from backend.datasets.validate import DatasetValidator
from backend.datasets.quality import QualityManager
from backend.datasets.models import DatasetManifest, DataSplitType


def test_dataset_catalog_manifests():
    """Verifies that the dataset catalog registers open physics datasets with SHA-256 hashes."""
    catalog = DatasetCatalog()
    manifests = catalog.list_manifests()
    assert len(manifests) >= 3

    airfrans = catalog.get_manifest("DATASET-AIRFRANS-1K")
    assert airfrans is not None
    assert airfrans.solver == "OpenFOAM (simpleFoam)"
    assert len(airfrans.checksum) == 64
    assert airfrans.conditions["mach_range"] == [0.15, 0.30]

    crm = catalog.get_manifest("DATASET-NASA-CRM-TRANSONIC")
    assert crm is not None
    assert crm.conditions["mach"] == 0.85


def test_geometry_level_splitter_zero_leakage():
    """
    Verifies that GeometryLevelSplitter eliminates data leakage across airfoils:
    an airfoil's data points must NEVER appear in both train and test.
    """
    # Sample dataset with multiple conditions per airfoil
    samples = []
    airfoils = [f"NACA {i:04d}" for i in range(10)]
    for af in airfoils:
        for aoa in [-4, 0, 4, 8, 12]:
            samples.append({"geometry": af, "aoa": aoa, "cl": 0.1 * aoa, "cd": 0.008})

    train, test, res = GeometryLevelSplitter.split(samples, train_ratio=0.7, seed=42)

    assert len(train) > 0
    assert len(test) > 0
    assert res.leakage_check_passed is True

    train_geoms = set(res.train_geometries)
    test_geoms = set(res.test_geometries)

    # Strictly zero intersection
    assert len(train_geoms.intersection(test_geoms)) == 0
    for s in train:
        assert s["geometry"] not in test_geoms
    for s in test:
        assert s["geometry"] not in train_geoms


def test_ood_splitter_extrapolation():
    """Verifies that OODSplitter properly partitions in-domain vs extrapolation sets."""
    samples = [
        {"geometry": "NACA 0012", "mach": 0.2},
        {"geometry": "NACA 0012", "mach": 0.3},
        {"geometry": "NACA 0012", "mach": 0.4},
        {"geometry": "NACA 0012", "mach": 0.6},
        {"geometry": "NACA 0012", "mach": 0.7},
    ]
    train, test, res = OODSplitter.split_ood(
        samples,
        condition_key="mach",
        in_domain_range=(0.1, 0.45),
        ood_range=(0.55, 0.8)
    )
    assert len(train) == 3
    assert len(test) == 2
    for s in train:
        assert s["mach"] <= 0.45
    for s in test:
        assert s["mach"] >= 0.55


def test_download_manager_hardware_guardrail():
    """Verifies that DownloadManager blocks downloads exceeding developer machine quotas."""
    manager = DownloadManager(cache_dir="data/test_dl")
    # Giant dataset (24.5 GB)
    giant_manifest = DatasetManifest(
        dataset_id="GIANT-CFD-DATASET",
        name="Giant 24GB Dataset",
        source="External",
        license="CC-BY-4.0",
        citation="Citation",
        url="https://example.com/giant.tar.gz",
        checksum="abcd"*16,
        size_bytes=24_500_000_000,
        domain="AERODYNAMICS",
        geometry="Generic",
        resolution="Fine",
        experimental_or_simulated="SIMULATED"
    )

    res = manager.download_dataset(giant_manifest)
    assert res["success"] is False
    assert "exceeds local developer machine quota" in res["error"]


def test_dataset_validator_aerodynamic_sanity():
    """Tests that DatasetValidator catches unphysical aerodynamic values."""
    valid_sample = {"mach": 0.3, "reynolds": 1e6, "cl": 0.5, "cd": 0.008}
    is_valid, errs = DatasetValidator.validate_aerodynamic_sample(valid_sample)
    assert is_valid is True
    assert len(errs) == 0

    invalid_sample = {"mach": -0.1, "reynolds": 0, "cl": 6.2, "cd": -0.01}
    is_valid, errs = DatasetValidator.validate_aerodynamic_sample(invalid_sample)
    assert is_valid is False
    assert len(errs) >= 3  # negative Mach, zero Re, excessive Cl, negative Cd


def test_quality_manager_deduplication():
    """Tests deduplication on flow condition keys."""
    samples = [
        {"geometry": "NACA 0012", "mach": 0.15, "aoa": 4.0, "cd": 0.0076},
        {"geometry": "NACA 0012", "mach": 0.15, "aoa": 4.0, "cd": 0.0076},  # duplicate
        {"geometry": "NACA 0012", "mach": 0.15, "aoa": 6.0, "cd": 0.0092},
    ]
    deduped, count = QualityManager.deduplicate(samples, key_fields=["geometry", "mach", "aoa"])
    assert count == 1
    assert len(deduped) == 2
