"""
AASI Phase 7 Verification Suite: Multi-Fidelity Physics, Active Learning 2.0,
Autonomous Research Loop, Quality Control, and Model Promotion.
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app

from backend.multifidelity.models import (
    FidelityLevel,
    CFDQualityClassification,
    FlowConditions,
    MultiFidelityResult,
    DiscrepancyResult,
    UncertaintyCalibrationMetrics,
)
from backend.multifidelity.discrepancy import MultiFidelityDiscrepancyEngine
from backend.multifidelity.calibration import UncertaintyCalibrationEngine
from backend.multifidelity.resolver import MultiFidelityResolver
from backend.multifidelity.consistency import CrossFidelityConsistencyValidator
from backend.multifidelity.fusion import MultiFidelityFusionEngine
from backend.multifidelity.registry import MultiFidelityRegistry
from backend.multifidelity.service import multi_fidelity_service

from backend.simulation.job_spec import (
    CFDJobSpec,
    SolverType,
    ExecutionBackend,
    MeshSpecification,
    PhysicsSpecification,
    ValidationRequirements,
    EstimatedComputeCost,
)
from backend.simulation.quality_control import CFDQualityControlEngine
from backend.simulation.ingest import SimulationIngestionService
from backend.compute.user_provided import UserProvidedCaseGenerator
from backend.compute.models import ComputeRequest, ComputeBackendType

from backend.physics_ai.active_learning import (
    ActiveLearning2Engine,
    AcquisitionStrategy,
    CandidateStatus,
    ActiveLearningCandidateRecord,
    ActiveLearningCandidateRegistry,
    active_learning_registry,
)
from backend.research.models import (
    ResearchObjective,
    ObjectiveStatus,
    ResearchExperiment,
    ExperimentStatus,
    ResearchNotebook,
)
from backend.research.simulation_planner import SimulationPlanner, CampaignPlan
from backend.research.benchmarks import FixedBenchmarkSuite, BenchmarkEvaluationResult
from backend.research.comparison import ModelComparisonEngine, ModelComparisonReport
from backend.research.promotion import ModelPromotionPipeline, PromotionTier
from backend.research.report_generator import ScientificReportGenerator
from backend.research.service import research_loop_service
from backend.datasets.versioning import dataset_version_manager

from backend.physics.dimensional import AerodynamicDimensionalizer
from backend.physics.constraints import AerodynamicConstraintEngine
from backend.physics_ai.field.surrogate import SurfaceCpSurrogate


client = TestClient(app)


# ==========================================
# 1. Multi-Fidelity Scientific Fabric Tests
# ==========================================

def test_fidelity_hierarchy_and_enums():
    tiers = [
        FidelityLevel.EXPERIMENT,
        FidelityLevel.HIGH_FIDELITY_CFD,
        FidelityLevel.LOW_FIDELITY_CFD,
        FidelityLevel.ANALYTICAL,
        FidelityLevel.SURROGATE,
        FidelityLevel.SYNTHETIC_TEST_DATA,
        FidelityLevel.USER_PROVIDED,
    ]
    assert len(tiers) == 7
    assert FidelityLevel.EXPERIMENT.value == "EXPERIMENT"


def test_multifidelity_discrepancy_calculation():
    cond = FlowConditions(mach=0.15, reynolds=3.0e6, aoa_deg=4.0)
    high_res = MultiFidelityResult(
        result_id="EXP-1",
        geometry="NACA 0012",
        geometry_hash="GEOM-0012",
        fidelity=FidelityLevel.EXPERIMENT,
        quantity="CL",
        value=0.440,
        uncertainty=0.015,
        conditions=cond,
        source="NASA-TR-824"
    )
    low_res = MultiFidelityResult(
        result_id="SURR-1",
        geometry="NACA 0012",
        geometry_hash="GEOM-0012",
        fidelity=FidelityLevel.SURROGATE,
        quantity="CL",
        value=0.420,
        uncertainty=0.025,
        conditions=cond,
        source="AeroSurrogateV1"
    )

    disc = MultiFidelityDiscrepancyEngine.calculate_discrepancy(high_res, low_res)
    assert isinstance(disc, DiscrepancyResult)
    assert pytest.approx(disc.bias_estimate, 1e-4) == 0.020
    assert disc.absolute_discrepancy > 0.01
    assert len(disc.physical_explanation) > 0


def test_uncertainty_calibration_engine():
    preds = [0.44, 0.88, 1.25, 1.42, 0.0, 0.22]
    trues = [0.45, 0.87, 1.24, 1.39, 0.01, 0.23]
    uncs = [0.03, 0.03, 0.04, 0.05, 0.02, 0.02]

    metrics = UncertaintyCalibrationEngine.evaluate_calibration(
        predicted_values=preds,
        true_values=trues,
        predicted_uncertainties=uncs,
        model_id="TEST-MODEL"
    )
    assert isinstance(metrics, UncertaintyCalibrationMetrics)
    assert metrics.empirical_coverage_1sigma >= 60.0
    assert metrics.empirical_coverage_2sigma >= 80.0
    assert metrics.average_interval_width > 0.0


def test_multifidelity_resolver_cascade():
    resolver = MultiFidelityResolver()
    # Query exact condition where experiment exists in registry
    res = resolver.resolve_best_source(
        geometry="NACA 0012",
        mach=0.15,
        reynolds=3.0e6,
        aoa_deg=0.0,
        quantity="CL"
    )
    assert "resolution_tier" in res
    assert "value" in res
    assert "provenance_hash" in res



def test_multifidelity_registry_persistence_and_queries():
    registry = MultiFidelityRegistry()
    assert registry.count() > 1000  # Automatically loaded authentic records
    results = registry.query_results(geometry="NACA 0012", quantity="CL")
    assert len(results) > 0
    assert all(r.geometry == "NACA 0012" for r in results)


def test_cross_fidelity_consistency_validator():
    is_valid, msgs = CrossFidelityConsistencyValidator.validate_physical_consistency(
        cl=0.85, cd=0.012, cm=-0.01, aoa_deg=8.0
    )
    assert is_valid is True
    assert len(msgs) == 0

    # Negative CD violation
    is_valid_bad, msgs_bad = CrossFidelityConsistencyValidator.validate_physical_consistency(
        cl=0.85, cd=-0.005, cm=-0.01, aoa_deg=8.0
    )
    assert is_valid_bad is False
    assert any("CD" in m for m in msgs_bad)


# ==========================================
# 2. Simulation Planner & Ingestion QC Tests
# ==========================================

def test_canonical_cfd_job_spec():
    cond = FlowConditions(mach=0.25, reynolds=4.0e6, aoa_deg=6.0)
    spec = CFDJobSpec(
        job_id="JOB-TEST-001",
        geometry="NACA 0012",
        geometry_hash="AABBCC112233",
        flow_conditions=cond,
        solver=SolverType.OPENFOAM,
        execution_backend=ExecutionBackend.USER_EXECUTED
    )
    assert spec.provenance_hash != ""
    assert spec.solver == SolverType.OPENFOAM
    assert spec.mesh.target_cells == 45000


def test_cfd_quality_control_engine():
    # 1. Converged run (>= 10 steps, final tail stable)
    history_converged = [
        {"iteration": i * 10, "cl": 0.441 + (0.01 / (i + 1)), "cd": 0.0162 + (0.002 / (i + 1)), "cm": -0.01}
        for i in range(1, 25)
    ]
    status, report = CFDQualityControlEngine.audit_simulation_run(
        forces_history=history_converged,
        min_iterations=20
    )
    assert status == CFDQualityClassification.CONVERGED
    assert report["is_valid"] is True

    # 2. Invalid run (CD <= 0)
    history_invalid = [
        {"iteration": i * 10, "cl": 0.44, "cd": -0.005, "cm": -0.01}
        for i in range(1, 15)
    ]
    status_inv, report_inv = CFDQualityControlEngine.audit_simulation_run(
        forces_history=history_invalid,
        min_iterations=10
    )
    assert status_inv == CFDQualityClassification.INVALID
    assert report_inv["is_valid"] is False



def test_simulation_ingestion_service():
    # Provide >= 10 iterations so quality control engine evaluates convergence
    foam_lines = ["# Time       Cm          Cd          Cl          Cl(f)       Cl(r)"]
    for i in range(1, 25):
        foam_lines.append(f"{i*10}          -0.006      {0.0174 + 0.005/i:.5f}      {0.441 - 0.01/i:.5f}       0.220       0.221")
    sample_foam = "\n".join(foam_lines)

    cond = FlowConditions(mach=0.15, reynolds=3.0e6, aoa_deg=4.0)
    results, qc_status, report = SimulationIngestionService.ingest_openfoam_force_coeffs(
        file_content=sample_foam,
        geometry="NACA 0012",
        conditions=cond
    )
    assert qc_status in [CFDQualityClassification.CONVERGED, CFDQualityClassification.QUESTIONABLE]
    assert len(results) == 3  # CL, CD, CM
    cl_res = next(r for r in results if r.quantity == "CL")
    assert pytest.approx(cl_res.value, 1e-2) == 0.441


def test_user_provided_case_generator_phase7_structure(tmp_path):
    generator = UserProvidedCaseGenerator(base_output_dir=str(tmp_path))
    req = ComputeRequest(
        case_id="PHASE7-CASE-001",
        geometry="NACA 0012",
        mach=0.20,
        reynolds=3.0e6,
        aoa_deg=4.0,
        backend=ComputeBackendType.USER_EXECUTED
    )
    deck = generator.generate_case(req)
    case_path = tmp_path / "PHASE7-CASE-001"
    assert (case_path / "README.md").exists()
    assert (case_path / "validation" / "convergence.md").exists()
    assert (case_path / "validation" / "grid-study.md").exists()
    assert (case_path / "validation" / "expected-outputs.md").exists()
    assert (case_path / "metadata" / "mesh.json").exists()
    assert (case_path / "metadata" / "physics.json").exists()
    assert (case_path / "provenance.json").exists()



# ==========================================
# 3. Active Learning 2.0 & Candidate Lifecycle
# ==========================================

def test_active_learning_candidate_generation():
    existing = [
        {"mach": 0.15, "aoa": 0.0, "reynolds": 3.0e6},
        {"mach": 0.15, "aoa": 4.0, "reynolds": 3.0e6},
    ]
    candidates = ActiveLearning2Engine.generate_candidates(
        geometry="NACA 0012",
        existing_points=existing,
        strategy=AcquisitionStrategy.COST_AWARE,
        max_candidates=4
    )
    assert len(candidates) == 4
    assert candidates[0].composite_score >= candidates[1].composite_score
    assert candidates[0].status == CandidateStatus.PROPOSED
    assert len(candidates[0].audit_trail) > 0


def test_candidate_lifecycle_and_registry():
    registry = ActiveLearningCandidateRegistry(persistence_path="data/active_learning/test_candidates.json")
    cond = FlowConditions(mach=0.30, reynolds=3.0e6, aoa_deg=14.0)
    cand = ActiveLearningCandidateRecord(
        candidate_id="AL-TEST-001",
        geometry="NACA 0012",
        flow_conditions=cond,
        status=CandidateStatus.PROPOSED,
        composite_score=0.85
    )
    registry.register_candidate(cand)
    assert registry.get_candidate("AL-TEST-001") is not None

    # Transition to APPROVED
    updated = registry.update_status(
        candidate_id="AL-TEST-001",
        new_status=CandidateStatus.APPROVED,
        rationale="Approved by chief aerodynamicist."
    )
    assert updated.status == CandidateStatus.APPROVED
    assert len(updated.audit_trail) == 1
    assert updated.audit_trail[0].to_status == CandidateStatus.APPROVED


def test_parameter_coverage_map_generation():
    existing = [{"mach": 0.15, "aoa": 0.0}, {"mach": 0.20, "aoa": 4.0}]
    candidates = [
        ActiveLearningCandidateRecord(
            candidate_id="C-1",
            geometry="NACA 0012",
            flow_conditions=FlowConditions(mach=0.40, reynolds=3.0e6, aoa_deg=12.0),
            priority="HIGH"
        )
    ]
    cmap = ActiveLearning2Engine.compute_coverage_map(
        geometry="NACA 0012",
        existing_points=existing,
        candidate_points=candidates,
        plane="aoa_vs_mach"
    )
    assert cmap.geometry == "NACA 0012"
    assert len(cmap.existing_points) == 2
    assert len(cmap.candidate_points) == 1


# ==========================================
# 4. Research Loop, Benchmarks, Promotion
# ==========================================

def test_fixed_benchmark_suite_evaluation():
    # Accurate benchmark predictor matching reference polar cases
    def mock_predictor(geom, mach, re, aoa):
        for c in FixedBenchmarkSuite.BENCHMARK_CASES:
            if c["geometry"] == geom and abs(c["aoa_deg"] - aoa) < 0.1 and abs(c["mach"] - mach) < 0.05:
                return {"cl": c["exp_cl"], "cd": c["exp_cd"], "cm": c["exp_cm"]}
        return {"cl": 0.108 * aoa, "cd": 0.008 + 0.0004 * (aoa**2), "cm": 0.0}

    result = FixedBenchmarkSuite.evaluate_model(mock_predictor)
    assert isinstance(result, BenchmarkEvaluationResult)
    assert result.r2_cl > 0.90
    assert result.cd_positivity_pass_rate_pct == 100.0



def test_model_comparison_engine():
    def base_fn(geom, mach, re, aoa):
        return {"cl": 0.105 * aoa, "cd": 0.008 + 0.0004 * (aoa**2), "cm": 0.0}

    def cand_fn(geom, mach, re, aoa):
        return {"cl": 0.108 * aoa, "cd": 0.0075 + 0.0004 * (aoa**2), "cm": 0.0}

    report = ModelComparisonEngine.compare_models(
        baseline_id="AeroSurrogateV1",
        candidate_id="AeroSurrogateV2",
        baseline_predict_fn=base_fn,
        candidate_predict_fn=cand_fn
    )
    assert isinstance(report, ModelComparisonReport)
    assert report.improved is True
    assert report.regressed is False


def test_model_promotion_pipeline():
    def pred_fn(geom, mach, re, aoa):
        return {"cl": 0.108 * aoa, "cd": 0.0075 + 0.0004 * (aoa**2), "cm": 0.0}

    audit = ModelPromotionPipeline.evaluate_promotion(
        candidate_id="AeroSurrogateV2",
        baseline_id="AeroSurrogateV1",
        candidate_predict_fn=pred_fn,
        baseline_predict_fn=pred_fn
    )
    assert audit.model_id == "AeroSurrogateV2"
    assert len(audit.gate_results) == 3
    assert audit.promoted is True
    assert audit.target_tier == PromotionTier.ACTIVE


def test_scientific_report_generator():
    obj = ResearchObjective(
        objective_id="OBJ-TEST-001",
        title="High AoA Verification",
        description="Testing stall prediction."
    )
    md = ScientificReportGenerator.generate_markdown_report(obj)
    assert "# Autonomous Aerospace Research Report" in md
    assert "OBJ-TEST-001" in md

    latex = ScientificReportGenerator.generate_latex_report(obj)
    assert r"\documentclass[conference]{IEEEtran}" in latex


def test_dataset_version_manager():
    assert len(dataset_version_manager.versions) >= 1
    v1 = dataset_version_manager.versions["AERO-AIRFOIL-V1.0"]
    assert v1.quality_metrics.overall_quality_score > 80.0


# ==========================================
# 5. Dimensional Analysis & Physics Constraints
# ==========================================

def test_aerodynamic_dimensionalizer():
    state = AerodynamicDimensionalizer.compute_flow_state(
        mach=0.20,
        temperature_k=288.15,
        pressure_pa=101325.0,
        chord_m=1.0
    )
    assert pytest.approx(state.speed_of_sound_ms, 1.0) == 340.28
    assert state.mach == 0.20
    assert state.reynolds > 1.0e6
    assert state.dynamic_pressure_pa > 2000.0


def test_aerodynamic_constraint_engine():
    rep = AerodynamicConstraintEngine.check_aerodynamic_invariants(
        cl=0.85, cd=0.012, cm=-0.02, mach=0.2, aoa_deg=8.0
    )
    assert rep.is_physically_sound is True
    assert len(rep.violations) == 0

    # Negative drag violation
    rep_bad = AerodynamicConstraintEngine.check_aerodynamic_invariants(
        cl=0.85, cd=-0.005, cm=-0.02, mach=0.2, aoa_deg=8.0
    )
    assert rep_bad.is_physically_sound is False
    assert len(rep_bad.violations) > 0


def test_surface_cp_surrogate():
    dist = SurfaceCpSurrogate.predict_surface_cp(
        geometry="NACA 0012",
        mach=0.15,
        reynolds=3.0e6,
        aoa_deg=4.0,
        n_chord_points=33
    )
    assert len(dist.upper_surface) == 33
    assert len(dist.lower_surface) == 33
    assert dist.cp_min < 0.0  # Suction peak on upper surface
    assert dist.cl_integrated > 0.3  # Positive lift at AoA 4 deg
    assert dist.cd_integrated > 0.0  # Positive pressure drag


# ==========================================
# 6. REST API Endpoints Tests
# ==========================================

def test_api_multifidelity_resolve():
    res = client.post("/api/multifidelity/resolve", json={
        "geometry": "NACA 0012",
        "mach": 0.15,
        "reynolds": 3.0e6,
        "aoa_deg": 0.0,
        "quantity": "CL"
    })
    assert res.status_code == 200
    data = res.json()
    assert "resolution_tier" in data
    assert "value" in data


def test_api_multifidelity_calibration():
    res = client.get("/api/multifidelity/calibration?quantity=CL")
    assert res.status_code == 200
    data = res.json()
    assert "empirical_coverage_2sigma" in data



def test_api_multifidelity_statistics():
    res = client.get("/api/multifidelity/statistics")
    assert res.status_code == 200
    data = res.json()
    assert "total_records" in data
    assert data["total_records"] > 0


def test_api_active_learning_candidates():
    res = client.post("/api/active-learning/candidates", json={
        "geometry": "NACA 0012",
        "strategy": "COST_AWARE",
        "max_candidates": 3
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["candidates"]) == 3


def test_api_active_learning_coverage_map():
    res = client.post("/api/active-learning/coverage-map", json={
        "geometry": "NACA 0012",
        "plane": "aoa_vs_mach"
    })
    assert res.status_code == 200
    data = res.json()
    assert "existing_points" in data
    assert "candidate_points" in data


def test_api_research_objectives():
    res = client.get("/api/research/objectives")
    assert res.status_code == 200
    data = res.json()
    assert len(data["objectives"]) >= 2


def test_api_research_campaign_plan():
    res = client.post("/api/research/campaigns/plan?objective_id=OBJ-AERO-001&max_cases=2")
    assert res.status_code == 200
    data = res.json()
    assert "campaign_id" in data
    assert len(data["candidate_jobs"]) <= 2


def test_api_surface_cp():
    res = client.post("/api/physics/aerodynamics/surface-cp", json={
        "geometry": "NACA 0012",
        "mach": 0.15,
        "reynolds": 3.0e6,
        "aoa_deg": 4.0,
        "n_chord_points": 25
    })
    assert res.status_code == 200
    data = res.json()
    assert "upper_surface" in data
    assert data["cl_integrated"] > 0.0


def test_api_dimensional_flow_state():
    res = client.post("/api/physics/dimensional/state", json={
        "mach": 0.25,
        "temperature_k": 288.15
    })
    assert res.status_code == 200
    data = res.json()
    assert "speed_of_sound_ms" in data
    assert "reynolds" in data


def test_api_constraints_check():
    res = client.post("/api/physics/constraints/check", json={
        "cl": 0.5,
        "cd": 0.008,
        "cm": -0.01,
        "mach": 0.2,
        "aoa_deg": 4.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_physically_sound"] is True
