"""
AASI Feature Extractor for Physics-AI Surrogates.

Combines resampled geometry coordinates with normalized flow conditions
into structured feature tensors for neural network inference and training.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from backend.physics_ai.geometry import AirfoilGeometryProcessor
from backend.physics_ai.normalization import FlowConditionNormalizer


class AerodynamicFeatureExtractor:
    """Extracts combined geometry and flow condition feature vectors."""

    def __init__(self, target_coords_points: int = 64):
        self.geometry_processor = AirfoilGeometryProcessor(target_points=target_coords_points)
        self.condition_normalizer = FlowConditionNormalizer()

    def extract_features(
        self,
        coords: List[List[float]],
        mach: float,
        reynolds: float,
        aoa_deg: float,
        geometry_name: str = "custom_airfoil"
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Extracts:
        - geom_vector: [64, 2] resampled coordinates (flattened or 2D)
        - cond_vector: [3] normalized [Mach, log10(Re), AoA]
        - meta: dict with thickness, camber, quality flags
        """
        resampled, geo_features = self.geometry_processor.process_coordinates(
            coords, geometry_name=geometry_name
        )

        raw_cond = np.array([mach, reynolds, aoa_deg], dtype=np.float32)
        norm_cond = self.condition_normalizer.transform(raw_cond.reshape(1, -1)).flatten()

        metadata = {
            "geometry_name": geometry_name,
            "max_thickness": geo_features.max_thickness_ratio,
            "max_camber": geo_features.max_camber_ratio,
            "is_symmetric": geo_features.is_symmetric,
            "quality_flags": geo_features.quality_flags,
        }

        return resampled, norm_cond, metadata
