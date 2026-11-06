"""
AASI Stage 2 Unit & Integration Tests: Transonic Shock-Capturing Neural Operator.
Verifies Rankine-Hugoniot normal shock jump relations, critical pressure coefficient Cp*,
wave drag estimation, continuous-space flowfield generation, and AGARD reference benchmark validation.
"""

import math
import pytest
from fastapi.testclient import TestClient

from aasi_aero_fno.transonic_transolver import (
    calculate_cp_critical,
    rankine_hugoniot_normal_shock,
    estimate_wave_drag,
    TransonicTransolverEngine,
    AGARD_BENCHMARKS,
)
from backend.main import app

client = TestClient(app)


def test_cp_critical_formula():
    """Verifies critical pressure coefficient Cp* matches isentropic compressible flow relations."""
    cp_star_7 = calculate_cp_critical(0.70)
    cp_star_8 = calculate_cp_critical(0.80)

    # For M=0.70, Cp* should be approximately -0.78
    # For M=0.80, Cp* should be approximately -0.435
    assert -0.90 < cp_star_7 < -0.65
    assert -0.55 < cp_star_8 < -0.35
    # Cp* increases (becomes less negative) as Mach increases toward 1.0
    assert cp_star_8 > cp_star_7


def test_rankine_hugoniot_normal_shock():
    """Verifies normal shock jump conditions conform to the 2nd law of thermodynamics."""
    m1 = 1.40
    rh = rankine_hugoniot_normal_shock(m1)

    # Downstream Mach M2 must be subsonic (< 1.0)
    assert rh["m2"] < 1.0
    assert rh["m2"] > 0.65

    # Static pressure, density, and temperature must increase across compression shock
    assert rh["p2_p1"] > 2.0
    assert rh["rho2_rho1"] > 1.5
    assert rh["t2_t1"] > 1.2

    # Total (stagnation) pressure must decrease (p02/p01 < 1.0)
    assert rh["p02_p01"] < 1.0
    assert rh["p02_p01"] > 0.90

    # Entropy jump must be strictly positive (2nd Law of Thermodynamics)
    assert rh["delta_s_over_r"] > 0.0


def test_wave_drag_estimation():
    """Verifies wave drag is zero below sonic threshold and increases nonlinearly above."""
    cdw_subsonic = estimate_wave_drag(0.95)
    assert cdw_subsonic == 0.0

    cdw_mild = estimate_wave_drag(1.15)
    cdw_strong = estimate_wave_drag(1.45)

    assert cdw_mild > 0.0
    assert cdw_strong > cdw_mild


def test_transonic_transolver_rae2822_case9():
    """Tests continuous-space spectral Transolver prediction for AGARD RAE 2822 Case 9."""
    res = TransonicTransolverEngine.solve(
        airfoil="RAE 2822",
        mach_infinity=0.730,
        alpha_deg=3.19,
        reynolds=6.5e6,
        num_surface_points=100,
        include_field_grid=True,
    )

    # Verify shock detection and location
    assert res.shock_metrics.shock_detected is True
    assert 0.50 <= res.shock_metrics.x_shock_c <= 0.80

    # Verify pre-shock supersonic condition and post-shock subsonic condition
    assert res.shock_metrics.mach_pre_shock > 1.10
    assert res.shock_metrics.mach_post_shock < 1.0
    assert res.shock_metrics.static_pressure_ratio > 1.5

    # Verify wave drag contribution
    assert res.cd_wave > 0.003
    assert res.cd_total > res.cd_friction

    # Verify lift coefficient in AGARD ballpark
    assert 0.70 < res.cl < 1.25

    # Verify inference time is fast (< 35 ms)
    assert res.inference_time_ms < 35.0

    # Verify benchmark match
    assert res.matched_benchmark is not None
    assert res.matched_benchmark["airfoil"] == "RAE 2822"


def test_transonic_subsonic_fallback():
    """Verifies that at low subsonic Mach 0.20, no shock is detected and wave drag is zero."""
    res = TransonicTransolverEngine.solve(
        airfoil="NACA 0012",
        mach_infinity=0.20,
        alpha_deg=4.0,
        reynolds=3.0e6,
        include_field_grid=False,
    )

    assert res.shock_metrics.shock_detected is False
    assert res.cd_wave == 0.0
    assert res.shock_metrics.x_shock_c == 0.0


def test_api_transonic_solve_endpoint():
    """Tests FastAPI POST /api/aero/transonic/solve endpoint."""
    payload = {
        "airfoil": "RAE 2822",
        "mach_infinity": 0.730,
        "alpha_deg": 3.19,
        "reynolds": 6.5e6,
        "num_surface_points": 80,
        "include_field_grid": True,
    }
    response = client.post("/api/aero/transonic/solve", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["stage"] == 2
    assert "Transolver_3D" in data["architecture"]

    result = data["data"]
    assert result["airfoil"] == "RAE 2822"
    assert len(result["x_coords"]) == 80
    assert len(result["cp_upper"]) == 80
    assert result["shock_metrics"]["shock_detected"] is True
    assert result["flowfield"] is not None
    assert len(result["flowfield"]["mach_field"]) > 0


def test_api_transonic_benchmarks_endpoint():
    """Tests FastAPI GET /api/aero/transonic/benchmarks endpoint."""
    response = client.get("/api/aero/transonic/benchmarks")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "RAE_2822_CASE_6" in data["benchmarks"]
    assert "RAE_2822_CASE_9" in data["benchmarks"]
    assert "ONERA_M6_ETA_44" in data["benchmarks"]

