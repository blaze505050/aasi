"""
AASI Dataset Loader and In-Memory Scientific Dataset.

Loads curated aerodynamic airfoil geometries and polars, builds structured
tensors, maintains immutable provenance records per sample, and feeds PyTorch/NumPy.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

try:
    import torch
    from torch.utils.data import Dataset
    HAS_TORCH = True
except Exception:
    HAS_TORCH = False
    class Dataset:
        """Fallback base dataset class when PyTorch is not available."""
        pass

from backend.physics_ai.schemas import AirfoilSample
from backend.physics_ai.geometry import AirfoilGeometryProcessor
from backend.physics_ai.normalization import FlowConditionNormalizer, AerodynamicTargetScaler


class AerodynamicAirfoilDataset(Dataset):
    """Dataset holding aerodynamic samples with geometry and flow conditions."""

    def __init__(
        self,
        samples: List[AirfoilSample],
        geometries: Dict[str, Any],
        coords_points: int = 64,
        fit_normalizers: bool = False,
        condition_normalizer: Optional[FlowConditionNormalizer] = None,
        target_scaler: Optional[AerodynamicTargetScaler] = None,
    ):
        self.samples = samples
        self.geometries = geometries
        self.coords_points = coords_points
        self.geometry_processor = AirfoilGeometryProcessor(target_points=coords_points)

        # Precompute processed coordinates for each unique geometry
        self.geom_tensors: Dict[str, np.ndarray] = {}
        for name, gdata in geometries.items():
            pts = gdata.get("contour") or gdata.get("points") or (gdata.get("upper", []) + gdata.get("lower", []))
            resampled, _ = self.geometry_processor.process_coordinates(pts, geometry_name=name)
            self.geom_tensors[name] = resampled.astype(np.float32)

        # Extract conditions matrix [N, 3] and targets matrix [N, 3]
        n = len(samples)
        self.raw_conditions = np.zeros((n, 3), dtype=np.float32)
        self.raw_targets = np.zeros((n, 3), dtype=np.float32)
        self.sample_geoms: List[str] = []

        for i, s in enumerate(samples):
            self.raw_conditions[i, 0] = s.mach
            self.raw_conditions[i, 1] = s.reynolds
            self.raw_conditions[i, 2] = s.aoa_deg

            self.raw_targets[i, 0] = s.cl
            self.raw_targets[i, 1] = s.cd
            self.raw_targets[i, 2] = s.cm
            self.sample_geoms.append(s.geometry)

        # Set up normalizers
        if condition_normalizer is not None:
            self.condition_normalizer = condition_normalizer
        else:
            self.condition_normalizer = FlowConditionNormalizer()
            if fit_normalizers:
                self.condition_normalizer.fit(self.raw_conditions)

        if target_scaler is not None:
            self.target_scaler = target_scaler
        else:
            self.target_scaler = AerodynamicTargetScaler()
            if fit_normalizers:
                self.target_scaler.fit(self.raw_targets)

        # Scaled arrays
        self.norm_conditions = self.condition_normalizer.transform(self.raw_conditions)
        self.norm_targets = self.target_scaler.transform(self.raw_targets)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        s = self.samples[idx]
        geom_name = s.geometry
        geom_coords = self.geom_tensors.get(
            geom_name, np.zeros((self.coords_points, 2), dtype=np.float32)
        )

        if HAS_TORCH:
            return {
                "geom_coords": torch.tensor(geom_coords, dtype=torch.float32),  # [64, 2]
                "condition": torch.tensor(self.norm_conditions[idx], dtype=torch.float32),  # [3]
                "target": torch.tensor(self.norm_targets[idx], dtype=torch.float32),  # [3]
                "raw_condition": torch.tensor(self.raw_conditions[idx], dtype=torch.float32),
                "raw_target": torch.tensor(self.raw_targets[idx], dtype=torch.float32),
                "sample_id": s.sample_id,
                "geometry": geom_name,
                "provenance_hash": s.provenance_hash,
            }
        return {
            "geom_coords": geom_coords.astype(np.float32),
            "condition": self.norm_conditions[idx].astype(np.float32),
            "target": self.norm_targets[idx].astype(np.float32),
            "raw_condition": self.raw_conditions[idx].astype(np.float32),
            "raw_target": self.raw_targets[idx].astype(np.float32),
            "sample_id": s.sample_id,
            "geometry": geom_name,
            "provenance_hash": s.provenance_hash,
        }

    @classmethod
    def load_from_directory(
        cls,
        data_dir: str = "data/datasets/authentic_airfoils",
        fit_normalizers: bool = True
    ) -> "AerodynamicAirfoilDataset":
        """Loads dataset from authentic_airfoils JSON files."""
        p = Path(data_dir)
        geom_path = p / "airfoil_geometries.json"
        polars_path = p / "airfoil_polars.json"

        if not geom_path.exists() or not polars_path.exists():
            raise FileNotFoundError(f"Authentic dataset files not found in '{data_dir}'.")

        geometries = json.loads(geom_path.read_text(encoding="utf-8"))
        polar_data = json.loads(polars_path.read_text(encoding="utf-8"))
        raw_samples = polar_data.get("samples", [])

        samples = [AirfoilSample(**s) for s in raw_samples]
        return cls(samples, geometries, fit_normalizers=fit_normalizers)
