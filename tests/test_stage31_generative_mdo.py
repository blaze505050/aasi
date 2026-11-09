"""
Unit tests for Stage 31: Multidisciplinary Topology Optimization to 5-Axis CNC / LPBF Toolpaths.
Verifies SIMP compliance convergence, volume fraction constraint,
direct LPBF slicing toolpath generation, and REST API endpoints.
"""

import pytest
import numpy as np
from starlette.testclient import TestClient

from aasi_aero_fno.topology_optimization_lpbf import (
    AerospaceAlloy,
    SimpTopologyOptimizer,
    compute_q4_element_stiffness,
    compile_lpbf_toolpath,
    run_aerospace_generative_mdo,
    ALLOY_DATABASE,
)
from backend.main import app

client = TestClient(app)


def test_q4_element_stiffness_matrix_properties():
    """Verifies that the Q4 plane stress element stiffness matrix is symmetric."""
    ke = compute_q4_element_stiffness(youngs_modulus=1.0, nu=0.34)
    assert ke.shape == (8, 8)
    assert np.allclose(ke, ke.T)
    # Eigenvalues must be non-negative (positive semi-definite, with 3 rigid body modes = 0)
    eigenvalues = np.linalg.eigvalsh(ke)
    assert np.all(eigenvalues >= -1e-10)
    zero_modes = np.sum(np.isclose(eigenvalues, 0.0, atol=1e-5))
    assert zero_modes == 3  # 2 translations + 1 rotation rigid body modes


def test_simp_optimization_convergence_and_mass_reduction():
    """Verifies SIMP compliance minimization and target volume fraction achievement."""
    target_volfrac = 0.40
    opt = SimpTopologyOptimizer(
        nx=30,
        ny=15,
        target_volume_fraction=target_volfrac,
        penalization_power=3.0,
        filter_radius=1.5,
        alloy=AerospaceAlloy.TI_6AL_4V,
    )
    res = opt.optimize(max_iterations=15, load_case="CANTILEVER_TIP_LOAD")

    final_metrics = res["final_metrics"]
    # Final volume fraction must be close to target fraction (within 5%)
    assert abs(final_metrics["final_volume_fraction"] - target_volfrac) < 0.05
    # Mass reduction must be >= 50% for 0.40 target volume fraction
    assert final_metrics["mass_reduction_percent"] >= 50.0
    # Safety factor should be physically positive
    assert final_metrics["safety_factor"] > 1.0
    # Self-supporting ratio
    assert final_metrics["self_supporting_manufacturability_percent"] >= 60.0
    # Density field elements must be within [0.001, 1.0]
    densities = np.array(res["density_field"])
    assert np.all(densities >= 0.001)
    assert np.all(densities <= 1.0)


def test_direct_lpbf_slicing_and_toolpath_generation():
    """Verifies continuous density isosurface compilation into LPBF scanpath vectors."""
    # Synthetic solid beam density field
    nx, ny = 20, 10
    densities = [0.8 if (i < 5 or j == 0 or j == 9) else 0.1 for j in range(ny) for i in range(nx)]

    toolpath = compile_lpbf_toolpath(
        density_field_2d=densities,
        nx=nx,
        ny=ny,
        alloy=AerospaceAlloy.TI_6AL_4V,
    )

    assert toolpath["representative_layer_hatches"] > 0
    assert toolpath["total_laser_track_length_m"] > 0.0
    assert toolpath["estimated_build_time_hours"] > 0.0
    assert len(toolpath["hatch_samples"]) > 0


def test_generative_mdo_api_endpoints():
    """Verifies REST API endpoints for Stage 31."""
    resp_presets = client.get("/api/v1/generative-mdo/presets")
    assert resp_presets.status_code == 200
    presets = resp_presets.json()["data"]
    assert "TITANIUM_TRANSONIC_WING_RIB" in presets

    resp_alloys = client.get("/api/v1/generative-mdo/alloys")
    assert resp_alloys.status_code == 200
    alloys = resp_alloys.json()["data"]
    assert "TI_6AL_4V" in alloys
    assert alloys["TI_6AL_4V"]["youngs_modulus_gpa"] == 114.0

    resp_opt = client.post(
        "/api/v1/generative-mdo/optimize",
        json={
            "component_name": "TITANIUM_TRANSONIC_WING_RIB",
            "target_volume_fraction": 0.45,
            "alloy_choice": "TI_6AL_4V",
            "max_iterations": 10,
        },
    )
    assert resp_opt.status_code == 200
    data = resp_opt.json()["data"]
    assert data["optimization"]["final_metrics"]["mass_reduction_percent"] >= 45.0
    assert data["lpbf_toolpath"]["total_laser_track_length_m"] > 0.0
