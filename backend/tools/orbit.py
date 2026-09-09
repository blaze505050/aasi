"""
Orbital mechanics calculation tool for AASI.
Utilizes Astropy constants and units for high-precision physical calculations.
"""

import math
from typing import Any, Dict, List
import astropy.constants as const
import astropy.units as u


# Standard gravitational parameters (mu = G * M) and volumetric mean radii
BODIES: Dict[str, Dict[str, Any]] = {
    "earth": {
        "name": "Earth",
        "radius_km": (const.R_earth.to(u.km)).value,  # ~6378.137 km
        "mass_kg": (const.M_earth.to(u.kg)).value,    # ~5.972e24 kg
        "mu_km3_s2": (const.G * const.M_earth).to(u.km**3 / u.s**2).value,  # ~398600.44 km^3/s^2
    },
    "moon": {
        "name": "Moon",
        "radius_km": 1737.4,
        "mass_kg": 7.342e22,
        "mu_km3_s2": (const.G * (7.342e22 * u.kg)).to(u.km**3 / u.s**2).value,  # ~4902.8 km^3/s^2
    },
    "mars": {
        "name": "Mars",
        "radius_km": 3389.5,
        "mass_kg": 6.4171e23,
        "mu_km3_s2": (const.G * (6.4171e23 * u.kg)).to(u.km**3 / u.s**2).value,  # ~42828.37 km^3/s^2
    },
    "sun": {
        "name": "Sun",
        "radius_km": (const.R_sun.to(u.km)).value,
        "mass_kg": (const.M_sun.to(u.kg)).value,
        "mu_km3_s2": (const.G * const.M_sun).to(u.km**3 / u.s**2).value,
    },
}


def _get_body_data(body_name: str) -> Dict[str, Any]:
    key = body_name.strip().lower()
    if key not in BODIES:
        valid = ", ".join(b["name"] for b in BODIES.values())
        raise ValueError(f"Unknown central body '{body_name}'. Supported bodies: {valid}")
    return BODIES[key]


def calculate_circular_orbit(altitude_km: float, central_body: str = "Earth") -> Dict[str, Any]:
    """
    Calculate circular orbit velocity, period, and parameters.
    """
    if altitude_km < 0:
        raise ValueError(f"Orbital altitude must be non-negative (got {altitude_km} km).")

    body = _get_body_data(central_body)
    r_km = body["radius_km"] + altitude_km
    mu = body["mu_km3_s2"]

    # v = sqrt(mu / r) in km/s
    v_km_s = math.sqrt(mu / r_km)
    v_m_s = v_km_s * 1000.0

    # T = 2 * pi * sqrt(r^3 / mu) in seconds
    period_s = 2.0 * math.pi * math.sqrt((r_km ** 3) / mu)
    period_min = period_s / 60.0
    period_hr = period_s / 3600.0

    # Gravitational / centripetal acceleration: a = mu / r^2 in m/s^2
    a_m_s2 = (mu * 1e9) / ((r_km * 1000.0) ** 2)

    return {
        "tool": "orbit",
        "calculation": "circular_orbit",
        "inputs": {
            "altitude_km": altitude_km,
            "central_body": body["name"],
        },
        "results": {
            "orbital_radius_km": round(r_km, 3),
            "orbital_velocity_km_s": round(v_km_s, 4),
            "orbital_velocity_m_s": round(v_m_s, 2),
            "orbital_period_s": round(period_s, 2),
            "orbital_period_minutes": round(period_min, 2),
            "orbital_period_hours": round(period_hr, 3),
            "gravitational_acceleration_m_s2": round(a_m_s2, 4),
            "standard_gravitational_parameter_km3_s2": round(mu, 2),
        },
        "units": {
            "orbital_radius": "km",
            "orbital_velocity": "km/s and m/s",
            "orbital_period": "seconds, minutes, and hours",
            "gravitational_acceleration": "m/s^2",
            "standard_gravitational_parameter": "km^3/s^2",
        },
        "assumptions": [
            "Two-body Keplerian point-mass gravitational field",
            "Circular orbit with zero eccentricity (e = 0)",
            "Spherical central body with volumetric mean radius",
            "No atmospheric drag or higher-order gravitational perturbations (e.g. J2 oblateness)",
        ],
    }


def calculate_escape_velocity(altitude_km: float, central_body: str = "Earth") -> Dict[str, Any]:
    """
    Calculate parabolic escape velocity from a given altitude.
    """
    if altitude_km < 0:
        raise ValueError(f"Altitude must be non-negative (got {altitude_km} km).")

    body = _get_body_data(central_body)
    r_km = body["radius_km"] + altitude_km
    mu = body["mu_km3_s2"]

    # v_esc = sqrt(2 * mu / r)
    v_esc_km_s = math.sqrt(2.0 * mu / r_km)
    v_esc_m_s = v_esc_km_s * 1000.0
    v_circ_km_s = math.sqrt(mu / r_km)

    return {
        "tool": "orbit",
        "calculation": "escape_velocity",
        "inputs": {
            "altitude_km": altitude_km,
            "central_body": body["name"],
        },
        "results": {
            "orbital_radius_km": round(r_km, 3),
            "escape_velocity_km_s": round(v_esc_km_s, 4),
            "escape_velocity_m_s": round(v_esc_m_s, 2),
            "circular_velocity_reference_km_s": round(v_circ_km_s, 4),
            "ratio_to_circular": round(math.sqrt(2.0), 4),
        },
        "units": {
            "orbital_radius": "km",
            "escape_velocity": "km/s and m/s",
            "circular_velocity_reference": "km/s",
        },
        "assumptions": [
            "Two-body gravitational interaction",
            "Parabolic escape trajectory with infinite distance asymptote at zero velocity",
            "Central body spherical without third-body perturbations",
        ],
    }


def calculate_hohmann_transfer(
    initial_altitude_km: float,
    final_altitude_km: float,
    central_body: str = "Earth",
) -> Dict[str, Any]:
    """
    Calculate planar Hohmann transfer between two coplanar circular orbits.
    """
    if initial_altitude_km < 0 or final_altitude_km < 0:
        raise ValueError("Altitudes must be non-negative.")

    body = _get_body_data(central_body)
    r1 = body["radius_km"] + initial_altitude_km
    r2 = body["radius_km"] + final_altitude_km
    mu = body["mu_km3_s2"]

    if math.isclose(r1, r2, rel_tol=1e-5):
        raise ValueError("Initial and final altitudes cannot be identical for a Hohmann transfer.")

    # Circular velocities at initial and final orbits
    v_c1 = math.sqrt(mu / r1)
    v_c2 = math.sqrt(mu / r2)

    # Semi-major axis of the elliptical transfer orbit
    a_tx = (r1 + r2) / 2.0

    # Velocities at periapsis and apoapsis of transfer orbit (vis-viva: v^2 = mu * (2/r - 1/a))
    v_tx1 = math.sqrt(mu * (2.0 / r1 - 1.0 / a_tx))
    v_tx2 = math.sqrt(mu * (2.0 / r2 - 1.0 / a_tx))

    # Delta-v burns
    delta_v1 = abs(v_tx1 - v_c1)
    delta_v2 = abs(v_c2 - v_tx2)
    total_delta_v = delta_v1 + delta_v2

    # Transfer duration (half the period of the transfer ellipse)
    transfer_time_s = math.pi * math.sqrt((a_tx ** 3) / mu)
    transfer_time_min = transfer_time_s / 60.0
    transfer_time_hr = transfer_time_s / 3600.0

    return {
        "tool": "orbit",
        "calculation": "hohmann_transfer",
        "inputs": {
            "initial_altitude_km": initial_altitude_km,
            "final_altitude_km": final_altitude_km,
            "central_body": body["name"],
        },
        "results": {
            "initial_radius_km": round(r1, 3),
            "final_radius_km": round(r2, 3),
            "transfer_semi_major_axis_km": round(a_tx, 3),
            "initial_circular_velocity_km_s": round(v_c1, 4),
            "final_circular_velocity_km_s": round(v_c2, 4),
            "delta_v1_km_s": round(delta_v1, 4),
            "delta_v1_m_s": round(delta_v1 * 1000.0, 2),
            "delta_v2_km_s": round(delta_v2, 4),
            "delta_v2_m_s": round(delta_v2 * 1000.0, 2),
            "total_delta_v_km_s": round(total_delta_v, 4),
            "total_delta_v_m_s": round(total_delta_v * 1000.0, 2),
            "transfer_time_seconds": round(transfer_time_s, 2),
            "transfer_time_minutes": round(transfer_time_min, 2),
            "transfer_time_hours": round(transfer_time_hr, 3),
        },
        "units": {
            "radii_and_semi_major_axis": "km",
            "velocities_and_delta_v": "km/s and m/s",
            "transfer_time": "seconds, minutes, and hours",
        },
        "assumptions": [
            "Coplanar circular initial and final orbits",
            "Two impulsive tangential delta-v maneuvers (instantaneous velocity increments)",
            "Two-body point-mass Keplerian orbital mechanics",
            "Zero atmospheric drag or gravitational perturbations during transfer",
        ],
    }
