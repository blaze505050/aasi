"""
AASI Phase 21: Multi-Fidelity Aerodynamic Modeling Engine.
Governing Rule: Absolute Anti-Fabrication Rule.
Maintains strict 5-tier fidelity hierarchy and implements discrepancy / residual modeling.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class FidelityLevel(str, Enum):
    FIDELITY_0_ANALYTICAL = "FIDELITY_0_ANALYTICAL"  # Thin-airfoil theory & flat-plate skin friction
    FIDELITY_1_PANEL = "FIDELITY_1_PANEL"            # Inviscid vortex panel method with boundary layer
    FIDELITY_2_COARSE_RANS = "FIDELITY_2_COARSE_RANS"# Coarse mesh simpleFoam k-omega SST (~50k cells)
    FIDELITY_3_REFINED_RANS = "FIDELITY_3_REFINED_RANS"# Refined mesh simpleFoam k-omega SST (~200k cells)
    FIDELITY_4_EXPERIMENTAL = "FIDELITY_4_EXPERIMENTAL"# Authentic wind tunnel measurements (Abbott & von Doenhoff)


@dataclass
class MultiFidelityObservation:
    geometry_id: str
    geometry_hash: str
    flow_condition: Dict[str, Any]  # alpha_deg, reynolds, mach
    fidelity_level: FidelityLevel
    solver_or_source: str
    CL: float
    CD: float
    CM: float
    Cp_distribution: Optional[List[float]] = None
    uncertainty: float = 0.0
    mesh_resolution: Optional[str] = None
    provenance_hash: str = ""

    def to_feature_vector(self, rep_d_vector: np.ndarray) -> np.ndarray:
        """Combine geometric features with flow condition."""
        alpha = self.flow_condition.get("alpha_deg", 0.0)
        re = self.flow_condition.get("reynolds", 3e6)
        alpha_rad = np.radians(alpha)
        flow_feat = np.array([alpha, re / 1e6, np.sin(alpha_rad), np.cos(alpha_rad), (alpha / 10.0)**2])
        return np.concatenate([rep_d_vector, flow_feat])


class AnalyticalThinAirfoilBaseline:
    """
    Fidelity 0: Classical thin airfoil theory with flat-plate boundary layer drag.
    CL = 2 * pi * (alpha - alpha_0)
    alpha_0 = -2 * camber_m / pi (approx)
    CD = 2 * 0.074 / (Re^(1/5)) + CL^2 / (pi * AR)  (for 2D sectional, CD_min + induced/form proxy)
    """

    @staticmethod
    def predict(alpha_deg: float, reynolds: float, camber_m: float = 0.0, thickness_t: float = 0.12) -> Tuple[float, float, float]:
        alpha_rad = np.radians(alpha_deg)
        alpha_0_rad = -2.0 * camber_m  # classical approximation
        # Theoretical lift slope 2 * pi * (1 + 0.77 * t/c) for finite thickness
        lift_slope = 2.0 * np.pi * (1.0 + 0.77 * thickness_t)
        cl = float(lift_slope * (alpha_rad - alpha_0_rad))

        # Skin friction drag (turbulent flat plate Schoenherr/Prandtl line)
        re = max(1e4, reynolds)
        cf = 0.074 / (re ** 0.2)
        # Form factor (1 + 2 * t/c + 60 * (t/c)^4)
        form_factor = 1.0 + 2.0 * thickness_t + 60.0 * (thickness_t**4)
        cd_friction = 2.0 * cf * form_factor
        # Pressure drag approximation as function of lift squared
        cd_pressure = 0.005 + 0.015 * (cl**2)
        cd = float(cd_friction + cd_pressure)

        # Pitching moment about quarter-chord
        cm = float(-0.5 * np.pi * camber_m)

        return cl, max(0.001, cd), cm


class MultiFidelityDiscrepancySurrogate:
    """
    Implements multi-fidelity residual discrepancy modeling:
    y_high(x) = y_low(x) + delta(x)
    where y_low is predicted by the low-fidelity model and delta(x) is trained on high-fidelity residuals.
    """

    def __init__(self, low_fidelity_model: Any, high_fidelity_delta_model: Any):
        self.low_fidelity_model = low_fidelity_model
        self.high_fidelity_delta_model = high_fidelity_delta_model
        self.is_fitted = False

    def fit(
        self,
        X_low: np.ndarray,
        y_low: np.ndarray,
        X_high: np.ndarray,
        y_high: np.ndarray,
    ) -> "MultiFidelityDiscrepancySurrogate":
        """
        Train low-fidelity base surrogate on low-fidelity dataset,
        then train discrepancy surrogate delta(x) on residuals (y_high - y_low_pred).
        """
        # 1. Fit low-fidelity model
        self.low_fidelity_model.fit(X_low, y_low)

        # 2. Compute low-fidelity predictions at high-fidelity training points
        y_low_at_high = self.low_fidelity_model.predict(X_high)

        # 3. Compute residual discrepancy
        residuals = y_high - y_low_at_high

        # 4. Fit discrepancy model on residuals
        self.high_fidelity_delta_model.fit(X_high, residuals)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Evaluate y_pred = y_low(X) + delta(X)."""
        if not self.is_fitted:
            raise RuntimeError("Multi-fidelity model must be fitted before predict.")
        y_low_pred = self.low_fidelity_model.predict(X)
        delta_pred = self.high_fidelity_delta_model.predict(X)
        y_pred = y_low_pred + delta_pred

        # Physical post-processing: CD (column 1 if 2D) must be non-negative
        if y_pred.ndim == 2 and y_pred.shape[1] >= 2:
            y_pred[:, 1] = np.maximum(y_pred[:, 1], 0.0)
        return y_pred

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Compute R^2, RMSE, and MAE against test targets."""
        y_pred = self.predict(X_test)
        ss_res = np.sum((y_test - y_pred) ** 2, axis=0)
        ss_tot = np.sum((y_test - np.mean(y_test, axis=0)) ** 2, axis=0)
        r2 = np.where(ss_tot > 1e-9, 1.0 - (ss_res / ss_tot), 0.0)

        rmse = float(np.sqrt(np.mean((y_test - y_pred) ** 2)))
        mae = float(np.mean(np.abs(y_test - y_pred)))

        return {
            "r2": round(float(np.mean(r2)), 4),
            "r2_cl": round(float(r2[0]), 4) if len(r2) > 0 else 0.0,
            "r2_cd": round(float(r2[1]), 4) if len(r2) > 1 else 0.0,
            "rmse": round(rmse, 4),
            "mae": round(mae, 4),
        }
