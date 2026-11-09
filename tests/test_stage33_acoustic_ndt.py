"""
Unit and regression tests for Stage 33: Autonomous Ultrasonic & X-Ray CT NDT Defect Inpainting & POD.
Validates:
1. Elastodynamic wave velocities (longitudinal & shear), acoustic impedance, and reflection coefficients.
2. Pulse-echo A-scan RF waveforms, time-of-flight flaw localization, and 2D B-scan echograms.
3. Micro-CT Beer-Lambert radiograph generation, Otsu flaw segmentation, and physics-guided inpainting.
4. MIL-HDBK-1823A Probability of Detection (POD) curves, lower 95% confidence bounds, and a_90/95 thresholds.
5. FastAPI REST API endpoints.
"""

import math
import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.acoustic_xray_ndt import (
    NDT_MATERIALS,
    compute_reflection_coefficient,
    synthesize_ultrasonic_ascan,
    synthesize_ultrasonic_bscan,
    synthesize_micro_ct_slice,
    compute_mil_hdbk_pod_curve,
    AIR_ACOUSTIC_IMPEDANCE_MRAYLS,
)
from backend.main import app


def test_acoustic_material_velocities_and_impedance():
    """Validates elastodynamic wave propagation speeds and impedance matching."""
    ti = NDT_MATERIALS["TI_6AL_4V"]
    # Ti-6Al-4V longitudinal speed should be approx 6100-6350 m/s
    assert 5900.0 <= ti.longitudinal_velocity_mps <= 6450.0
    # Shear speed should be approx 3100 m/s
    assert 3000.0 <= ti.transverse_velocity_mps <= 3300.0
    # Acoustic impedance ~27 MRayls
    assert 25.0 <= ti.acoustic_impedance_mrayls <= 29.0

    inconel = NDT_MATERIALS["INCONEL_718"]
    assert 5500.0 <= inconel.longitudinal_velocity_mps <= 6000.0
    assert 44.0 <= inconel.acoustic_impedance_mrayls <= 50.0

    # Reflection at metal-void interface should be nearly total reflection (R -> -1.0)
    r_ti_void = compute_reflection_coefficient(ti.acoustic_impedance_mrayls, AIR_ACOUSTIC_IMPEDANCE_MRAYLS)
    assert -1.0 <= r_ti_void <= -0.999


def test_ultrasonic_ascan_and_bscan_pulse_echo():
    """Validates pulse-echo A-scan time of flight and 2D B-scan synthesis."""
    flaw_depth_mm = 12.5
    thickness_mm = 25.0
    ascan = synthesize_ultrasonic_ascan(
        material_key="TI_6AL_4V",
        specimen_thickness_mm=thickness_mm,
        flaw_depth_mm=flaw_depth_mm,
        flaw_diameter_um=350.0,
    )

    assert ascan["flaw_detected"] is True
    assert ascan["flaw_depth_mm"] == flaw_depth_mm
    assert ascan["flaw_amplitude_percent_fsh"] > 15.0

    c_l = ascan["longitudinal_velocity_mps"]
    expected_tof_flaw_us = (2.0 * flaw_depth_mm * 1e-3 / c_l) * 1e6 + 0.5  # include 0.5 us delay
    assert abs(ascan["time_of_flight_flaw_us"] - expected_tof_flaw_us) < 0.2

    # B-scan verification
    bscan = synthesize_ultrasonic_bscan(
        material_key="TI_6AL_4V",
        specimen_length_mm=30.0,
        specimen_thickness_mm=thickness_mm,
        flaw_x_mm=15.0,
        flaw_depth_mm=flaw_depth_mm,
        scan_steps=20,
    )
    assert bscan["num_x_steps"] == 20
    assert len(bscan["bscan_intensity_matrix"]) == 20
    assert bscan["num_depth_bins"] == 50


def test_micro_ct_xray_attenuation_and_inpainting():
    """Validates Beer-Lambert transmission, defect segmentation, and inpainting."""
    ct = synthesize_micro_ct_slice(
        material_key="TI_6AL_4V",
        grid_size=64,
        inject_voids=True,
        inject_crack=True,
    )

    assert ct["grid_resolution"] == 64
    assert len(ct["injected_defects"]) >= 4  # 3 voids + 1 crack
    assert ct["segmented_defect_voxels"] > 10
    assert 0.05 <= ct["void_fraction_percent"] <= 5.0

    # Ensure inpainted slice dimensions match raw slice
    assert len(ct["raw_ct_slice"]) == 64
    assert len(ct["inpainted_slice"]) == 64
    assert len(ct["defect_mask"]) == 64


def test_mil_hdbk_pod_curve_and_qualification():
    """Validates MIL-HDBK-1823A POD log-logistic regression and a_90/95 threshold."""
    pod = compute_mil_hdbk_pod_curve(
        material_key="TI_6AL_4V",
        inspection_modality="ULTRASONIC_5MHZ",
    )

    thresh = pod["qualification_thresholds_um"]
    a_50 = thresh["a_50_um"]
    a_90 = thresh["a_90_um"]
    a_90_95 = thresh["a_90_95_um"]

    # Monotonic ordering of qualification flaw sizes
    assert a_50 < a_90 < a_90_95
    # Standard aerospace bounds
    assert 120.0 <= a_50 <= 220.0
    assert 200.0 <= a_90 <= 350.0
    assert 250.0 <= a_90_95 <= 450.0

    # Monotonicity of POD curve
    nominal_pod = pod["curve_data"]["pod_nominal_percent"]
    for i in range(len(nominal_pod) - 1):
        assert nominal_pod[i] <= nominal_pod[i + 1]


def test_acoustic_ndt_api_endpoints():
    """Validates FastAPI REST endpoints for Stage 33."""
    client = TestClient(app)

    # 1. Materials DB
    res_mat = client.get("/api/v1/acoustic-ndt/materials")
    assert res_mat.status_code == 200
    mat_data = res_mat.json()["data"]
    assert "TI_6AL_4V" in mat_data
    assert "INCONEL_718" in mat_data

    # 2. A-scan endpoint
    res_ascan = client.post(
        "/api/v1/acoustic-ndt/ascan",
        json={
            "material_key": "TI_6AL_4V",
            "specimen_thickness_mm": 20.0,
            "transducer_freq_mhz": 5.0,
            "flaw_depth_mm": 10.0,
            "flaw_diameter_um": 300.0,
        },
    )
    assert res_ascan.status_code == 200
    assert res_ascan.json()["data"]["flaw_detected"] is True

    # 3. B-scan endpoint
    res_bscan = client.post(
        "/api/v1/acoustic-ndt/bscan",
        json={
            "material_key": "TI_6AL_4V",
            "specimen_length_mm": 30.0,
            "specimen_thickness_mm": 20.0,
            "flaw_x_mm": 15.0,
            "flaw_depth_mm": 10.0,
            "flaw_diameter_um": 300.0,
            "scan_steps": 25,
        },
    )
    assert res_bscan.status_code == 200
    assert res_bscan.json()["data"]["num_x_steps"] == 25

    # 4. Micro-CT endpoint
    res_ct = client.post(
        "/api/v1/acoustic-ndt/micro-ct",
        json={
            "material_key": "TI_6AL_4V",
            "grid_size": 48,
            "inject_voids": True,
            "inject_crack": True,
        },
    )
    assert res_ct.status_code == 200
    assert res_ct.json()["data"]["grid_resolution"] == 48

    # 5. POD curve endpoint
    res_pod = client.post(
        "/api/v1/acoustic-ndt/pod-curve",
        json={
            "material_key": "TI_6AL_4V",
            "inspection_modality": "ULTRASONIC_5MHZ",
            "false_call_rate_percent": 1.0,
        },
    )
    assert res_pod.status_code == 200
    assert "qualification_thresholds_um" in res_pod.json()["data"]
