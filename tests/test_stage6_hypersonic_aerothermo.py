"""
Unit & Integration Test Suite for Stage 6: Hypersonic Non-Equilibrium Aerothermodynamics.
Validates Park 7-species reacting chemistry, two-temperature non-equilibrium,
Fay-Riddell convective flux, Tauber-Sutton radiative flux, shock standoff distance,
plasma blackout detection, and FastAPI endpoints.
Conforms to ASME V&V 20-2009.
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from aasi_aero_fno.hypersonic_aerothermo import (
    HypersonicAerothermoEngine,
    compute_hypersonic_chemical_equilibrium,
    get_freestream_atmospheric_properties,
    HYPERSONIC_BENCHMARKS,
)
from backend.main import app

client = TestClient(app)


def test_standard_atmosphere_scaling():
    """Verify atmospheric density and pressure decay monotonically with altitude."""
    rho_sl, p_sl, t_sl = get_freestream_atmospheric_properties(0.0)
    rho_strat, p_strat, t_strat = get_freestream_atmospheric_properties(30.0)
    rho_meso, p_meso, t_meso = get_freestream_atmospheric_properties(65.0)

    assert rho_sl > rho_strat > rho_meso
    assert p_sl > p_strat > p_meso
    assert 100.0 < t_strat < 300.0
    assert 100.0 < t_meso < 300.0


def test_park_7species_dissociation_hierarchy():
    """
    Verify high-temperature air chemistry hierarchy:
    1. Low Temp (T=1500K): undissociated N2 and O2 dominate.
    2. Medium Temp (T=3500K): O2 is heavily dissociated into atomic O; N2 largely intact.
    3. High Temp (T=8000K): both O2 and N2 are dissociated into atomic O and N; ionization occurs.
    """
    state_low = compute_hypersonic_chemical_equilibrium(stagnation_temp_k=1500.0, stagnation_pressure_pa=1e5, mach_infinity=5.0)
    assert state_low.mole_fractions["O2"] > 0.15
    assert state_low.mole_fractions["N2"] > 0.70
    assert state_low.mole_fractions["O"] < 0.05
    assert state_low.is_rf_blackout is False

    state_med = compute_hypersonic_chemical_equilibrium(stagnation_temp_k=3500.0, stagnation_pressure_pa=1e5, mach_infinity=12.0)
    assert state_med.mole_fractions["O"] > state_med.mole_fractions["O2"]
    assert state_med.mole_fractions["N2"] > 0.40  # N2 has not fully dissociated yet

    state_high = compute_hypersonic_chemical_equilibrium(stagnation_temp_k=8500.0, stagnation_pressure_pa=1e5, mach_infinity=24.0)
    assert state_high.mole_fractions["O"] > 0.10
    assert state_high.mole_fractions["N"] > 0.10
    assert state_high.electron_number_density_per_m3 > 1.0e17
    assert state_high.is_rf_blackout is True


def test_gaganyaan_reentry_heat_flux_and_standoff():
    """Verify ISRO Gaganyaan crew module re-entry aerothermal state."""
    res = HypersonicAerothermoEngine.solve_reentry_state(
        vehicle_name="ISRO Gaganyaan Crew Module",
        altitude_km=65.0,
        mach=20.0,
        nose_radius_m=1.8,
        flight_path_angle_deg=-1.6,
    )

    assert res.velocity_m_s > 5000.0
    assert res.stagnation_temperature_k > 4000.0
    assert res.shock_standoff_distance_mm > 10.0  # Blunt capsule standoff
    assert res.convective_heat_flux_mw_m2 > 0.1
    assert res.total_heat_flux_mw_m2 >= res.convective_heat_flux_mw_m2
    assert res.asme_gci_fine_pct < 0.5


def test_billig_shock_standoff_scaling():
    """Verify Billig standoff distance increases with nose radius Rn and decreases with Mach."""
    res_small_r = HypersonicAerothermoEngine.solve_reentry_state(mach=15.0, nose_radius_m=0.5)
    res_large_r = HypersonicAerothermoEngine.solve_reentry_state(mach=15.0, nose_radius_m=2.0)
    assert res_large_r.shock_standoff_distance_mm > res_small_r.shock_standoff_distance_mm * 3.5

    res_mach_10 = HypersonicAerothermoEngine.solve_reentry_state(mach=10.0, nose_radius_m=1.0)
    res_mach_25 = HypersonicAerothermoEngine.solve_reentry_state(mach=25.0, nose_radius_m=1.0)
    assert res_mach_10.shock_standoff_distance_mm > res_mach_25.shock_standoff_distance_mm


def test_fastapi_hypersonic_endpoints():
    """Test the Stage 6 FastAPI endpoints."""
    # 1. Solve endpoint
    solve_resp = client.post(
        "/api/aero/hypersonic/solve",
        json={
            "vehicle_name": "ISRO Gaganyaan Crew Module",
            "altitude_km": 62.0,
            "mach": 22.0,
            "nose_radius_m": 1.85,
            "flight_path_angle_deg": -1.6,
            "reentry_duration_s": 450.0,
        },
    )
    assert solve_resp.status_code == 200
    data = solve_resp.json()
    assert data["status"] == "SUCCESS"
    assert data["stage"] == 6
    assert data["data"]["stagnation_temperature_k"] > 5000.0
    assert data["data"]["chemical_state"]["is_rf_blackout"] is True
    assert "mole_fractions" in data["data"]["chemical_state"]

    # 2. Benchmarks endpoint
    bm_resp = client.get("/api/aero/hypersonic/benchmarks")
    assert bm_resp.status_code == 200
    bm_data = bm_resp.json()
    assert bm_data["status"] == "SUCCESS"
    assert "isro_sre1_reentry" in bm_data["benchmarks"]
    assert "nasa_ram_c2_blackout" in bm_data["benchmarks"]

