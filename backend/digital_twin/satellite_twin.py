"""
AASI 2.0 Satellite Digital Twin — J2 Orbital Perturbations, Eclipse Power & Thermal Dynamics.

Deterministic orbital mechanics engine:
- Keplerian orbit propagation + Earth oblateness J2 nodal regression and perigee rotation
- Atmospheric drag orbital decay & LEO lifetime estimation (scale-height density)
- Solar illumination & cylindrical Earth shadow eclipse model
- Solar array electrical generation & Li-Ion battery depth-of-discharge (DoD)
- Stefan-Boltzmann thermal radiation equilibrium (solar, Earth albedo, Earth IR, internal)
- Fault injection: Solar array degradation, reaction wheel saturation, geomagnetic drag surge
"""

from __future__ import annotations

import math
import uuid
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.digital_twin.models import (
    VehicleType,
    SimulationMode,
    FaultType,
    FaultInjectionConfig,
    TelemetryFrame,
    MissionEvent,
    DigitalTwinSimulationResult,
)


class SatelliteDigitalTwinConfig(BaseModel):
    vehicle_name: str = "AASI-Sentinel-LEO"
    satellite_mass_kg: float = 380.0
    cross_section_area_m2: float = 2.4
    drag_coefficient_cd: float = 2.2
    initial_altitude_km: float = 520.0
    inclination_deg: float = 97.4  # Sun-synchronous orbit
    eccentricity: float = 0.0012
    solar_array_area_m2: float = 3.6
    solar_cell_efficiency: float = 0.30  # Triple-junction GaAs
    battery_capacity_wh: float = 2400.0
    internal_power_consumption_w: float = 280.0
    thermal_absorptivity_alpha: float = 0.25
    thermal_emissivity_epsilon: float = 0.85
    radiator_area_m2: float = 2.2
    simulation_orbits: float = 3.0
    time_step_s: float = 10.0


class SatelliteDigitalTwin:
    """Deterministic Low Earth Orbit (LEO) Satellite Simulator."""

    EARTH_RADIUS_M = 6378137.0
    EARTH_MU = 3.986004418e14
    EARTH_J2 = 1.08263e-3
    SOLAR_FLUX_W_M2 = 1361.0
    STEFAN_BOLTZMANN = 5.670374419e-8
    EARTH_ALBEDO = 0.30
    EARTH_IR_W_M2 = 237.0

    @classmethod
    def leo_atmospheric_density(cls, altitude_km: float) -> float:
        """Jacchia/Harris-Priester exponential scale height density (kg/m³)."""
        h = max(150.0, altitude_km)
        # Empirical baseline fit for 400-800 km
        # At 500 km, rho ~ 1.5e-12 kg/m³
        return 1.5e-12 * math.exp(-(h - 500.0) / 62.0)

    @classmethod
    def simulate(
        cls,
        config: Optional[SatelliteDigitalTwinConfig] = None,
        fault: Optional[FaultInjectionConfig] = None,
    ) -> DigitalTwinSimulationResult:
        cfg = config or SatelliteDigitalTwinConfig()
        dt = cfg.time_step_s

        r_orbit_m = cls.EARTH_RADIUS_M + (cfg.initial_altitude_km * 1000.0)
        semi_major_axis_m = r_orbit_m
        ecc = cfg.eccentricity
        inc_rad = math.radians(cfg.inclination_deg)

        # Orbital period: T = 2*pi*sqrt(a^3 / mu)
        period_s = 2.0 * math.pi * math.sqrt((semi_major_axis_m ** 3) / cls.EARTH_MU)
        total_sim_time = period_s * cfg.simulation_orbits

        # J2 Nodal Precession rate dOmega/dt (rad/s)
        mean_motion = math.sqrt(cls.EARTH_MU / (semi_major_axis_m ** 3))
        p_param = semi_major_axis_m * (1.0 - ecc ** 2)
        raan_drift_rate_rad_s = -1.5 * cls.EARTH_J2 * ((cls.EARTH_RADIUS_M / p_param) ** 2) * mean_motion * math.cos(inc_rad)

        time_s = 0.0
        raan_deg = 45.0
        true_anomaly_rad = 0.0

        current_battery_wh = cfg.battery_capacity_wh
        max_dod_pct = 0.0
        total_altitude_loss_m = 0.0

        solar_health = 1.0
        drag_multiplier = 1.0
        attitude_jitter_arcsec = 1.2

        frames: List[TelemetryFrame] = []
        events: List[MissionEvent] = []
        safety_violations: List[str] = []

        events.append(MissionEvent(timestamp_s=0.0, event_name="ORBIT_PROPAGATION_START", description=f"Initial orbit: {cfg.initial_altitude_km:.1f} km SSO (i={cfg.inclination_deg:.1f}°). Period: {period_s/60.0:.1f} min."))

        in_eclipse_prev = False
        step_counter = 0
        sampling_stride = max(1, int(30.0 / dt))  # Store frame every 30s

        min_temp_c = 100.0
        max_temp_c = -100.0

        while time_s <= total_sim_time:
            step_counter += 1
            current_alt_km = (semi_major_axis_m - cls.EARTH_RADIUS_M) / 1000.0

            # Fault injection check
            if fault and (fault.target_vehicle is None or fault.target_vehicle == VehicleType.SATELLITE):
                if time_s >= fault.onset_time_s:
                    if fault.fault_type == FaultType.SOLAR_PANEL_DEGRADATION:
                        solar_health = max(0.1, 1.0 - fault.severity)
                        if not any(e.event_name == "FAULT_SOLAR_DEGRADATION" for e in events):
                            events.append(
                                MissionEvent(
                                    timestamp_s=round(time_s, 1),
                                    event_name="FAULT_SOLAR_DEGRADATION",
                                    description=f"Solar panel bus string fault! Array output reduced by {fault.severity*100:.0f}%.",
                                    severity="CRITICAL",
                                )
                            )
                            safety_violations.append(f"Solar array power loss of {fault.severity*100:.0f}% at t={time_s:.0f}s")
                    elif fault.fault_type == FaultType.ATMOSPHERIC_DRAG_SURGE:
                        drag_multiplier = 1.0 + 3.5 * fault.severity
                        if not any(e.event_name == "FAULT_DRAG_SURGE" for e in events):
                            events.append(
                                MissionEvent(
                                    timestamp_s=round(time_s, 1),
                                    event_name="FAULT_DRAG_SURGE",
                                    description="Severe geomagnetic space weather event! Upper thermosphere density surged 350%.",
                                    severity="WARNING",
                                )
                            )
                    elif fault.fault_type == FaultType.REACTION_WHEEL_DESAT:
                        attitude_jitter_arcsec = 18.0 * fault.severity

            # Orbital Position & True Anomaly
            true_anomaly_rad += mean_motion * dt
            current_r = (semi_major_axis_m * (1.0 - ecc ** 2)) / (1.0 + ecc * math.cos(true_anomaly_rad))
            vel_orbital_ms = math.sqrt(cls.EARTH_MU * (2.0 / current_r - 1.0 / semi_major_axis_m))

            # J2 RAAN regression
            raan_deg += math.degrees(raan_drift_rate_rad_s) * dt

            # Earth Eclipse Shadow Geometry
            # For cylindrical shadow: angle around orbit from subsolar point
            orbit_phase = (true_anomaly_rad % (2.0 * math.pi))
            # Eclipse occurs when satellite is behind Earth relative to sun (approx 120 deg arc)
            eclipse_half_angle = math.asin(cls.EARTH_RADIUS_M / current_r)
            in_eclipse = (math.pi - eclipse_half_angle) < orbit_phase < (math.pi + eclipse_half_angle)

            if in_eclipse and not in_eclipse_prev:
                events.append(MissionEvent(timestamp_s=round(time_s, 1), event_name="UMBRA_ENTRY", description="Entering Earth eclipse (umbra). Solar generation offline; battery discharge active."))
            elif not in_eclipse and in_eclipse_prev:
                events.append(MissionEvent(timestamp_s=round(time_s, 1), event_name="UMBRA_EXIT", description="Emerging into sunlight. Solar array re-illuminated; battery fast-charge engaged."))
            in_eclipse_prev = in_eclipse

            # Atmospheric Drag Orbital Decay
            rho = cls.leo_atmospheric_density(current_alt_km) * drag_multiplier
            drag_force_n = 0.5 * rho * (vel_orbital_ms ** 2) * cfg.cross_section_area_m2 * cfg.drag_coefficient_cd
            # da/dt = - rho * sqrt(mu * a) * (Cd * A / m)
            da_dt = -rho * math.sqrt(cls.EARTH_MU * semi_major_axis_m) * (cfg.drag_coefficient_cd * cfg.cross_section_area_m2 / cfg.satellite_mass_kg)
            semi_major_axis_m += da_dt * dt
            total_altitude_loss_m += abs(da_dt * dt)

            # Power Generation & Battery State
            if in_eclipse:
                solar_power_gen_w = 0.0
                battery_drain_w = cfg.internal_power_consumption_w
                current_battery_wh = max(0.0, current_battery_wh - (battery_drain_w * dt) / 3600.0)
            else:
                sun_incidence = max(0.0, math.cos(orbit_phase - math.pi / 2.0))
                solar_power_gen_w = (
                    cls.SOLAR_FLUX_W_M2 * cfg.solar_array_area_m2 * cfg.solar_cell_efficiency * solar_health * max(0.2, sun_incidence)
                )
                net_recharge_w = max(0.0, solar_power_gen_w - cfg.internal_power_consumption_w)
                current_battery_wh = min(cfg.battery_capacity_wh, current_battery_wh + (net_recharge_w * 0.92 * dt) / 3600.0)

            battery_soc_pct = (current_battery_wh / cfg.battery_capacity_wh) * 100.0
            dod_pct = 100.0 - battery_soc_pct
            if dod_pct > max_dod_pct:
                max_dod_pct = dod_pct

            # Thermal Balance (Stefan-Boltzmann radiation equilibrium)
            if in_eclipse:
                q_in = cfg.internal_power_consumption_w + cls.EARTH_IR_W_M2 * 0.5 * cfg.radiator_area_m2
            else:
                q_solar = cls.SOLAR_FLUX_W_M2 * cfg.thermal_absorptivity_alpha * (cfg.cross_section_area_m2 * 0.6)
                q_albedo = cls.SOLAR_FLUX_W_M2 * cls.EARTH_ALBEDO * 0.25 * cfg.radiator_area_m2
                q_earth_ir = cls.EARTH_IR_W_M2 * 0.5 * cfg.radiator_area_m2
                q_in = q_solar + q_albedo + q_earth_ir + cfg.internal_power_consumption_w

            # Q_out = epsilon * sigma * A_rad * T^4
            temp_k = ((q_in) / max(1e-8, cfg.thermal_emissivity_epsilon * cls.STEFAN_BOLTZMANN * cfg.radiator_area_m2)) ** 0.25
            temp_c = temp_k - 273.15
            if temp_c > max_temp_c:
                max_temp_c = temp_c
            if temp_c < min_temp_c:
                min_temp_c = temp_c

            # Telemetry Frame Recording
            if step_counter % sampling_stride == 0 or time_s >= total_sim_time:
                frames.append(
                    TelemetryFrame(
                        timestamp_s=round(time_s, 1),
                        altitude_m=round(current_alt_km * 1000.0, 1),
                        velocity_ms=round(vel_orbital_ms, 1),
                        mach=round(vel_orbital_ms / 300.0, 2),
                        dynamic_pressure_pa=round(0.5 * rho * (vel_orbital_ms ** 2), 6),
                        acceleration_g=round((cls.EARTH_MU / (current_r ** 2)) / 9.80665, 3),
                        mass_kg=round(cfg.satellite_mass_kg, 1),
                        propellant_or_battery_pct=round(battery_soc_pct, 1),
                        temperature_c=round(temp_c, 1),
                        subsystem_health={
                            "solar_arrays": round(solar_health, 2),
                            "battery": round(battery_soc_pct / 100.0, 2),
                            "reaction_wheels": round(max(0.0, 1.0 - (attitude_jitter_arcsec / 20.0)), 2),
                            "payload_telemetry": 1.0,
                        },
                        vehicle_specific={
                            "in_eclipse": in_eclipse,
                            "solar_power_w": round(solar_power_gen_w, 1),
                            "battery_wh": round(current_battery_wh, 1),
                            "drag_force_mn": round(drag_force_n * 1000.0, 3),
                            "raan_deg": round(raan_deg, 3),
                            "orbital_period_min": round(period_s / 60.0, 2),
                            "attitude_jitter_arcsec": round(attitude_jitter_arcsec, 2),
                        },
                    )
                )

            time_s += dt

        # Estimate orbital lifetime in years:
        # Lifetime ~ H / (365.25 * 86400 * |da/dt|_avg)
        avg_da_dt_day = abs(da_dt) * 86400.0
        decay_years = ((cfg.initial_altitude_km - 180.0) * 1000.0) / max(1e-4, avg_da_dt_day * 365.25)

        passed = len(safety_violations) == 0 and max_dod_pct < 35.0 and max_temp_c < 65.0 and min_temp_c > -40.0

        summary = {
            "orbits_simulated": cfg.simulation_orbits,
            "orbit_period_min": round(period_s / 60.0, 2),
            "raan_precession_deg_day": round(math.degrees(raan_drift_rate_rad_s) * 86400.0, 3),
            "eclipse_time_per_orbit_min": round((eclipse_half_angle / math.pi) * (period_s / 60.0), 1),
            "max_depth_of_discharge_pct": round(max_dod_pct, 1),
            "thermal_min_c": round(min_temp_c, 1),
            "thermal_max_c": round(max_temp_c, 1),
            "total_orbit_decay_m": round(total_altitude_loss_m, 2),
            "projected_orbital_lifetime_years": round(decay_years, 1),
            "leo_space_safety_compliance": passed,
        }

        sim_id = f"SAT-{uuid.uuid4().hex[:8]}"
        provenance = DigitalTwinSimulationResult.compute_provenance({
            "sim_id": sim_id,
            "vehicle": cfg.vehicle_name,
            "summary": summary,
            "events_count": len(events),
        })

        return DigitalTwinSimulationResult(
            simulation_id=sim_id,
            vehicle_type=VehicleType.SATELLITE,
            vehicle_name=cfg.vehicle_name,
            simulation_mode=SimulationMode.FAULT_INJECTION if fault else SimulationMode.NOMINAL,
            duration_s=round(time_s, 1),
            time_step_s=dt,
            total_samples=len(frames),
            frames=frames,
            events=events,
            summary_metrics=summary,
            safety_envelope_passed=passed,
            safety_violations=safety_violations,
            provenance_hash=provenance,
        )
