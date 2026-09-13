"""
AASI Phase 21 Adversarial Integrity Test Suite.
Governing Rule: Absolute Anti-Fabrication Rule.

30+ rigorous adversarial tests verifying that every CFD execution, convergence check,
physical gate, multi-fidelity model, field operator, adaptive conformal interval,
scientific claim, and discovery iteration fails closed against tampering and fabrication.
"""

import json
import math
import os
from pathlib import Path
import tempfile
import numpy as np
import pytest

from backend.cfd.case_validator import CFDCaseValidator
from backend.cfd.convergence import CFDConvergenceEvaluator
from backend.cfd.environment_probe import CFDEnvironmentProbe
from backend.cfd.force_parser import CFDForceParser
from backend.cfd.openfoam_runner import OpenFOAMRunner
from backend.cfd.provenance import CFDProvenanceEngine
from backend.cfd.residual_parser import CFDResidualParser
from backend.cfd.result_ingestor import CFDResultIngestor
from backend.cfd.solver_interface import ConvergenceState, PhysicalValidationState, SolverMode
from backend.physics_ai.acquisition import ActiveAcquisitionEngine
from backend.physics_ai.benchmark_models import RandomForestSurrogate
from backend.physics_ai.discovery_loop import AutonomousDiscoveryController
from backend.physics_ai.field_models import (
    AerodynamicFieldIntegrator,
    FieldPhysicalValidator,
    SurfacePressureFieldSurrogate,
)
from backend.physics_ai.geometry_representation import GeometryRepresentationEngine
from backend.physics_ai.multifidelity import (
    AnalyticalThinAirfoilBaseline,
    FidelityLevel,
    MultiFidelityDiscrepancySurrogate,
)
from backend.research.experiment_registry import PersistentExperimentRegistry, PromotionStage
from backend.research.reproduction_verifier_phase21 import Phase21ReproductionVerifier
from backend.research.scientific_claims import (
    EvidenceType,
    ScientificClaim,
    ScientificClaimValidator,
    SupportLevel,
)


# =============================================================================
# 1. CFD Case & Environment Integrity Tests
# =============================================================================

def test_missing_solver_returns_user_executed_required(tmp_path):
    """Test 1: When solver is absent on host, runner returns USER_EXECUTED_REQUIRED."""
    runner = OpenFOAMRunner(default_output_dir=tmp_path)
    case_dir = runner.prepare_case("CASE-TEST-001", "NACA 0012", [[0, 0], [1, 0]], 4.0, 3e6)
    res = runner.execute(case_dir)
    assert res.status == "USER_EXECUTED_REQUIRED"
    assert res.convergence_state == ConvergenceState.NOT_RUN


def test_wsl_docker_absence_handled_gracefully():
    """Test 2: Environment probe honestly detects and reports WSL2/Docker status."""
    probe = CFDEnvironmentProbe.probe_all()
    assert "modes" in probe
    assert "selected_mode" in probe
    assert probe["modes"]["degraded_fallback"]["status"] == "USER_EXECUTED_REQUIRED"


def test_geometry_hash_mismatch_rejected(tmp_path):
    """Test 3: Case validator rejects case when geometry coordinates do not match expected hash."""
    case_dir = tmp_path / "case_mismatch"
    case_dir.mkdir()
    geom_file = case_dir / "geometry.dat"
    geom_file.write_text("0.0 0.0\n1.0 0.0\n", encoding="utf-8")

    res = CFDCaseValidator.validate_case_directory(
        case_dir, expected_geometry_hash="fake_hash_that_does_not_match"
    )
    assert res["valid"] is False
    assert any("Geometry hash mismatch" in err for err in res["errors"])


def test_missing_mandatory_dictionaries_rejected(tmp_path):
    """Test 4: Case validator rejects incomplete OpenFOAM directory missing controlDict."""
    empty_case = tmp_path / "empty_case"
    empty_case.mkdir()
    res = CFDCaseValidator.validate_case_directory(empty_case)
    assert res["valid"] is False
    assert any("Missing mandatory simulation dictionary" in err for err in res["errors"])


# =============================================================================
# 2. Residuals & Convergence Integrity Tests
# =============================================================================

def test_fake_exit_code_alone_rejected_without_residuals():
    """Test 5: Exit code 0 without residual history fails closed with CONVERGENCE_NOT_ESTABLISHED."""
    res = CFDConvergenceEvaluator.evaluate_convergence(
        residual_data={"residuals": {}, "total_iterations": 0},
        force_data={"parsed": False},
        solver_exit_code=0,
    )
    assert res["converged"] is False
    assert res["convergence_state"] == ConvergenceState.CONVERGENCE_NOT_ESTABLISHED.value


def test_nan_residuals_flagged_diverged():
    """Test 6: Simulation with NaN residuals is immediately classified as DIVERGED."""
    log_text = """
    Solving for p, Initial residual = 0.5, Final residual = 0.01
    Solving for p, Initial residual = NaN, Final residual = NaN
    """
    res_data = CFDResidualParser.parse_log_text(log_text)
    assert res_data["has_nan_or_inf"] is True
    eval_res = CFDConvergenceEvaluator.evaluate_convergence(res_data, {}, solver_exit_code=0)
    assert eval_res["converged"] is False
    assert eval_res["convergence_state"] == ConvergenceState.DIVERGED.value


def test_unconverged_high_residual_floor_rejected():
    """Test 7: Simulation with high residual floor (e.g. 0.05 > 1e-3) is marked UNCONVERGED."""
    residual_data = {
        "residuals": {"p": [0.1] * 100, "Ux": [0.08] * 100, "Uy": [0.06] * 100},
        "total_iterations": 100,
        "summary": {
            "p": {"final": 0.05, "order_of_magnitude_drop": 0.3},
            "Ux": {"final": 0.04, "order_of_magnitude_drop": 0.2},
            "Uy": {"final": 0.03, "order_of_magnitude_drop": 0.2},
        },
        "has_nan_or_inf": False,
    }
    eval_res = CFDConvergenceEvaluator.evaluate_convergence(residual_data, {"parsed": False}, solver_exit_code=0)
    assert eval_res["converged"] is False
    assert eval_res["convergence_state"] == ConvergenceState.UNCONVERGED.value


def test_real_convergence_verified_with_full_evidence():
    """Test 8: Real convergence requires low residual floor, drop, and stabilized forces."""
    residual_data = {
        "residuals": {"p": [1e-2] + [1e-5] * 99, "Ux": [1e-2] + [1e-5] * 99, "Uy": [1e-2] + [1e-5] * 99},
        "total_iterations": 100,
        "summary": {
            "p": {"final": 5e-6, "order_of_magnitude_drop": 3.5},
            "Ux": {"final": 2e-5, "order_of_magnitude_drop": 3.2},
            "Uy": {"final": 2e-5, "order_of_magnitude_drop": 3.2},
        },
        "continuity_global": [1e-6],
        "has_nan_or_inf": False,
    }
    force_data = {
        "parsed": True,
        "CL": {"final": 0.45, "relative_variation": 0.001},
        "CD": {"final": 0.0085, "relative_variation": 0.001},
    }
    eval_res = CFDConvergenceEvaluator.evaluate_convergence(residual_data, force_data, solver_exit_code=0)
    assert eval_res["converged"] is True
    assert eval_res["convergence_state"] == ConvergenceState.CONVERGED.value


# =============================================================================
# 3. Physical Validation Gates & Force Tests
# =============================================================================

def test_negative_drag_rejected_by_physical_gate():
    """Test 9: CFD result with negative drag CD < 0 fails physical validation."""
    force_data = {
        "parsed": True,
        "CL": {"final": 0.45},
        "CD": {"final": -0.005},  # Unphysical!
        "CM": {"final": -0.02},
    }
    res = CFDResultIngestor.validate_physics(force_data, {"alpha_deg": 4.0})
    assert res["valid"] is False
    assert res["state"] == PhysicalValidationState.PHYSICS_GATE_FAILED.value
    assert any("negative drag" in err for err in res["errors"])


def test_excessive_drag_rejected_by_physical_gate():
    """Test 10: Unphysical excessive drag (CD = 2.5 > 1.5) fails physical gate."""
    force_data = {
        "parsed": True,
        "CL": {"final": 0.45},
        "CD": {"final": 2.5},
        "CM": {"final": 0.0},
    }
    res = CFDResultIngestor.validate_physics(force_data, {"alpha_deg": 4.0})
    assert res["valid"] is False
    assert any("excessive drag" in err for err in res["errors"])


def test_unphysical_lift_direction_rejected():
    """Test 11: Negative lift at positive AoA = 8 deg for positive camber airfoil is rejected."""
    force_data = {
        "parsed": True,
        "CL": {"final": -0.40},  # Negative lift at positive angle!
        "CD": {"final": 0.02},
        "CM": {"final": 0.0},
    }
    res = CFDResultIngestor.validate_physics(force_data, {"alpha_deg": 8.0, "camber_m": 0.04})
    assert res["valid"] is False
    assert any("negative lift" in err for err in res["errors"])


def test_unconverged_cfd_cannot_be_ingested():
    """Test 12: Ingestor raises ValueError if simulation was not converged."""
    with pytest.raises(ValueError, match="not converged"):
        CFDResultIngestor.ingest_to_observation(
            case_name="CASE-01",
            geometry_id="NACA 0012",
            geometry_hash="hash_1",
            flow_condition={"alpha_deg": 4.0, "reynolds": 3e6},
            force_data={"parsed": True, "CL": {"final": 0.4}, "CD": {"final": 0.01}, "CM": {"final": 0.0}},
            convergence_data={"converged": False, "reason": "Residuals high"},
            provenance_hash="prov_1",
        )


# =============================================================================
# 4. Multi-Fidelity Modeling & Hierarchy Tests
# =============================================================================

def test_multifidelity_levels_strictly_distinguished():
    """Test 13: Fidelity levels are distinct and cannot be silently interchanged."""
    assert FidelityLevel.FIDELITY_0_ANALYTICAL != FidelityLevel.FIDELITY_3_REFINED_RANS
    assert FidelityLevel.FIDELITY_1_PANEL != FidelityLevel.FIDELITY_4_EXPERIMENTAL


def test_analytical_baseline_produces_physical_drag():
    """Test 14: Analytical thin-airfoil + flat-plate baseline produces positive drag."""
    cl, cd, cm = AnalyticalThinAirfoilBaseline.predict(alpha_deg=4.0, reynolds=3e6, camber_m=0.02, thickness_t=0.12)
    assert cd > 0.001
    assert cl > 0.0


def test_multifidelity_discrepancy_requires_fitting():
    """Test 15: Unfitted MultiFidelityDiscrepancySurrogate raises error on predict."""
    from backend.physics_ai.benchmark_models import PolynomialRidgeSurrogate
    low = PolynomialRidgeSurrogate()
    delta = PolynomialRidgeSurrogate()
    mf = MultiFidelityDiscrepancySurrogate(low, delta)
    with pytest.raises(RuntimeError, match="must be fitted"):
        mf.predict(np.zeros((5, 4)))


def test_multifidelity_discrepancy_enforces_non_negative_drag():
    """Test 16: Discrepancy surrogate strictly enforces CD >= 0 even if delta is negative."""
    from backend.physics_ai.benchmark_models import PolynomialRidgeSurrogate
    low = PolynomialRidgeSurrogate(degree=1)
    delta = PolynomialRidgeSurrogate(degree=1)
    mf = MultiFidelityDiscrepancySurrogate(low, delta)

    # Train on simple data
    X = np.array([[0.0, 1.0], [2.0, 1.0], [4.0, 1.0]])
    y = np.array([[0.0, 0.008], [0.2, 0.010], [0.4, 0.014]])
    mf.fit(X, y, X, y)

    # Predict extreme negative AoA where unconstrained linear model might produce CD < 0
    preds = mf.predict(np.array([[-50.0, 1.0]]))
    assert preds[0, 1] >= 0.0


# =============================================================================
# 5. Field-Level Learning & Operator Tests
# =============================================================================

def test_stagnation_pressure_exceeding_limit_rejected():
    """Test 17: Field physical validator rejects Cp profiles with max(Cp) > 1.05."""
    unphysical_cp = np.array([1.35] + [0.2] * 63)  # Exceeds Bernoulli stagnation limit!
    val = FieldPhysicalValidator.validate_pressure_profile(unphysical_cp, alpha_deg=4.0)
    assert val["valid"] is False
    assert any("stagnation pressure" in err for err in val["errors"])


def test_missing_suction_peak_rejected():
    """Test 18: At positive AoA=6 deg, lack of suction peak (min(Cp) >= -0.1) fails physical gate."""
    flat_cp = np.array([0.5] * 64)
    val = FieldPhysicalValidator.validate_pressure_profile(flat_cp, alpha_deg=6.0)
    assert val["valid"] is False
    assert any("Missing suction peak" in err for err in val["errors"])


def test_field_integration_recovers_positive_lift():
    """Test 19: Field integrator numerically integrates valid Cp profile to positive lift."""
    x = np.linspace(0.0, 1.0, 32)
    x_contour = np.concatenate([x, x[::-1]])
    y_contour = np.concatenate([0.06 * np.sqrt(x) * (1 - x), -0.06 * np.sqrt(x) * (1 - x)])
    # Upper suction, lower positive pressure
    upper_cp = -0.8 * (1.0 - x)
    lower_cp = 0.4 * (1.0 - x)
    cp_profile = np.concatenate([upper_cp, lower_cp[::-1]])

    cl, cd, cm = AerodynamicFieldIntegrator.integrate_cp(x_contour, y_contour, cp_profile, alpha_deg=4.0)
    assert cl > 0.1
    assert cd > 0.0


# =============================================================================
# 6. Active Acquisition & Experimental Design Tests
# =============================================================================

def test_active_acquisition_ranks_by_composite_score():
    """Test 20: Acquisition engine sorts candidates in strictly descending order."""
    engine = ActiveAcquisitionEngine()
    candidates = [
        {"candidate_id": "CAND-A", "uncertainty": 0.02, "disagreement": 0.01, "alpha_deg": 2.0},
        {"candidate_id": "CAND-B", "uncertainty": 0.15, "disagreement": 0.08, "alpha_deg": 14.0},
    ]
    ranked = engine.rank_candidates(candidates, {"CAND-B": 1.5, "CAND-A": 0.2})
    assert len(ranked) == 2
    assert ranked[0].total_acquisition_score >= ranked[1].total_acquisition_score
    assert ranked[0].candidate_id == "CAND-B"


def test_candidate_includes_scientific_rationale():
    """Test 21: Every ranked candidate includes an explicit, non-empty scientific rationale."""
    engine = ActiveAcquisitionEngine()
    candidates = [{"candidate_id": "CAND-X", "uncertainty": 0.1, "alpha_deg": 14.0}]
    ranked = engine.rank_candidates(candidates, {"CAND-X": 0.5})
    assert len(ranked[0].selection_rationale) > 10


# =============================================================================
# 7. Autonomous Discovery Loop Tests
# =============================================================================

def test_discovery_loop_halts_on_safety_reserve_violation(tmp_path, monkeypatch):
    """Test 22: Discovery loop halts immediately if disk safety reserve (<15 GB) is threatened."""
    controller = AutonomousDiscoveryController(output_dir=tmp_path)
    # Mock hardware probe to simulate disk below safety reserve
    monkeypatch.setattr(
        CFDEnvironmentProbe,
        "probe_hardware",
        lambda: {"safety_reserve_met": False, "disk_available_gb": 12.5},
    )
    rec = controller.run_iteration(1, None, [{"candidate_id": "C1"}], {}, 0.95)
    assert rec.loop_terminated is True
    assert rec.solver_status == "RESOURCE_LIMITED"


def test_discovery_loop_halts_on_evidence_saturation(tmp_path):
    """Test 23: Loop halts when Expected Information Gain falls below threshold."""
    controller = AutonomousDiscoveryController(output_dir=tmp_path)
    # Candidate with near-zero uncertainty and distance
    candidates = [
        {"candidate_id": "SAT-01", "uncertainty": 0.0001, "disagreement": 0.0001, "alpha_deg": 0.0}
    ]
    rec = controller.run_iteration(1, None, candidates, {"SAT-01": 0.001}, 0.98)
    assert rec.loop_terminated is True
    assert "Evidence Saturation" in (rec.stopping_criterion_triggered or "")


# =============================================================================
# 8. Scientific Claims Discipline Tests
# =============================================================================

def test_causal_claim_rejected_without_two_experiments():
    """Test 24: Causal claim with fewer than 2 experiments is rejected as UNSUPPORTED."""
    claim = ScientificClaim(
        claim_id="C-001",
        claim_text="Thickness causes immediate stall delay",
        evidence_type=EvidenceType.CAUSAL_CLAIM,
        support_level=SupportLevel.STRONG_EMPIRICAL,
        datasets=["AirfRANS"],
        experiments=["EXP-1"],  # Only 1 experiment!
        limitations=[],
        falsification_criteria="Stall onset invariant",
    )
    checked = ScientificClaimValidator.validate_claim(claim)
    assert checked.is_valid is False
    assert checked.support_level == SupportLevel.UNSUPPORTED
    assert "Causal claims require at least two" in (checked.rejection_reason or "")


def test_claim_without_falsification_criteria_rejected():
    """Test 25: Claims with empty falsification criteria are rejected."""
    claim = ScientificClaim(
        claim_id="C-002",
        claim_text="Lift increases with angle",
        evidence_type=EvidenceType.SUPPORTED_HYPOTHESIS,
        support_level=SupportLevel.MODERATE_EMPIRICAL,
        datasets=["AirfRANS"],
        experiments=["EXP-1"],
        limitations=[],
        falsification_criteria="",  # Missing!
    )
    checked = ScientificClaimValidator.validate_claim(claim)
    assert checked.is_valid is False
    assert "falsifiable criteria" in (checked.rejection_reason or "")


# =============================================================================
# 9. Extended 8-Stage Model Promotion Tests
# =============================================================================

def test_promotion_cannot_skip_external_validation():
    """Test 26: Model cannot be promoted to SCIENTIFICALLY_TRUSTED without external validation."""
    stage, is_trusted, reason = PersistentExperimentRegistry.audit_promotion_phase21(
        in_domain_valid=True,
        physics_valid=True,
        uncertainty_calibrated=True,
        ood_tested=True,
        externally_validated=False,  # Lacks external validation!
        reproducible=True,
        ood_r2=0.95,
    )
    assert stage == PromotionStage.STAGE_5_OOD_TESTED
    assert is_trusted is False
    assert "external" in reason.lower()


def test_full_8_stage_promotion_awarded():
    """Test 27: Model passing all 8 stages earns STAGE_8_SCIENTIFICALLY_TRUSTED."""
    stage, is_trusted, reason = PersistentExperimentRegistry.audit_promotion_phase21(
        in_domain_valid=True,
        physics_valid=True,
        uncertainty_calibrated=True,
        ood_tested=True,
        externally_validated=True,
        reproducible=True,
        ood_r2=0.96,
    )
    assert stage == PromotionStage.STAGE_8_SCIENTIFICALLY_TRUSTED
    assert is_trusted is True


# =============================================================================
# 10. Provenance & Reproduction Verifier Tests
# =============================================================================

def test_tampered_bundle_file_detected(tmp_path):
    """Test 28: Modifying any file inside reproduction bundle invalidates verification."""
    bundle_info = Phase21ReproductionVerifier.assemble_bundle(bundle_dir=tmp_path / "TEST-BUNDLE")
    assert Path(bundle_info["hashes_file"]).exists()

    # Tamper with a file inside bundle
    tamper_target = tmp_path / "TEST-BUNDLE" / "README.md"
    tamper_target.write_text("TAMPERED CONTENT", encoding="utf-8")

    v_res = Phase21ReproductionVerifier.verify_bundle(bundle_dir=tmp_path / "TEST-BUNDLE")
    assert v_res["verified"] is False
    assert v_res["status"] == "REPRODUCIBILITY_FAILED"
    assert len(v_res["corrupted_files"]) > 0


def test_merkle_provenance_hash_changes_on_case_edit(tmp_path):
    """Test 29: Any edit to case dictionaries changes the Merkle root hash."""
    case_dir = tmp_path / "prov_case"
    case_dir.mkdir()
    (case_dir / "system").mkdir()
    (case_dir / "system/controlDict").write_text("version 1;", encoding="utf-8")

    prov1 = CFDProvenanceEngine.compute_case_provenance(case_dir, "simpleFoam", "OpenFOAM")
    root1 = prov1["merkle_root"]

    # Edit controlDict
    (case_dir / "system/controlDict").write_text("version 2;", encoding="utf-8")
    prov2 = CFDProvenanceEngine.compute_case_provenance(case_dir, "simpleFoam", "OpenFOAM")
    root2 = prov2["merkle_root"]

    assert root1 != root2


def test_hardware_safety_reserve_enforced_strictly():
    """Test 30: Minimum disk safety reserve is strictly 15.0 GB."""
    assert CFDEnvironmentProbe.MIN_DISK_SAFETY_RESERVE_GB == 15.0
    hw = CFDEnvironmentProbe.probe_hardware()
    assert hw["disk_safety_reserve_gb"] == 15.0
