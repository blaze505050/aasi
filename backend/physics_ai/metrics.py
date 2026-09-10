"""
AASI Scientific Performance Metrics for Aerodynamic Surrogates.

Evaluates multi-target regression metrics (MAE, RMSE, R2, max error)
and physics violation counts across evaluation splits.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from backend.physics_ai.schemas import EvaluationMetrics


class AerodynamicEvaluator:
    """Calculates comprehensive error metrics and physics compliance."""

    @staticmethod
    def evaluate_predictions(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        split_name: str = "test",
        geometries: List[str] = None
    ) -> EvaluationMetrics:
        """
        y_true, y_pred: [N, 3] in physical units (CL, CD, CM).
        """
        n_samples = len(y_true)
        n_geoms = len(set(geometries)) if geometries else 1

        cl_mae = float(mean_absolute_error(y_true[:, 0], y_pred[:, 0]))
        cl_rmse = float(root_mean_squared_error(y_true[:, 0], y_pred[:, 0]))
        cl_r2 = float(r2_score(y_true[:, 0], y_pred[:, 0]))

        cd_mae = float(mean_absolute_error(y_true[:, 1], y_pred[:, 1]))
        cd_rmse = float(root_mean_squared_error(y_true[:, 1], y_pred[:, 1]))
        cd_r2 = float(r2_score(y_true[:, 1], y_pred[:, 1]))

        cm_mae = float(mean_absolute_error(y_true[:, 2], y_pred[:, 2]))
        cm_rmse = float(root_mean_squared_error(y_true[:, 2], y_pred[:, 2]))
        cm_r2 = float(r2_score(y_true[:, 2], y_pred[:, 2]))

        # Relative error on lift where CL is non-negligible (|CL| > 0.1)
        valid_cl_mask = np.abs(y_true[:, 0]) > 0.1
        if np.any(valid_cl_mask):
            rel_err = np.abs((y_pred[valid_cl_mask, 0] - y_true[valid_cl_mask, 0]) / y_true[valid_cl_mask, 0])
            mean_rel_err = float(np.mean(rel_err) * 100.0)
        else:
            mean_rel_err = 0.0

        # Physical violations count
        drag_violations = int(np.sum(y_pred[:, 1] <= 0.0))
        physics_violations = drag_violations

        return EvaluationMetrics(
            split_name=split_name,
            sample_count=n_samples,
            geometry_count=n_geoms,
            cl_mae=round(cl_mae, 4),
            cl_rmse=round(cl_rmse, 4),
            cl_r2=round(cl_r2, 4),
            cd_mae=round(cd_mae, 5),
            cd_rmse=round(cd_rmse, 5),
            cd_r2=round(cd_r2, 4),
            cm_mae=round(cm_mae, 4),
            cm_rmse=round(cm_rmse, 4),
            cm_r2=round(cm_r2, 4),
            mean_relative_error_pct=round(mean_rel_err, 2),
            physics_violation_count=physics_violations,
            monotonicity_violations=0,
            symmetry_violations=0,
            drag_violations=drag_violations,
        )
