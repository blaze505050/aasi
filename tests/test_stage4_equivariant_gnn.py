"""
Unit & Integration Test Suite for Stage 4: SE(3)-Equivariant 3D Airframe GNN.
Validates continuous Lie group SO(3) equivariance, translation invariance of scalar coefficients,
canonical airframe mesh generators, and FastAPI endpoints.
Conforms to ASME V&V 20-2009.
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from aasi_aero_fno.equivariant_gnn import (
    SE3EquivariantAirframeGNN,
    generate_canonical_airframe_mesh,
    euler_to_rotation_matrix,
    verify_so3_orthonormality,
    AEROSPACE_3D_BENCHMARKS,
)
from backend.main import app

client = TestClient(app)


def test_so3_matrix_orthonormality():
    """Verify euler_to_rotation_matrix produces valid orthogonal SO(3) matrices."""
    # Test arbitrary 3D angles
    for yaw in [-120.0, -45.0, 0.0, 30.0, 150.0]:
        for pitch in [-60.0, 0.0, 45.0]:
            for roll in [-170.0, 0.0, 90.0]:
                R = euler_to_rotation_matrix(yaw, pitch, roll)
                assert verify_so3_orthonormality(R, eps=1e-7)
                assert abs(np.linalg.det(R) - 1.0) < 1e-7
                assert np.allclose(R.T @ R, np.eye(3), atol=1e-7)


def test_se3_force_vector_equivariance():
    """
    Verify fundamental Lie algebra equivariance:
    For any R in SO(3) and translation t in R^3:
    F(R * X + t) == R * F(X)
    """
    # 1. Base evaluation at identity (0, 0, 0)
    base_res = SE3EquivariantAirframeGNN.evaluate(
        airframe_type="nasa_crm",
        mach=0.85,
        alpha_deg=2.2,
        yaw_deg=0.0,
        pitch_deg=0.0,
        roll_deg=0.0,
        translation_m=(0.0, 0.0, 0.0),
    )
    F_base = np.array(base_res.force_vector_N)

    # 2. Transformed evaluation at arbitrary 3D attitude and translation
    yaw = 45.0
    pitch = 20.0
    roll = -35.0
    trans = (100.0, -50.0, 25.0)

    R = euler_to_rotation_matrix(yaw, pitch, roll)
    trans_res = SE3EquivariantAirframeGNN.evaluate(
        airframe_type="nasa_crm",
        mach=0.85,
        alpha_deg=2.2,
        yaw_deg=yaw,
        pitch_deg=pitch,
        roll_deg=roll,
        translation_m=trans,
    )
    F_trans = np.array(trans_res.force_vector_N)

    # Expected transformed force: R * F_base
    F_expected = R @ F_base

    # Numerical equivariance error must be zero (within floating point precision)
    rel_error = np.linalg.norm(F_trans - F_expected) / np.linalg.norm(F_base)
    assert rel_error < 1e-5
    assert trans_res.is_strictly_equivariant is True


def test_scalar_coefficients_invariance():
    """Verify scalar aerodynamic coefficients CL, CD, CY, L/D are invariant under SE(3)."""
    base_res = SE3EquivariantAirframeGNN.evaluate(airframe_type="lca_tejas", mach=0.90, alpha_deg=10.0)
    rotated_res = SE3EquivariantAirframeGNN.evaluate(
        airframe_type="lca_tejas",
        mach=0.90,
        alpha_deg=10.0,
        yaw_deg=75.0,
        pitch_deg=-30.0,
        roll_deg=120.0,
        translation_m=(500.0, -200.0, 1000.0),
    )

    assert abs(base_res.cl - rotated_res.cl) < 1e-6
    assert abs(base_res.cd - rotated_res.cd) < 1e-6
    assert abs(base_res.cl_over_cd - rotated_res.cl_over_cd) < 1e-4


def test_canonical_airframe_mesh_generation():
    """Verify NASA CRM, LCA Tejas, and RLV-TD meshes generate valid geometry."""
    for foil in ["nasa_crm", "lca_tejas", "rlv_td"]:
        mesh = generate_canonical_airframe_mesh(foil, grid_density=30)
        assert len(mesh.nodes_xyz) > 50
        assert len(mesh.normals_xyz) == len(mesh.nodes_xyz)
        assert mesh.reference_area_sref > 0.0
        assert mesh.reference_chord_cref > 0.0
        assert mesh.reference_span_bref > 0.0


def test_fastapi_gnn_endpoints():
    """Test the Stage 4 FastAPI endpoints."""
    # 1. GNN Solve
    solve_resp = client.post(
        "/api/aero/gnn/solve",
        json={
            "airframe_type": "nasa_crm",
            "mach": 0.85,
            "alpha_deg": 2.2,
            "beta_deg": 0.0,
            "reynolds": 5.0e6,
            "yaw_deg": 30.0,
            "pitch_deg": 10.0,
            "roll_deg": 0.0,
            "translation_m": [10.0, 0.0, -5.0],
            "grid_density": 30,
        },
    )
    assert solve_resp.status_code == 200
    solve_data = solve_resp.json()
    assert solve_data["status"] == "SUCCESS"
    assert solve_data["stage"] == 4
    assert solve_data["data"]["is_strictly_equivariant"] is True
    assert len(solve_data["data"]["force_vector_N"]) == 3

    # 2. Mesh retrieval
    mesh_resp = client.get("/api/aero/gnn/mesh?airframe_type=lca_tejas&grid_density=25")
    assert mesh_resp.status_code == 200
    mesh_data = mesh_resp.json()
    assert mesh_data["status"] == "SUCCESS"
    assert len(mesh_data["nodes_xyz"]) > 20

    # 3. Benchmarks
    bm_resp = client.get("/api/aero/gnn/benchmarks")
    assert bm_resp.status_code == 200
    bm_data = bm_resp.json()
    assert bm_data["status"] == "SUCCESS"
    assert "nasa_crm_dpw4" in bm_data["benchmarks"]
    assert "lca_tejas_high_alpha" in bm_data["benchmarks"]

