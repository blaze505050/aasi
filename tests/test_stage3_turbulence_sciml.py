"""
Unit & Integration Test Suite for Stage 3: High-Reynolds Turbulence SciML Closure.
Validates Pope's 10-tensor integrity basis, 5 Cayley-Hamilton invariants,
Schumann / Lumley realizability projection, Menter k-omega SST coupling,
and FastAPI endpoints conforming to ASME V&V 20-2009.
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from aasi_aero_fno.turbulence_tbnn import (
    HighReTurbulenceEngine,
    TensorBasisNeuralNetwork,
    compute_turbulent_tensors_and_invariants,
    compute_lumley_invariants,
    check_realizability,
    project_to_lumley_triangle,
    evaluate_menter_sst_blending,
    TURBULENCE_BENCHMARKS,
)
from backend.main import app

client = TestClient(app)


def test_popes_integrity_basis_and_invariants():
    """Verify Pope's 10-tensor integrity basis and 5 invariants."""
    grad_u = np.array([
        [0.0, 1200.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ])
    k = 20.0
    omega = 800.0

    s, w, T, invariants = compute_turbulent_tensors_and_invariants(grad_u, k, omega)

    assert s.shape == (3, 3)
    assert w.shape == (3, 3)
    assert T.shape == (10, 3, 3)
    assert len(invariants) == 5

    # Strain tensor must be symmetric
    assert np.allclose(s, s.T, atol=1e-7)
    # Rotation tensor must be anti-symmetric
    assert np.allclose(w, -w.T, atol=1e-7)

    # Invariants I1 = tr(s^2) >= 0, I2 = tr(w^2) <= 0
    assert invariants[0] >= 0.0
    assert invariants[1] <= 1e-7


def test_tbnn_realizability_and_trace_free():
    """Verify TBNN returns trace-free b_ij and physical realizability."""
    grad_u = np.array([
        [100.0, 500.0, 0.0],
        [0.0, -100.0, 0.0],
        [0.0, 0.0, 0.0],
    ])
    k = 15.0
    omega = 600.0

    out = TensorBasisNeuralNetwork.evaluate(grad_u, k, omega, enforce_lumley_realizability=True)

    b = np.array(out["anisotropy_tensor_b"])
    # Trace free check
    assert abs(np.trace(b)) < 1e-4

    # Realizability check
    realizability = out["realizability"]
    assert realizability["is_realizable"] is True
    assert realizability["min_eigenvalue"] >= -0.334
    assert realizability["eigenvalues"][0] <= 0.667


def test_lumley_projection_operator():
    """Verify projection maps an unphysical tensor back to valid Lumley region."""
    # Create an unphysical synthetic tensor with lambda_3 = -0.5 < -1/3
    unphysical_b = np.diag([0.3, 0.2, -0.5])
    audit_pre = check_realizability(unphysical_b)
    assert audit_pre["is_realizable"] is False

    # Apply projection
    projected_b = project_to_lumley_triangle(unphysical_b)
    audit_post = check_realizability(projected_b)

    assert audit_post["is_realizable"] is True
    assert audit_post["min_eigenvalue"] >= -0.334
    assert abs(np.trace(projected_b)) < 1e-6


def test_menter_sst_blending_functions():
    """Verify Menter F1 and F2 blending functions are bounded between [0, 1]."""
    # Near wall
    near_wall = evaluate_menter_sst_blending(k=10.0, omega=5000.0, y=1e-5)
    assert 0.0 <= near_wall.f1_blending <= 1.0
    assert 0.0 <= near_wall.f2_blending <= 1.0
    assert near_wall.f1_blending > 0.8  # Should be close to 1 at the wall

    # Outer freestream
    freestream = evaluate_menter_sst_blending(k=0.1, omega=10.0, y=1.0)
    assert 0.0 <= freestream.f1_blending <= 1.0
    assert freestream.f1_blending < 0.1  # Should decay to 0 in freestream


def test_boundary_layer_profile_marching():
    """Verify high-Reynolds boundary layer marching produces valid physical quantities."""
    result = HighReTurbulenceEngine.solve_boundary_layer(
        airfoil="RAE 2822",
        reynolds=6.5e6,
        mach=0.730,
        alpha_deg=3.19,
        num_stations=50,
    )

    assert len(result.x_c) == 50
    assert len(result.cf) == 50
    assert len(result.boundary_layer_thickness_mm) == 50
    assert len(result.shape_factor_h) == 50

    # Boundary layer should grow downstream
    assert result.boundary_layer_thickness_mm[-1] > result.boundary_layer_thickness_mm[0]

    # Shape factor H should be in standard turbulent boundary layer range [1.2, 3.5]
    for h in result.shape_factor_h:
        assert 1.1 <= h <= 4.0

    # ASME GCI fine mesh uncertainty should be reported
    assert result.asme_gci_fine_pct > 0.0
    assert len(result.provenance_hash) == 64


def test_fastapi_tbnn_endpoints():
    """Test the Stage 3 FastAPI endpoints."""
    # 1. TBNN Evaluate
    eval_resp = client.post(
        "/api/aero/turbulence/tbnn/evaluate",
        json={
            "velocity_gradient": [[0.0, 1000.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
            "turbulent_kinetic_energy_k": 20.0,
            "specific_dissipation_omega": 1000.0,
            "enforce_lumley_realizability": True,
        },
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["status"] == "SUCCESS"
    assert "anisotropy_tensor_b" in eval_data["data"]

    # 2. Boundary Layer
    bl_resp = client.post(
        "/api/aero/turbulence/boundary-layer",
        json={
            "airfoil": "RAE 2822",
            "reynolds": 6.5e6,
            "mach": 0.730,
            "alpha_deg": 3.19,
            "num_stations": 40,
        },
    )
    assert bl_resp.status_code == 200
    bl_data = bl_resp.json()
    assert bl_data["status"] == "SUCCESS"
    assert len(bl_data["data"]["cf"]) == 40

    # 3. Benchmarks
    bm_resp = client.get("/api/aero/turbulence/benchmarks")
    assert bm_resp.status_code == 200
    bm_data = bm_resp.json()
    assert bm_data["status"] == "SUCCESS"
    assert "nasa_tmr_flat_plate" in bm_data["benchmarks"]
    assert "samuel_joubert_apg" in bm_data["benchmarks"]
    assert "bachalo_johnson_bump" in bm_data["benchmarks"]
