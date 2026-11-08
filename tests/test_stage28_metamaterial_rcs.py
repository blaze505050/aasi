"""
Unit tests for Stage 28: Electromagnetic Metamaterial Radar Cross Section (RCS) & Inverse Stealth Synthesizer.
"""

import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.metamaterial_rcs_synthesizer import (
    RadarBand,
    compute_salisbury_screen_reflection,
    synthesize_airframe_rcs_profile,
)
from backend.main import app

client = TestClient(app)


def test_salisbury_screen_reflection_absorption():
    # Resonant quarter-wavelength spacer at 10 GHz (lambda/4 ~ 7.32 mm for eps_r = 1.05)
    res = compute_salisbury_screen_reflection(
        freq_ghz=10.0,
        design_freq_ghz=10.0,
        spacer_thickness_mm=7.32,
        relative_permittivity=1.05,
    )
    assert res["absorption_pct"] > 95.0
    assert res["reflection_coeff_db"] < -20.0
    assert res["input_impedance_real_ohms"] > 0.0


def test_amca_stealth_airframe_vlo_signature():
    profile = synthesize_airframe_rcs_profile(
        model_name="AMCA_5TH_GEN_STEALTH",
        radar_band=RadarBand.X_BAND,
        frequency_ghz=10.0,
        enable_metamaterial_ram=True,
    )
    assert profile["frontal_rcs_dbsm"] < -30.0
    assert profile["frontal_rcs_m2"] < 0.001
    assert profile["stealth_classification"] == "VERY_LOW_OBSERVABLE_VLO"
    assert len(profile["polar_rcs_signature"]) == 72


def test_metamaterial_ram_reduction_comparison():
    with_ram = synthesize_airframe_rcs_profile(
        model_name="AMCA_5TH_GEN_STEALTH",
        enable_metamaterial_ram=True,
    )
    without_ram = synthesize_airframe_rcs_profile(
        model_name="AMCA_5TH_GEN_STEALTH",
        enable_metamaterial_ram=False,
    )
    assert with_ram["frontal_rcs_m2"] < without_ram["frontal_rcs_m2"]
    assert with_ram["mean_rcs_m2"] < without_ram["mean_rcs_m2"]


def test_rcs_api_endpoints():
    # 1. Presets endpoint
    res_presets = client.get("/api/rcs/presets")
    assert res_presets.status_code == 200
    presets = res_presets.json()
    assert "AMCA_5TH_GEN_STEALTH" in presets
    assert "HYPERSONIC_STRIKE_HGV" in presets

    # 2. Status endpoint
    res_status = client.get("/api/rcs/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["status"] == "OPERATIONAL"
    assert status_data["vlo_threshold_dbsm"] == -30.0

    # 3. Simulate endpoint
    payload = {
        "model_name": "AMCA_5TH_GEN_STEALTH",
        "radar_band": "X_BAND",
        "frequency_ghz": 10.0,
        "enable_metamaterial_ram": True,
        "ram_thickness_mm": 2.8,
    }
    res_sim = client.post("/api/rcs/simulate", json=payload)
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert "frontal_rcs_dbsm" in sim_data
    assert "polar_rcs_signature" in sim_data
    assert "frequency_sweep" in sim_data
