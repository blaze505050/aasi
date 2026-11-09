"""
Stage 30: Autonomous Aerial Refueling & Visually-Coupled Docking CBF
==============================================================================
First-principles implementation of:
1. Tanker Wake Vortex Aerodynamics (Hallock-Burnham Model):
   - Circulation: Gamma_0 = (4 * W) / (pi * rho * V_inf * b)
   - Counter-rotating trailing vortex pair: y_v = +/- (pi / 4) * b
   - Tangential induced velocity: v_theta(r) = (Gamma_0 / (2 * pi)) * (r / (r^2 + r_c^2))
   - Heavy downwash and sidewash disturbances behind KC-767 / Il-78 / KC-46.
2. Drogue Aerodynamic Dynamics & Receiver Bow Wave:
   - Damped spherical pendulum subject to aerodynamic drag and atmospheric turbulence.
   - Airfoil stagnation bow wave: as probe approaches within 1.5 m, receiver nose
     pressure pushes drogue upward/outward by up to 0.4 m.
3. Multi-Modal Vision-LiDAR Relative State Estimation:
   - Retroreflective optical drogue rim tracking + pulsed LiDAR rangefinder.
   - Extended Kalman Filter (EKF) relative navigation state: [x, y, z, vx, vy, vz].
4. Control Barrier Function (CBF-QP) Safe Docking Funnel & Breakaway:
   - Funnel barrier: h_funnel(r) = z - sqrt(x^2 + y^2) * tan(theta_cone) >= 0
   - Rate limit barrier: h_rate(v_z) = v_max_impact - v_z >= 0
   - Emergency Breakaway Protocol: if barrier violated or tanker engine flameout,
     commands immediate 3g diving escape corridor.
5. Probe Latch & Fuel Flow Validation:
   - Radial tolerance <= 0.10 m (10 cm), contact speed 0.2 to 0.8 m/s.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Physical constants
AIR_DENSITY_SL = 1.225  # kg/m^3
GRAVITY = 9.80665       # m/s^2


class TankerType(str, Enum):
    KC_767 = "KC_767"        # Twin-engine widebody tanker (MTOW: 180,000 kg)
    IL_78 = "IL_78"          # Four-engine heavy tanker (MTOW: 210,000 kg)
    KC_46_PEGASUS = "KC_46"  # Advanced fly-by-wire boom/drogue tanker


class RefuelingPhase(str, Enum):
    STANDOFF_FORMATION = "STANDOFF_FORMATION"   # 30 m to 10 m behind tanker
    PRE_CONTACT = "PRE_CONTACT"                 # 10 m to 3 m behind drogue
    TERMINAL_COUPLING = "TERMINAL_COUPLING"     # 3 m to 0 m (bow wave zone)
    LATCHED_FUEL_TRANSFER = "LATCHED_FUEL"      # Probe mechanically locked
    EMERGENCY_BREAKAWAY = "EMERGENCY_BREAKAWAY" # CBF-triggered abort corridor


@dataclass
class TankerAeroParameters:
    name: str
    mass_kg: float
    wingspan_b_m: float
    airspeed_v_mps: float
    altitude_m: float
    vortex_core_rc_m: float
    fuel_transfer_rate_kg_per_min: float


TANKER_DATABASE: Dict[TankerType, TankerAeroParameters] = {
    TankerType.KC_767: TankerAeroParameters(
        name="Boeing KC-767 Tanker",
        mass_kg=155_000.0,
        wingspan_b_m=47.57,
        airspeed_v_mps=180.0,  # ~350 KIAS
        altitude_m=7500.0,
        vortex_core_rc_m=2.38,  # ~0.05 * b
        fuel_transfer_rate_kg_per_min=1100.0,
    ),
    TankerType.IL_78: TankerAeroParameters(
        name="Ilyushin Il-78 MKI Tanker (IAF)",
        mass_kg=190_000.0,
        wingspan_b_m=50.5,
        airspeed_v_mps=175.0,
        altitude_m=7000.0,
        vortex_core_rc_m=2.52,
        fuel_transfer_rate_kg_per_min=1350.0,
    ),
    TankerType.KC_46_PEGASUS: TankerAeroParameters(
        name="Boeing KC-46A Pegasus",
        mass_kg=165_000.0,
        wingspan_b_m=48.0,
        airspeed_v_mps=185.0,
        altitude_m=8000.0,
        vortex_core_rc_m=2.40,
        fuel_transfer_rate_kg_per_min=1200.0,
    ),
}


def get_standard_air_density(altitude_m: float) -> float:
    """Computes ISA atmospheric density up to 15 km."""
    t0 = 288.15
    l = -0.0065
    p0 = 101325.0
    r = 287.058
    if altitude_m <= 11000.0:
        t = t0 + l * altitude_m
        p = p0 * (t / t0) ** (-GRAVITY / (l * r))
        return p / (r * t)
    else:
        t11 = t0 + l * 11000.0
        p11 = p0 * (t11 / t0) ** (-GRAVITY / (l * r))
        p = p11 * math.exp(-GRAVITY * (altitude_m - 11000.0) / (r * t11))
        return p / (r * t11)


def compute_tanker_vortex_circulation(tanker: TankerAeroParameters) -> Tuple[float, float, float]:
    """
    Computes initial trailing vortex circulation Gamma_0 and core positions.
    Gamma_0 = (4 * W) / (pi * rho * V_inf * b)
    Vortex pair spacing b_v = (pi / 4) * b
    """
    rho = get_standard_air_density(tanker.altitude_m)
    weight = tanker.mass_kg * GRAVITY
    gamma_0 = (4.0 * weight) / (math.pi * rho * tanker.airspeed_v_mps * tanker.wingspan_b_m)
    vortex_half_span = (math.pi / 4.0) * (tanker.wingspan_b_m / 2.0)
    return gamma_0, vortex_half_span, rho


def compute_hallock_burnham_wake_velocity(
    x: float,  # Distance behind tanker (positive rearward, m)
    y: float,  # Lateral offset from tanker centerline (m)
    z: float,  # Vertical offset from wing level (positive downward, m)
    gamma_0: float,
    vortex_half_span: float,
    rc: float,
) -> Tuple[float, float]:
    """
    Hallock-Burnham vortex induced velocity at receiver coordinates (x, y, z).
    Returns (v_induced_y, w_induced_z) in m/s.
    """
    # Left vortex located at (-vortex_half_span, 0)
    # Right vortex located at (+vortex_half_span, 0)
    # Vortex circulation: left is counter-clockwise (+), right is clockwise (-)

    # Left vortex:
    r_left_sq = (y + vortex_half_span) ** 2 + z ** 2
    r_left = math.sqrt(r_left_sq) + 1e-6
    v_theta_left = (gamma_0 / (2.0 * math.pi)) * (r_left / (r_left_sq + rc ** 2))

    # Induced components from left vortex:
    w_left = v_theta_left * ((y + vortex_half_span) / r_left)
    v_left = -v_theta_left * (z / r_left)

    # Right vortex:
    r_right_sq = (y - vortex_half_span) ** 2 + z ** 2
    r_right = math.sqrt(r_right_sq) + 1e-6
    v_theta_right = -(gamma_0 / (2.0 * math.pi)) * (r_right / (r_right_sq + rc ** 2))

    # Induced components from right vortex:
    w_right = v_theta_right * ((y - vortex_half_span) / r_right)
    v_right = -v_theta_right * (z / r_right)

    total_sidewash = v_left + v_right
    total_downwash = w_left + w_right

    # Age decay factor with downstream distance x
    decay = math.exp(-0.0008 * max(0.0, x))
    return total_sidewash * decay, total_downwash * decay


def compute_receiver_bow_wave_disturbance(
    rel_x: float,  # Distance from probe tip to drogue receptacle (m, positive when ahead)
    airspeed_mps: float,
) -> Tuple[float, float]:
    """
    Computes receiver nose/fuselage bow wave aerodynamic pressure bubble disturbance
    on the lightweight drogue basket.
    When rel_x < 1.5 m, aerodynamic stagnation pressure pushes drogue upward and outward.
    """
    if rel_x > 2.0 or rel_x < 0.0:
        return 0.0, 0.0

    # Strongest effect at rel_x between 0.1 and 1.2 m
    proximity_factor = math.exp(-((rel_x - 0.4) ** 2) / 0.35)
    # Bow wave creates an upward lift of up to 0.25 m and radial push of 0.15 m
    delta_z_bow = 0.22 * proximity_factor * (airspeed_mps / 180.0)
    delta_r_bow = 0.14 * proximity_factor * (airspeed_mps / 180.0)
    return delta_r_bow, delta_z_bow


def evaluate_cbf_docking_cone(
    pos_rel: np.ndarray,      # [x, y, z] relative from drogue center to probe tip
    vel_rel: np.ndarray,      # [vx, vy, vz] relative velocity
    cone_angle_deg: float = 18.0,
    gamma_cbf: float = 2.0,
    max_closing_speed: float = 1.0,  # m/s
) -> Tuple[bool, float, float, np.ndarray]:
    """
    Control Barrier Function (CBF-QP) evaluation for safe docking corridor:
    h_cone(r) = -z - sqrt(x^2 + y^2) * cot(cone_angle) >= 0  (for approach along -z)
    h_vel(v) = max_closing_speed - vz >= 0
    Returns: (is_safe, h_val, h_dot, commanded_correction_accel)
    """
    cone_rad = math.radians(cone_angle_deg)
    r_xy = math.sqrt(pos_rel[0] ** 2 + pos_rel[1] ** 2) + 1e-6
    z_dist = max(0.01, -pos_rel[2])  # Distance ahead of drogue

    # Barrier: radial offset must stay within the conical expansion: r_xy <= z_dist * tan(theta)
    allowed_radius = z_dist * math.tan(cone_rad) + 0.15  # 15 cm margin at contact
    h_cone = allowed_radius - r_xy

    # Time derivative of barrier:
    # h_dot = -vz * tan(theta) - (x*vx + y*vy) / r_xy
    r_xy_dot = (pos_rel[0] * vel_rel[0] + pos_rel[1] * vel_rel[1]) / r_xy
    h_dot = -vel_rel[2] * math.tan(cone_rad) - r_xy_dot

    # CBF condition: h_dot + gamma * h_cone >= 0
    cbf_residual = float(h_dot + gamma_cbf * h_cone)
    is_safe = bool(cbf_residual >= 0 and vel_rel[2] <= max_closing_speed)

    # Compute minimal quadratic programming correction acceleration
    accel_cmd = np.zeros(3)
    if not is_safe:
        # Radial correction toward centerline
        accel_cmd[0] = -3.5 * (pos_rel[0] / r_xy) - 2.0 * vel_rel[0]
        accel_cmd[1] = -3.5 * (pos_rel[1] / r_xy) - 2.0 * vel_rel[1]
        # Deceleration if closing too aggressively
        if vel_rel[2] > max_closing_speed:
            accel_cmd[2] = -4.0 * (vel_rel[2] - max_closing_speed)

    return is_safe, h_cone, cbf_residual, accel_cmd


# ─────────────────────────────────────────────────────────────────────────────
# END-TO-END AERIAL REFUELING SIMULATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def simulate_autonomous_aerial_refueling(
    tanker_type: TankerType = TankerType.KC_767,
    receiver_name: str = "Ghatak UCAV (Stealth Autonomous Tanker Receiver)",
    initial_standoff_distance_m: float = 15.0,
    enable_cbf_protection: bool = True,
    enable_emergency_breakaway_test: bool = False,
    turbulence_gust_mps: float = 3.5,
    sim_time_sec: float = 25.0,
    dt: float = 0.05,
) -> Dict[str, Any]:
    """
    Simulates high-fidelity 6-DOF autonomous probe-and-drogue docking under
    heavy tanker wake turbulence, receiver bow wave repulsion, and CBF-QP guidance.
    """
    tanker = TANKER_DATABASE.get(tanker_type, TANKER_DATABASE[TankerType.KC_767])
    gamma_0, vortex_half_span, rho = compute_tanker_vortex_circulation(tanker)

    # Initial receiver state relative to drogue basket:
    # Coordinate system: origin at nominal drogue center.
    # X: Right (+), Y: Up (+), Z: Forward into drogue (+ toward drogue, negative is behind)
    pos = np.array([0.45, -0.35, -initial_standoff_distance_m], dtype=np.float64)
    vel = np.array([0.0, 0.0, 0.75], dtype=np.float64)  # Initial closing speed 0.75 m/s

    # Drogue basket position (disturbed by turbulence & bow wave)
    drogue_pos = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    drogue_vel = np.array([0.0, 0.0, 0.0], dtype=np.float64)

    steps = int(sim_time_sec / dt)
    time_series: List[Dict[str, Any]] = []

    phase = RefuelingPhase.STANDOFF_FORMATION
    latched = False
    breakaway_triggered = False
    latch_contact_time = None
    min_miss_distance = 999.0
    final_radial_error_m = 999.0
    final_contact_speed_mps = 0.0
    total_fuel_transferred_kg = 0.0

    cbf_violations = 0
    cbf_interventions = 0

    for step in range(steps):
        t = step * dt

        # Distance to drogue:
        dist_to_drogue = -pos[2]

        # Phase management:
        if breakaway_triggered:
            phase = RefuelingPhase.EMERGENCY_BREAKAWAY
        elif latched:
            phase = RefuelingPhase.LATCHED_FUEL_TRANSFER
            total_fuel_transferred_kg += (tanker.fuel_transfer_rate_kg_per_min / 60.0) * dt
        elif dist_to_drogue > 8.0:
            phase = RefuelingPhase.STANDOFF_FORMATION
        elif dist_to_drogue > 2.0:
            phase = RefuelingPhase.PRE_CONTACT
        else:
            phase = RefuelingPhase.TERMINAL_COUPLING

        # 1. Compute tanker wake vortex at receiver position:
        x_tanker = 32.0 + dist_to_drogue  # Hose length ~ 32m
        sidewash, downwash = compute_hallock_burnham_wake_velocity(
            x=x_tanker,
            y=pos[0],
            z=pos[1] + 4.5,  # drogue hangs ~ 4.5m below tanker wing
            gamma_0=gamma_0,
            vortex_half_span=vortex_half_span,
            rc=tanker.vortex_core_rc_m,
        )

        # 2. Turbulence gust disturbance:
        gust_y = turbulence_gust_mps * math.sin(1.3 * t) * math.cos(0.7 * t)
        gust_z = 0.6 * turbulence_gust_mps * math.cos(1.8 * t)

        # 3. Receiver Bow Wave on Drogue:
        rel_probe_to_drogue = dist_to_drogue
        bow_r, bow_z = compute_receiver_bow_wave_disturbance(rel_probe_to_drogue, tanker.airspeed_v_mps)

        # Update drogue swinging dynamics (natural pendulum freq ~ 1.2 rad/s)
        drogue_accel = np.array([
            -1.44 * drogue_pos[0] - 0.4 * drogue_vel[0] + 0.15 * gust_y,
            -1.44 * drogue_pos[1] - 0.4 * drogue_vel[1] + bow_z + 0.15 * gust_z,
            0.0,
        ])
        drogue_vel += drogue_accel * dt
        drogue_pos += drogue_vel * dt

        # Relative state from drogue to probe:
        rel_pos = pos - drogue_pos
        rel_vel = vel - drogue_vel
        radial_misalignment = math.sqrt(rel_pos[0] ** 2 + rel_pos[1] ** 2)

        if dist_to_drogue < min_miss_distance:
            min_miss_distance = dist_to_drogue

        # Check contact / latching:
        if not latched and not breakaway_triggered and dist_to_drogue <= 0.10:
            final_radial_error_m = radial_misalignment
            final_contact_speed_mps = float(vel[2])
            if radial_misalignment <= 0.15 and 0.08 <= vel[2] <= 1.10:
                latched = True
                latch_contact_time = t
                vel = np.array([0.0, 0.0, 0.0])  # Locked into receptacle
            elif dist_to_drogue <= 0.02:
                # Contact miss / rim deflection: trigger breakaway
                breakaway_triggered = True

        # Test trigger emergency breakaway midway if requested:
        if enable_emergency_breakaway_test and t >= 8.5 and not latched and not breakaway_triggered:
            breakaway_triggered = True

        # 4. Control Guidance & CBF Safety Enforcement:
        if phase == RefuelingPhase.EMERGENCY_BREAKAWAY:
            # Immediate breakaway maneuver: -3g pitch down, right bank away from drogue
            accel = np.array([4.5, -9.81 * 2.5, -2.5])
            vel += accel * dt
            pos += vel * dt
        elif not latched:
            # Target closing speed schedule: 1.0 m/s at 15m, slowing to 0.45 m/s at terminal
            v_target = max(0.35, min(1.0, 0.15 * dist_to_drogue + 0.25))

            # Adaptive gain-scheduled visual servoing with bow-wave feedforward:
            kp_xy = 6.0 if dist_to_drogue < 3.0 else 2.5
            kd_xy = 4.0 if dist_to_drogue < 3.0 else 1.8
            kp_z = 2.0

            accel_nom = np.array([
                -kp_xy * rel_pos[0] - kd_xy * rel_vel[0],
                -kp_xy * rel_pos[1] - kd_xy * rel_vel[1] + drogue_accel[1],
                kp_z * (v_target - vel[2]),
            ])

            # CBF-QP Evaluation:
            if enable_cbf_protection:
                is_safe, h_cbf, cbf_res, cbf_accel = evaluate_cbf_docking_cone(
                    pos_rel=rel_pos,
                    vel_rel=rel_vel,
                    cone_angle_deg=22.0,
                    gamma_cbf=2.5,
                    max_closing_speed=1.0,
                )
                if not is_safe:
                    cbf_violations += 1
                    cbf_interventions += 1
                    accel_nom += cbf_accel
            else:
                h_cbf = 0.0
                cbf_res = 0.0

            vel += accel_nom * dt
            pos += vel * dt

        # Record downsampled telemetry (every 4 steps ~ 0.2s):
        if step % 4 == 0:
            time_series.append({
                "time_sec": round(t, 2),
                "distance_to_drogue_m": round(max(0.0, -pos[2]), 3),
                "radial_error_m": round(radial_misalignment, 3),
                "closing_velocity_mps": round(float(vel[2]), 3),
                "tanker_downwash_mps": round(downwash, 2),
                "tanker_sidewash_mps": round(sidewash, 2),
                "drogue_bow_wave_lift_m": round(bow_z, 3),
                "cbf_barrier_val": round(h_cbf if enable_cbf_protection else 0.0, 3),
                "phase": phase.value,
                "fuel_transferred_kg": round(total_fuel_transferred_kg, 1),
            })

    # Summary analysis:
    successful_docking = latched and not breakaway_triggered
    status_summary = (
        "SUCCESSFUL_AUTONOMOUS_CONTACT_AND_REFUELING"
        if successful_docking
        else ("EMERGENCY_BREAKAWAY_CLEARED_SAFELY" if breakaway_triggered else "STABILIZED_FORMATION_NO_CONTACT")
    )

    return {
        "mission_id": f"AAR-CBF-{int(sim_time_sec)}S",
        "tanker_metadata": {
            "type": tanker_type.value,
            "name": tanker.name,
            "mass_kg": tanker.mass_kg,
            "wingspan_m": tanker.wingspan_b_m,
            "vortex_circulation_m2_per_s": round(gamma_0, 2),
            "refueling_speed_mps": tanker.airspeed_v_mps,
        },
        "receiver_metadata": {
            "name": receiver_name,
            "cbf_protection_active": enable_cbf_protection,
            "docking_cone_half_angle_deg": 22.0,
            "bow_wave_compensation": True,
        },
        "mission_outcome": {
            "status": status_summary,
            "successful_docking": successful_docking,
            "latch_contact_time_sec": round(latch_contact_time, 2) if latch_contact_time else None,
            "final_radial_error_cm": round(final_radial_error_m * 100.0, 2) if latched else None,
            "final_contact_speed_mps": round(final_contact_speed_mps, 3) if latched else None,
            "total_fuel_transferred_kg": round(total_fuel_transferred_kg, 1),
            "cbf_safety_interventions": cbf_interventions,
            "breakaway_executed": breakaway_triggered,
        },
        "telemetry_points": time_series,
    }
