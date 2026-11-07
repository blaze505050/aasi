"""
Unit and integration tests for AASI Stage 9: Deep RL Closed-Loop Active Flow Control (AFC).
Verifies synthetic jet & plasma actuation dynamics, dynamic stall delay (> 6 deg),
boundary layer separation suppression, net energy balance (COP > 1.0), benchmarks, and API routes.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure package roots are on sys.path
_repo_root = Path(__file__).resolve().parent.parent
_fno_pkg = _repo_root / "aasi-aero-fno"
for p in [str(_repo_root), str(_fno_pkg)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from aasi_aero_fno.active_flow_control import (
    ActiveFlowControlEngine,
    AFCSystemResult,
    FLOW_CONTROL_BENCHMARKS,
)
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_afc_dynamic_stall_delay():
    """Verifies active flow control delays stall angle of attack by over 5 degrees."""
    res_active = ActiveFlowControlEngine.evaluate_flow_control(
        airfoil="NACA 0015",
        mach=0.15,
        alpha_deg=18.0,
        actuation_frequency_f_plus=1.25,
        momentum_coefficient_c_mu=0.018,
        is_afc_active=True,
    )
    res_baseline = ActiveFlowControlEngine.evaluate_flow_control(
        airfoil="NACA 0015",
        mach=0.15,
        alpha_deg=18.0,
        is_afc_active=False,
    )

    assert isinstance(res_active, AFCSystemResult)
    assert res_active.stall_delay_deg >= 5.0
    assert res_active.stall_alpha_afc_deg > res_active.stall_alpha_baseline_deg + 5.0
    # At alpha = 18 deg (post-stall for baseline, pre-stall for AFC):
    assert res_active.cl_achieved > res_baseline.cl_achieved
    assert res_active.cd_achieved < res_baseline.cd_baseline
    assert res_active.delta_cl_pct > 15.0
    assert len(res_active.provenance_hash) == 64


def test_afc_boundary_layer_reattachment():
    """Verifies that AFC pushes separation onset downstream and reduces bubble length."""
    res_active = ActiveFlowControlEngine.evaluate_flow_control(alpha_deg=17.0, is_afc_active=True)
    res_baseline = ActiveFlowControlEngine.evaluate_flow_control(alpha_deg=17.0, is_afc_active=False)

    sep_active = res_active.separation_profile
    sep_base = res_baseline.separation_profile

    assert sep_active.separation_onset_x_c is not None
    assert sep_base.separation_onset_x_c is not None
    # AFC separation onset must occur significantly further aft
    assert sep_active.separation_onset_x_c > sep_base.separation_onset_x_c
    assert sep_active.separation_bubble_length_c < sep_base.separation_bubble_length_c


def test_afc_energy_coefficient_of_performance():
    """Verifies aerodynamic power saved exceeds electrical actuation power (COP > 1.0)."""
    res = ActiveFlowControlEngine.evaluate_flow_control(alpha_deg=16.0, is_afc_active=True)
    assert res.coefficient_of_performance_cop > 1.0
    assert res.aerodynamic_power_saved_watts_per_m > res.actuation_power_watts_per_m


def test_flow_control_benchmarks_catalog():
    """Verifies Seifert and Greenblatt wind tunnel benchmark dataset."""
    assert "seifert_naca0015_periodic" in FLOW_CONTROL_BENCHMARKS
    assert "greenblatt_high_lift_afc" in FLOW_CONTROL_BENCHMARKS
    seifert = FLOW_CONTROL_BENCHMARKS["seifert_naca0015_periodic"]
    assert seifert["stall_delay_deg"] >= 6.0
    assert seifert["cop_peak"] > 4.0


def test_api_afc_evaluate(client):
    """Verifies POST /api/aero/afc/evaluate returns 200 with closed-loop flow control solution."""
    resp = client.post(
        "/api/aero/afc/evaluate",
        json={
            "airfoil": "ISRO RLV Landing Section",
            "mach": 0.18,
            "reynolds": 2.0e6,
            "alpha_deg": 17.5,
            "actuator_type": "ZNMF_Synthetic_Jet",
            "actuation_frequency_f_plus": 1.25,
            "momentum_coefficient_c_mu": 0.02,
            "slot_location_x_c": 0.12,
            "is_afc_active": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["stage"] == 9
    payload = data["data"]
    assert payload["airfoil"] == "ISRO RLV Landing Section"
    assert payload["stall_delay_deg"] >= 5.0
    assert payload["coefficient_of_performance_cop"] > 1.0


def test_api_afc_benchmarks(client):
    """Verifies GET /api/aero/afc/benchmarks returns 200 with benchmarks catalog."""
    resp = client.get("/api/aero/afc/benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["stage"] == 9
    assert "seifert_naca0015_periodic" in data["benchmarks"]
