"""
Tests for Grid Convergence Index & Richardson Extrapolation (ASME V&V 20).

Verifies:
- Monotonic convergence calculation
- Apparent order of accuracy (p)
- Richardson extrapolation to zero grid spacing (h -> 0)
- Grid convergence index for fine and medium meshes (GCI_fine, GCI_medium)
- Verification of asymptotic range of convergence.
"""

import pytest
from backend.validation.grid_convergence import GridConvergenceService, GCIResult


def test_monotonic_grid_convergence():
    # Canonical second-order convergence case:
    # h = 1.0, 1.414, 2.0 (r = 1.414)
    # f1 = 1.01, f2 = 1.04, f3 = 1.10
    res = GridConvergenceService.compute_gci(
        f1=1.01, f2=1.04, f3=1.10, r21=1.4142, r32=1.4142, metric_name="test_scalar"
    )
    assert isinstance(res, GCIResult)
    assert res.convergence_type == "MONOTONIC_CONVERGENCE"
    assert res.apparent_order_p > 1.5
    assert res.apparent_order_p < 2.5
    assert res.extrapolated_value < res.provenance["f_fine"]
    assert res.gci_fine_pct < res.gci_medium_pct


def test_identical_grid_solutions():
    res = GridConvergenceService.compute_gci(
        f1=0.50, f2=0.50, f3=0.50, r21=1.4142, r32=1.4142
    )
    assert res.gci_fine_pct == 0.0
    assert res.is_in_asymptotic_range is True


def test_benchmark_cfd_mesh_studies():
    studies = GridConvergenceService.get_benchmark_grid_studies()
    assert "lift_analysis" in studies
    assert "drag_analysis" in studies
    assert studies["lift_analysis"]["apparent_order_p"] > 1.0
    assert studies["drag_analysis"]["apparent_order_p"] > 1.0
