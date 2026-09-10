"""
AASI Feature and Target Normalization.

Provides explicit, transparent, and reversible scaling for flow conditions
(Mach, Reynolds, AoA) and aerodynamic targets (CL, CD, CM).
Ensures CD (order ~0.008) has commensurate gradients to CL (order ~0.5)
without hidden transformations.
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Any, Optional


class FlowConditionNormalizer:
    """Standardizes input condition vectors [Mach, log10(Reynolds), AoA]."""

    def __init__(self):
        # Defaults based on subsonic/transonic aerodynamics envelope
        self.mean_ = np.array([0.20, 6.30, 4.0], dtype=np.float32)   # Mach ~0.20, Re ~2e6, AoA ~4 deg
        self.scale_ = np.array([0.10, 0.50, 6.0], dtype=np.float32)  # std spreads
        self.fitted = False

    def fit(self, conditions: np.ndarray):
        """Fits mean and std from dataset conditions matrix [N, 3]."""
        # conditions[:, 0] = Mach, conditions[:, 1] = log10(Re), conditions[:, 2] = AoA
        self.mean_ = np.mean(conditions, axis=0).astype(np.float32)
        self.scale_ = np.std(conditions, axis=0).astype(np.float32)
        self.scale_[self.scale_ < 1e-4] = 1.0
        self.fitted = True

    def transform(self, conditions: np.ndarray) -> np.ndarray:
        """Forward standardization: z = (x - mu) / sigma."""
        cond = np.copy(conditions).astype(np.float32)
        if cond.shape[-1] == 3 and np.any(cond[..., 1] > 100.0):
            # Take log10 of Reynolds number if raw values provided
            cond[..., 1] = np.log10(np.maximum(cond[..., 1], 1e3))
        return (cond - self.mean_) / self.scale_

    def inverse_transform(self, z_conditions: np.ndarray) -> np.ndarray:
        """Reverse transform: x = z * sigma + mu."""
        res = (z_conditions * self.scale_) + self.mean_
        return res

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean": self.mean_.tolist(),
            "scale": self.scale_.tolist(),
            "features": ["mach", "log10_reynolds", "aoa_deg"]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlowConditionNormalizer":
        norm = cls()
        norm.mean_ = np.array(data["mean"], dtype=np.float32)
        norm.scale_ = np.array(data["scale"], dtype=np.float32)
        norm.fitted = True
        return norm


class AerodynamicTargetScaler:
    """Scales multi-target [CL, CD, CM] to ensure balanced gradients across orders of magnitude."""

    def __init__(self):
        # Default scaling parameters:
        # CL: ~[-1.0, 1.5], mean 0.4, scale 0.6
        # CD: ~[0.005, 0.08], mean 0.015, scale 0.015
        # CM: ~[-0.15, 0.05], mean -0.05, scale 0.05
        self.mean_ = np.array([0.40, 0.015, -0.05], dtype=np.float32)
        self.scale_ = np.array([0.60, 0.015, 0.05], dtype=np.float32)
        self.fitted = False

    def fit(self, targets: np.ndarray):
        """Fits target statistics from [N, 3] matrix."""
        self.mean_ = np.mean(targets, axis=0).astype(np.float32)
        self.scale_ = np.std(targets, axis=0).astype(np.float32)
        self.scale_[self.scale_ < 1e-5] = 1.0
        self.fitted = True

    def transform(self, targets: np.ndarray) -> np.ndarray:
        """Scales target coefficients: z = (y - mu) / sigma."""
        return (targets - self.mean_) / self.scale_

    def inverse_transform(self, z_targets: np.ndarray) -> np.ndarray:
        """Reconstructs physical aerodynamic coefficients."""
        res = (z_targets * self.scale_) + self.mean_
        # Physical clamp: CD cannot be negative
        if res.ndim == 1:
            res[1] = max(0.0005, float(res[1]))
        else:
            res[:, 1] = np.maximum(0.0005, res[:, 1])
        return res

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean": self.mean_.tolist(),
            "scale": self.scale_.tolist(),
            "targets": ["CL", "CD", "CM"]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AerodynamicTargetScaler":
        scaler = cls()
        scaler.mean_ = np.array(data["mean"], dtype=np.float32)
        scaler.scale_ = np.array(data["scale"], dtype=np.float32)
        scaler.fitted = True
        return scaler
