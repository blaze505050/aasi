"""
Unit and integration tests for AASI Stage 7: Fluid-Structure Interaction (FSI) & Transonic Flutter Prediction.
Verifies canonical p-k eigenvalue method, frequency coalescence, damping crossing (g=0),
transonic dip identification, FAR 25.629 margin, and API routes.
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

from aasi_aero_fno.fsi_flutter import (
    PKFlutterSolver,
    FlutterBoundaryResult,
    FlutterVelocityStation,
    AEROELASTIC_BENCHMARKS,
)
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_pk_flutter_solver_subsonic():
    """Verifies baseline subsonic flutter prediction on AGARD 445.6 wing."""
    result = PKFlutterSolver.solve_flutter_boundary(
        wing_name="AGARD 445.6 Aeroelastic Wing",
        mach=0.50,
        altitude_km=0.0,
        semichord_b=0.279,
        mass_ratio_mu=33.2,
        omega_h_rad_s=60.3,
        omega_alpha_rad_s=240.0,
        v_min=100.0,
        v_max=450.0,
        num_v_steps=35,
    )
    assert isinstance(result, FlutterBoundaryResult)
    assert result.mach == 0.50
    assert result.transonic_dip_factor == 1.0  # No transonic dip at M=0.50
    assert result.flutter_speed_vf_m_s is not None
    assert 300.0 <= result.flutter_speed_vf_m_s <= 370.0
    assert result.flutter_frequency_hz is not None
    assert result.far_25_629_safe_dive_speed_m_s is not None
    # FAR 25.629 safety margin: V_D = V_F / 1.15
    assert abs(result.far_25_629_safe_dive_speed_m_s - round(result.flutter_speed_vf_m_s / 1.15, 1)) < 1e-4
    assert len(result.velocity_stations) == 35
    assert len(result.provenance_hash) == 64


def test_transonic_flutter_dip():
    """
    Verifies that transonic flow (Mach ~0.96) experiences a significant dip
    in flutter speed due to shock movement phase lag, as observed in AGARD 445.6 tests.
    """
    res_subsonic = PKFlutterSolver.solve_flutter_boundary(mach=0.50)
    res_transonic = PKFlutterSolver.solve_flutter_boundary(mach=0.96)

    assert res_transonic.transonic_dip_factor < 0.80
    assert res_transonic.flutter_speed_vf_m_s is not None
    assert res_subsonic.flutter_speed_vf_m_s is not None
    # Flutter speed at M=0.96 must be lower than subsonic flutter speed by ~25%
    assert res_transonic.flutter_speed_vf_m_s < res_subsonic.flutter_speed_vf_m_s * 0.85


def test_frequency_coalescence_and_damping():
    """Verifies bending and torsion frequency convergence and damping behavior across speed range."""
    result = PKFlutterSolver.solve_flutter_boundary(mach=0.85, v_min=100.0, v_max=400.0, num_v_steps=20)
    
    first_station = result.velocity_stations[0]
    last_station = result.velocity_stations[-1]

    # Mode 1: Bending, Mode 2: Torsion
    f1_start = first_station.modes[0].frequency_hz
    f2_start = first_station.modes[1].frequency_hz

    f1_end = last_station.modes[0].frequency_hz
    f2_end = last_station.modes[1].frequency_hz

    # In classical flutter, bending frequency increases while torsional drops towards coalescence
    assert f1_end > f1_start
    assert f2_end < f2_start
    # Frequency gap must narrow
    assert (f2_end - f1_end) < (f2_start - f1_start)

    # Damping of Mode 2 (torsion) must increase (become less negative, then positive)
    g2_start = first_station.modes[1].damping_factor_g
    g2_end = last_station.modes[1].damping_factor_g
    assert g2_end > g2_start


def test_aeroelastic_benchmarks_catalog():
    """Verifies AGARD 445.6 and Isogai benchmark catalog."""
    assert "agard_445_6_mach_096" in AEROELASTIC_BENCHMARKS
    assert "isogai_2dof_airfoil" in AEROELASTIC_BENCHMARKS
    agard = AEROELASTIC_BENCHMARKS["agard_445_6_mach_096"]
    assert agard["mach"] == 0.96
    assert agard["experimental_flutter_speed_m_s"] == 242.5
    assert agard["asme_gci_pct"] <= 0.5


def test_api_flutter_solve(client):
    """Verifies POST /api/aero/flutter/solve returns 200 with valid aeroelastic boundary."""
    resp = client.post(
        "/api/aero/flutter/solve",
        json={
            "wing_name": "ISRO RLV Reusable Wing",
            "mach": 0.92,
            "altitude_km": 5.0,
            "semichord_b": 0.35,
            "mass_ratio_mu": 40.0,
            "omega_h_rad_s": 55.0,
            "omega_alpha_rad_s": 220.0,
            "v_min": 100.0,
            "v_max": 450.0,
            "num_v_steps": 25,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["stage"] == 7
    flutter_data = data["data"]
    assert flutter_data["wing_name"] == "ISRO RLV Reusable Wing"
    assert flutter_data["mach"] == 0.92
    assert "velocity_stations" in flutter_data
    assert len(flutter_data["velocity_stations"]) == 25
    assert flutter_data["flutter_speed_vf_m_s"] is not None


def test_api_flutter_benchmarks(client):
    """Verifies GET /api/aero/flutter/benchmarks returns 200 with benchmark dataset."""
    resp = client.get("/api/aero/flutter/benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["stage"] == 7
    assert "agard_445_6_mach_096" in data["benchmarks"]

