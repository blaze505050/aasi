"""
AASI Standard Aerodynamic Baselines.

Implements Ridge regression, Random Forest, and small MLP baselines
to establish quantitative performance thresholds for neural surrogates.
"""

from typing import Dict, Any, Tuple
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score


class AerodynamicBaselines:
    """Trains and benchmarks standard regression baselines on aerodynamic data."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models = {
            "baseline_ridge": Ridge(alpha=1.0),
            "baseline_random_forest": RandomForestRegressor(n_estimators=50, max_depth=8, random_state=random_state),
            "baseline_mlp": MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=300, random_state=random_state),
        }
        self.trained = False

    def fit_and_evaluate(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, Dict[str, float]]:
        """
        Trains all 3 baselines and evaluates MAE, RMSE, and R2 on the test set.
        """
        results = {}
        for name, model in self.models.items():
            model.fit(X_train, y_train)
            preds = model.predict(X_test)

            cl_mae = float(mean_absolute_error(y_test[:, 0], preds[:, 0]))
            cl_rmse = float(root_mean_squared_error(y_test[:, 0], preds[:, 0]))
            cl_r2 = float(r2_score(y_test[:, 0], preds[:, 0]))

            cd_mae = float(mean_absolute_error(y_test[:, 1], preds[:, 1]))
            cd_rmse = float(root_mean_squared_error(y_test[:, 1], preds[:, 1]))
            cd_r2 = float(r2_score(y_test[:, 1], preds[:, 1]))

            cm_mae = float(mean_absolute_error(y_test[:, 2], preds[:, 2]))
            cm_rmse = float(root_mean_squared_error(y_test[:, 2], preds[:, 2]))
            cm_r2 = float(r2_score(y_test[:, 2], preds[:, 2]))

            results[name] = {
                "cl_mae": cl_mae,
                "cl_rmse": cl_rmse,
                "cl_r2": cl_r2,
                "cd_mae": cd_mae,
                "cd_rmse": cd_rmse,
                "cd_r2": cd_r2,
                "cm_mae": cm_mae,
                "cm_rmse": cm_rmse,
                "cm_r2": cm_r2,
                "mean_rmse": float((cl_rmse + cd_rmse + cm_rmse) / 3.0),
            }

        self.trained = True
        return results
