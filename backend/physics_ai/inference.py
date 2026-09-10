"""
AASI Aerodynamic Surrogate Inference Engine.

Performs forward inference on trained AeroSurrogateV1:
- Loads checkpoint with cryptographic SHA-256 validation
- Processes airfoil coordinates (standard NACA or custom contour)
- Evaluates flow conditions (Mach, Reynolds, AoA)
- Calculates epistemic uncertainty and out-of-distribution (OOD) score
- Enforces aerodynamic sanity rules
- Supports single-point evaluation and full polar sweeps.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np

from backend.physics_ai.schemas import (
    AerodynamicPrediction,
    UncertaintyMetrics,
    DomainStatusEnum,
    AirfoilGeometryDefinition
)
from backend.physics_ai.models import AeroSurrogateV1
from backend.physics_ai.geometry import AirfoilGeometryProcessor
from backend.physics_ai.normalization import FlowConditionNormalizer, AerodynamicTargetScaler
from backend.physics_ai.uncertainty import EpistemicUncertaintyEngine
from backend.physics_ai.validation import PhysicsAwareValidator
from backend.physics_ai.checkpoints import CheckpointManager


class AerodynamicInferenceEngine:
    """Production inference engine for AeroSurrogateV1."""

    def __init__(self, checkpoint_path: Optional[str] = None):
        self.checkpoint_path = self._resolve_checkpoint_path(checkpoint_path)
        self.geometry_processor = AirfoilGeometryProcessor(target_points=64)
        self.known_geometries: Dict[str, np.ndarray] = {}
        self._load_known_geometries()
        self._load_model_and_normalizers()

    def _resolve_checkpoint_path(self, path: Optional[str]) -> Path:
        if path and Path(path).exists():
            return Path(path)
        candidates = [
            Path("data/checkpoints/aero_surrogate_v1.npz"),
            Path("data/training_runs/TR-AERO-SURROGATE-V1-001/checkpoints/aero_surrogate_v1.npz"),
        ]
        for c in candidates:
            if c.exists():
                return c
        # Default target
        return Path("data/checkpoints/aero_surrogate_v1.npz")

    def _load_known_geometries(self):
        geom_file = Path("data/datasets/authentic_airfoils/airfoil_geometries.json")
        if geom_file.exists():
            data = json.loads(geom_file.read_text(encoding="utf-8"))
            for name, g in data.items():
                pts = g.get("contour") or g.get("points") or (g.get("upper", []) + g.get("lower", []))
                coords, _ = self.geometry_processor.process_coordinates(pts, geometry_name=name)
                self.known_geometries[name.lower()] = coords

    def _load_model_and_normalizers(self):
        if not self.checkpoint_path.exists():
            # If checkpoint not found, initialize fresh model
            self.model = AeroSurrogateV1()
            self.condition_normalizer = FlowConditionNormalizer()
            self.target_scaler = AerodynamicTargetScaler()
            self.metadata = {}
            self.checksum = "UNINITIALIZED"
        else:
            ckpt_mgr = CheckpointManager()
            self.model, self.condition_normalizer, self.target_scaler, self.metadata, self.checksum = (
                ckpt_mgr.load_checkpoint(self.checkpoint_path)
            )

        # Build uncertainty engine with training conditions manifold
        train_cond_pts = self._build_training_manifold()
        self.uncertainty_engine = EpistemicUncertaintyEngine(
            training_conditions=train_cond_pts,
            validity_envelope={
                "mach": [0.05, 0.40],
                "reynolds": [5.0e5, 6.0e6],
                "aoa_deg": [-8.0, 18.0]
            }
        )

    def _build_training_manifold(self) -> np.ndarray:
        # Load authentic training polars to construct real training manifold in normalized space
        polars_file = Path("data/datasets/authentic_airfoils/airfoil_polars.json")
        if polars_file.exists():
            data = json.loads(polars_file.read_text(encoding="utf-8"))
            raw = []
            for s in data.get("samples", []):
                raw.append([s["mach"], s["reynolds"], s["aoa_deg"]])
            if raw:
                raw_arr = np.array(raw, dtype=np.float32)
                return self.condition_normalizer.transform(raw_arr)
        # Fallback grid
        grid = np.array([
            [0.1, 1e6, 0.0], [0.2, 2e6, 4.0], [0.3, 3e6, 8.0],
            [0.15, 1.5e6, -2.0], [0.25, 2.5e6, 12.0]
        ], dtype=np.float32)
        return self.condition_normalizer.transform(grid)

    def get_geometry_coordinates(
        self,
        geometry: Union[str, List[List[float]], np.ndarray]
    ) -> np.ndarray:
        """Resolves input geometry to [64, 2] normalized coordinates."""
        if isinstance(geometry, str):
            clean_name = geometry.strip().lower()
            if clean_name in self.known_geometries:
                return self.known_geometries[clean_name]
            # If NACA 4-digit formula
            if clean_name.startswith("naca") and len(clean_name) == 8 and clean_name[4:].isdigit():
                coords, _ = self.geometry_processor.generate_naca_4digit(clean_name[4:])
                return coords
            # Fallback to standard NACA 0012
            if "0012" in self.known_geometries:
                return self.known_geometries["0012"]
            coords, _ = self.geometry_processor.generate_naca_4digit("0012")
            return coords

        # Raw points list or array
        coords, _ = self.geometry_processor.process_coordinates(geometry)
        return coords

    def predict(
        self,
        geometry: Union[str, List[List[float]], np.ndarray],
        mach: float,
        reynolds: float,
        aoa_deg: float,
        fidelity_level: str = "SURROGATE"
    ) -> AerodynamicPrediction:
        """Executes a single aerodynamic point prediction with uncertainty quantification."""
        geom_coords = self.get_geometry_coordinates(geometry)  # [64, 2]
        geom_batch = geom_coords.reshape(1, 64, 2).astype(np.float32)

        raw_cond = np.array([[mach, reynolds, aoa_deg]], dtype=np.float32)
        norm_cond = self.condition_normalizer.transform(raw_cond)

        # Forward pass
        norm_pred = self.model.forward(geom_batch, norm_cond)
        phys_pred = self.target_scaler.inverse_transform(norm_pred)[0]

        cl_val = float(round(float(phys_pred[0]), 4))
        cd_val = float(round(max(0.003, float(phys_pred[1])), 5))
        cm_val = float(round(float(phys_pred[2]), 4))

        # Uncertainty evaluation
        domain_status, uncertainty = self.uncertainty_engine.evaluate_uncertainty(
            norm_cond=norm_cond[0],
            raw_mach=mach,
            raw_reynolds=reynolds,
            raw_aoa=aoa_deg
        )

        # Physics checks
        geom_str = geometry if isinstance(geometry, str) else "custom_airfoil"
        is_sym = any(s in geom_str.lower() for s in ["0012", "0009", "0006"])
        phys_check = PhysicsAwareValidator.validate_prediction(
            cl=cl_val, cd=cd_val, cm=cm_val, aoa_deg=aoa_deg, is_symmetric=is_sym
        )

        geom_name = geometry if isinstance(geometry, str) else "custom"

        return AerodynamicPrediction(
            geometry=geom_name,
            mach=round(mach, 4),
            reynolds=float(reynolds),
            aoa_deg=round(aoa_deg, 2),
            cl=cl_val,
            cd=cd_val,
            cm=cm_val,
            domain_status=domain_status,
            uncertainty=uncertainty,
            model_id=self.model.model_id,
            model_version=self.model.model_version,
            physics_checks=phys_check.get("checks", {}),
            provenance={"sha256_checksum": self.checksum, "physics_valid": phys_check["is_physically_valid"]}
        )


    def predict_polar(
        self,
        geometry: Union[str, List[List[float]], np.ndarray],
        mach: float,
        reynolds: float,
        aoa_start: float = -4.0,
        aoa_end: float = 14.0,
        aoa_step: float = 1.0
    ) -> Dict[str, Any]:
        """Calculates aerodynamic polar sweep over an angle of attack range."""
        aoas = np.arange(aoa_start, aoa_end + 0.1 * aoa_step, aoa_step).tolist()
        predictions: List[AerodynamicPrediction] = []

        cls = []
        cds = []
        cms = []

        for a in aoas:
            pred = self.predict(geometry, mach=mach, reynolds=reynolds, aoa_deg=float(a))
            predictions.append(pred)
            cls.append(pred.cl)
            cds.append(pred.cd)
            cms.append(pred.cm)

        geom_str = geometry if isinstance(geometry, str) else "custom"
        is_sym = any(s in geom_str.lower() for s in ["0012", "0009", "0006"])
        sweep_val = PhysicsAwareValidator.validate_polar_sweep(
            aoas=aoas, cls=cls, cds=cds, cms=cms, is_symmetric=is_sym
        )

        return {
            "geometry": geom_str,
            "mach": mach,
            "reynolds": reynolds,
            "sweep_validation": sweep_val,
            "points": [p.model_dump() for p in predictions],
            "model_id": self.model.model_id,
            "checksum": self.checksum,
        }
