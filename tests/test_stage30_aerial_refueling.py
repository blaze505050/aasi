"""
Unit tests for Stage 30: Autonomous Aerial Refueling & Visually-Coupled Docking CBF.
Verifies Hallock-Burnham wake vortex aerodynamics, bow wave disturbance,
Control Barrier Function (CBF-QP) cone containment, and REST API endpoints.
"""

import pytest
import numpy as np
from starlette.testclient import TestClient

from aasi_aero_fno.aerial_refueling_cbf import (
    TankerType,
    RefuelingPhase,
    compute_tanker_vortex_circulation,
    compute_hallock_burnham_wake_velocity,
    compute_receiver_bow_wave_disturbance,
    evaluate_cbf_docking_cone,
    simulate_autonomous_aerial_refueling,
    TANKER_DATABASE,
)
from backend.main import app

client = TestClient(app)


def test_tanker_wake_vortex_circulation_and_velocity():
    """Verifies Hallock-Burnham trailing vortex circulation and downwash calculations."""
    tanker = TANKER_DATABASE[TankerType.KC_767]
    gamma_0, vortex_half_span, rho = compute_tanker_vortex_circulation(tanker)

    # Physical bounds for KC-767 (MTOW ~ 155,000 kg)
    assert 250.0 <= gamma_0 <= 650.0  # Circulation in m^2/s
    assert 15.0 <= vortex_half_span <= 22.0  # ~ pi/4 * b/2
    assert 0.4 <= rho <= 0.7  # Air density at 7500m

    # Downwash between vortex cores behind wing (y = 0, z = 4.0m)
    sidewash, downwash = compute_hallock_burnham_wake_velocity(
        x=35.0,
        y=0.0,
        z=4.0,
        gamma_0=gamma_0,
        vortex_half_span=vortex_half_span,
        rc=tanker.vortex_core_rc_m,
    )
    # Tanker centerline must experience net downwash and negligible sidewash
    assert downwash > 0.5  # Positive downward
    assert abs(sidewash) < 0.2  # Symmetric centerline cancellation


def test_receiver_bow_wave_disturbance():
    """Verifies aerodynamic stagnation pressure bubble lifts and deflects drogue basket."""
    # Far away (> 2m): bow wave should be negligible
    r_far, z_far = compute_receiver_bow_wave_disturbance(rel_x=4.0, airspeed_mps=180.0)
    assert r_far == 0.0
    assert z_far == 0.0

    # In terminal approach zone (0.4m): bow wave must push upward and outward
    r_close, z_close = compute_receiver_bow_wave_disturbance(rel_x=0.4, airspeed_mps=180.0)
    assert z_close > 0.15  # Upward lift > 15 cm
    assert r_close > 0.08  # Radial push > 8 cm


def test_cbf_docking_cone_containment():
    """Verifies Control Barrier Function identifies unsafe excursions and computes corrections."""
    # Inside safe cone
    pos_inside = np.array([0.05, 0.05, -5.0])
    vel_inside = np.array([0.0, 0.0, 0.5])
    is_safe, h_cbf, cbf_res, accel = evaluate_cbf_docking_cone(pos_inside, vel_inside, cone_angle_deg=20.0)
    assert is_safe is True
    assert h_cbf > 0.0

    # Outside safe cone (excessive radial offset for given standoff distance)
    pos_outside = np.array([2.5, 1.8, -2.0])
    vel_outside = np.array([0.4, 0.3, 1.2])
    is_safe_bad, h_bad, cbf_bad, accel_bad = evaluate_cbf_docking_cone(pos_outside, vel_outside, cone_angle_deg=20.0)
    assert is_safe_bad is False
    assert np.linalg.norm(accel_bad) > 0.0  # CBF intervention active


def test_end_to_end_autonomous_aerial_refueling_mission():
    """Verifies complete simulation loop from 15m standoff to mechanical latch and fuel transfer."""
    res = simulate_autonomous_aerial_refueling(
        tanker_type=TankerType.KC_767,
        receiver_name="Ghatak UCAV (Stealth Autonomous Tanker Receiver)",
        initial_standoff_distance_m=12.0,
        enable_cbf_protection=True,
        enable_emergency_breakaway_test=False,
        turbulence_gust_mps=2.0,
        sim_time_sec=25.0,
    )
    outcome = res["mission_outcome"]
    assert outcome["successful_docking"] is True
    assert outcome["status"] == "SUCCESSFUL_AUTONOMOUS_CONTACT_AND_REFUELING"
    assert outcome["final_radial_error_cm"] <= 15.0  # < 15 cm contact tolerance (NATO drogue basket throat)
    assert outcome["total_fuel_transferred_kg"] > 50.0  # Fuel transferred after latch
    assert len(res["telemetry_points"]) > 20


def test_emergency_breakaway_maneuver():
    """Verifies automated emergency breakaway commands 3g diving escape corridor."""
    res = simulate_autonomous_aerial_refueling(
        tanker_type=TankerType.IL_78,
        receiver_name="Loyal Wingman",
        initial_standoff_distance_m=10.0,
        enable_cbf_protection=True,
        enable_emergency_breakaway_test=True,  # Force breakaway abort midway
        sim_time_sec=15.0,
    )
    outcome = res["mission_outcome"]
    assert outcome["breakaway_executed"] is True
    assert outcome["status"] == "EMERGENCY_BREAKAWAY_CLEARED_SAFELY"


def test_aerial_refueling_api_endpoints():
    """Verifies REST API endpoints for Stage 30."""
    resp_presets = client.get("/api/v1/aerial-refueling/presets")
    assert resp_presets.status_code == 200
    presets = resp_presets.json()["data"]
    assert "KC767_GHATAK_UCAV" in presets

    resp_status = client.get("/api/v1/aerial-refueling/status")
    assert resp_status.status_code == 200
    assert "Hallock-Burnham" in resp_status.json()["wake_vortex_model"]

    resp_sim = client.post(
        "/api/v1/aerial-refueling/simulate",
        json={
            "tanker_type": "KC_767",
            "receiver_name": "Ghatak UCAV",
            "initial_standoff_distance_m": 10.0,
            "enable_cbf_protection": True,
            "enable_emergency_breakaway_test": False,
            "turbulence_gust_mps": 2.5,
            "sim_time_sec": 20.0,
        },
    )
    assert resp_sim.status_code == 200
    data = resp_sim.json()["data"]
    assert data["mission_outcome"]["successful_docking"] is True
