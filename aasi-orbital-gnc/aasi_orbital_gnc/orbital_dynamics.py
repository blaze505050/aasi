"""
AASI 6-DOF Relative Orbital Dynamics & Vehicle Parameterizations.
Models coupled translational (Hill-Clohessy-Wiltshire + J2 + Drag)
and rotational (Euler equations with inertia tensor) dynamics
for SpaDeX, Chandrayaan-4, and the Bharatiya Antariksh Station (BAS-01).
"""

from __future__ import annotations

import math
import numpy as np
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field


class OrbitalVehicleConfig(BaseModel):
    vehicle_name: str
    mass_kg: float
    inertia_tensor_kg_m2: Tuple[float, float, float]  # (Ixx, Iyy, Izz)
    docking_port_diameter_mm: float
    max_rcs_thrust_n: float
    approach_cone_angle_deg: float = 10.0
    nominal_altitude_km: float = 470.0
    orbit_eccentricity: float = 0.001
    terminal_docking_speed_limit_mps: float = 0.015  # 15 mm/s maximum capture


# ISRO Vehicle Presets
SPADEX_CONFIG = OrbitalVehicleConfig(
    vehicle_name="ISRO SpaDeX (SDX01 Chaser / SDX02 Target)",
    mass_kg=220.0,
    inertia_tensor_kg_m2=(42.5, 38.2, 51.0),
    docking_port_diameter_mm=450.0,
    max_rcs_thrust_n=10.0,
    nominal_altitude_km=470.0,
    orbit_eccentricity=0.0012,
    terminal_docking_speed_limit_mps=0.012,
)

CHANDRAYAAN4_CONFIG = OrbitalVehicleConfig(
    vehicle_name="ISRO Chandrayaan-4 (5-Module Lunar Sample Stack)",
    mass_kg=9200.0,
    inertia_tensor_kg_m2=(8450.0, 7920.0, 9150.0),
    docking_port_diameter_mm=450.0,
    max_rcs_thrust_n=440.0,
    nominal_altitude_km=100.0,  # Low Lunar Orbit
    orbit_eccentricity=0.025,
    terminal_docking_speed_limit_mps=0.010,
)

BAS01_CONFIG = OrbitalVehicleConfig(
    vehicle_name="Bharatiya Antariksh Station (BAS-01 Module)",
    mass_kg=20000.0,
    inertia_tensor_kg_m2=(65000.0, 58000.0, 72000.0),
    docking_port_diameter_mm=800.0,
    max_rcs_thrust_n=800.0,
    nominal_altitude_km=400.0,
    orbit_eccentricity=0.0005,
    terminal_docking_speed_limit_mps=0.015,
)


class OrbitalState6DOF(BaseModel):
    # Relative translational state in Hill/LVLH frame:
    # x: Radial (outward from Earth center)
    # y: Along-track / V-bar (along velocity vector)
    # z: Cross-track (normal to orbital plane)
    rel_pos_m: Tuple[float, float, float] = (0.0, 225.0, 0.0)  # Starts at 225m drift anomaly point
    rel_vel_mps: Tuple[float, float, float] = (0.0, -0.15, 0.0)  # Closing along V-bar

    # Rotational state: Euler angles (roll, pitch, yaw) in deg and rates in rad/s
    attitude_deg: Tuple[float, float, float] = (0.5, -0.2, 0.8)
    angular_velocity_rad_s: Tuple[float, float, float] = (0.001, -0.002, 0.001)

    time_s: float = 0.0
    mass_kg: float = 220.0
    fuel_remaining_kg: float = 18.5


class RelativeOrbitalDynamics6DOF:
    """
    Integrates coupled 6-DOF equations of relative orbital motion.
    Features Hill-Clohessy-Wiltshire (HCW) with J2 oblateness perturbation
    and differential thermospheric drag.
    """

    MU_EARTH = 3.986004418e14  # m^3/s^2
    R_EARTH = 6378137.0  # m
    J2_EARTH = 1.08263e-3

    def __init__(self, config: OrbitalVehicleConfig):
        self.config = config
        self.orbital_radius = self.R_EARTH + (config.nominal_altitude_km * 1000.0)
        # Mean motion omega = sqrt(mu / r^3)
        self.omega = math.sqrt(self.MU_EARTH / (self.orbital_radius ** 3))

    def compute_j2_acceleration(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """Differential J2 perturbation in LVLH frame."""
        r = self.orbital_radius + x
        factor = 1.5 * self.J2_EARTH * self.MU_EARTH * (self.R_EARTH ** 2) / (r ** 4)
        a_j2_x = factor * (1.0 - 3.0 * (z / r) ** 2) * 1e-4
        a_j2_y = 0.0
        a_j2_z = factor * (2.0 * z / r) * 1e-4
        return a_j2_x, a_j2_y, a_j2_z

    def compute_differential_drag(self, vy: float) -> float:
        """Atmospheric drag perturbation along velocity vector V-bar."""
        rho_atm = 1.8e-12  # kg/m^3 at 470 km
        v_orb = self.omega * self.orbital_radius
        drag_accel = -0.5 * rho_atm * (v_orb ** 2) * (2.2 * 1.5 / self.config.mass_kg) * 1e-3
        return drag_accel

    def step_rk4(
        self,
        current_state: OrbitalState6DOF,
        rcs_force_n: Tuple[float, float, float],
        rcs_torque_nm: Tuple[float, float, float],
        dt: float = 0.1,
    ) -> OrbitalState6DOF:
        """
        4th-order Runge-Kutta numerical integration of coupled 6-DOF state.
        """
        # Mass depletion
        thrust_mag = math.sqrt(sum(f ** 2 for f in rcs_force_n))
        mass_flow = thrust_mag / (220.0 * 9.80665)  # Isp ~ 220s for cold-gas/hydrazine
        new_fuel = max(0.0, current_state.fuel_remaining_kg - mass_flow * dt)
        current_mass = self.config.mass_kg - (self.config.mass_kg * 0.1) + new_fuel

        # Translational derivatives: HCW + J2 + Drag
        def deriv_trans(pos, vel):
            x, y, z = pos
            vx, vy, vz = vel
            a_j2_x, a_j2_y, a_j2_z = self.compute_j2_acceleration(x, y, z)
            a_drag = self.compute_differential_drag(vy)

            # Hill-Clohessy-Wiltshire equations:
            # x_ddot = 2 * omega * y_dot + 3 * omega^2 * x + Fx/m + J2_x
            # y_ddot = -2 * omega * x_dot + Fy/m + J2_y + Drag
            # z_ddot = -omega^2 * z + Fz/m + J2_z
            ax = 2.0 * self.omega * vy + 3.0 * (self.omega ** 2) * x + (rcs_force_n[0] / current_mass) + a_j2_x
            ay = -2.0 * self.omega * vx + (rcs_force_n[1] / current_mass) + a_j2_y + a_drag
            az = -(self.omega ** 2) * z + (rcs_force_n[2] / current_mass) + a_j2_z
            return np.array([vx, vy, vz]), np.array([ax, ay, az])

        # RK4 integration for translation
        p0 = np.array(current_state.rel_pos_m)
        v0 = np.array(current_state.rel_vel_mps)

        k1_v, k1_a = deriv_trans(p0, v0)
        k2_v, k2_a = deriv_trans(p0 + 0.5 * dt * k1_v, v0 + 0.5 * dt * k1_a)
        k3_v, k3_a = deriv_trans(p0 + 0.5 * dt * k2_v, v0 + 0.5 * dt * k2_a)
        k4_v, k4_a = deriv_trans(p0 + dt * k3_v, v0 + dt * k3_a)

        new_pos = p0 + (dt / 6.0) * (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v)
        new_vel = v0 + (dt / 6.0) * (k1_a + 2.0 * k2_a + 2.0 * k3_a + k4_a)

        # Rotational derivatives: Euler's equations
        Ixx, Iyy, Izz = self.config.inertia_tensor_kg_m2
        w = np.array(current_state.angular_velocity_rad_s)
        tau = np.array(rcs_torque_nm)

        # dw_x = (tau_x - (Izz - Iyy) * wy * wz) / Ixx
        # dw_y = (tau_y - (Ixx - Izz) * wx * wz) / Iyy
        # dw_z = (tau_z - (Iyy - Ixx) * wx * wy) / Izz
        dw_x = (tau[0] - (Izz - Iyy) * w[1] * w[2]) / Ixx
        dw_y = (tau[1] - (Ixx - Izz) * w[0] * w[2]) / Iyy
        dw_z = (tau[2] - (Iyy - Ixx) * w[0] * w[1]) / Izz
        alpha_ang = np.array([dw_x, dw_y, dw_z])

        new_w = w + alpha_ang * dt
        # Integrate Euler angles
        att_deg = np.array(current_state.attitude_deg) + np.degrees(new_w * dt)

        return OrbitalState6DOF(
            rel_pos_m=(float(new_pos[0]), float(new_pos[1]), float(new_pos[2])),
            rel_vel_mps=(float(new_vel[0]), float(new_vel[1]), float(new_vel[2])),
            attitude_deg=(float(att_deg[0]), float(att_deg[1]), float(att_deg[2])),
            angular_velocity_rad_s=(float(new_w[0]), float(new_w[1]), float(new_w[2])),
            time_s=current_state.time_s + dt,
            mass_kg=current_mass,
            fuel_remaining_kg=new_fuel,
        )

