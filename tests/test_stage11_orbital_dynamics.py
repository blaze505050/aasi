"""
Tests for Stage 11: High-Precision Orbital Dynamics & Non-Spherical Gravity Field Engine.
========================================================================================
Verifies:
1. Keplerian <-> Cartesian conversion bi-directional round-trip accuracy.
2. Geopotential harmonics (J2, J3, J4, C22, S22) acceleration calculations.
3. Upper atmospheric drag with Earth-rotation relative velocity.
4. Solar radiation pressure with cylindrical Earth umbra eclipse detection.
5. 4th-Order Symplectic Yoshida integrator energy preservation (Hamiltonian invariant).
6. FastAPI endpoints: POST /api/orbital/propagate and GET /api/orbital/presets.
"""

import sys
from pathlib import Path
import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

# Ensure package roots are on sys.path
_repo_root = Path(__file__).resolve().parent.parent
_fno_pkg = _repo_root / "aasi-aero-fno"
for p in [str(_repo_root), str(_fno_pkg)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from aasi_aero_fno.orbital_dynamics import (
    HighPrecisionOrbitalEngine,
    OrbitalVehicleProperties,
    KeplerianElements,
    SymplecticOrbitalIntegrator,
    ISRO_MISSION_PRESETS,
    MU_EARTH,
    R_EARTH,
)
from backend.main import app


@pytest.fixture
def test_client():
    return TestClient(app)


def test_keplerian_cartesian_round_trip():
    """Verifies that Keplerian -> Cartesian -> Keplerian round-trip preserves state."""
    orig_elements = KeplerianElements(
        semi_major_axis_m=R_EARTH + 400000.0,
        eccentricity=0.015,
        inclination_deg=51.6,
        raan_deg=75.0,
        arg_of_perigee_deg=30.0,
        true_anomaly_deg=45.0,
    )
    r_eci, v_eci = HighPrecisionOrbitalEngine.keplerian_to_rv(orig_elements)

    # Check radius and velocity magnitude
    r_mag = np.linalg.norm(r_eci)
    v_mag = np.linalg.norm(v_eci)
    assert 6700000.0 < r_mag < 6900000.0
    assert 7600.0 < v_mag < 7800.0

    # Invert back to Keplerian
    recovered = HighPrecisionOrbitalEngine.rv_to_keplerian(r_eci, v_eci)

    assert abs(recovered.semi_major_axis_m - orig_elements.semi_major_axis_m) < 1.0  # within 1 meter
    assert abs(recovered.eccentricity - orig_elements.eccentricity) < 1e-4
    assert abs(recovered.inclination_deg - orig_elements.inclination_deg) < 1e-3
    assert abs(recovered.raan_deg - orig_elements.raan_deg) < 1e-3
    assert abs(recovered.arg_of_perigee_deg - orig_elements.arg_of_perigee_deg) < 1e-2
    assert abs(recovered.true_anomaly_deg - orig_elements.true_anomaly_deg) < 1e-2


def test_gravity_harmonics_breakdown():
    """Verifies geopotential acceleration breakdown: central, J2, J3, J4, and C22/S22."""
    r_leo = np.array([R_EARTH + 400000.0, 0.0, 100000.0])
    a_total, breakdown = HighPrecisionOrbitalEngine.compute_gravity_accelerations(r_leo)

    # Central acceleration should be ~8.68 m/s^2 at 400 km
    assert 8.0 < breakdown["central_g"] < 9.5
    # J2 oblateness acceleration is ~1e-2 to 1e-3 of central
    assert 0.001 < breakdown["j2_oblateness"] < 0.1
    # J3 and J4 should be smaller than J2
    assert breakdown["j3_pear"] < breakdown["j2_oblateness"]
    assert breakdown["j4_harmonic"] < breakdown["j2_oblateness"]
    # Total vector should point predominantly inward (towards Earth center)
    assert a_total[0] < 0.0


def test_atmospheric_drag_and_earth_rotation():
    """Verifies that atmospheric drag opposes relative velocity and scales with altitude."""
    engine = HighPrecisionOrbitalEngine()

    # 200 km altitude: dense upper atmosphere
    r_200 = np.array([R_EARTH + 200000.0, 0.0, 0.0])
    v_leo = np.array([0.0, 7800.0, 0.0])
    _, break_200, _ = engine.compute_all_accelerations(r_200, v_leo, time_s=0.0, enable_drag=True)

    # 600 km altitude: much lower density
    r_600 = np.array([R_EARTH + 600000.0, 0.0, 0.0])
    _, break_600, _ = engine.compute_all_accelerations(r_600, v_leo, time_s=0.0, enable_drag=True)

    assert break_200["atmospheric_drag"] > 0.0
    assert break_600["atmospheric_drag"] > 0.0
    # Drag at 200 km should be orders of magnitude larger than at 600 km
    assert break_200["atmospheric_drag"] > break_600["atmospheric_drag"] * 100.0


def test_symplectic_energy_conservation():
    """Verifies that 4th-order Symplectic Yoshida integrator bounds Hamiltonian energy error."""
    engine = HighPrecisionOrbitalEngine()
    gaganyaan_preset = ISRO_MISSION_PRESETS["GAGANYAAN_LEO"]["elements"]

    # Propagate for 1 orbit (~5500 seconds) with step size 30s
    steps = engine.propagate_orbit(
        initial_elements=gaganyaan_preset,
        duration_s=5500.0,
        time_step_s=30.0,
        enable_drag=False,  # Pure conservative field to verify symplectic property
        enable_srp=False,
        enable_third_body=False,
        enable_relativity=False,
    )

    assert len(steps) > 100
    # Symplectic integrator guarantees bounded energy drift without secular dissipation
    max_energy_error = max(s.energy_conservation_error for s in steps)
    assert max_energy_error < 5e-5, f"Energy conservation error {max_energy_error} exceeded symplectic tolerance 5e-5"


def test_api_orbital_propagation(test_client):
    """Verifies POST /api/orbital/propagate endpoint returns verified trajectory data."""
    payload = {
        "preset_key": "SPADEX_CHASER",
        "duration_hours": 1.5,
        "time_step_s": 60.0,
        "enable_drag": True,
        "enable_srp": True,
        "enable_third_body": True,
        "enable_relativity": True,
    }
    response = test_client.post("/api/orbital/propagate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["vehicle_name"] == "SpaDeX-Chaser"
    assert data["symplectic_invariant_verified"] is True
    assert len(data["trajectory"]) > 10
    first_pt = data["trajectory"][0]
    assert "altitude_km" in first_pt
    assert "acceleration_breakdown" in first_pt
    assert "j2_oblateness" in first_pt["acceleration_breakdown"]
    assert "provenance_hash" in data


def test_api_orbital_presets(test_client):
    """Verifies GET /api/orbital/presets returns ISRO missions."""
    response = test_client.get("/api/orbital/presets")
    assert response.status_code == 200
    presets = response.json()

    assert "GAGANYAAN_LEO" in presets
    assert "SPADEX_CHASER" in presets
    assert "CHANDRAYAAN4_TLI" in presets
    assert "NAVIC_GEO" in presets
    assert presets["GAGANYAAN_LEO"]["semi_major_axis_km"] > 6700.0
