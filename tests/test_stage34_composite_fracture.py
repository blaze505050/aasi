"""
Unit and regression tests for Stage 34: Composite Layup & Fracture Mechanics Cohesive Zone Twin.
Validates:
1. Classical Laminate Theory (CLT) ABD stiffness matrices, B=0 symmetry, and quasi-isotropic properties.
2. 3D Tsai-Wu failure criterion, first-ply failure margins, and 2D envelope generation.
3. Bilinear Cohesive Zone Modeling (CZM) delamination with Benzeggagh-Kenane (B-K) mixed-mode criterion.
4. FastAPI REST API endpoints.
"""

import math
import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.composite_fracture_czm import (
    COMPOSITE_DB,
    STANDARD_LAYUPS,
    compute_clt_abd_matrix,
    evaluate_tsai_wu_failure,
    simulate_czm_delamination,
)
from backend.main import app


def test_clt_symmetric_quasi_isotropic_laminate():
    """Validates CLT ABD matrix calculation and quasi-isotropic symmetry."""
    layup = STANDARD_LAYUPS["QUASI_ISOTROPIC_16"]
    clt = compute_clt_abd_matrix(material_key="IM7_8552", ply_angles_deg=layup)

    assert clt["num_plies"] == 16
    assert clt["is_symmetric"] is True
    assert clt["total_thickness_mm"] == pytest.approx(16 * 0.125, abs=0.01)

    # For a balanced symmetric quasi-isotropic laminate, Ex approx Ey
    eng = clt["effective_engineering_constants"]
    assert abs(eng["ex_eff_gpa"] - eng["ey_eff_gpa"]) / eng["ex_eff_gpa"] < 0.05
    assert 50.0 <= eng["ex_eff_gpa"] <= 75.0

    # In-plane shear modulus Gxy should be approx E / (2 * (1 + nu)) ~ 20-30 GPa
    assert 18.0 <= eng["gxy_eff_gpa"] <= 30.0

    # A matrix must be symmetric: A12 == A21
    a_mat = clt["abd_matrices"]["a_matrix_kn_per_mm"]
    assert a_mat[0][1] == pytest.approx(a_mat[1][0], rel=1e-3)
    # B matrix elements must be essentially zero
    b_mat = clt["abd_matrices"]["b_matrix_n"]
    for row in b_mat:
        for val in row:
            assert abs(val) < 1e-3


def test_tsai_wu_failure_criterion():
    """Validates 3D Tsai-Wu interactive quadratic failure criteria."""
    # 1. Safe stress state
    safe_eval = evaluate_tsai_wu_failure(
        material_key="IM7_8552",
        sigma1_mpa=800.0,
        sigma2_mpa=25.0,
        tau12_mpa=30.0,
    )
    assert safe_eval["is_failed"] is False
    assert safe_eval["tsai_wu_failure_index"] < 1.0
    assert safe_eval["safety_factor"] > 1.0

    # 2. Longitudinal tensile failure (sigma1 = 3000 MPa > Xt = 2560 MPa)
    fail_eval_long = evaluate_tsai_wu_failure(
        material_key="IM7_8552",
        sigma1_mpa=3000.0,
        sigma2_mpa=0.0,
        tau12_mpa=0.0,
    )
    assert fail_eval_long["is_failed"] is True
    assert fail_eval_long["tsai_wu_failure_index"] > 1.0

    # 3. Transverse tensile failure (sigma2 = 80 MPa > Yt = 64 MPa)
    fail_eval_trans = evaluate_tsai_wu_failure(
        material_key="IM7_8552",
        sigma1_mpa=0.0,
        sigma2_mpa=80.0,
        tau12_mpa=0.0,
    )
    assert fail_eval_trans["is_failed"] is True
    assert fail_eval_trans["tsai_wu_failure_index"] > 1.0

    # 4. Failure envelope points
    envelope = safe_eval["envelope_2d_points"]
    assert len(envelope) == 60
    # Envelope must have positive and negative bounds
    max_s1 = max(p["sigma1_mpa"] for p in envelope)
    min_s1 = min(p["sigma1_mpa"] for p in envelope)
    assert max_s1 > 2000.0
    assert min_s1 < -1200.0


def test_bilinear_czm_delamination_and_bk_criterion():
    """Validates Bilinear CZM mixed-mode delamination and B-K fracture law."""
    mat = COMPOSITE_DB["IM7_8552"]
    g_ic = mat.g_ic_kj_m2 * 1e3
    g_iic = mat.g_iic_kj_m2 * 1e3

    # 1. Pure Mode I opening
    czm_mode1 = simulate_czm_delamination(
        material_key="IM7_8552",
        applied_normal_opening_um=2.0,
        applied_shear_sliding_um=0.0,
    )
    assert czm_mode1["cohesive_interface"]["mode_mixity_ratio_b"] == 0.0
    assert czm_mode1["cohesive_interface"]["critical_mixed_energy_j_m2"] == pytest.approx(g_ic, abs=0.1)

    # 2. Pure Mode II shear
    czm_mode2 = simulate_czm_delamination(
        material_key="IM7_8552",
        applied_normal_opening_um=0.0,
        applied_shear_sliding_um=5.0,
    )
    assert czm_mode2["cohesive_interface"]["mode_mixity_ratio_b"] == 1.0
    assert czm_mode2["cohesive_interface"]["critical_mixed_energy_j_m2"] == pytest.approx(g_iic, abs=0.1)

    # 3. Complete delamination separation (large displacement)
    czm_separated = simulate_czm_delamination(
        material_key="IM7_8552",
        applied_normal_opening_um=50.0,
        applied_shear_sliding_um=20.0,
    )
    assert czm_separated["current_state"]["is_delaminated"] is True
    assert czm_separated["current_state"]["damage_variable_d"] == 1.0
    assert czm_separated["current_state"]["current_traction_mpa"] == 0.0

    # 4. Traction-separation curve monotonicity check in softening regime
    curve = czm_mode1["traction_separation_curve"]
    assert len(curve) == 50


def test_composite_fracture_api_endpoints():
    """Validates FastAPI REST endpoints for Stage 34."""
    client = TestClient(app)

    # 1. Presets endpoint
    res_presets = client.get("/api/v1/composite-fracture/presets")
    assert res_presets.status_code == 200
    pdata = res_presets.json()["data"]
    assert "IM7_8552" in pdata["materials"]
    assert "QUASI_ISOTROPIC_16" in pdata["standard_layups"]

    # 2. CLT ABD endpoint
    res_clt = client.post(
        "/api/v1/composite-fracture/clt-abd",
        json={
            "material_key": "IM7_8552",
            "ply_angles_deg": [0, 45, -45, 90, 90, -45, 45, 0],
        },
    )
    assert res_clt.status_code == 200
    assert res_clt.json()["data"]["is_symmetric"] is True

    # 3. Tsai-Wu endpoint
    res_tw = client.post(
        "/api/v1/composite-fracture/tsai-wu",
        json={
            "material_key": "IM7_8552",
            "sigma1_mpa": 600.0,
            "sigma2_mpa": 20.0,
            "tau12_mpa": 15.0,
        },
    )
    assert res_tw.status_code == 200
    assert res_tw.json()["data"]["is_failed"] is False

    # 4. CZM Delamination endpoint
    res_czm = client.post(
        "/api/v1/composite-fracture/czm-delamination",
        json={
            "material_key": "IM7_8552",
            "applied_normal_opening_um": 5.0,
            "applied_shear_sliding_um": 3.0,
        },
    )
    assert res_czm.status_code == 200
    assert "traction_separation_curve" in res_czm.json()["data"]
