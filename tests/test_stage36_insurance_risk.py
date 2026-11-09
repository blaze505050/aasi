"""
Unit and regression tests for Stage 36: Constellation Collision Insurance Risk Underwriting Engine.
Validates:
1. NASA ORDEM / ESA MASTER calibrated spatial debris density profile across LEO.
2. Poisson compound conjunction rates and autonomous avoidance risk reduction.
3. Actuarial Solvency II 99.5% VaR, CVaR, Pure Premium, and commercial policy pricing.
4. FastAPI REST API endpoints.
"""

import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.constellation_insurance_engine import (
    compute_leo_debris_density,
    calculate_constellation_conjunction_risk,
    underwrite_constellation_insurance,
    INSURANCE_PRESETS,
)
from backend.main import app


def test_orbital_debris_density_and_flux():
    """Validates spatial debris density profile and peak belts."""
    rho_400 = compute_leo_debris_density(400.0)
    rho_820 = compute_leo_debris_density(820.0)  # Cosmos-Iridium debris peak
    rho_1400 = compute_leo_debris_density(1400.0)

    # 820 km peak must be strictly greater than 400 km and 1400 km
    assert rho_820 > rho_400
    assert rho_820 > rho_1400
    assert 1.0e-8 <= rho_820 <= 4.0e-8


def test_constellation_conjunction_risk_poisson():
    """Validates Poisson collision kinetics and autonomous maneuver credit."""
    # 1. 240 smallsats vs 24 smallsats
    risk_large = calculate_constellation_conjunction_risk(
        altitude_km=550.0,
        constellation_size=240,
        has_autonomous_avoidance=False,
    )
    risk_small = calculate_constellation_conjunction_risk(
        altitude_km=550.0,
        constellation_size=24,
        has_autonomous_avoidance=False,
    )
    assert risk_large["annual_expected_conjunctions"] > risk_small["annual_expected_conjunctions"]

    # 2. Autonomous avoidance effect
    risk_avoid = calculate_constellation_conjunction_risk(
        altitude_km=550.0,
        constellation_size=100,
        has_autonomous_avoidance=True,
    )
    risk_no_avoid = calculate_constellation_conjunction_risk(
        altitude_km=550.0,
        constellation_size=100,
        has_autonomous_avoidance=False,
    )
    # Effective rate with autonomous CBF thruster response should be ~8% of unmitigated
    assert risk_avoid["effective_annual_collision_rate"] < 0.15 * risk_no_avoid["effective_annual_collision_rate"]
    assert 0.0 <= risk_avoid["cumulative_mission_collision_probability_percent"] <= 100.0


def test_actuarial_underwriting_and_solvency_ii():
    """Validates Solvency II 99.5% VaR/CVaR and commercial premium pricing."""
    policy = underwrite_constellation_insurance(
        altitude_km=550.0,
        constellation_size=120,
        satellite_unit_cost_usd=1.5e6,
        has_autonomous_avoidance=True,
    )

    tiv = policy["constellation_profile"]["total_insurable_value_usd"]
    assert tiv == 120 * 1.5e6  # $180,000,000

    act = policy["actuarial_metrics"]
    var_995 = act["solvency_ii_var_995_usd"]
    cvar_995 = act["solvency_ii_cvar_995_usd"]

    # Solvency II properties
    assert 0.0 < var_995 <= tiv
    assert cvar_995 >= var_995
    assert act["worst_case_loss_fraction_percent"] <= 100.0

    # Pricing
    comm = policy["commercial_policy_pricing"]
    assert comm["commercial_annual_premium_usd"] > 25000.0
    assert comm["rate_on_line_percent"] > 0.0
    assert comm["autonomous_maneuver_discount_usd"] > 0.0

    # Exceedance curve
    curve = policy["loss_exceedance_curve"]
    assert len(curve) == 50


def test_insurance_api_endpoints():
    """Validates FastAPI REST endpoints for Stage 36."""
    client = TestClient(app)

    # 1. Presets endpoint
    res_presets = client.get("/api/v1/insurance-risk/presets")
    assert res_presets.status_code == 200
    pdata = res_presets.json()["data"]["presets"]
    assert "LEO_BROADBAND_MEGACONSTELLATION" in pdata

    # 2. Conjunction risk endpoint
    res_risk = client.post(
        "/api/v1/insurance-risk/conjunction-risk",
        json={
            "altitude_km": 550.0,
            "constellation_size": 100,
            "mission_duration_years": 5.0,
            "has_autonomous_avoidance": True,
        },
    )
    assert res_risk.status_code == 200
    assert "effective_annual_collision_rate" in res_risk.json()["data"]

    # 3. Underwrite endpoint
    res_uw = client.post(
        "/api/v1/insurance-risk/underwrite",
        json={
            "altitude_km": 550.0,
            "constellation_size": 80,
            "satellite_unit_cost_usd": 2.0e6,
            "mission_duration_years": 5.0,
            "has_autonomous_avoidance": True,
        },
    )
    assert res_uw.status_code == 200
    assert "commercial_policy_pricing" in res_uw.json()["data"]
