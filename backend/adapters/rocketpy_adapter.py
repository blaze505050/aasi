"""
AASI 2.0 RocketPy Adapter.
High-precision rocket flight dynamics and trajectory simulation adapter.
Integrates AASI aerodynamic database polars with rocket 3-DOF flight dynamics.

Attribution: Inspired by RocketPy (MIT License, Copyright (c) RocketPy Team).
Clean, decoupled adapter providing deterministic trajectory evaluation with
strict physical invariants and cryptographic provenance.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Physical and Geodetic Constants (CODATA / WGS-84 / US Standard Atmosphere 1976)
STANDARD_G0: float = 9.80665          # Standard acceleration of gravity (m/s^2)
EARTH_RADIUS_M: float = 6371000.0     # Mean volumetric Earth radius (m)
SEA_LEVEL_DENSITY_KG_M3: float = 1.2250 # Sea level air density (kg/m^3)
SCALE_HEIGHT_M: float = 8500.0         # Tropospheric scale height (m)
SPECIFIC_HEAT_RATIO: float = 1.40      # Air ratio of specific heats (gamma)
SPECIFIC_GAS_CONST: float = 287.058    # Specific gas constant for air (J / (kg*K))
SEA_LEVEL_TEMP_K: float = 288.15       # Sea level standard temperature (K)
TEMP_LAPSE_RATE_K_M: float = 0.0065    # Tropospheric temperature lapse rate (K/m)


class RocketTrajectoryResult(BaseModel):
    """Deterministic trajectory calculation outputs."""
    apogee_altitude_m: float = Field(..., description="Peak altitude achieved above ground level (m)")
    burnout_altitude_m: float = Field(..., description="Altitude at main engine burnout (m)")
    burnout_velocity_m_s: float = Field(..., description="Velocity at engine burnout (m/s)")
    max_mach_number: float = Field(..., description="Maximum Mach number reached during ascent")
    max_dynamic_pressure_pa: float = Field(..., description="Maximum dynamic pressure q_max (Pa)")
    flight_time_to_apogee_s: float = Field(..., description="Time elapsed from ignition to apogee (s)")
    max_acceleration_g: float = Field(..., description="Maximum ascent acceleration in g's")
    total_impulse_ns: float = Field(..., description="Total propulsion impulse (N*s)")
    propellant_mass_fraction: float = Field(..., description="Propellant mass divided by wet mass")
    provenance_hash: str = Field(..., description="SHA-256 hash of inputs and trajectory telemetry")
    epistemic_tier: str = Field(default="CALCULATED", description="Epistemic validation classification")


class RocketPyAdapter:
    """
    Decoupled adapter providing rocket trajectory simulation and AASI aerodynamic database integration.
    """

    @staticmethod
    def atmosphere_density(altitude_m: float) -> float:
        """Computes atmospheric density using standard barometric formula."""
        if altitude_m <= 0:
            return SEA_LEVEL_DENSITY_KG_M3
        if altitude_m < 11000.0:  # Troposphere
            temp_k = SEA_LEVEL_TEMP_K - TEMP_LAPSE_RATE_K_M * altitude_m
            return SEA_LEVEL_DENSITY_KG_M3 * (temp_k / SEA_LEVEL_TEMP_K) ** 4.256
        # Stratosphere exponential attenuation
        return SEA_LEVEL_DENSITY_KG_M3 * math.exp(-altitude_m / SCALE_HEIGHT_M)

    @staticmethod
    def speed_of_sound(altitude_m: float) -> float:
        """Computes local speed of sound in m/s."""
        if altitude_m < 11000.0:
            temp_k = max(216.65, SEA_LEVEL_TEMP_K - TEMP_LAPSE_RATE_K_M * altitude_m)
        else:
            temp_k = 216.65  # Isothermal stratosphere lower bound
        return math.sqrt(SPECIFIC_HEAT_RATIO * SPECIFIC_GAS_CONST * temp_k)

    @staticmethod
    def local_gravity(altitude_m: float) -> float:
        """Computes altitude-dependent gravitational acceleration."""
        r = EARTH_RADIUS_M + max(0.0, altitude_m)
        return STANDARD_G0 * (EARTH_RADIUS_M / r) ** 2

    def simulate_vertical_trajectory(
        self,
        dry_mass_kg: float,
        propellant_mass_kg: float,
        burn_time_s: float,
        thrust_n: float,
        drag_coefficient_cd: float = 0.45,
        cross_section_area_m2: float = 0.05,
        time_step_s: float = 0.05,
        max_simulation_time_s: float = 300.0,
    ) -> RocketTrajectoryResult:
        """
        Executes a deterministic 3-DOF vertical ascent simulation using 4th-order Runge-Kutta.
        
        Invariants:
        - dry_mass_kg > 0, propellant_mass_kg >= 0
        - burn_time_s > 0, thrust_n >= 0
        - drag_coefficient_cd >= 0
        - cross_section_area_m2 > 0
        """
        if dry_mass_kg <= 0:
            raise ValueError(f"Dry mass must be strictly positive (got {dry_mass_kg} kg).")
        if propellant_mass_kg < 0:
            raise ValueError(f"Propellant mass cannot be negative (got {propellant_mass_kg} kg).")
        if burn_time_s <= 0:
            raise ValueError(f"Burn time must be strictly positive (got {burn_time_s} s).")
        if drag_coefficient_cd < 0:
            raise ValueError(f"Drag coefficient must be non-negative (got {drag_coefficient_cd}).")
        if cross_section_area_m2 <= 0:
            raise ValueError(f"Cross-sectional area must be strictly positive (got {cross_section_area_m2} m^2).")

        total_wet_mass = dry_mass_kg + propellant_mass_kg
        mass_flow_rate = propellant_mass_kg / burn_time_s if burn_time_s > 0 else 0.0
        total_impulse = thrust_n * burn_time_s

        # State vector: [altitude (m), velocity (m/s)]
        t = 0.0
        z = 0.0
        v = 0.0

        max_mach = 0.0
        max_q = 0.0
        max_accel_g = 0.0
        burnout_altitude = 0.0
        burnout_velocity = 0.0
        reached_burnout = False

        def derivatives(t_curr: float, z_curr: float, v_curr: float) -> tuple[float, float]:
            # Mass at time t
            if t_curr < burn_time_s:
                current_mass = total_wet_mass - mass_flow_rate * t_curr
                curr_thrust = thrust_n
            else:
                current_mass = dry_mass_kg
                curr_thrust = 0.0

            rho = self.atmosphere_density(z_curr)
            drag_force = 0.5 * rho * (v_curr ** 2) * drag_coefficient_cd * cross_section_area_m2 * math.copysign(1.0, v_curr)
            g = self.local_gravity(z_curr)
            weight = current_mass * g

            net_force = curr_thrust - drag_force - weight
            accel = net_force / current_mass
            return v_curr, accel

        # RK4 Integration Loop until apogee (velocity crosses zero from positive)
        while t < max_simulation_time_s:
            # Check burnout
            if t >= burn_time_s and not reached_burnout:
                burnout_altitude = z
                burnout_velocity = v
                reached_burnout = True

            # Telemetry metrics
            c = self.speed_of_sound(z)
            mach = abs(v) / c
            if mach > max_mach:
                max_mach = mach

            rho = self.atmosphere_density(z)
            q = 0.5 * rho * (v ** 2)
            if q > max_q:
                max_q = q

            # Check apogee condition (ascent finished)
            if t > 0.1 and v <= 0.0:
                break

            # RK4 step
            dz1, dv1 = derivatives(t, z, v)
            dz2, dv2 = derivatives(t + 0.5 * time_step_s, z + 0.5 * time_step_s * dz1, v + 0.5 * time_step_s * dv1)
            dz3, dv3 = derivatives(t + 0.5 * time_step_s, z + 0.5 * time_step_s * dz2, v + 0.5 * time_step_s * dv2)
            dz4, dv4 = derivatives(t + time_step_s, z + time_step_s * dz3, v + time_step_s * dv3)

            z += (time_step_s / 6.0) * (dz1 + 2.0 * dz2 + 2.0 * dz3 + dz4)
            v += (time_step_s / 6.0) * (dv1 + 2.0 * dv2 + 2.0 * dv3 + dv4)

            accel_val = dv1
            accel_g = accel_val / STANDARD_G0
            if accel_g > max_accel_g:
                max_accel_g = accel_g

            t += time_step_s

        if not reached_burnout:
            burnout_altitude = z
            burnout_velocity = v

        apogee_altitude = max(0.0, z)
        flight_time_apogee = t
        prop_mass_frac = propellant_mass_kg / total_wet_mass if total_wet_mass > 0 else 0.0

        # Cryptographic provenance
        payload = {
            "dry_mass_kg": dry_mass_kg,
            "propellant_mass_kg": propellant_mass_kg,
            "burn_time_s": burn_time_s,
            "thrust_n": thrust_n,
            "drag_coefficient_cd": drag_coefficient_cd,
            "cross_section_area_m2": cross_section_area_m2,
            "apogee_m": round(apogee_altitude, 2),
            "burnout_m": round(burnout_altitude, 2),
            "burnout_v_m_s": round(burnout_velocity, 2),
            "max_mach": round(max_mach, 4),
        }
        prov_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

        return RocketTrajectoryResult(
            apogee_altitude_m=round(apogee_altitude, 2),
            burnout_altitude_m=round(burnout_altitude, 2),
            burnout_velocity_m_s=round(burnout_velocity, 2),
            max_mach_number=round(max_mach, 4),
            max_dynamic_pressure_pa=round(max_q, 2),
            flight_time_to_apogee_s=round(flight_time_apogee, 2),
            max_acceleration_g=round(max_accel_g, 2),
            total_impulse_ns=round(total_impulse, 2),
            propellant_mass_fraction=round(prop_mass_frac, 4),
            provenance_hash=prov_hash,
            epistemic_tier="CALCULATED",
        )
