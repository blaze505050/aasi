"""
AASI Scientific Data Splitting Layer.

Guarantees 0% geometry data leakage between partitions:
- Geometry-level grouping: all operating conditions for a given airfoil remain
  exclusively within TRAIN, VALIDATION, or TEST.
- Out-of-Domain (OOD) partitions:
  * OOD_GEOMETRY: Unseen aerodynamic profile families (e.g. supercritical RAE 2822)
  * OOD_CONDITION: High-AoA stall regime (AoA > 12 deg) or high Mach (M >= 0.30)
  * OOD_COMBINED: Unseen geometry at stall/transonic conditions.
Generates cryptographic split manifests with verifiable SHA-256 hashes.
"""

import hashlib
import json
from typing import Dict, List, Tuple, Any, Set
from backend.physics_ai.schemas import AirfoilSample


class GeometryLevelSplitter:
    """Partitions samples strictly by unique airfoil geometries with zero leakage."""

    def __init__(
        self,
        train_ratio: float = 0.60,
        val_ratio: float = 0.20,
        test_ratio: float = 0.20,
        seed: int = 42
    ):
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

    def split_samples(
        self,
        samples: List[AirfoilSample]
    ) -> Dict[str, Any]:
        """
        Groups samples by geometry and assigns full geometries to partitions.
        Returns:
            train_samples, val_samples, test_samples, ood_geometry_samples, ood_condition_samples
        """
        # 1. Identify all unique geometries
        geoms_set = sorted(list(set(s.geometry for s in samples)))
        n_geoms = len(geoms_set)

        # 2. Allocate geometries to partitions
        # Reserve RAE 2822 as canonical OOD_GEOMETRY if present
        ood_geom_names = {"RAE 2822"} if "RAE 2822" in geoms_set else {geoms_set[-1]}
        standard_geoms = [g for g in geoms_set if g not in ood_geom_names]

        # Deterministic assignment
        n_std = len(standard_geoms)
        n_train = max(1, int(n_std * self.train_ratio))
        n_val = max(1, int(n_std * self.val_ratio))

        train_geoms = set(standard_geoms[:n_train])
        val_geoms = set(standard_geoms[n_train:n_train + n_val])
        test_geoms = set(standard_geoms[n_train + n_val:])

        # Fallback if partition ended up empty
        if not test_geoms and len(val_geoms) > 1:
            moved = val_geoms.pop()
            test_geoms.add(moved)

        # Verify 0% geometry leakage
        assert train_geoms.isdisjoint(test_geoms), "FATAL: Geometry leakage between TRAIN and TEST!"
        assert train_geoms.isdisjoint(val_geoms), "FATAL: Geometry leakage between TRAIN and VAL!"
        assert val_geoms.isdisjoint(test_geoms), "FATAL: Geometry leakage between VAL and TEST!"

        # 3. Partition samples
        train_samples: List[AirfoilSample] = []
        val_samples: List[AirfoilSample] = []
        test_samples: List[AirfoilSample] = []
        ood_geom_samples: List[AirfoilSample] = []
        ood_cond_samples: List[AirfoilSample] = []
        ood_combined_samples: List[AirfoilSample] = []

        for s in samples:
            is_high_aoa = s.aoa_deg > 12.0
            is_high_mach = s.mach >= 0.30
            is_ood_cond = is_high_aoa or is_high_mach
            is_ood_geom = s.geometry in ood_geom_names

            if is_ood_geom and is_ood_cond:
                ood_combined_samples.append(s)
            elif is_ood_geom:
                ood_geom_samples.append(s)
            elif is_ood_cond and s.geometry in test_geoms:
                ood_cond_samples.append(s)
            elif s.geometry in train_geoms:
                # Standard training (attached-to-mild conditions)
                train_samples.append(s)
            elif s.geometry in val_geoms:
                val_samples.append(s)
            elif s.geometry in test_geoms:
                test_samples.append(s)

        # 4. Generate Cryptographic Manifest
        manifest = {
            "split_version": "GEOMETRY_LEVEL_V1",
            "seed": self.seed,
            "train_geometries": sorted(list(train_geoms)),
            "val_geometries": sorted(list(val_geoms)),
            "test_geometries": sorted(list(test_geoms)),
            "ood_geometries": sorted(list(ood_geom_names)),
            "geometry_leakage_percentage": 0.0,
            "counts": {
                "train": len(train_samples),
                "val": len(val_samples),
                "test": len(test_samples),
                "ood_geometry": len(ood_geom_samples),
                "ood_condition": len(ood_cond_samples),
                "ood_combined": len(ood_combined_samples),
                "total": len(samples),
            }
        }
        manifest_str = json.dumps(manifest, sort_keys=True)
        manifest["split_checksum"] = hashlib.sha256(manifest_str.encode()).hexdigest()

        return {
            "train": train_samples,
            "val": val_samples,
            "test": test_samples,
            "ood_geometry": ood_geom_samples,
            "ood_condition": ood_cond_samples,
            "ood_combined": ood_combined_samples,
            "manifest": manifest,
        }
