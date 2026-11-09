"""
Unit tests for Stage 32: In-Situ LPBF Melt-Pool PINN Digital Twin.
Verifies Rosenthal 3D thermal conduction, Marangoni surface convection,
defect regime diagnosis (Keyholing, Lack of Fusion, Conduction Mode),
coaxial pyrometer telemetry with feedforward power control, and REST API.
"""

import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.lpbf_meltpool_pinn import (
    MeltPoolRegime,
    compute_rosenthal_temperature,
    solve_melt_pool_dimensions,
    simulate_coaxial_pyrometer_scanpass,
    ALLOY_THERMAL_DB,
)
from backend.main import app

client = TestClient(app)


def test_rosenthal_temperature_physics():
    """Verifies Rosenthal thermal conduction scaling with distance and power."""
    alpha = 6.25e-6  # High-temp Ti-6Al-4V diffusivity
    k = 18.0         # High-temp thermal conductivity
    eta = 0.35

    t_close = compute_rosenthal_temperature(
        x=0.0, y=0.0, z=20e-6,
        laser_power_w=280.0,
        scan_speed_mps=1.2,
        absorptivity=eta,
        k_thermal=k,
        diffusivity=alpha,
    )
    t_far = compute_rosenthal_temperature(
        x=0.0, y=0.0, z=200e-6,
        laser_power_w=280.0,
        scan_speed_mps=1.2,
        absorptivity=eta,
        k_thermal=k,
        diffusivity=alpha,
    )
    # Temperature must decrease with distance from the laser heat source
    assert t_close > t_far
    assert t_close > 2000.0  # Above Ti-6Al-4V melting point (1928 K)
    assert t_far < 1000.0


def test_melt_pool_dimensions_and_marangoni_convection():
    """Verifies melt-pool dimensions and Marangoni surface shear velocity."""
    res = solve_melt_pool_dimensions(
        laser_power_w=280.0,
        scan_speed_mps=1.2,
        beam_radius_um=50.0,
        alloy_key="TI_6AL_4V",
    )
    dims = res["dimensions"]
    thermal = res["thermal_field"]

    # Physical bounds for standard LPBF Ti-6Al-4V single bead:
    assert 40.0 <= dims["depth_um"] <= 120.0
    assert 80.0 <= dims["width_um"] <= 250.0
    assert 120.0 <= dims["length_um"] <= 450.0

    # Aspect ratio should be in optimal conduction range ~ 0.4 to 1.1
    assert 0.3 <= dims["aspect_ratio_d_w"] <= 1.2

    # Peak temperature should exceed melting point (1655 °C)
    assert thermal["peak_temperature_c"] > 1655.0

    # Marangoni convection velocity must be physically positive
    assert thermal["marangoni_velocity_mps"] > 0.05


def test_defect_regime_classification():
    """Verifies defect identification: Keyholing at 750W, Lack of Fusion at 60W, Optimal at 280W."""
    # 1. Lack of Fusion: low power (70W) fails to penetrate 40um layer
    res_lof = solve_melt_pool_dimensions(
        laser_power_w=70.0,
        scan_speed_mps=1.5,
        layer_thickness_um=40.0,
        alloy_key="TI_6AL_4V",
    )
    assert res_lof["process_window"]["regime"] == MeltPoolRegime.LACK_OF_FUSION.value

    # 2. Keyhole Porosity: extreme power (800W) creates vapor cavity
    res_keyhole = solve_melt_pool_dimensions(
        laser_power_w=800.0,
        scan_speed_mps=0.4,
        layer_thickness_um=40.0,
        alloy_key="TI_6AL_4V",
    )
    assert res_keyhole["process_window"]["regime"] == MeltPoolRegime.KEYHOLE_POROSITY.value

    # 3. Optimal Conduction mode: balanced 280W at 1.2 m/s
    res_opt = solve_melt_pool_dimensions(
        laser_power_w=280.0,
        scan_speed_mps=1.2,
        layer_thickness_um=40.0,
        alloy_key="TI_6AL_4V",
    )
    assert res_opt["process_window"]["regime"] == MeltPoolRegime.CONDUCTION_OPTIMAL.value


def test_pyrometer_scanpass_feedforward_power_adaptation():
    """Verifies closed-loop pyrometer telemetry and power modulation over overhang."""
    # Run with feedforward active
    res_ctrl = simulate_coaxial_pyrometer_scanpass(
        alloy_key="TI_6AL_4V",
        nominal_laser_power_w=280.0,
        scan_speed_mps=1.2,
        enable_feedforward_control=True,
        inject_overhang_geometry=True,
        scan_track_length_mm=15.0,
    )
    # Run without feedforward
    res_no_ctrl = simulate_coaxial_pyrometer_scanpass(
        alloy_key="TI_6AL_4V",
        nominal_laser_power_w=280.0,
        scan_speed_mps=1.2,
        enable_feedforward_control=False,
        inject_overhang_geometry=True,
        scan_track_length_mm=15.0,
    )
    # Active feedforward must yield higher overall quality score by preventing keyhole overheating
    assert res_ctrl["summary"]["overall_quality_score_percent"] >= res_no_ctrl["summary"]["overall_quality_score_percent"]
    assert len(res_ctrl["telemetry_stream"]) > 10


def test_lpbf_meltpool_api_endpoints():
    """Verifies REST API endpoints for Stage 32."""
    resp_alloys = client.get("/api/v1/lpbf-meltpool/alloys")
    assert resp_alloys.status_code == 200
    alloys = resp_alloys.json()["data"]
    assert "TI_6AL_4V" in alloys

    resp_solve = client.post(
        "/api/v1/lpbf-meltpool/solve",
        json={
            "laser_power_w": 280.0,
            "scan_speed_mps": 1.2,
            "beam_radius_um": 50.0,
            "layer_thickness_um": 40.0,
            "alloy_key": "TI_6AL_4V",
        },
    )
    assert resp_solve.status_code == 200
    data = resp_solve.json()["data"]
    assert data["dimensions"]["depth_um"] > 30.0

    resp_pyro = client.post(
        "/api/v1/lpbf-meltpool/pyrometer-scan",
        json={
            "alloy_key": "TI_6AL_4V",
            "nominal_laser_power_w": 280.0,
            "scan_speed_mps": 1.2,
            "enable_feedforward_control": True,
            "inject_overhang_geometry": True,
            "scan_track_length_mm": 10.0,
        },
    )
    assert resp_pyro.status_code == 200
    assert "telemetry_stream" in resp_pyro.json()["data"]
