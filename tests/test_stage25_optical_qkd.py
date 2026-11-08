"""
Unit tests for Stage 25: Autonomous Deep Space Optical Communications & Quantum Key Distribution (QKD).
"""

import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.optical_qkd_pointing import (
    compute_atmospheric_turbulence,
    compute_adaptive_optics_correction,
    compute_optical_link_budget,
    simulate_decoy_state_bb84_qkd,
    simulate_fine_pointing_assembly,
    execute_optical_qkd_dossier,
)
from backend.main import app

client = TestClient(app)


def test_atmospheric_turbulence_and_ao():
    turb = compute_atmospheric_turbulence(
        wavelength_m=1550e-9,
        zenith_angle_deg=25.0,
        cn2_ground=1.7e-14,
        propagation_distance_m=20000.0,
        wind_speed_mps=10.0,
    )
    assert 0.02 <= turb["fried_parameter_r0_m"] <= 0.45
    assert turb["scintillation_index"] > 0.0
    assert turb["greenwood_freq_hz"] > 20.0

    ao = compute_adaptive_optics_correction(
        d_telescope_m=1.2,
        r0_m=turb["fried_parameter_r0_m"],
        ao_actuators_count=128,
        ao_sampling_rate_hz=2500.0,
        greenwood_freq_hz=turb["greenwood_freq_hz"],
    )
    assert 0.40 <= ao["strehl_ratio"] <= 0.99
    assert ao["wavefront_rms_error_nm"] < 250.0


def test_optical_link_budget_ppm():
    budget = compute_optical_link_budget(
        tx_power_w=5.0,
        wavelength_m=1550e-9,
        tx_aperture_m=0.22,
        rx_aperture_m=5.0,
        distance_m=384400e3,
        ppm_order=64,
        pointing_jitter_nrad=120.0,
        strehl_ratio=0.75,
    )
    assert budget["ppm_order"] == 64
    assert budget["bits_per_symbol"] == 6.0
    assert budget["data_rate_mbps"] > 10.0  # deep-space multi-megabit throughput
    assert budget["photon_efficiency_bits_per_photon"] > 2.0
    assert budget["received_power_dbm"] < 0.0  # reasonable negative dBm


def test_decoy_state_bb84_qkd():
    # 1. Nominal secure condition without eavesdropper
    qkd_nominal = simulate_decoy_state_bb84_qkd(
        distance_km=550.0,
        fiber_or_free_space="free_space",
        tx_rep_rate_hz=1e8,
        eve_eavesdropping_present=False,
    )
    assert qkd_nominal["qber_pct"] < 6.0
    assert not qkd_nominal["eve_detected"]
    assert qkd_nominal["secure_key_rate_bps"] > 1000.0
    assert qkd_nominal["security_status"] == "SECURE_QUANTUM_ADVANTAGE"

    # 2. Under active Eve eavesdropping (intercept-resend/PNS attack)
    qkd_eavesdropped = simulate_decoy_state_bb84_qkd(
        distance_km=550.0,
        fiber_or_free_space="free_space",
        tx_rep_rate_hz=1e8,
        eve_eavesdropping_present=True,
    )
    assert qkd_eavesdropped["qber_pct"] > 11.0  # Shor-Preskill threshold exceeded
    assert qkd_eavesdropped["eve_detected"] is True
    assert qkd_eavesdropped["secure_key_rate_bps"] == 0.0
    assert "EAVESDROPPER_DETECTED" in qkd_eavesdropped["security_status"]


def test_fine_pointing_assembly():
    fsm = simulate_fine_pointing_assembly(
        initial_jitter_urad=8.5,
        fsm_bandwidth_hz=1400.0,
        sensor_noise_nrad=12.0,
    )
    assert fsm["fsm_rms_residual_jitter_nrad"] < 500.0
    assert fsm["jitter_suppression_factor_db"] > 20.0
    assert len(fsm["sample_time_series"]) > 0


def test_optical_qkd_dossier():
    dossier = execute_optical_qkd_dossier("ISRO_LEO_GROUND_QKD")
    assert dossier["mission_id"] == "ISRO_LEO_GROUND_QKD"
    assert "optical_throughput_mbps" in dossier["executive_summary"]
    assert "secure_key_rate_kbps" in dossier["executive_summary"]
    assert dossier["executive_summary"]["qber_pct"] < 6.0


def test_optical_qkd_api_endpoints():
    # 1. Presets endpoint
    res_presets = client.get("/api/optical-qkd/presets")
    assert res_presets.status_code == 200
    presets = res_presets.json()
    assert "ISRO_LEO_GROUND_QKD" in presets
    assert "LUNAR_GATEWAY_DSOC" in presets

    # 2. Status endpoint
    res_status = client.get("/api/optical-qkd/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["status"] == "OPERATIONAL"
    assert status_data["shor_preskill_qber_threshold_pct"] == 11.0

    # 3. Simulate endpoint
    payload = {"mission_id": "LUNAR_GATEWAY_DSOC"}
    res_sim = client.post("/api/optical-qkd/simulate", json=payload)
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert "optical_link_budget" in sim_data
    assert "quantum_key_distribution" in sim_data
    assert sim_data["optical_link_budget"]["ppm_order"] == 64
