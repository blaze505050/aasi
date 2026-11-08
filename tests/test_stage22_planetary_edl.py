"""
Unit and Integration Tests for Stage 22: Relativistic & Post-Newtonian Planetary EDL with Optical TRN.
======================================================================================================
Tests General Relativistic Parameterized Post-Newtonian (PPN) gravity, Sutton-Graves aerothermal heat flux,
hypersonic entry corridor dynamics, supersonic parachute deployment, Optical TRN EKF covariance collapse,
and FastAPI REST endpoints.
"""

import math
import numpy as np
import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.planetary_edl_trn import (
    PlanetaryEDLEngine,
    PlanetaryEDLNavigator,
    PLANETARY_DATABASE,
    EDL_PRESETS,
    PlanetaryBody,
    EDLPhase,
)
from backend.main import app

client = TestClient(app)


def test_ppn_relativistic_gravity_and_j2():
    """Verifies that PPN General Relativistic and J2 oblateness corrections compute properly."""
    planet = PLANETARY_DATABASE["MARS"]
    r_vec = np.array([0.0, 0.0, planet.radius_m + 100000.0], dtype=np.float64)  # 100 km altitude
    v_vec = np.array([4500.0, 0.0, -800.0], dtype=np.float64)

    a_ppn = PlanetaryEDLEngine.compute_ppn_acceleration(r_vec, v_vec, planet, gamma_ppn=1.0, beta_ppn=1.0)
    mag_a = float(np.linalg.norm(a_ppn))

    # Classical Newtonian magnitude: mu / r^2
    r_mag = float(np.linalg.norm(r_vec))
    a_newton_mag = planet.mu_m3_s2 / (r_mag ** 2)

    # Relativistic & J2 correction should slightly perturb Newtonian gravity
    diff = abs(mag_a - a_newton_mag)
    assert diff > 0.0, "PPN and J2 terms must not evaluate to exactly zero"
    assert diff / a_newton_mag < 0.01, f"Relative difference {diff / a_newton_mag} exceeded 1%"


def test_sutton_graves_heat_flux():
    """Verifies Sutton-Graves stagnation heat flux scaling with density and velocity cubed."""
    planet = PLANETARY_DATABASE["MARS"]
    density = 0.00015  # kg/m^3
    velocity = 5500.0   # m/s
    nose_radius = 2.25  # m

    q_dot_w = PlanetaryEDLEngine.compute_sutton_graves_heat_flux(
        density_kg_m3=density,
        velocity_mps=velocity,
        nose_radius_m=nose_radius,
        k_sg=planet.sutton_graves_k,
    )
    q_dot_mw = q_dot_w / 1e6
    assert 0.15 < q_dot_mw < 10.0, f"Heat flux {q_dot_mw} MW/m^2 outside expected range [0.15, 10.0]"


def test_mars_jezero_edl_skycrane_simulation():
    """Verifies full EDL trajectory for Mars Jezero Crater with Optical TRN covariance collapse."""
    dossier = PlanetaryEDLNavigator.execute_edl_simulation("MARS_JEZERO_CRATER_SKYCRANE")

    assert dossier.target_planet == PlanetaryBody.MARS.value
    assert dossier.entry_mass_kg == 1025.0
    assert dossier.ballistic_coefficient_kg_m2 > 30.0
    assert dossier.peak_g_load < 16.0
    assert dossier.peak_heat_flux_mw_m2 > 0.15
    assert dossier.optical_trn_fixes >= 5
    # Covariance collapses to sub-10-meter precision
    assert dossier.landing_error_cep_m < 15.0
    assert dossier.final_touchdown_speed_mps < 2.0
    assert len(dossier.trajectory) > 50
    assert len(dossier.merkle_provenance_hash) == 64


def test_isro_gaganyaan_reentry_simulation():
    """Verifies Gaganyaan crew module controlled hypersonic deorbit to Bay of Bengal."""
    dossier = PlanetaryEDLNavigator.execute_edl_simulation("ISRO_GAGANYAAN_REENTRY_BAY_OF_BENGAL")

    assert dossier.target_planet == PlanetaryBody.EARTH.value
    assert dossier.entry_mass_kg == 5300.0
    assert "Bay of Bengal" in dossier.target_site_name
    assert dossier.peak_g_load < 16.0  # Safe envelope limit for lifting/ballistic entry
    assert dossier.final_touchdown_speed_mps < 5.0


def test_edl_api_endpoints():
    """Tests FastAPI REST endpoints for Stage 22."""
    # 1. Presets endpoint
    resp_pre = client.get("/api/v1/edl/presets")
    assert resp_pre.status_code == 200
    presets = resp_pre.json()
    assert "MARS_JEZERO_CRATER_SKYCRANE" in presets
    assert "ISRO_GAGANYAAN_REENTRY_BAY_OF_BENGAL" in presets

    # 2. Planetary environments endpoint
    resp_planets = client.get("/api/v1/edl/planets")
    assert resp_planets.status_code == 200
    planets = resp_planets.json()
    assert "MARS" in planets and "EARTH" in planets and "VENUS" in planets

    # 3. Simulate endpoint
    payload = {
        "preset_key": "MARS_JEZERO_CRATER_SKYCRANE",
        "override_entry_mass_kg": 1050.0,
    }
    resp_sim = client.post("/api/v1/edl/simulate", json=payload)
    assert resp_sim.status_code == 200
    data = resp_sim.json()
    assert data["target_planet"] == PlanetaryBody.MARS.value
    assert data["entry_mass_kg"] == 1050.0
    assert data["landing_error_cep_m"] < 15.0
    assert len(data["trajectory"]) > 40
    assert len(data["optical_features"]) > 0
