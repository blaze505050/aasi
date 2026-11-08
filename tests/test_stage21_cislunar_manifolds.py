"""
Unit and Integration Tests for Stage 21: Autonomous Cislunar & Lagrange Point Halo Orbit Manifold Navigator (CR3BP).
===================================================================================================================
Tests Circular Restricted Three-Body Problem (CR3BP) synodic equations of motion, exact Newton-Raphson L1-L5
libration point coordinates, Jacobi energy constant conservation, 3D Halo / NRHO periodic orbit synthesis,
Monodromy matrix stability indices, invariant manifold tube generation (W^s, W^u), and FastAPI endpoints.
"""

import math
import numpy as np
import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.cislunar_manifolds import (
    CislunarDynamicsEngine,
    CislunarManifoldNavigator,
    StateCR3BP,
    LagrangePointType,
    OrbitFamily,
    generate_halo_orbit,
    compute_invariant_manifold_tubes,
    CISLUNAR_MISSION_PRESETS,
    MU_EARTH_MOON,
    CHAR_DISTANCE_KM,
)
from backend.main import app

client = TestClient(app)


def test_cr3bp_jacobi_conservation():
    """Verifies that numerical RK4 integration preserves the Jacobi energy constant within tolerance."""
    # Start at a state near L2
    init_state = StateCR3BP(x=1.12, y=0.0, z=0.05, vx=0.0, vy=-0.15, vz=0.0)
    c0 = CislunarDynamicsEngine.compute_jacobi_constant(init_state)

    curr = init_state.to_array()
    dt = 0.001
    for _ in range(120):
        curr = CislunarDynamicsEngine.rk4_step(curr, dt)

    c_final = CislunarDynamicsEngine.compute_jacobi_constant(StateCR3BP.from_array(curr))
    drift = abs(c_final - c0)
    assert drift < 1e-8, f"Jacobi constant drift {drift} exceeded tolerance 1e-8"


def test_lagrange_points_exact_coordinates():
    """Verifies exact coordinates and energy hierarchy for all 5 Earth-Moon libration points."""
    pts = CislunarDynamicsEngine.compute_lagrange_points()

    assert "L1" in pts and "L2" in pts and "L3" in pts and "L4" in pts and "L5" in pts

    l1 = pts["L1"]
    l2 = pts["L2"]
    l3 = pts["L3"]
    l4 = pts["L4"]
    l5 = pts["L5"]

    # In Earth-Moon system: L1 is between Earth and Moon (0.83 < x < 0.84)
    assert 0.83 < l1.x_synodic < 0.84, f"L1 x {l1.x_synodic} out of range"
    assert l1.y_synodic == 0.0

    # L2 is beyond Moon (1.15 < x < 1.16)
    assert 1.15 < l2.x_synodic < 1.16, f"L2 x {l2.x_synodic} out of range"
    assert l2.y_synodic == 0.0

    # L3 is opposite side of Earth (x < -1.0)
    assert l3.x_synodic < -1.0, f"L3 x {l3.x_synodic} out of range"

    # L4 and L5 are triangular (x = 0.5 - mu, y = +/- sqrt(3)/2)
    expected_x = 0.5 - MU_EARTH_MOON
    expected_y = math.sqrt(3.0) / 2.0
    assert abs(l4.x_synodic - expected_x) < 1e-5
    assert abs(l4.y_synodic - expected_y) < 1e-5
    assert abs(l5.y_synodic - (-expected_y)) < 1e-5

    # Jacobi energy hierarchy: C_L1 > C_L2 > C_L3 > C_L4 == C_L5
    assert l1.jacobi_constant > l2.jacobi_constant > l3.jacobi_constant > l4.jacobi_constant
    assert abs(l4.jacobi_constant - l5.jacobi_constant) < 1e-4


def test_halo_orbit_and_nrho_synthesis():
    """Verifies periodic 3D Halo orbit and NRHO generation around L1 and L2."""
    halo_l2 = generate_halo_orbit(
        lp_name="L2",
        family=OrbitFamily.SOUTHERN_HALO.value,
        amplitude_z_km=32000.0,
    )
    assert halo_l2.lagrange_point == "L2"
    assert halo_l2.period_days > 10.0 and halo_l2.period_days < 16.0
    assert len(halo_l2.trajectory_synodic_km) > 100
    assert halo_l2.pericynthion_km > 0.0
    assert halo_l2.stability_index_nu > 1.0

    nrho_l1 = generate_halo_orbit(
        lp_name="L1",
        family=OrbitFamily.NEAR_RECTILINEAR_HALO.value,
        amplitude_z_km=70000.0,
    )
    assert nrho_l1.lagrange_point == "L1"
    assert nrho_l1.period_days > 5.0 and nrho_l1.period_days < 8.0  # 9:2 resonance ~ 6.7 days
    assert nrho_l1.stability_index_nu > 1.0


def test_invariant_manifold_transfer_tubes():
    """Verifies synthesis of stable (W^s) and unstable (W^u) invariant manifold transfer branches."""
    halo = generate_halo_orbit(
        lp_name="L2",
        family=OrbitFamily.SOUTHERN_HALO.value,
        amplitude_z_km=32000.0,
    )
    stable_mf, unstable_mf = compute_invariant_manifold_tubes(
        halo_orbit=halo,
        num_branches=4,
        propagation_days=20.0,
    )

    assert len(stable_mf) == 4
    assert len(unstable_mf) == 4
    for b in stable_mf:
        assert b.branch_type == "STABLE_W_S"
        assert len(b.trajectory_points_km) > 50
        assert b.delta_v_insertion_mps < 50.0  # Zero-propellant coasting asymptotic insertion

    for b in unstable_mf:
        assert b.branch_type == "UNSTABLE_W_U"
        assert len(b.trajectory_points_km) > 50


def test_cislunar_navigator_dossier():
    """Verifies complete cislunar mission dossier generation with cryptographic Merkle proof."""
    dossier = CislunarManifoldNavigator.execute_cislunar_navigation(
        preset_key="ISRO_GAGANYAAN_LUNAR_GATEWAY_L2"
    )
    assert dossier.mission_name == "ISRO Gaganyaan Cislunar Space Station L2 Gateway"
    assert dossier.primary_lagrange_point == "L2"
    assert dossier.ballistic_delta_v_savings_pct >= 25.0
    assert len(dossier.merkle_provenance_hash) == 64


def test_cislunar_api_endpoints():
    """Tests FastAPI REST endpoints for Stage 21."""
    # 1. Presets endpoint
    resp = client.get("/api/v1/cislunar/presets")
    assert resp.status_code == 200
    presets = resp.json()
    assert "ISRO_GAGANYAAN_LUNAR_GATEWAY_L2" in presets
    assert "ARTEMIS_NRHO_L1_INSERTION" in presets

    # 2. Lagrange points endpoint
    resp_lp = client.get("/api/v1/cislunar/lagrange-points")
    assert resp_lp.status_code == 200
    lp_data = resp_lp.json()
    assert "L1" in lp_data and "L2" in lp_data and "L4" in lp_data

    # 3. Navigation simulation endpoint
    payload = {
        "preset_key": "ISRO_GAGANYAAN_LUNAR_GATEWAY_L2",
        "override_amplitude_z_km": 35000.0,
    }
    resp_nav = client.post("/api/v1/cislunar/navigate", json=payload)
    assert resp_nav.status_code == 200
    res = resp_nav.json()
    assert res["mission_name"] == "ISRO Gaganyaan Cislunar Space Station L2 Gateway"
    assert res["primary_lagrange_point"] == "L2"
    assert res["ballistic_delta_v_savings_pct"] >= 25.0
    assert len(res["stable_manifolds"]) == 4
    assert len(res["unstable_manifolds"]) == 4
    assert res["orbit_solution"]["amplitude_z_km"] == 35000.0
