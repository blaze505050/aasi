"""
Rocket propulsion and trajectory estimation tool for AASI.
Implements preliminary rocketry sizing, Tsiolkovsky calculations, and mass fraction analysis.
"""

import math
from typing import Any, Dict

# Standard Earth gravitational acceleration (CODATA / RocketPy standard)
STANDARD_G0: float = 9.80665  # m/s^2


def rocket_equation(
    isp_s: float,
    initial_mass_kg: float,
    final_mass_kg: float,
) -> Dict[str, Any]:
    """
    Calculate ideal velocity increment (Delta-v) using the Tsiolkovsky rocket equation.
    """
    if isp_s <= 0:
        raise ValueError(f"Specific impulse (Isp) must be positive (got {isp_s} s).")
    if initial_mass_kg <= 0 or final_mass_kg <= 0:
        raise ValueError("Initial and final mass must both be positive.")
    if final_mass_kg >= initial_mass_kg:
        raise ValueError(
            f"Final dry mass ({final_mass_kg} kg) must be strictly less than initial wet mass ({initial_mass_kg} kg)."
        )

    # Mass ratio R = m0 / mf
    mass_ratio = initial_mass_kg / final_mass_kg
    propellant_mass_kg = initial_mass_kg - final_mass_kg
    propellant_fraction = propellant_mass_kg / initial_mass_kg

    # Effective exhaust velocity c = g0 * Isp
    effective_exhaust_velocity_m_s = STANDARD_G0 * isp_s

    # Delta-v = c * ln(m0 / mf)
    delta_v_m_s = effective_exhaust_velocity_m_s * math.log(mass_ratio)
    delta_v_km_s = delta_v_m_s / 1000.0

    return {
        "tool": "rocket",
        "calculation": "tsiolkovsky_rocket_equation",
        "inputs": {
            "specific_impulse_s": isp_s,
            "initial_mass_kg": initial_mass_kg,
            "final_mass_kg": final_mass_kg,
            "standard_gravity_m_s2": STANDARD_G0,
        },
        "results": {
            "delta_v_m_s": round(delta_v_m_s, 2),
            "delta_v_km_s": round(delta_v_km_s, 4),
            "mass_ratio": round(mass_ratio, 4),
            "propellant_mass_kg": round(propellant_mass_kg, 2),
            "propellant_mass_fraction": round(propellant_fraction, 4),
            "effective_exhaust_velocity_m_s": round(effective_exhaust_velocity_m_s, 2),
        },
        "units": {
            "specific_impulse": "seconds",
            "masses": "kilograms (kg)",
            "velocities_and_delta_v": "m/s and km/s",
            "mass_ratio": "dimensionless",
        },
        "assumptions": [
            "Ideal rocket motion in a gravity-free, drag-free vacuum",
            "Constant effective exhaust velocity throughout combustion",
            "One-dimensional collinear thrust with no steering or pitch losses",
            "Preliminary sizing calculation only; does not replace 6-DOF flight simulation",
        ],
    }


def required_mass_ratio(delta_v_m_s: float, isp_s: float) -> Dict[str, Any]:
    """
    Calculate the required mass ratio (m0 / mf) and propellant fraction for a target Delta-v.
    """
    if delta_v_m_s <= 0:
        raise ValueError("Target Delta-v must be strictly positive.")
    if isp_s <= 0:
        raise ValueError("Specific impulse (Isp) must be strictly positive.")

    c = STANDARD_G0 * isp_s
    mass_ratio = math.exp(delta_v_m_s / c)
    propellant_fraction = 1.0 - (1.0 / mass_ratio)

    return {
        "tool": "rocket",
        "calculation": "required_mass_ratio",
        "inputs": {
            "target_delta_v_m_s": delta_v_m_s,
            "specific_impulse_s": isp_s,
            "standard_gravity_m_s2": STANDARD_G0,
        },
        "results": {
            "required_mass_ratio": round(mass_ratio, 4),
            "required_propellant_fraction": round(propellant_fraction, 4),
            "effective_exhaust_velocity_m_s": round(c, 2),
            "mass_multiplier_per_kg_dry": round(mass_ratio, 4),
        },
        "units": {
            "target_delta_v": "m/s",
            "specific_impulse": "seconds",
            "required_mass_ratio": "dimensionless",
            "required_propellant_fraction": "fraction of total wet mass",
        },
        "assumptions": [
            "Single-stage ideal rocket in vacuum",
            "Constant specific impulse",
            "Zero atmospheric, gravitational, or steering losses",
        ],
    }


def propellant_mass_estimation(
    dry_mass_kg: float,
    isp_s: float,
    delta_v_m_s: float,
) -> Dict[str, Any]:
    """
    Estimate propellant and wet mass required to propel a given dry mass by a target Delta-v.
    """
    if dry_mass_kg <= 0:
        raise ValueError("Dry mass must be strictly positive.")
    if isp_s <= 0:
        raise ValueError("Specific impulse must be strictly positive.")
    if delta_v_m_s <= 0:
        raise ValueError("Target Delta-v must be strictly positive.")

    c = STANDARD_G0 * isp_s
    r = math.exp(delta_v_m_s / c)
    wet_mass_kg = dry_mass_kg * r
    propellant_mass_kg = wet_mass_kg - dry_mass_kg

    return {
        "tool": "rocket",
        "calculation": "propellant_mass_estimation",
        "inputs": {
            "dry_mass_kg": dry_mass_kg,
            "specific_impulse_s": isp_s,
            "target_delta_v_m_s": delta_v_m_s,
        },
        "results": {
            "total_wet_mass_kg": round(wet_mass_kg, 2),
            "propellant_mass_kg": round(propellant_mass_kg, 2),
            "dry_mass_kg": round(dry_mass_kg, 2),
            "mass_ratio": round(r, 4),
        },
        "units": {
            "masses": "kilograms (kg)",
            "specific_impulse": "seconds",
            "target_delta_v": "m/s",
        },
        "assumptions": [
            "Ideal single-stage vehicle with zero external drag or gravity losses",
            "Constant specific impulse",
        ],
    }
