"""
Tests for AASI Flagship Research Pipeline, Dataset Lifecycle, Benchmark Engine,
Active Learning State Enforcement, and End-to-End ResearchRun Execution.
"""

import pytest
import math
from fastapi.testclient import TestClient
from backend.main import app
from backend.datasets.models import DatasetManifest, DatasetLifecycle, StorageStatus
from backend.datasets.pipeline import DatasetPipelineOrchestrator
from backend.physics.training_models import ModelLifecycleStatus, RegisteredModel, TrainingConfig
from backend.physics.model_registry import PhysicsModelRegistry, physics_registry
from backend.physics.benchmark import AerodynamicBenchmarkEngine, BenchmarkReport, BenchmarkDataPoint
from backend.compute.artifacts import ArtifactIngestionService
from backend.compute.models import IngestionResult
from backend.physics_ai.active_learning import (
    ActiveLearningCandidateRegistry,
    ActiveLearningCandidateRecord,
    CandidateStatus,
    AcquisitionStrategy,
)
from backend.multifidelity.models import FlowConditions
from backend.research.models import ResearchRunStatus, ResearchStage
from backend.research.service import ResearchRunOrchestrator, research_loop_service

client = TestClient(app)

SAMPLE_COORDS = """NACA 0012 Airfoil Coordinates
 1.000000  0.001260
 0.950000  0.014720
 0.800000  0.045430
 0.600000  0.058000
 0.500000  0.060000
 0.400000  0.058000
 0.200000  0.046830
 0.100000  0.034000
 0.050000  0.024000
 0.000000  0.000000
 0.050000 -0.024000
 0.100000 -0.034000
 0.200000 -0.046830
 0.400000 -0.058000
 0.500000 -0.060000
 0.600000 -0.058000
 0.800000 -0.045430
 0.950000 -0.014720
 1.000000 -0.001260
"""


def test_dataset_pipeline_8_stage_lifecycle():
    manifest = DatasetManifest(
        dataset_id="TEST-NACA0012-POLAR",
        name="Test NACA 0012 Coordinates",
        source="UIUC Airfoil Coordinate Database",
        license="Public Domain",
        geometry="NACA 0012",
        storage_status=StorageStatus.LOCAL
    )
    result = DatasetPipelineOrchestrator.execute_full_pipeline(
        manifest=manifest,
        raw_content=SAMPLE_COORDS.encode("utf-8"),
        is_airfoil_geometry=True
    )
    assert result["success"] is True
    assert result["current_stage"] == DatasetLifecycle.READY_FOR_TRAINING.value
    assert len(manifest.transition_history) == 7  # 7 state transitions
    stages_visited = [e["to_stage"] for e in manifest.transition_history]
    assert DatasetLifecycle.LICENSE_VERIFIED.value in stages_visited
    assert DatasetLifecycle.DOWNLOADED.value in stages_visited
    assert DatasetLifecycle.HASH_VERIFIED.value in stages_visited
    assert DatasetLifecycle.PARSED.value in stages_visited
    assert DatasetLifecycle.VALIDATED.value in stages_visited
    assert DatasetLifecycle.SPLIT.value in stages_visited
    assert DatasetLifecycle.READY_FOR_TRAINING.value in stages_visited


def test_dataset_pipeline_fail_closed_invalid_license():
    manifest = DatasetManifest(
        dataset_id="TEST-INVALID-LIC",
        name="Test Insecure Airfoil",
        source="Unknown Scrape",
        license="Proprietary Non-Commercial",
        geometry="NACA 0012",
    )
    result = DatasetPipelineOrchestrator.execute_full_pipeline(
        manifest=manifest,
        raw_content=SAMPLE_COORDS.encode("utf-8")
    )
    assert result["success"] is False
    assert result["stage"] == DatasetLifecycle.FAILED.value
    assert manifest.lifecycle_stage == DatasetLifecycle.FAILED


def test_model_promotion_gates():
    reg = PhysicsModelRegistry()
    # Test valid promotion on MODEL-AERO-SURROGATE-V1
    val_metrics_pass = {
        "cl_r2": 0.94,
        "cd_positive": True,
        "monotonic_lift": True,
    }
    res_pass = reg.promote_model("MODEL-AERO-SURROGATE-V1", validation_metrics=val_metrics_pass)
    assert res_pass["promoted"] is True
    assert res_pass["lifecycle_status"] == ModelLifecycleStatus.VERIFIED_PRODUCTION.value

    # Test rejection on low R^2
    val_metrics_low_r2 = {
        "cl_r2": 0.72,
        "cd_positive": True,
        "monotonic_lift": True,
    }
    res_low_r2 = reg.promote_model("MODEL-AERO-SURROGATE-V1", validation_metrics=val_metrics_low_r2)
    assert res_low_r2["promoted"] is False
    assert "below minimum production threshold" in res_low_r2["reason"]

    # Test rejection on negative drag
    val_metrics_bad_cd = {
        "cl_r2": 0.92,
        "cd_positive": False,
        "monotonic_lift": True,
    }
    res_bad_cd = reg.promote_model("MODEL-AERO-SURROGATE-V1", validation_metrics=val_metrics_bad_cd)
    assert res_bad_cd["promoted"] is False
    assert "drag positivity violated" in res_bad_cd["reason"]


def test_aerodynamic_benchmark_engine():
    res = AerodynamicBenchmarkEngine.evaluate_airfoil_benchmark(
        geometry="NACA 0012",
        mach=0.15,
        reynolds=3000000.0,
        aoa_list=[-4.0, 0.0, 4.0, 8.0, 12.0, 16.0]
    )
    assert len(res.comparison_table) == 6
    assert "lift_slope_per_deg" in res.metrics
    assert "slope_error_vs_theory_pct" in res.metrics
    assert "symmetry_max_error" in res.metrics
    assert 0.08 < res.metrics["lift_slope_per_deg"] < 0.13
    assert res.metrics["symmetry_max_error"] < 0.05
    assert res.metrics["zero_lift_offset"] < 0.02


def test_mesh_convergence_asme_vv20():
    svc = ArtifactIngestionService()
    fine_res = IngestionResult(case_id="case_fine", status="SUCCESS", validation_status="VALIDATED", solver="openfoam", converged=True, iterations=800, coefficients={"cl": 1.09}, provenance_hash="hash_fine", validation_notes=[])
    med_res = IngestionResult(case_id="case_med", status="SUCCESS", validation_status="VALIDATED", solver="openfoam", converged=True, iterations=600, coefficients={"cl": 1.08}, provenance_hash="hash_med", validation_notes=[])
    coarse_res = IngestionResult(case_id="case_coarse", status="SUCCESS", validation_status="VALIDATED", solver="openfoam", converged=True, iterations=400, coefficients={"cl": 1.05}, provenance_hash="hash_coarse", validation_notes=[])

    study = svc.evaluate_mesh_convergence_study(
        fine_result=fine_res,
        medium_result=med_res,
        coarse_result=coarse_res,
        metric="cl",
        grid_metadata={"fine_cells": 450000, "medium_cells": 150000, "coarse_cells": 50000}
    )
    assert study["valid"] is True
    assert "cfd_validation_status" in study
    assert study["cfd_validation_status"] in ["VALIDATED_CFD", "CAUTION_MARGINAL", "UNCONVERGED_GRID"]
    assert "mesh_record" in study
    assert study["mesh_record"]["fine_cells"] == 450000


def test_active_learning_honest_state_transitions():
    registry = ActiveLearningCandidateRegistry()
    cand = ActiveLearningCandidateRecord(
        candidate_id="AL-TEST-001",
        geometry="NACA 0012",
        flow_conditions=FlowConditions(mach=0.15, reynolds=3000000.0, aoa_deg=10.0),
        acquisition_strategy=AcquisitionStrategy.UNCERTAINTY,
        status=CandidateStatus.PROPOSED
    )
    registry.register_candidate(cand)

    # Illegal jump directly to INGESTED must raise ValueError
    with pytest.raises(ValueError, match="Illegal candidate transition"):
        registry.update_status("AL-TEST-001", CandidateStatus.INGESTED, validate_transition=True)

    # Honest progression
    registry.update_status("AL-TEST-001", CandidateStatus.APPROVED, validate_transition=True)
    assert registry.get_candidate("AL-TEST-001").status == CandidateStatus.APPROVED

    registry.update_status("AL-TEST-001", CandidateStatus.GENERATED_DECK, validate_transition=True)
    assert registry.get_candidate("AL-TEST-001").status == CandidateStatus.GENERATED_DECK

    # Solver failure logs without polluting training sets
    registry.record_failed_solver("AL-TEST-001", "simpleFoam continuity error: divergent residual in p field")
    updated = registry.get_candidate("AL-TEST-001")
    assert updated.status == CandidateStatus.FAILED_SOLVER
    assert "divergent residual" in updated.audit_trail[-1].rationale


def test_flagship_research_run_orchestrator():
    run = ResearchRunOrchestrator.execute_flagship_naca0012()
    assert run.is_flagship is True
    assert run.target_geometry == "NACA 0012"
    assert run.status == ResearchRunStatus.COMPLETED
    assert len(run.steps) == 7

    stages = [s.stage for s in run.steps]
    assert stages == [
        ResearchStage.QUESTION,
        ResearchStage.EVIDENCE,
        ResearchStage.DATA,
        ResearchStage.COMPUTATION,
        ResearchStage.VALIDATION,
        ResearchStage.PROVENANCE,
        ResearchStage.CONCLUSION,
    ]

    comp_step = run.steps[3]
    assert comp_step.status == "USER_EXECUTED_REQUIRED"
    assert "case_deck" in comp_step.details["cfd_deck"]["case_id"] or "case_run" in comp_step.details["cfd_deck"]["case_id"]
    assert "openfoam" in comp_step.details["cfd_deck"]["solver"]

    assert "composite_fingerprint" in run.provenance_trail
    assert len(run.provenance_trail["composite_fingerprint"]) == 64

    conclusion = run.scientific_conclusion
    assert conclusion["verdict"] == "HYPOTHESIS_CONFIRMED_WITH_REGIME_LIMITS"
    assert "linear_regime" in conclusion["regimes_of_validity"]
    assert "limitations" in conclusion


def test_research_run_api_endpoints():
    # 1. Flagship execution
    resp = client.post("/api/research/runs/execute-flagship")
    assert resp.status_code == 200
    data = resp.json()
    run_id = data["run_id"]
    assert data["status"] == "COMPLETED"
    assert data["is_flagship"] is True
    assert len(data["steps"]) == 7

    # 2. Get specific run
    resp_get = client.get(f"/api/research/runs/{run_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["run_id"] == run_id

    # 3. List runs
    resp_list = client.get("/api/research/runs")
    assert resp_list.status_code == 200
    assert len(resp_list.json()["runs"]) >= 1

    # 4. Unknown geometry fails closed with INSUFFICIENT_EVIDENCE
    custom_payload = {
        "question": "Assess supersonic shock angle for unknown wedge",
        "hypothesis": "Shock will detach at Mach 1.1",
        "geometry": "UNKNOWN_WEDGE_99",
        "flow_conditions": {"mach": 1.1}
    }
    resp_custom = client.post("/api/research/runs", json=custom_payload)
    assert resp_custom.status_code == 200
    custom_data = resp_custom.json()
    assert custom_data["status"] == "INSUFFICIENT_EVIDENCE"
    assert custom_data["scientific_conclusion"]["verdict"] == "INSUFFICIENT_EVIDENCE"
