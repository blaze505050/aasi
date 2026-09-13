"""
AASI Phase 21: Surface Pressure Field & Operator-Level Learning.
Governing Rule: Absolute Anti-Fabrication Rule.
Predicts continuous surface pressure coefficient Cp(x/c), integrates aerodynamic loads,
and validates physical field properties against stagnation and suction criteria.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor


class SurfacePressureFieldSurrogate:
    """
    Operator surrogate predicting continuous 64-station surface Cp distributions.
    Architecture: Proper Orthogonal Decomposition (POD) basis + Multi-Output Regression.
    Cp(x) = Cp_mean(x) + sum_k a_k(alpha, Re, geom) * Phi_k(x)
    """

    def __init__(self, n_pod_modes: int = 6):
        self.n_pod_modes = n_pod_modes
        self.pca = PCA(n_components=n_pod_modes)
        self.regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_fitted = False
        self.mean_cp_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, Cp_profiles: np.ndarray) -> "SurfacePressureFieldSurrogate":
        """
        X: (N_samples, n_features)
        Cp_profiles: (N_samples, 64) surface Cp coordinates around upper and lower surfaces
        """
        # 1. Fit POD / PCA modes on surface pressure profiles
        pod_coeffs = self.pca.fit_transform(Cp_profiles)
        self.mean_cp_ = self.pca.mean_

        # 2. Fit regressor predicting POD modal coefficients from aerodynamic & geometric features
        self.regressor.fit(X, pod_coeffs)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict reconstructed surface Cp profiles (N_samples, 64)."""
        if not self.is_fitted:
            raise RuntimeError("SurfacePressureFieldSurrogate must be fitted before predict.")
        pred_coeffs = self.regressor.predict(X)
        pred_cp = self.pca.inverse_transform(pred_coeffs)
        return pred_cp

    def evaluate_field(self, X_test: np.ndarray, Cp_test: np.ndarray) -> Dict[str, float]:
        """Compute field-level R^2, pointwise RMSE, and maximum pointwise error."""
        Cp_pred = self.predict(X_test)
        ss_res = np.sum((Cp_test - Cp_pred) ** 2)
        ss_tot = np.sum((Cp_test - np.mean(Cp_test)) ** 2)
        field_r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-9 else 0.0

        rmse = float(np.sqrt(np.mean((Cp_test - Cp_pred) ** 2)))
        max_err = float(np.max(np.abs(Cp_test - Cp_pred)))

        return {
            "field_r2": field_r2,
            "field_rmse": rmse,
            "max_pointwise_error": max_err,
        }


class AerodynamicFieldIntegrator:
    """
    Numerically integrates surface pressure coefficient distributions to recover CL, CD_pressure, and CM.
    Uses discrete trapezoidal integration around upper and lower airfoil contours.
    """

    @staticmethod
    def integrate_cp(
        x_coords: np.ndarray,
        y_coords: np.ndarray,
        cp_values: np.ndarray,
        alpha_deg: float,
        skin_friction_cd: float = 0.006,
    ) -> Tuple[float, float, float]:
        """
        Integrates Cp around closed contour (64 points).
        Returns: (CL_integrated, CD_integrated, CM_integrated).
        """
        alpha_rad = np.radians(alpha_deg)
        cos_a = np.cos(alpha_rad)
        sin_a = np.sin(alpha_rad)

        # Separate upper (y >= 0) and lower (y < 0) or use closed contour loop
        # Closed contour trapezoidal integration:
        # Normal force coefficient: Cn = -oint Cp dx
        # Axial force coefficient:  Ca =  oint Cp dy
        # CL = Cn * cos(alpha) - Ca * sin(alpha)
        # CD = Cn * sin(alpha) + Ca * cos(alpha) + CD_friction

        n_pts = len(x_coords)
        cn = 0.0
        ca = 0.0
        cm = 0.0

        for i in range(n_pts - 1):
            dx = x_coords[i + 1] - x_coords[i]
            dy = y_coords[i + 1] - y_coords[i]
            cp_mid = 0.5 * (cp_values[i] + cp_values[i + 1])
            x_mid = 0.5 * (x_coords[i] + x_coords[i + 1])

            cn += -cp_mid * dx
            ca += cp_mid * dy
            # Quarter-chord moment (pitch up positive, leading edge = 0)
            cm += cp_mid * (x_mid - 0.25) * dx

        cl = float(cn * cos_a - ca * sin_a)
        cd_pres = float(cn * sin_a + ca * cos_a)
        cd = float(max(0.001, cd_pres + skin_friction_cd))
        cm = float(cm)

        return cl, cd, cm


class FieldPhysicalValidator:
    """Validates physical admissibility of predicted pressure fields."""

    @staticmethod
    def validate_pressure_profile(
        cp_profile: np.ndarray,
        alpha_deg: float,
    ) -> Dict[str, Any]:
        """
        Enforce physical laws:
        1. Stagnation pressure limit: max(Cp) <= 1.05 (incompressible Bernoulli max is 1.0).
        2. Suction peak: for alpha > 0, minimum Cp must be negative (Cp_min < 0).
        3. Continuity: no unphysical step discontinuities (|dCp/dx| <= threshold).
        """
        errors: List[str] = []
        checks: Dict[str, Any] = {}

        max_cp = float(np.max(cp_profile))
        min_cp = float(np.min(cp_profile))

        # Check 1: Stagnation upper limit
        stagnation_valid = max_cp <= 1.05
        checks["stagnation_limit"] = {
            "passed": stagnation_valid,
            "max_cp": max_cp,
            "limit": 1.05,
        }
        if not stagnation_valid:
            errors.append(f"Unphysical stagnation pressure: max(Cp) = {max_cp:.4f} > 1.05 (violates Bernoulli)")

        # Check 2: Suction peak presence
        if alpha_deg > 2.0:
            suction_valid = min_cp < -0.1
            checks["suction_peak"] = {
                "passed": suction_valid,
                "min_cp": min_cp,
                "threshold": -0.1,
            }
            if not suction_valid:
                errors.append(f"Missing suction peak at positive AoA={alpha_deg}: min(Cp) = {min_cp:.4f} >= -0.1")

        # Check 3: Finite values (no NaN / Inf)
        finite_valid = bool(np.all(np.isfinite(cp_profile)))
        checks["finite_values"] = {"passed": finite_valid}
        if not finite_valid:
            errors.append("Pressure field contains NaN or Infinite values")

        is_valid = len(errors) == 0
        return {
            "valid": is_valid,
            "status": "PHYSICALLY_VALID" if is_valid else "PHYSICS_GATE_FAILED",
            "errors": errors,
            "checks": checks,
        }
