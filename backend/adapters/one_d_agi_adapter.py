"""
AASI 2.0 1D-AGI Adapter.
Symbolic physics regression, dimensional analysis (Buckingham Pi), and physical scaling law extraction.

Attribution: Inspired by 1D-AGI (MIT License).
Decoupled adapter providing automated dimensional analysis and power-law scaling discovery
for fluid dynamics and aerospace flight data.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field


class DimensionlessGroup(BaseModel):
    """Derived dimensionless group from dimensional variables."""
    symbol: str
    name: str
    formula: str
    calculated_value: float
    physical_significance: str


class SymbolicScalingLaw(BaseModel):
    """Discovered symbolic power-law relationship."""
    target_variable: str
    governing_features: List[str]
    formula_str: str
    leading_coefficient: float
    power_exponents: Dict[str, float]
    r_squared: float
    is_physically_consistent: bool
    provenance_hash: str
    epistemic_tier: str = Field(default="SYMBOLIC_REGRESSION", description="Epistemic data classification")


class OneDAGIAdapter:
    """
    Adapter for symbolic physical law discovery and Buckingham Pi dimensional reduction.
    """

    @classmethod
    def compute_aerodynamic_dimensionless_groups(
        cls,
        velocity_ms: float,
        chord_m: float,
        density_kg_m3: float,
        dynamic_viscosity_pa_s: float,
        speed_of_sound_ms: float,
        lift_force_n: float,
        drag_force_n: float,
        wing_area_m2: float,
    ) -> List[DimensionlessGroup]:
        """
        Synthesizes standard Buckingham Pi dimensionless groups from primary physical observables:
        [L, M, T] dimensions reduced to Re, M, CL, CD.
        """
        # Dynamic pressure q = 0.5 * rho * V^2
        q = 0.5 * density_kg_m3 * (velocity_ms ** 2)

        # Reynolds number Re = (rho * V * c) / mu
        re = (density_kg_m3 * velocity_ms * chord_m) / max(1.0e-9, dynamic_viscosity_pa_s)

        # Mach number M = V / a
        mach = velocity_ms / max(1.0, speed_of_sound_ms)

        # Lift coefficient CL = L / (q * S)
        cl = lift_force_n / max(1.0e-5, q * wing_area_m2)

        # Drag coefficient CD = D / (q * S)
        cd = drag_force_n / max(1.0e-5, q * wing_area_m2)

        # Lift-to-drag ratio L/D = CL / CD
        lod = cl / max(1.0e-5, cd)

        return [
            DimensionlessGroup(
                symbol="Re",
                name="Reynolds Number",
                formula="(rho * V * c) / mu",
                calculated_value=round(re, 1),
                physical_significance="Ratio of inertial forces to viscous forces in boundary layer",
            ),
            DimensionlessGroup(
                symbol="M",
                name="Mach Number",
                formula="V / a",
                calculated_value=round(mach, 4),
                physical_significance="Ratio of flow velocity to local speed of sound (compressibility)",
            ),
            DimensionlessGroup(
                symbol="CL",
                name="Lift Coefficient",
                formula="L / (0.5 * rho * V^2 * S)",
                calculated_value=round(cl, 4),
                physical_significance="Normalized non-dimensional aerodynamic lifting capability",
            ),
            DimensionlessGroup(
                symbol="CD",
                name="Drag Coefficient",
                formula="D / (0.5 * rho * V^2 * S)",
                calculated_value=round(cd, 5),
                physical_significance="Normalized non-dimensional aerodynamic drag resistance",
            ),
            DimensionlessGroup(
                symbol="L/D",
                name="Aerodynamic Efficiency",
                formula="CL / CD",
                calculated_value=round(lod, 2),
                physical_significance="Vehicle gliding ratio and range efficiency parameter",
            ),
        ]

    @classmethod
    def discover_power_law_scaling(
        cls,
        x_values: List[float],
        y_values: List[float],
        x_name: str = "Reynolds",
        y_name: str = "Cf",
    ) -> SymbolicScalingLaw:
        """
        Discovers the optimal power-law scaling relationship: y = C * x^alpha
        via log-log linear least-squares regression with mathematical verification.
        """
        x_arr = np.array(x_values, dtype=float)
        y_arr = np.array(y_values, dtype=float)

        # Filter strictly positive values for log transformation
        valid = (x_arr > 0) & (y_arr > 0)
        x_clean = x_arr[valid]
        y_clean = y_arr[valid]

        if len(x_clean) < 2:
            raise ValueError("At least 2 strictly positive data points required for power-law discovery.")

        ln_x = np.log(x_clean)
        ln_y = np.log(y_clean)

        # Linear regression: ln(y) = alpha * ln(x) + ln(C)
        coeffs = np.polyfit(ln_x, ln_y, 1)
        alpha = float(coeffs[0])
        ln_c = float(coeffs[1])
        c = float(np.exp(ln_c))

        # Evaluate R^2 goodness of fit
        y_pred = c * (x_clean ** alpha)
        ss_res = float(np.sum((y_clean - y_pred) ** 2))
        ss_tot = float(np.sum((y_clean - np.mean(y_clean)) ** 2))
        r2 = 1.0 - (ss_res / max(1.0e-9, ss_tot))

        formula = f"{y_name} = {round(c, 4)} * {x_name}^({round(alpha, 3)})"
        is_consistent = r2 >= 0.90

        payload = {
            "x_name": x_name,
            "y_name": y_name,
            "alpha": alpha,
            "c": c,
            "r2": r2,
        }
        prov_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

        return SymbolicScalingLaw(
            target_variable=y_name,
            governing_features=[x_name],
            formula_str=formula,
            leading_coefficient=round(c, 5),
            power_exponents={x_name: round(alpha, 4)},
            r_squared=round(r2, 4),
            is_physically_consistent=is_consistent,
            provenance_hash=prov_hash,
            epistemic_tier="SYMBOLIC_REGRESSION",
        )

