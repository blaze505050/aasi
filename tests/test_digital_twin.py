"""
AASI 2.0 Aerospace Digital Twin & Exporters Comprehensive Verification Suite.

Tests physics correctness, fault injection resilience, envelope compliance,
and cryptographic provenance for:
- Rocket Digital Twin (Multi-stage, gravity turn, Max-Q, orbital insertion)
- Drone / eVTOL Digital Twin (BEMT, battery ECM, motor thermals, gust response)
- Aeroplane Digital Twin (3D aero polar, TSFC, Breguet range, OEI trim)
- Satellite Digital Twin (J2 precession, drag decay lifetime, eclipse cycle)
- JSBSim & PX4 Autopilot Exporters
- Digital Twin REST API Endpoints
"""

import math
import pytest
from fastapi.testclient import TestClient

from backend.digital_twin import (
    VehicleType,
    SimulationMode,
    FaultType,
    FaultInjectionConfig,
    RocketDigitalTwin,
    RocketDigitalTwinConfig,
    DroneDigitalTwin,
    DroneDigitalTwinConfig,
    AeroplaneDigitalTwin,
    AeroplaneDigitalTwinConfig,
    SatelliteDigitalTwin,
    SatelliteDigitalTwinConfig,
    DigitalTwinOrchestrator,
)
from backend.export.jsbsim_export import JSBSimExporter, JSBSimMetrics, JSBSimAeroDerivatives
from backend.export.px4_export import PX4Exporter, PX4AirframeConfig, AirframeType
from backend.physics.vlm_3d import VortexLatticeSolver, evaluate_aircraft_vlm
from backend.main import app


# ─── 1. Rocket Digital Twin Tests ─────────────────────────────────────────────

def test_rocket_nominal_ascent_and_orbital_insertion():
    cfg = RocketDigitalTwinConfig()
    result = RocketDigitalTwin.simulate(cfg)

    assert result.vehicle_type == VehicleType.ROCKET
    assert result.simulation_mode == SimulationMode.NOMINAL
    assert len(result.frames) > 100
    assert result.total_samples == len(result.frames)
    assert result.provenance_hash is not None
    assert len(result.provenance_hash) == 64

    # Max-Q check (slender orbital rocket typically experiences Max-Q between 15-45 kPa)
    max_q_kpa = result.summary_metrics["max_q_kpa"]
    assert 15.0 <= max_q_kpa <= 45.0

    # Final orbital altitude and velocity
    final_alt_km = result.summary_metrics["final_altitude_km"]
    final_vel_ms = result.summary_metrics["final_velocity_ms"]
    assert final_alt_km > 180.0
    assert final_vel_ms > 7400.0  # Near orbital velocity ~7.8 km/s
    assert result.summary_metrics["orbit_status"] in ["STABLE_INSERTION", "SUBORBITAL_REENTRY"]
    assert result.safety_envelope_passed is True

    # Milestone events check
    event_names = [e.event_name for e in result.events]
    assert "LIFTOFF" in event_names
    assert "MECO" in event_names
    assert "STAGE_SEP" in event_names
    assert "SES-1" in event_names


def test_rocket_fault_injection_premature_cutoff():
    fault = FaultInjectionConfig(
        target_vehicle=VehicleType.ROCKET,
        fault_type=FaultType.ENGINE_SHUTDOWN_EARLY,
        onset_time_s=75.0,
        severity=0.85,
    )
    result = RocketDigitalTwin.simulate(fault=fault)

    assert result.simulation_mode == SimulationMode.FAULT_INJECTION
    assert result.safety_envelope_passed is False
    assert len(result.safety_violations) > 0
    assert any("Engine thrust dropped" in v for v in result.safety_violations)
    assert any(e.event_name == "FAULT_ENGINE_SHUTDOWN" for e in result.events)


# ─── 2. Drone / eVTOL Digital Twin Tests ──────────────────────────────────────

def test_drone_nominal_mission_and_bemt():
    cfg = DroneDigitalTwinConfig(takeoff_mass_kg=8.5, cruise_speed_ms=14.0)
    result = DroneDigitalTwin.simulate(cfg)

    assert result.vehicle_type == VehicleType.DRONE
    assert result.simulation_mode == SimulationMode.NOMINAL
    assert result.summary_metrics["mission_completed"] is True
    assert result.summary_metrics["max_altitude_m"] == cfg.mission_cruise_altitude_m
    assert result.summary_metrics["final_battery_soc_pct"] > 15.0
    assert result.summary_metrics["max_motor_temp_c"] < 90.0
    assert result.safety_envelope_passed is True

    # Milestones
    event_names = [e.event_name for e in result.events]
    assert "ARM_AND_TAKEOFF" in event_names
    assert "CRUISE_CEILING_REACHED" in event_names
    assert "TOUCHDOWN" in event_names


def test_drone_motor_failure_fault_injection():
    fault = FaultInjectionConfig(
        target_vehicle=VehicleType.DRONE,
        fault_type=FaultType.MOTOR_FAILURE,
        onset_time_s=40.0,
        severity=1.0,
    )
    result = DroneDigitalTwin.simulate(fault=fault)

    assert result.simulation_mode == SimulationMode.FAULT_INJECTION
    assert result.safety_envelope_passed is False
    assert any("Rotor #1 lost" in v for v in result.safety_violations)
    assert any(e.event_name == "FAULT_MOTOR_FAILURE" for e in result.events)


# ─── 3. Aeroplane Digital Twin Tests ──────────────────────────────────────────

def test_aeroplane_nominal_breguet_flight():
    cfg = AeroplaneDigitalTwinConfig(cruise_mach=0.78, mission_range_km=2000.0)
    result = AeroplaneDigitalTwin.simulate(cfg)

    assert result.vehicle_type == VehicleType.AEROPLANE
    assert result.summary_metrics["mission_completed"] is True
    assert result.summary_metrics["max_cruise_mach"] >= 0.75
    assert result.summary_metrics["reserve_fuel_remaining_kg"] > 1500.0
    assert result.safety_envelope_passed is True

    event_names = [e.event_name for e in result.events]
    assert "TAKEOFF_ROLL" in event_names
    assert "ROTATION_VR" in event_names
    assert "CRUISE_LEVEL" in event_names
    assert "LANDED_BRAKES" in event_names


def test_aeroplane_oei_fault_injection():
    fault = FaultInjectionConfig(
        target_vehicle=VehicleType.AEROPLANE,
        fault_type=FaultType.ONE_ENGINE_INOPERATIVE,
        onset_time_s=500.0,
        severity=1.0,
    )
    result = AeroplaneDigitalTwin.simulate(fault=fault)

    assert result.simulation_mode == SimulationMode.FAULT_INJECTION
    assert result.safety_envelope_passed is False
    assert any("Engine 2 failure" in v for v in result.safety_violations)
    assert any(e.event_name == "FAULT_OEI_ENG2" for e in result.events)


# ─── 4. Satellite Digital Twin Tests ──────────────────────────────────────────

def test_satellite_j2_orbit_and_thermal_balance():
    cfg = SatelliteDigitalTwinConfig(initial_altitude_km=500.0, simulation_orbits=2.0)
    result = SatelliteDigitalTwin.simulate(cfg)

    assert result.vehicle_type == VehicleType.SATELLITE
    assert result.summary_metrics["orbits_simulated"] == 2.0
    assert 90.0 <= result.summary_metrics["orbit_period_min"] <= 100.0
    assert result.summary_metrics["max_depth_of_discharge_pct"] < 35.0
    assert result.summary_metrics["thermal_min_c"] < 0.0  # Cold during eclipse
    assert result.summary_metrics["thermal_max_c"] > 20.0 # Warm during sunlit pass
    assert result.summary_metrics["projected_orbital_lifetime_years"] > 5.0
    assert result.safety_envelope_passed is True

    event_names = [e.event_name for e in result.events]
    assert "ORBIT_PROPAGATION_START" in event_names
    assert "UMBRA_ENTRY" in event_names
    assert "UMBRA_EXIT" in event_names


def test_satellite_solar_degradation_fault():
    fault = FaultInjectionConfig(
        target_vehicle=VehicleType.SATELLITE,
        fault_type=FaultType.SOLAR_PANEL_DEGRADATION,
        onset_time_s=600.0,
        severity=0.6,
    )
    result = SatelliteDigitalTwin.simulate(fault=fault)

    assert result.simulation_mode == SimulationMode.FAULT_INJECTION
    assert result.safety_envelope_passed is False
    assert any("Solar array power loss" in v for v in result.safety_violations)


# ─── 5. Exporters & VLM 3D Tests ──────────────────────────────────────────────

def test_jsbsim_exporter_xml_generation():
    metrics = JSBSimMetrics(aircraft_name="AASI_Test_Plane", empty_weight_lbs=2400.0)
    aero = JSBSimAeroDerivatives(cl_0=0.3, cl_alpha_per_rad=5.0, cm_alpha_per_rad=-0.8)
    res = JSBSimExporter.generate_fdm_xml(metrics, aero)

    assert res.aircraft_name == "AASI_Test_Plane"
    assert "<fdm_config name=\"AASI_Test_Plane\"" in res.fdm_xml
    assert "<axis name=\"LIFT\">" in res.fdm_xml
    assert "<axis name=\"DRAG\">" in res.fdm_xml
    assert "<axis name=\"PITCH\">" in res.fdm_xml
    assert len(res.provenance_hash) == 64


def test_px4_exporter_deck_generation():
    cfg = PX4AirframeConfig(
        airframe_name="AASI_VTOL_Test",
        airframe_type=AirframeType.VTOL_QUADPLANE,
        vehicle_mass_kg=4.0,
    )
    res = PX4Exporter.generate_px4_deck(cfg)

    assert res.airframe_name == "AASI_VTOL_Test"
    assert "SYS_AUTOSTART\t\t13000" in res.params_content
    assert "FW_AIRSPD_MIN" in res.params_content
    assert "R: 4x" in res.mixer_content
    assert len(res.provenance_hash) == 64


def test_vlm_3d_solver_execution():
    res = evaluate_aircraft_vlm(wingspan_m=12.0, aspect_ratio=8.0, sweep_deg=6.0, alpha_deg=4.0)
    assert res.cl > 0.0
    assert res.cd_total > 0.0
    assert res.lift_to_drag > 5.0
    assert res.cl_alpha > 0.0
    assert res.cm_alpha < 0.0  # Statically stable
    assert res.static_margin_pct > 0.0


# ─── 6. Digital Twin REST API Endpoints Tests ─────────────────────────────────

def test_api_digital_twin_catalog_endpoint():
    client = TestClient(app)
    response = client.get("/api/digital-twin/catalog")
    assert response.status_code == 200
    catalog = response.json()
    assert len(catalog) == 4
    types = [item["vehicle_type"] for item in catalog]
    assert "ROCKET" in types
    assert "DRONE" in types
    assert "AEROPLANE" in types
    assert "SATELLITE" in types


def test_api_digital_twin_simulate_endpoint():
    client = TestClient(app)
    payload = {
        "vehicle_type": "DRONE",
        "custom_config": {"takeoff_mass_kg": 6.0, "cruise_speed_ms": 12.0},
    }
    response = client.post("/api/digital-twin/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_type"] == "DRONE"
    assert len(data["frames"]) > 20
    assert data["provenance_hash"] is not None


def test_api_digital_twin_fault_injection_endpoint():
    client = TestClient(app)
    payload = {
        "vehicle_type": "ROCKET",
        "fault_type": "ENGINE_SHUTDOWN_EARLY",
        "onset_time_s": 60.0,
        "severity": 0.8,
    }
    response = client.post("/api/digital-twin/fault-injection", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["simulation_mode"] == "FAULT_INJECTION"
    assert data["safety_envelope_passed"] is False
    assert len(data["safety_violations"]) > 0
