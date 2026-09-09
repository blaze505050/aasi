"""
Deterministic Engineering Benchmarks for AASI.
Validates numerical physical solvers against known analytical solutions
with physically meaningful tolerances.
"""

import math
import pytest
from backend.tools.orbit import calculate_circular_orbit, calculate_escape_velocity, calculate_hohmann_transfer
from backend.tools.rocket import rocket_equation, required_mass_ratio


def test_benchmark_earth_circular_orbit_500km():
    """
    Benchmark 1: Earth Circular LEO at 500 km altitude.
    - Reference radius: 6878.137 km
    - Expected velocity: 7.6126 km/s (tol: 0.1%)
    - Expected period: 94.615 minutes (tol: 0.2%)
    """
    res = calculate_circular_orbit(altitude_km=500.0, central_body="Earth")
    results = res["results"]

    expected_v_km_s = 7.6126
    expected_period_min = 94.615

    assert math.isclose(results["orbital_velocity_km_s"], expected_v_km_s, rel_tol=1e-3), (
        f"Velocity {results['orbital_velocity_km_s']} differs from benchmark {expected_v_km_s}"
    )
    assert math.isclose(results["orbital_period_minutes"], expected_period_min, rel_tol=2e-3), (
        f"Period {results['orbital_period_minutes']} differs from benchmark {expected_period_min}"
    )


def test_benchmark_earth_escape_velocity_500km():
    """
    Benchmark 2: Earth Parabolic Escape Velocity at 500 km altitude.
    - Expected escape velocity: sqrt(2) * v_circ = 10.7658 km/s (tol: 0.1%)
    """
    res = calculate_escape_velocity(altitude_km=500.0, central_body="Earth")
    results = res["results"]

    expected_v_esc_km_s = 10.7658

    assert math.isclose(results["escape_velocity_km_s"], expected_v_esc_km_s, rel_tol=1e-3), (
        f"Escape velocity {results['escape_velocity_km_s']} differs from benchmark {expected_v_esc_km_s}"
    )
    assert math.isclose(results["ratio_to_circular"], math.sqrt(2.0), rel_tol=1e-4)


def test_benchmark_hohmann_transfer_leo_200_to_500km():
    """
    Benchmark 3: Planar Hohmann Transfer between 200 km and 500 km Earth circular orbits.
    - Expected total Delta-v: 169.8 m/s (tol: 0.5%)
    - Expected transfer duration: 45.77 minutes (tol: 0.5%)
    """
    res = calculate_hohmann_transfer(initial_altitude_km=200.0, final_altitude_km=500.0, central_body="Earth")
    results = res["results"]

    expected_total_dv_m_s = 171.63
    expected_duration_min = 45.77

    assert math.isclose(results["total_delta_v_m_s"], expected_total_dv_m_s, rel_tol=1e-3), (
        f"Total Delta-v {results['total_delta_v_m_s']} differs from benchmark {expected_total_dv_m_s}"
    )
    assert math.isclose(results["transfer_time_minutes"], expected_duration_min, rel_tol=5e-3), (
        f"Transfer duration {results['transfer_time_minutes']} differs from benchmark {expected_duration_min}"
    )


def test_benchmark_tsiolkovsky_rocket_stage():
    """
    Benchmark 4: Tsiolkovsky rocket equation for a standard upper-stage configuration.
    - Inputs: Isp = 350.0 s, m0 = 10000.0 kg, mf = 3000.0 kg, g0 = 9.80665 m/s^2
    - Expected Delta-v: 4132.39 m/s (tol: 0.05%)
    - Expected mass ratio: 3.3333 (tol: 0.05%)
    """
    res = rocket_equation(isp_s=350.0, initial_mass_kg=10000.0, final_mass_kg=3000.0)
    results = res["results"]

    expected_dv_m_s = 4132.39
    expected_ratio = 10000.0 / 3000.0

    assert math.isclose(results["delta_v_m_s"], expected_dv_m_s, rel_tol=5e-4), (
        f"Delta-v {results['delta_v_m_s']} differs from benchmark {expected_dv_m_s}"
    )
    assert math.isclose(results["mass_ratio"], expected_ratio, rel_tol=5e-4), (
        f"Mass ratio {results['mass_ratio']} differs from benchmark {expected_ratio}"
    )
    assert results["propellant_mass_kg"] == 7000.0
