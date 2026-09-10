"""
AASI Aerodynamic Dimensional Analysis & Unit Transformation Engine.

Implements rigorous dimensional scaling, isentropic relations,
nondimensionalization, and unit conversions.
"""

from typing import Dict, Any, Optional, Tuple
import math
from pydantic import BaseModel


class DimensionlessFlowState(BaseModel):
    mach: float
    reynolds: float
    dynamic_pressure_pa: float
    speed_of_sound_ms: float
    stagnation_temperature_k: float
    stagnation_pressure_pa: float
    kinematic_viscosity_m2s: float


class AerodynamicDimensionalizer:
    """Computes nondimensional numbers and converts aerodynamic quantities."""

    GAMMA = 1.4              # Ratio of specific heats for air
    R_SPECIFIC = 287.058     # Specific gas constant for air, J/(kg*K)
    SUTHERLAND_C = 120.0     # Sutherland constant, K
    SUTHERLAND_T0 = 291.15   # Reference temperature, K
    SUTHERLAND_MU0 = 1.827e-5 # Reference dynamic viscosity, Pa*s

    @classmethod
    def dynamic_viscosity_sutherland(cls, temperature_k: float) -> float:
        """Sutherland's law for dynamic viscosity of air."""
        t = max(1.0, temperature_k)
        mu = cls.SUTHERLAND_MU0 * ((t / cls.SUTHERLAND_T0) ** 1.5) * ((cls.SUTHERLAND_T0 + cls.SUTHERLAND_C) / (t + cls.SUTHERLAND_C))
        return mu

    @classmethod
    def speed_of_sound(cls, temperature_k: float) -> float:
        """Computes speed of sound in ideal gas: a = sqrt(gamma * R * T)."""
        return math.sqrt(cls.GAMMA * cls.R_SPECIFIC * max(1.0, temperature_k))

    @classmethod
    def compute_flow_state(
        cls,
        velocity_ms: Optional[float] = None,
        mach: Optional[float] = None,
        altitude_m: float = 0.0,
        temperature_k: float = 288.15,
        pressure_pa: float = 101325.0,
        chord_m: float = 1.0
    ) -> DimensionlessFlowState:
        """Derives full dimensional & dimensionless aerodynamic state."""
        # Speed of sound
        a = cls.speed_of_sound(temperature_k)

        if mach is not None and velocity_ms is None:
            v = mach * a
            m = mach
        elif velocity_ms is not None:
            v = velocity_ms
            m = v / a if a > 0 else 0.0
        else:
            m = 0.15
            v = m * a

        # Air density from ideal gas law: rho = p / (R * T)
        rho = pressure_pa / (cls.R_SPECIFIC * temperature_k)

        # Dynamic pressure: q = 0.5 * rho * v^2
        q = 0.5 * rho * (v ** 2)

        # Dynamic & kinematic viscosity
        mu = cls.dynamic_viscosity_sutherland(temperature_k)
        nu = mu / rho

        # Reynolds number: Re = (rho * v * c) / mu = (v * c) / nu
        re = (v * chord_m) / nu if nu > 0 else 0.0

        # Isentropic stagnation quantities
        t_ratio = 1.0 + 0.5 * (cls.GAMMA - 1.0) * (m ** 2)
        t0 = temperature_k * t_ratio
        p0 = pressure_pa * (t_ratio ** (cls.GAMMA / (cls.GAMMA - 1.0)))

        return DimensionlessFlowState(
            mach=round(m, 4),
            reynolds=round(re, 1),
            dynamic_pressure_pa=round(q, 2),
            speed_of_sound_ms=round(a, 2),
            stagnation_temperature_k=round(t0, 2),
            stagnation_pressure_pa=round(p0, 1),
            kinematic_viscosity_m2s=nu
        )

    @classmethod
    def nondimensionalize_forces(
        cls,
        lift_n: float,
        drag_n: float,
        pitching_moment_nm: float,
        dynamic_pressure_pa: float,
        reference_area_m2: float,
        chord_m: float
    ) -> Dict[str, float]:
        """Calculates CL, CD, CM from dimensional forces."""
        denom_force = dynamic_pressure_pa * reference_area_m2
        denom_moment = denom_force * chord_m

        cl = lift_n / denom_force if denom_force > 0 else 0.0
        cd = drag_n / denom_force if denom_force > 0 else 0.0
        cm = pitching_moment_nm / denom_moment if denom_moment > 0 else 0.0

        return {
            "cl": round(cl, 5),
            "cd": round(cd, 6),
            "cm": round(cm, 5)
        }

    @classmethod
    def dimensionalize_forces(
        cls,
        cl: float,
        cd: float,
        cm: float,
        dynamic_pressure_pa: float,
        reference_area_m2: float,
        chord_m: float
    ) -> Dict[str, float]:
        """Calculates dimensional Lift (N), Drag (N), and Pitching Moment (N*m)."""
        denom_force = dynamic_pressure_pa * reference_area_m2
        denom_moment = denom_force * chord_m

        return {
            "lift_n": round(cl * denom_force, 2),
            "drag_n": round(cd * denom_force, 2),
            "pitching_moment_nm": round(cm * denom_moment, 3)
        }

    @classmethod
    def pressure_coefficient(
        cls,
        static_pressure_pa: float,
        freestream_pressure_pa: float,
        dynamic_pressure_pa: float
    ) -> float:
        """Computes Cp = (p - p_inf) / q_inf."""
        if dynamic_pressure_pa <= 0:
            return 0.0
        return round((static_pressure_pa - freestream_pressure_pa) / dynamic_pressure_pa, 4)
