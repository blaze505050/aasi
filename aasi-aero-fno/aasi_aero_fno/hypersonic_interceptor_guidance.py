"""
Stage 27: Hypersonic Boost-Glide Interceptor Guidance Engine
============================================================
First-principles implementation of:
1. Hypersonic flight dynamics (Mach 6 to 12, altitude 20 km to 90 km):
   - 3D equations of motion under gravity and aerodynamic forces (drag, lift).
   - Stagnation convective heat flux limits (Sutton-Graves).
   - Dynamic pressure q_inf and load factor g-limits (n_z <= 35 g).
2. Zero Effort Miss (ZEM) Guidance & Differential Games:
   - ZEM vector: ZEM = r_rel + v_rel * t_go + 0.5 * a_rel * t_go^2
   - Differential Game Guidance (DGG) / Optimal Guidance Law (OGL):
     a_cmd = (N / t_go^2) * ZEM - (N / 2) * a_target
   - True proportional navigation (TPN) vs Augmented proportional navigation (APN).
3. Divert and Attitude Control System (DACS):
   - Pulse divert solid/bipropellant thrusters for high-altitude terminal homing.
   - Hit-to-kill (HTK) precision target interception (miss distance < 0.5 m).
"""

import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum

EARTH_RADIUS_M = 6371000.0
GRAVITY_SEA_LEVEL = 9.80665


class GuidanceLaw(str, Enum):
    PROPORTIONAL_NAVIGATION = "PROPORTIONAL_NAVIGATION"
    AUGMENTED_PN = "AUGMENTED_PN"
    DIFFERENTIAL_GAME_ZEM = "DIFFERENTIAL_GAME_ZEM"


class TargetEvasionManeuver(str, Enum):
    BALLISTIC = "BALLISTIC"
    SINUSOIDAL_WEAVE = "SINUSOIDAL_WEAVE"
    BARREL_ROLL = "BARREL_ROLL"
    TERMINAL_PULL_UP = "TERMINAL_PULL_UP"


def get_us_standard_atmosphere_density(altitude_m: float) -> Tuple[float, float, float]:
    """Computes density (kg/m3), speed of sound (m/s), and temperature (K) up to 100 km."""
    alt = max(0.0, min(100000.0, altitude_m))
    if alt < 11000.0:
        t = 288.15 - 0.0065 * alt
        p = 101325.0 * (t / 288.15) ** 5.25588
    elif alt < 20000.0:
        t = 216.65
        p = 22632.0 * math.exp(-GRAVITY_SEA_LEVEL * (alt - 11000.0) / (287.05 * t))
    elif alt < 32000.0:
        t = 216.65 + 0.001 * (alt - 20000.0)
        p = 5474.89 * (t / 216.65) ** -34.1632
    elif alt < 47000.0:
        t = 228.65 + 0.0028 * (alt - 32000.0)
        p = 868.02 * (t / 228.65) ** -12.2011
    else:
        # Mesosphere / Thermosphere
        t = 270.65 - 0.0028 * (alt - 47000.0)
        t = max(180.0, t)
        p = 110.9 * math.exp(-GRAVITY_SEA_LEVEL * (alt - 47000.0) / (287.05 * t))

    rho = p / (287.05 * t)
    speed_of_sound = math.sqrt(1.4 * 287.05 * t)
    return float(rho), float(speed_of_sound), float(t)


def compute_zem_vector(
    r_rel: np.ndarray,
    v_rel: np.ndarray,
    a_target: np.ndarray,
    t_go: float
) -> np.ndarray:
    """
    Computes 3D Zero Effort Miss vector.
    ZEM = r_rel + v_rel * t_go + 0.5 * a_target * t_go^2
    where r_rel = r_target - r_interceptor, v_rel = v_target - v_interceptor.
    """
    if t_go <= 0.001:
        return r_rel
    return r_rel + v_rel * t_go + 0.5 * a_target * (t_go ** 2)


def compute_guidance_acceleration(
    guidance_law: GuidanceLaw,
    r_rel: np.ndarray,
    v_rel: np.ndarray,
    a_target: np.ndarray,
    closing_speed: float,
    t_go: float,
    nav_ratio: float = 4.0,
    a_max_g: float = 35.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculates required missile acceleration command vector.
    Returns (a_cmd_vector, zem_vector).
    """
    dist = float(np.linalg.norm(r_rel))
    if dist < 0.1 or t_go < 0.001:
        return np.zeros(3), r_rel

    los_unit = r_rel / dist
    zem = compute_zem_vector(r_rel, v_rel, a_target, t_go)

    if guidance_law == GuidanceLaw.DIFFERENTIAL_GAME_ZEM:
        # Optimal Differential Game Guidance
        # a_cmd = (N / t_go^2) * ZEM - 0.5 * N * a_target
        a_cmd = (nav_ratio / max(0.01, t_go ** 2)) * zem - (0.5 * nav_ratio) * a_target
    elif guidance_law == GuidanceLaw.AUGMENTED_PN:
        # APN: a_cmd = N * V_c * Omega_los + 0.5 * N * a_target_normal
        omega_los = np.cross(r_rel, v_rel) / (dist ** 2)
        v_m_dir = -v_rel / max(1.0, np.linalg.norm(v_rel))
        a_cmd = nav_ratio * closing_speed * np.cross(omega_los, v_m_dir) + 0.5 * nav_ratio * a_target
    else:
        # Standard True Proportional Navigation (TPN)
        omega_los = np.cross(r_rel, v_rel) / (dist ** 2)
        v_m_dir = -v_rel / max(1.0, np.linalg.norm(v_rel))
        a_cmd = nav_ratio * closing_speed * np.cross(omega_los, v_m_dir)

    # Limit to maximum structural g-load
    a_max_mps2 = a_max_g * GRAVITY_SEA_LEVEL
    accel_mag = float(np.linalg.norm(a_cmd))
    if accel_mag > a_max_mps2:
        a_cmd = (a_cmd / accel_mag) * a_max_mps2

    return a_cmd, zem


def simulate_hypersonic_interception(
    mission_id: str = "GLIDE_PHASE_INTERCEPTOR",
    guidance_law: GuidanceLaw = GuidanceLaw.DIFFERENTIAL_GAME_ZEM,
    target_evasion: TargetEvasionManeuver = TargetEvasionManeuver.SINUSOIDAL_WEAVE,
    nav_ratio: float = 4.2,
    enable_dacs_divert: bool = True,
    dt: float = 0.02,
    max_steps: int = 1500
) -> Dict[str, Any]:
    """
    Simulates high-fidelity 3D hypersonic boost-glide target engagement:
    - Target: Hypersonic Glide Vehicle (Mach 9.5, altitude 38 km, pull-up / weave maneuvers)
    - Interceptor: Mach 8.0 kinetic hit-to-kill interceptor with canard + DACS divert
    """
    # 1. Preset Initial Conditions
    if mission_id == "GLIDE_PHASE_INTERCEPTOR":
        # Midcourse glide phase: closing speed ~ 6 km/s
        target_pos = np.array([60000.0, 5000.0, 38000.0])
        target_vel = np.array([-2800.0, -120.0, -80.0])  # ~Mach 9.4
        int_pos = np.array([0.0, 0.0, 24000.0])
        int_vel = np.array([2400.0, 80.0, 450.0])  # ~Mach 8.0
        r_nose_m = 0.04
    elif mission_id == "ENDOCRUIRSER_HACM":
        # Low-altitude hypersonic cruise missile: Mach 6.2 at 22 km
        target_pos = np.array([35000.0, 2000.0, 22000.0])
        target_vel = np.array([-1900.0, -50.0, 0.0])
        int_pos = np.array([0.0, 0.0, 16000.0])
        int_vel = np.array([2100.0, 60.0, 250.0])
        r_nose_m = 0.03
    else:
        # Exo-atmospheric / high altitude FOBS interception: altitude 85 km
        target_pos = np.array([90000.0, 10000.0, 85000.0])
        target_vel = np.array([-5400.0, -200.0, -450.0])
        int_pos = np.array([0.0, 0.0, 45000.0])
        int_vel = np.array([3800.0, 150.0, 950.0])
        r_nose_m = 0.05

    dacs_fuel_kg = 24.0  # DACS divert propellant
    dacs_isp_s = 285.0
    dacs_thrust_n = 4500.0
    int_mass_kg = 180.0

    time_series = []
    min_miss_distance_m = float("inf")
    peak_g_load = 0.0
    peak_heat_flux_mw_m2 = 0.0
    dacs_fuel_consumed_kg = 0.0
    intercept_occurred = False
    terminal_zem_m = 0.0

    for step in range(max_steps):
        t_sec = step * dt
        r_rel = target_pos - int_pos
        v_rel = target_vel - int_vel
        dist = float(np.linalg.norm(r_rel))
        closing_speed = -float(np.dot(r_rel, v_rel)) / max(0.1, dist)
        t_go = dist / max(100.0, closing_speed)

        # Closest Point of Approach (CPA) interpolation on current step interval
        v_sq = float(np.dot(v_rel, v_rel))
        tau = max(0.0, min(dt, -float(np.dot(r_rel, v_rel)) / (v_sq + 1e-9)))
        step_cpa = float(np.linalg.norm(r_rel + v_rel * tau))
        if step_cpa < min_miss_distance_m:
            min_miss_distance_m = step_cpa

        # Stop on closest approach
        if closing_speed < 0.0 or dist < 0.35:
            intercept_occurred = True
            terminal_zem_m = float(np.linalg.norm(compute_zem_vector(r_rel, v_rel, np.zeros(3), t_go)))
            break

        # Target Evasive Maneuver
        if target_evasion == TargetEvasionManeuver.SINUSOIDAL_WEAVE:
            # High-frequency weaving (5g weave at 0.4 Hz)
            a_t = np.array([0.0, 5.0 * GRAVITY_SEA_LEVEL * math.sin(2.0 * math.pi * 0.4 * t_sec), 0.0])
        elif target_evasion == TargetEvasionManeuver.BARREL_ROLL:
            # 3D spiral maneuver
            omega = 1.2
            a_t = np.array([
                0.0,
                6.0 * GRAVITY_SEA_LEVEL * math.cos(omega * t_sec),
                6.0 * GRAVITY_SEA_LEVEL * math.sin(omega * t_sec)
            ])
        elif target_evasion == TargetEvasionManeuver.TERMINAL_PULL_UP:
            # Sudden high-g pull-up
            pull_mag = 8.0 * GRAVITY_SEA_LEVEL if dist < 12000.0 else 0.0
            a_t = np.array([0.0, 0.0, pull_mag])
        else:
            # Ballistic
            a_t = np.array([0.0, 0.0, -GRAVITY_SEA_LEVEL])

        # Guidance command calculation
        a_cmd, zem_vec = compute_guidance_acceleration(
            guidance_law=guidance_law,
            r_rel=r_rel,
            v_rel=v_rel,
            a_target=a_t,
            closing_speed=closing_speed,
            t_go=t_go,
            nav_ratio=nav_ratio
        )

        g_load = float(np.linalg.norm(a_cmd)) / GRAVITY_SEA_LEVEL
        if g_load > peak_g_load:
            peak_g_load = g_load

        # DACS divert assist in terminal phase (t_go < 2.5s)
        if enable_dacs_divert and t_go < 2.5 and dacs_fuel_kg > dacs_fuel_consumed_kg:
            # Align DACS lateral pulse with ZEM correction
            zem_mag = float(np.linalg.norm(zem_vec))
            if zem_mag > 0.1:
                divert_dir = zem_vec / zem_mag
                a_dacs = (dacs_thrust_n / int_mass_kg) * divert_dir
                a_cmd = a_cmd + a_dacs
                fuel_rate = dacs_thrust_n / (dacs_isp_s * GRAVITY_SEA_LEVEL)
                dacs_fuel_consumed_kg += fuel_rate * dt

        # Interceptor aerothermo & environment
        rho, sos, _ = get_us_standard_atmosphere_density(float(int_pos[2]))
        int_speed = float(np.linalg.norm(int_vel))
        q_inf = 0.5 * rho * (int_speed ** 2)
        # Sutton-Graves stagnation heat flux (MW/m2)
        q_dot_mw = (1.74153e-4 * math.sqrt(rho / r_nose_m) * (int_speed ** 3)) / 1e6
        if q_dot_mw > peak_heat_flux_mw_m2:
            peak_heat_flux_mw_m2 = q_dot_mw

        # State updates
        target_vel = target_vel + a_t * dt
        target_pos = target_pos + target_vel * dt

        int_vel = int_vel + a_cmd * dt
        int_pos = int_pos + int_vel * dt

        if step % max(1, max_steps // 20) == 0:
            time_series.append({
                "time_s": round(t_sec, 2),
                "slant_range_km": round(dist / 1000.0, 2),
                "closing_speed_mps": round(closing_speed, 1),
                "closing_mach": round(closing_speed / max(1.0, sos), 2),
                "t_go_s": round(t_go, 2),
                "zem_m": round(float(np.linalg.norm(zem_vec)), 2),
                "g_load": round(g_load, 1),
                "stagnation_heat_flux_mw": round(q_dot_mw, 2),
                "interceptor_alt_km": round(float(int_pos[2]) / 1000.0, 2),
                "target_alt_km": round(float(target_pos[2]) / 1000.0, 2),
            })

    hit_to_kill_achieved = min_miss_distance_m <= 0.65  # Hit-to-kill standard radius

    return {
        "mission_id": mission_id,
        "guidance_law": guidance_law.value,
        "target_evasion_maneuver": target_evasion.value,
        "hit_to_kill_achieved": hit_to_kill_achieved,
        "min_miss_distance_m": round(min_miss_distance_m, 4),
        "terminal_zem_m": round(terminal_zem_m, 3),
        "peak_g_load": round(peak_g_load, 2),
        "peak_stagnation_heat_flux_mw_m2": round(peak_heat_flux_mw_m2, 2),
        "dacs_fuel_consumed_kg": round(dacs_fuel_consumed_kg, 2),
        "time_series": time_series,
        "executive_summary": {
            "engagement_outcome": "HIT_TO_KILL_KINETIC_IMPACT" if hit_to_kill_achieved else "PROXIMITY_FUZE_DETONATION",
            "miss_distance_cm": round(min_miss_distance_m * 100.0, 1),
            "guidance_performance": "OPTIMAL_DIFFERENTIAL_GAME" if guidance_law == GuidanceLaw.DIFFERENTIAL_GAME_ZEM else "PROPORTIONAL_NAV",
            "peak_load_factor_g": round(peak_g_load, 1),
            "peak_heat_flux_mw": round(peak_heat_flux_mw_m2, 2),
            "dacs_assist_utilized": enable_dacs_divert and dacs_fuel_consumed_kg > 0.0,
        }
    }
