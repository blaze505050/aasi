"""
Unit and Integration Tests for AASI Modular Architecture & Benchmark Registry.

Verifies:
1. Module Contract interface adherence (solve, uncertainty, benchmarks, evidence)
2. Airfoil2DModule multi-fidelity execution (L0, L1, L2)
3. VLM3DModule 3D wing aerodynamics and ONERA M6 benchmark validation
4. Continuous Validation BenchmarkRegistry execution and reporting
"""

import pytest
from backend.modules.base import (
    FidelityLevel,
    EpistemicClassification,
    ModuleResult,
    EvidenceRecord,
)
from backend.modules.airfoil_2d import Airfoil2DModule
from backend.modules.vlm_3d import VLM3DModule
from backend.modules.benchmark_registry import (
    BenchmarkRegistry,
    benchmark_registry,
    PlatformValidationSuiteReport,
)


def test_airfoil_2d_module_contract():
    """Verify Airfoil2DModule satisfies all requirements of the module contract."""
    mod = Airfoil2DModule()

    assert mod.problem_id == 0
    assert mod.tier == 1
    assert mod.module_id == "airfoil_2d_panel"

    # L0 Analytic solve
    res_l0 = mod.solve({"airfoil": "NACA 0012", "alpha_deg": 4.0}, fidelity=FidelityLevel.L0_ANALYTIC)
    assert isinstance(res_l0, ModuleResult)
    assert res_l0.fidelity_level == FidelityLevel.L0_ANALYTIC
    assert res_l0.epistemic_classification == EpistemicClassification.ESTIMATED
    assert "CL" in res_l0.outputs
    assert 0.40 <= res_l0.outputs["CL"] <= 0.55

    # L1 Reduced Order panel solve
    res_l1 = mod.solve({"airfoil": "NACA 0012", "alpha_deg": 4.0}, fidelity=FidelityLevel.L1_REDUCED_ORDER)
    assert isinstance(res_l1, ModuleResult)
    assert res_l1.fidelity_level == FidelityLevel.L1_REDUCED_ORDER
    assert res_l1.epistemic_classification == EpistemicClassification.CALCULATED
    assert 0.42 <= res_l1.outputs["CL"] <= 0.52
    assert "cp_distribution" in res_l1.outputs

    # Uncertainty quantification
    uncert = mod.uncertainty({"airfoil": "NACA 0012", "alpha_deg": 4.0})
    assert uncert["status"] == "QUANTIFIED"
    assert uncert["coverage_factor_k"] == 1.96
    assert uncert["cl_uncertainty_u95"] > 0.0

    # Evidence record
    assert isinstance(res_l1.evidence, EvidenceRecord)
    assert len(res_l1.evidence.provenance_hash) == 64  # SHA-256


def test_vlm_3d_module_contract_and_physics():
    """Verify VLM3DModule 3D aerodynamics and finite-span induced drag."""
    mod = VLM3DModule()

    assert mod.problem_id == 1
    assert mod.tier == 1
    assert mod.module_id == "aero_3d_vlm"

    # Solve ONERA M6 planform at 3.06 deg AoA
    res = mod.solve(
        {
            "span": 1.1963 * 2.0,
            "root_chord": 0.8059,
            "tip_chord": 0.4529,
            "sweep_le_deg": 30.0,
            "alpha_deg": 3.06,
            "mach": 0.20,
        },
        fidelity=FidelityLevel.L1_REDUCED_ORDER,
    )

    outputs = res.outputs
    assert 0.18 <= outputs["CL"] <= 0.22
    assert 0.055 <= outputs["CL_alpha_per_deg"] <= 0.075
    assert 0.80 <= outputs["oswald_efficiency_e"] <= 1.05
    assert outputs["CDi"] > 0.0
    assert outputs["aspect_ratio"] == pytest.approx(3.8, rel=0.05)

    # Symmetry check: CL at alpha=0 must be zero
    res_zero = mod.solve(
        {
            "span": 1.1963 * 2.0,
            "root_chord": 0.8059,
            "tip_chord": 0.4529,
            "sweep_le_deg": 30.0,
            "alpha_deg": 0.0,
        }
    )
    assert abs(res_zero.outputs["CL"]) < 0.01


def test_onera_m6_benchmarks():
    """Verify that VLM3DModule passes all published ONERA M6 reference benchmarks."""
    mod = VLM3DModule()
    evaluations = mod.verify_benchmarks()

    assert len(evaluations) >= 3
    for ev in evaluations:
        assert ev.passed, f"Benchmark {ev.case_id} failed: {ev.metrics}"


def test_airfoil_2d_benchmarks():
    """Verify that Airfoil2DModule passes published NACA 0012, RAE 2822, and E387 benchmarks."""
    mod = Airfoil2DModule()
    evaluations = mod.verify_benchmarks()

    assert len(evaluations) >= 4
    for ev in evaluations:
        assert ev.passed, f"Benchmark {ev.case_id} failed: {ev.metrics}"


def test_benchmark_registry_platform_suite():
    """Verify BenchmarkRegistry runs cross-module continuous validation suite."""
    registry = BenchmarkRegistry()
    report = registry.run_all()

    assert isinstance(report, PlatformValidationSuiteReport)
    assert report.total_modules >= 2
    assert report.total_benchmark_cases >= 7
    assert report.total_failed == 0
    assert report.overall_status == "ALL_BENCHMARKS_PASSED"
    assert len(report.provenance_hash) == 64
