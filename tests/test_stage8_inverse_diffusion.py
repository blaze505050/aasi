"""
Unit and integration tests for AASI Stage 8: Inverse Generative Diffusion for Shock-Free Supercritical Airframes.
Verifies score-based reverse SDE sampler, sonic rooftop pressure plateau, wave drag reduction,
trailing-edge closure, supercritical benchmarks catalog, and API routes.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure package roots are on sys.path
_repo_root = Path(__file__).resolve().parent.parent
_fno_pkg = _repo_root / "aasi-aero-fno"
for p in [str(_repo_root), str(_fno_pkg)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from aasi_aero_fno.inverse_diffusion import (
    InverseAirfoilDiffusionEngine,
    InverseAirfoilGenerationResult,
    INVERSE_DIFFUSION_BENCHMARKS,
)
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_inverse_diffusion_sample_nominal():
    """Verifies inverse diffusion sampling produces a valid supercritical airfoil."""
    result = InverseAirfoilDiffusionEngine.sample_shock_free_airfoil(
        target_mach=0.78,
        target_cl=0.70,
        target_thickness_pct=12.0,
        guidance_strength=3.5,
        num_diffusion_steps=50,
        random_seed=42,
    )
    assert isinstance(result, InverseAirfoilGenerationResult)
    assert result.target_mach == 0.78
    assert abs(result.achieved_cl - 0.70) < 0.05
    assert abs(result.max_thickness_ratio_pct - 12.0) < 1.5
    assert result.is_shock_free is True
    assert result.wave_drag_reduction_pct > 70.0
    assert result.achieved_cd_wave_counts < result.baseline_cd_wave_counts

    # Check geometric admissibility: trailing edge must close
    assert abs(result.geometry.y_upper[-1]) < 1e-4
    assert abs(result.geometry.y_lower[-1]) < 1e-4
    # Leading edge radius must be positive
    assert result.leading_edge_radius_r_le_c > 0.01

    # Pressure distribution checks
    assert len(result.pressure_distribution.cp_upper) == len(result.pressure_distribution.x_c)
    assert result.pressure_distribution.cp_sonic_star < 0.0
    assert len(result.provenance_hash) == 64


def test_supercritical_rooftop_vs_shock():
    """
    Verifies that high guidance strength yields a smooth shock-free rooftop
    pressure profile with no sharp shock jump, whereas low guidance has shock discontinuity.
    """
    res_guided = InverseAirfoilDiffusionEngine.sample_shock_free_airfoil(
        target_mach=0.80, guidance_strength=4.0
    )
    res_unguided = InverseAirfoilDiffusionEngine.sample_shock_free_airfoil(
        target_mach=0.80, guidance_strength=1.0
    )

    assert res_guided.is_shock_free is True
    assert res_unguided.is_shock_free is False
    assert res_guided.wave_drag_reduction_pct > res_unguided.wave_drag_reduction_pct
    assert res_guided.achieved_cd_wave_counts < res_unguided.achieved_cd_wave_counts


def test_supercritical_benchmarks_catalog():
    """Verifies standard benchmark catalog entries."""
    assert "rae_2822_case_9" in INVERSE_DIFFUSION_BENCHMARKS
    assert "nasa_sc2_0714_whitcomb" in INVERSE_DIFFUSION_BENCHMARKS
    assert "isro_rlv_supercritical_section" in INVERSE_DIFFUSION_BENCHMARKS

    whitcomb = INVERSE_DIFFUSION_BENCHMARKS["nasa_sc2_0714_whitcomb"]
    assert whitcomb["mach"] == 0.760
    assert whitcomb["shock_location_x_c"] is None  # Shock-free design
    assert whitcomb["wave_drag_counts"] <= 5.0


def test_api_diffusion_sample(client):
    """Verifies POST /api/aero/diffusion/sample returns 200 with generated airfoil."""
    resp = client.post(
        "/api/aero/diffusion/sample",
        json={
            "target_mach": 0.82,
            "target_cl": 0.65,
            "target_thickness_pct": 11.0,
            "guidance_strength": 4.0,
            "num_diffusion_steps": 40,
            "random_seed": 101,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["stage"] == 8
    payload = data["data"]
    assert payload["target_mach"] == 0.82
    assert "geometry" in payload
    assert len(payload["geometry"]["x_upper"]) > 50
    assert payload["is_shock_free"] is True


def test_api_diffusion_benchmarks(client):
    """Verifies GET /api/aero/diffusion/benchmarks returns 200 with benchmarks."""
    resp = client.get("/api/aero/diffusion/benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["stage"] == 8
    assert "nasa_sc2_0714_whitcomb" in data["benchmarks"]

