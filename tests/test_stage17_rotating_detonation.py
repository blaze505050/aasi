"""
Test Suite for Stage 17: Cryogenic & Rotating Detonation Engine (RDE) Propulsion Digital Twin.
=============================================================================================
Validates:
1. Chapman-Jouguet detonation velocity D_CJ, Mach number, and Von Neumann spike pressure.
2. Pressure-gain combustion (PGC) advantage: Delta_p / p_inj >= 14% and Isp increase >= +8.5%.
3. Annular azimuthal wave tracking, wave rotation frequency (1.5 kHz to 4.5 kHz), and 360-deg pressure profile.
4. Regenerative nozzle cooling thermal equilibrium.
5. FastAPI integration endpoints (/api/rde/presets, /api/rde/simulate).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from aasi_aero_fno.rotating_detonation import (
    RotatingDetonationEngine,
    PROPELLANT_DATABASE,
    RDE_PRESETS,
)

client = TestClient(app)


def test_chapman_jouguet_detonation_physics():
    """Validates CJ detonation velocity and von Neumann spike pressure calculation for Hydrolox."""
    prop = PROPELLANT_DATABASE["ISRO_CE20_HYDROLOX"]
    d_cj, m_cj, p_vn, p_cj, delta_ind = RotatingDetonationEngine.calculate_cj_detonation_state(
        propellant=prop,
        p_inj_bar=40.0,
    )

    # For LOX/LH2, D_CJ is typically between 2600 and 3000 m/s
    assert 2600.0 < d_cj < 3100.0, f"Expected D_CJ ~ 2850 m/s, got {d_cj}"
    assert 5.0 < m_cj < 8.0, f"Expected M_CJ ~ 6.5, got {m_cj}"
    # Von Neumann spike is significantly higher than injection pressure
    assert p_vn > p_cj > 40.0
    assert 0.1 < delta_ind < 2.0


def test_rde_digital_twin_simulation_ce20():
    """Validates ISRO CE-20 Cryogenic RDE simulation metrics."""
    res = RotatingDetonationEngine.simulate_rde_digital_twin(
        preset_key="ISRO_CE20_HYDROLOX",
        injection_pressure_bar=45.0,
        mass_flow_kg_s=42.0,
        number_of_waves=2,
        chamber_diameter_mm=180.0,
        annulus_gap_mm=9.0,
    )

    assert "ISRO CE-20" in res.engine_name
    assert res.number_of_waves == 2
    # Wave rotation frequency for 2 waves on a 180mm diameter chamber should be ~3.0 - 4.5 kHz
    assert 2500.0 < res.wave_frequency_hz < 5500.0
    # Pressure gain must be positive
    assert res.pressure_gain_pct >= 14.0
    assert res.mean_chamber_pressure_bar > res.injection_pressure_bar
    # Specific impulse should be improved over baseline 443s
    assert res.specific_impulse_vacuum_s > 480.0
    assert res.issp_improvement_pct >= 9.0
    # Regenerative cooling must be in equilibrium
    assert res.regenerative_cooling_status == "REGENERATIVE_EQUILIBRIUM_SAFE"
    assert res.wall_max_temperature_k <= 1180.0
    # Azimuthal profiles
    assert len(res.azimuth_deg) == 360
    assert len(res.static_pressure_bar) == 360
    assert max(res.static_pressure_bar) >= res.von_neumann_pressure_bar * 0.95
    assert len(res.merkle_provenance_hash) == 64


def test_methalox_and_semicryo_presets():
    """Validates Methalox deep-space and Semi-Cryogenic SCE-200 presets."""
    res_meth = RotatingDetonationEngine.simulate_rde_digital_twin(
        preset_key="METHALOX_ADVANCED_RDE",
        injection_pressure_bar=38.0,
        mass_flow_kg_s=60.0,
        number_of_waves=2,
    )
    assert res_meth.propellant_name == "Advanced Methalox (LOX / LCH4)"
    assert res_meth.specific_impulse_vacuum_s > 410.0

    res_semi = RotatingDetonationEngine.simulate_rde_digital_twin(
        preset_key="ISRO_SCE200_SEMICRYO",
        injection_pressure_bar=55.0,
        mass_flow_kg_s=650.0,
        number_of_waves=3,
    )
    assert res_semi.thrust_vacuum_kn > 2000.0  # Heavy-lift booster class


def test_api_rde_routes():
    """Validates FastAPI /api/rde/presets and /api/rde/simulate endpoints."""
    # Presets
    res_presets = client.get("/api/rde/presets")
    assert res_presets.status_code == 200
    presets_data = res_presets.json()
    assert "ISRO_CE20_HYDROLOX" in presets_data
    assert "METHALOX_ADVANCED_RDE" in presets_data

    # Simulate POST
    payload = {
        "preset_key": "ISRO_CE20_HYDROLOX",
        "injection_pressure_bar": 40.0,
        "mass_flow_kg_s": 38.0,
        "number_of_waves": 2,
        "chamber_diameter_mm": 180.0,
        "annulus_gap_mm": 9.0,
    }
    res_sim = client.post("/api/rde/simulate", json=payload)
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert "CE-20" in sim_data["engine_name"]
    assert sim_data["pressure_gain_pct"] >= 14.0
    assert len(sim_data["azimuth_deg"]) == 360
    assert sim_data["asme_vv20_status"] == "PRESSURE_GAIN_COMBUSTION_VERIFIED"
