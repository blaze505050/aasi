"""
AASI Target Processing and Multi-Objective Loss Formulation.

Formulates weighted aerodynamic loss:
    L = w_cl * L_cl + w_cd * L_cd + w_cm * L_cm
and handles inverse transformations to restore physical SI and dimensionless units.
"""

import numpy as np
from typing import Dict, Any, Tuple
from backend.physics_ai.normalization import AerodynamicTargetScaler


class TargetProcessor:
    """Manages target transformation and multi-objective loss computation."""

    def __init__(self, loss_weights: Dict[str, float] = None):
        self.loss_weights = loss_weights or {"cl": 1.0, "cd": 5.0, "cm": 2.0}
        self.scaler = AerodynamicTargetScaler()

    def transform_targets(self, raw_targets: np.ndarray) -> np.ndarray:
        """Scales raw [N, 3] targets [CL, CD, CM]."""
        return self.scaler.transform(raw_targets)

    def inverse_transform_targets(self, scaled_targets: np.ndarray) -> np.ndarray:
        """Inverses scaling to restore physical [CL, CD, CM]."""
        return self.scaler.inverse_transform(scaled_targets)

    def compute_weighted_loss(
        self,
        y_pred: np.ndarray,
        y_true: np.ndarray
    ) -> Tuple[float, Dict[str, float]]:
        """
        Computes weighted MSE loss:
        L = w_cl * MSE(cl) + w_cd * MSE(cd) + w_cm * MSE(cm)
        """
        diff = y_pred - y_true
        mse_cl = float(np.mean(diff[:, 0] ** 2))
        mse_cd = float(np.mean(diff[:, 1] ** 2))
        mse_cm = float(np.mean(diff[:, 2] ** 2))

        w_cl = self.loss_weights.get("cl", 1.0)
        w_cd = self.loss_weights.get("cd", 5.0)
        w_cm = self.loss_weights.get("cm", 2.0)

        total_loss = w_cl * mse_cl + w_cd * mse_cd + w_cm * mse_cm
        components = {
            "loss_total": total_loss,
            "loss_cl": mse_cl,
            "loss_cd": mse_cd,
            "loss_cm": mse_cm
        }
        return total_loss, components
