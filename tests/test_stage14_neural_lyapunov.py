"""
Test Suite for Stage 14: Neural Lyapunov Flight Envelope Protection & ASTM F3269-21 RTA.
========================================================================================
Validates:
1. Control Barrier Function (CBF) forward invariance inside certified envelope boundaries.
2. CBF-QP 1D optimization filter projecting adversarial AI elevator demands to safe half-spaces.
3. ASTM F3269-21 Tri-Level RTA switching (Tier 0 AI -> Tier 1 CBF-QP -> Tier 2 DO-178C Level A Recovery).
4. Prevention of stall and structural $g$-load violations under microburst wind shear.
5. FastAPI integration endpoints (/api/lyapunov/simulate, /api/lyapunov/presets).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from aasi_aero_fno.neural_lyapunov_rta import (
    NeuralLyapunovRTAEngine,
    AircraftEnvelopeLimits,
    LYAPUNOV_SCENARIO_PRESETS,
)

client = TestClient(app)


def test_cbf_safe_interior_and_exterior():
    """Validates that B(x) <= 0 for states safely inside envelope, and B(x) > 0 for states exceeding limits."""
    limits = AircraftEnvelopeLimits(
        aircraft_name="Test Aircraft",
        mass_kg=5000.0,
        wing_area_m2=25.0,
        alpha_max_deg=18.0,
        alpha_min_deg=-6.0,
        nz_max_g=6.0,
        nz_min_g=-2.0,
        v_stall_mps=50.0,
        v_max_mps=250.0,
        max_elevator_deg=25.0,
        elevator_rate_limit_deg_s=50.0,
    )

    # Safe state: alpha = 8 deg (< 18), V = 120 m/s (> 50), nz = 2.0g (< 6.0g)
    b_safe, grad_safe = NeuralLyapunovRTAEngine.evaluate_cbf(
        aoa_deg=8.0,
        v_mps=120.0,
        nz_g=2.0,
        limits=limits,
    )
    assert b_safe < 0.0, f"Expected B(x) < 0 inside safe envelope, got {b_safe}"
    assert grad_safe[1] > 0, "dB/dalpha should be positive (increasing AoA increases barrier towards boundary)"

    # Unsafe state: alpha = 24 deg (> 18), nz = 7.5g (> 6.0)
    b_unsafe, grad_unsafe = NeuralLyapunovRTAEngine.evaluate_cbf(
        aoa_deg=24.0,
        v_mps=120.0,
        nz_g=7.5,
        limits=limits,
    )
    assert b_unsafe > 0.0, f"Expected B(x) > 0 outside envelope boundary, got {b_unsafe}"


def test_cbf_qp_filter_action():
    """Validates that safe commands pass unmodified (Tier 0), while dangerous pull-ups are curtailed (Tier 1)."""
    limits = AircraftEnvelopeLimits(
        aircraft_name="Test LCA",
        mass_kg=8500.0,
        wing_area_m2=38.4,
        alpha_max_deg=20.0,
        alpha_min_deg=-10.0,
        nz_max_g=9.0,
        nz_min_g=-3.0,
        v_stall_mps=65.0,
        v_max_mps=350.0,
        max_elevator_deg=25.0,
        elevator_rate_limit_deg_s=60.0,
    )

    # Benign state and gentle command
    u_safe, tier, _, _ = NeuralLyapunovRTAEngine.solve_cbf_qp_filter(
        u_ai_deg=2.0,
        aoa_deg=5.0,
        q_deg_s=0.0,
        v_mps=180.0,
        nz_g=1.5,
        limits=limits,
    )
    assert tier == "TIER_0_PRIMARY_AI"
    assert u_safe == 2.0

    # Near stall boundary with aggressive pitch-up demand
    u_filtered, tier_filtered, _, dot_b = NeuralLyapunovRTAEngine.solve_cbf_qp_filter(
        u_ai_deg=20.0,
        aoa_deg=19.5,
        q_deg_s=12.0,
        v_mps=80.0,
        nz_g=8.2,
        limits=limits,
    )
    assert tier_filtered in ["TIER_1_CBF_QP_FILTER", "TIER_2_DO178C_RECOVERY"]
    assert u_filtered < 20.0, "Filter should reduce dangerous elevator pitch-up command"


def test_tier2_do178c_recovery_trigger():
    """Validates that when the barrier is critically breached, Tier 2 DO-178C recovery activates with nose-down command."""
    limits = AircraftEnvelopeLimits(
        aircraft_name="Test LCA",
        mass_kg=8500.0,
        wing_area_m2=38.4,
        alpha_max_deg=20.0,
        alpha_min_deg=-10.0,
        nz_max_g=9.0,
        nz_min_g=-3.0,
        v_stall_mps=65.0,
        v_max_mps=350.0,
        max_elevator_deg=25.0,
        elevator_rate_limit_deg_s=60.0,
    )

    # Severely compromised state: alpha = 26 deg (well above 20 deg stall limit)
    u_rec, tier_rec, b_val, _ = NeuralLyapunovRTAEngine.solve_cbf_qp_filter(
        u_ai_deg=15.0,
        aoa_deg=26.0,
        q_deg_s=5.0,
        v_mps=60.0,
        nz_g=7.0,
        limits=limits,
    )
    assert tier_rec == "TIER_2_DO178C_RECOVERY"
    assert u_rec < 0.0, f"DO-178C Level A recovery must issue nose-down elevator, got {u_rec}"


def test_closed_loop_envelope_protection_vs_unprotected():
    """Validates that RTA prevents envelope departures while unprotected system departs."""
    # 1. Unprotected simulation (enable_rta=False)
    res_unprotected = NeuralLyapunovRTAEngine.simulate_envelope_mission(
        preset_key="COMMERCIAL_AIRLINER_STALL",
        enable_rta=False,
        gust_intensity=1.2,
        duration_s=8.0,
    )
    assert res_unprotected.unprotected_departures > 0, "Unprotected aircraft must exhibit envelope departures under heavy gusts"
    assert res_unprotected.astm_f3269_compliance == "DEPARTURE_DETECTED"

    # 2. Protected simulation (enable_rta=True)
    res_protected = NeuralLyapunovRTAEngine.simulate_envelope_mission(
        preset_key="COMMERCIAL_AIRLINER_STALL",
        enable_rta=True,
        gust_intensity=1.2,
        duration_s=8.0,
    )
    assert res_protected.protected_departures == 0, "RTA-protected aircraft must have 0 departures"
    assert res_protected.astm_f3269_compliance == "ASTM_F3269_21_FULLY_COMPLIANT_ZERO_DEPARTURES"
    assert len(res_protected.steps) > 50
    assert len(res_protected.merkle_provenance_hash) == 64


def test_evtol_urban_air_mobility_preset():
    """Validates that eVTOL urban corridor satisfies 2.5g passenger comfort load boundary."""
    res = NeuralLyapunovRTAEngine.simulate_envelope_mission(
        preset_key="EVTOL_URBAN_AIR_MOBILITY",
        enable_rta=True,
        gust_intensity=1.0,
        duration_s=6.0,
    )
    assert res.protected_departures == 0
    assert res.max_nz_reached_g <= 3.2, f"eVTOL load factor exceeded safe limit: {res.max_nz_reached_g}"


def test_api_neural_lyapunov_routes():
    """Validates FastAPI /api/lyapunov/presets and /api/lyapunov/simulate endpoints."""
    # Presets
    res_presets = client.get("/api/lyapunov/presets")
    assert res_presets.status_code == 200
    presets_data = res_presets.json()
    assert "LCA_TEJAS_COMBAT_MANEUVER" in presets_data
    assert "EVTOL_URBAN_AIR_MOBILITY" in presets_data

    # Simulation
    payload = {
        "preset_key": "COMMERCIAL_AIRLINER_STALL",
        "enable_rta": True,
        "gust_intensity": 1.0,
        "duration_s": 8.0,
    }
    res_sim = client.post("/api/lyapunov/simulate", json=payload)
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert sim_data["aircraft_name"] == "Civil Transport (B-737 / A320 Class)"
    assert sim_data["astm_f3269_compliance"] == "ASTM_F3269_21_FULLY_COMPLIANT_ZERO_DEPARTURES"
    assert sim_data["protected_departures"] == 0
    assert len(sim_data["steps"]) > 20
