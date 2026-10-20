"""
Tests for AASI Autopilot Exporter (PX4 and ArduPilot parameter decks).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.export.autopilot_exporter import AutopilotExporter, AirframeFlightConditions

client = TestClient(app)


def test_autopilot_tuning_basic():
    af = AirframeFlightConditions(
        mass_kg=3.0,
        wing_span_m=2.0,
        wing_area_m2=0.5,
        mean_chord_m=0.25,
        air_density_kg_m3=1.225,
        cg_pos_ratio=0.25,
    )
    result = AutopilotExporter.compute_autopilot_parameters(
        geometry_name="NACA 2412",
        cl_alpha_per_deg=0.108,
        cm_alpha_per_deg=-0.022,
        cl_max=1.40,
        cd0=0.009,
        x_ac=0.25,
        alpha_zero_lift_deg=-2.0,
        airframe=af,
    )

    assert result.geometry_name == "NACA 2412"
    assert result.stall_speed_ms > 0
    assert result.cruise_speed_ms > result.stall_speed_ms
    assert result.max_speed_ms > result.cruise_speed_ms
    assert "FW_AIRSPD_MIN" in result.px4_params_deck
    assert "FW_PSP_OFF" in result.px4_params_deck
    assert "ARSPD_FBW_MIN" in result.ardupilot_param_deck
    assert "TRIM_PITCH_CD" in result.ardupilot_param_deck
    assert result.structured_parameters["px4"]["FW_AIRSPD_MIN"] > 0


def test_autopilot_api_endpoint():
    response = client.post(
        "/api/export/autopilot",
        params={
            "geometry": "NACA 0012",
            "cl_alpha": 0.105,
            "cm_alpha": -0.025,
            "cl_max": 1.35,
            "cd0": 0.008,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "px4_params_deck" in data
    assert "ardupilot_param_deck" in data
    assert "structured_parameters" in data


def test_autopilot_download_endpoints():
    # PX4 download
    res_px4 = client.get("/api/export/autopilot/download?format=px4&geometry=NACA_0012")
    assert res_px4.status_code == 200
    assert "FW_AIRSPD_TRIM" in res_px4.text
    assert "attachment; filename=\"AASI_NACA_0012_PX4_Tuning.params\"" in res_px4.headers.get("content-disposition", "")

    # ArduPilot download
    res_ap = client.get("/api/export/autopilot/download?format=ardupilot&geometry=NACA_0012")
    assert res_ap.status_code == 200
    assert "ARSPD_FBW_CRUISE" in res_ap.text
    assert "attachment; filename=\"AASI_NACA_0012_ArduPilot_Tuning.param\"" in res_ap.headers.get("content-disposition", "")
