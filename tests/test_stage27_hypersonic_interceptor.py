"""
Unit tests for Stage 27: Hypersonic Boost-Glide Interceptor Guidance Engine.
"""

import pytest
import numpy as np
from starlette.testclient import TestClient

from aasi_aero_fno.hypersonic_interceptor_guidance import (
    GuidanceLaw,
    TargetEvasionManeuver,
    compute_zem_vector,
    compute_guidance_acceleration,
    simulate_hypersonic_interception,
)
from backend.main import app

client = TestClient(app)


def test_zem_vector_calculation():
    r_rel = np.array([1000.0, 0.0, 0.0])
    v_rel = np.array([-500.0, 0.0, 0.0])
    t_go = 2.0
    a_t = np.array([0.0, 0.0, 0.0])
    zem = compute_zem_vector(r_rel, v_rel, a_t, t_go)
    assert np.allclose(zem, [0.0, 0.0, 0.0])


def test_differential_game_vs_pn_against_weave():
    # 1. Optimal Differential Game Guidance
    res_dgg = simulate_hypersonic_interception(
        mission_id="GLIDE_PHASE_INTERCEPTOR",
        guidance_law=GuidanceLaw.DIFFERENTIAL_GAME_ZEM,
        target_evasion=TargetEvasionManeuver.SINUSOIDAL_WEAVE,
        nav_ratio=4.2,
        enable_dacs_divert=True,
    )
    assert res_dgg["hit_to_kill_achieved"] is True
    assert res_dgg["min_miss_distance_m"] < 0.65
    assert res_dgg["executive_summary"]["engagement_outcome"] == "HIT_TO_KILL_KINETIC_IMPACT"

    # 2. Compare against standard Proportional Navigation
    res_pn = simulate_hypersonic_interception(
        mission_id="GLIDE_PHASE_INTERCEPTOR",
        guidance_law=GuidanceLaw.PROPORTIONAL_NAVIGATION,
        target_evasion=TargetEvasionManeuver.SINUSOIDAL_WEAVE,
        nav_ratio=3.5,
        enable_dacs_divert=False,
    )
    # Both achieve sub-meter hit-to-kill direct kinetic impact
    assert res_pn["hit_to_kill_achieved"] is True
    assert res_dgg["min_miss_distance_m"] < 0.65
    assert res_pn["min_miss_distance_m"] < 0.65


def test_aerothermal_and_g_load_bounds():
    res = simulate_hypersonic_interception(
        mission_id="ENDOCRUIRSER_HACM",
        guidance_law=GuidanceLaw.AUGMENTED_PN,
        target_evasion=TargetEvasionManeuver.BARREL_ROLL,
        nav_ratio=4.0,
    )
    assert res["peak_g_load"] <= 35.0
    assert res["peak_stagnation_heat_flux_mw_m2"] > 0.0
    assert len(res["time_series"]) > 0


def test_interceptor_api_endpoints():
    # 1. Presets endpoint
    res_presets = client.get("/api/interceptor/presets")
    assert res_presets.status_code == 200
    presets = res_presets.json()
    assert "GLIDE_PHASE_INTERCEPTOR" in presets
    assert "ENDOCRUIRSER_HACM" in presets
    assert "EXO_ORBITAL_FOBS" in presets

    # 2. Status endpoint
    res_status = client.get("/api/interceptor/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["status"] == "OPERATIONAL"
    assert status_data["hit_to_kill_criterion_m"] == 0.65

    # 3. Simulate endpoint
    payload = {
        "mission_id": "GLIDE_PHASE_INTERCEPTOR",
        "guidance_law": "DIFFERENTIAL_GAME_ZEM",
        "target_evasion": "TERMINAL_PULL_UP",
        "nav_ratio": 4.5,
        "enable_dacs_divert": True,
    }
    res_sim = client.post("/api/interceptor/simulate", json=payload)
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert "min_miss_distance_m" in sim_data
    assert "executive_summary" in sim_data
    assert sim_data["guidance_law"] == "DIFFERENTIAL_GAME_ZEM"
