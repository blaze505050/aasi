"""
Tests for AASI Independent Scientific Reproducibility, Real Solver Execution,
ASME V&V 20 Grid Convergence, and 5-Tier Epistemic Uncertainty Quantification.

Adversarially tests that:
1. When CFD solver binary is unavailable, the system strictly returns USER_EXECUTED_REQUIRED
   with SOLVER_UNAVAILABLE, refusing to fabricate residuals or aerodynamic forces.
2. Divergence or NaN values in solver logs are detected and flagged as DIVERGED.
3. Insufficient iterations / unconverged residuals without force convergence are rejected as UNCONVERGED.
4. Non-monotonic or oscillatory grid refinement strictly refuses to guess GCI, returning
   appropriate failure status (fail-closed).
5. File tampering in a reproducibility bundle is caught via SHA-256 verification, triggering REPRODUCTION_FAILED.
6. Cyclic dependencies in the evidence DAG are flagged by ledger.verify_integrity().
7. Orphan records (unlinked from conclusion) are caught by ledger.verify_integrity().
8. 5-tier GUM uncertainty model computes valid root-sum-of-squares intervals and coverage U_95.
9. Canonical flagship NACA 0012 run bundle passes automated verification as VERIFIED_REPRODUCIBLE.
10. The POST /api/research/reproduce/verify API endpoint operates end-to-end.
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.simulation.executor import (
    OpenFOAMExecutionEngine,
    SolverExecutionStatus,
    ConvergenceStatus,
    ResidualHistory,
    ForceCoeffHistory,
    SolverExecutionResult
)
from backend.simulation.grid_study import (
    ASMEGridConvergenceStudy,
    GridCaseDefinition,
    GridConvergenceStatus,
)
from backend.physics.uncertainty_model import (
    AerodynamicUncertaintyQuantifier,
    UncertaintyStatus,
)
from backend.research.verifier import (
    ReproducibilityVerifier,
    ReproducibilityStatus,
)
from backend.research.evidence_ledger import (
    EvidenceLedger,
    EvidenceRecord,
    EvidenceType,
    EpistemicStatus,
)
from backend.research.service import research_loop_service
from backend.research.bundle import ResearchBundleExporter


client = TestClient(app)


def test_01_solver_unavailable_returns_clean_user_executed_required(tmp_path):
    """Verify that when host solver is missing, system stages case cleanly without fake numbers."""
    fake_case = tmp_path / "case_naca0012"
    fake_case.mkdir()
    (fake_case / "system").mkdir()
    (fake_case / "system" / "controlDict").write_text("// test controlDict", encoding="utf-8")

    result = OpenFOAMExecutionEngine.execute_or_stage(
        case_dir=fake_case,
        case_id="case_test_01"
    )

    assert result.execution_status == SolverExecutionStatus.USER_EXECUTED_REQUIRED
    assert "SOLVER_UNAVAILABLE" in result.stdout_summary
    assert result.exit_code is None
    assert result.convergence_report is not None
    assert result.convergence_report.is_converged is False


def test_02_solver_divergence_detected():
    """Verify that NaN or unbounded residuals in solver logs are detected as diverged."""
    diverged_log = """
Time = 1
Solving for Ux, Initial residual = 1.0
Solving for Uy, Initial residual = 1.0
Solving for p, Initial residual = 0.5
Time = 2
Solving for Ux, Initial residual = 100000.0
Time = 3
Solving for Ux, Initial residual = NaN
    """
    res_hist, _ = OpenFOAMExecutionEngine.parse_openfoam_log(diverged_log)
    force_hist = ForceCoeffHistory()
    report = OpenFOAMExecutionEngine.analyze_convergence(res_hist, force_hist)
    assert report.is_converged is False
    assert report.divergence_detected is True
    assert report.convergence_status == ConvergenceStatus.DIVERGED


def test_03_solver_exit_zero_without_forces_rejected():
    """Verify that marginal residuals without force convergence do not claim convergence."""
    empty_log = """
Time = 1
Solving for Ux, Initial residual = 0.05
Solving for Uy, Initial residual = 0.05
Solving for p, Initial residual = 0.02
    """
    res_hist, _ = OpenFOAMExecutionEngine.parse_openfoam_log(empty_log)
    force_hist = ForceCoeffHistory()
    report = OpenFOAMExecutionEngine.analyze_convergence(res_hist, force_hist)

    assert report.is_converged is False
    assert report.convergence_status == ConvergenceStatus.UNCONVERGED


def test_04_non_monotonic_grid_study_refuses_to_guess_gci():
    """Verify that non-monotonic or oscillatory grid refinement fails closed without guessing GCI."""
    # Oscillatory case: phi1 = 1.0, phi2 = 0.9, phi3 = 0.95 -> e32 = 0.05, e21 = -0.1 -> R < 0
    fine = GridCaseDefinition(
        grid_name="fine",
        cell_count=400000,
        representative_cell_size_h=0.001,
        mesh_hash="sha_fine",
        cl=1.00,
        cd=0.015
    )
    med = GridCaseDefinition(
        grid_name="medium",
        cell_count=100000,
        representative_cell_size_h=0.002,
        mesh_hash="sha_med",
        cl=0.90,
        cd=0.016
    )
    coarse = GridCaseDefinition(
        grid_name="coarse",
        cell_count=25000,
        representative_cell_size_h=0.004,
        mesh_hash="sha_coarse",
        cl=0.95,
        cd=0.017
    )

    study = ASMEGridConvergenceStudy.evaluate_grid_study(fine, med, coarse, metric="cl")
    assert study.grid_status == GridConvergenceStatus.OSCILLATORY_CONVERGENCE
    assert study.gci_fine_pct is None
    assert study.richardson_extrapolated_value is None
    assert any("oscillatory" in n.lower() for n in study.notes)


def test_05_bundle_tampering_detected(tmp_path):
    """Verify that altering 1 byte in a reproducibility bundle triggers REPRODUCTION_FAILED."""
    run = research_loop_service.execute_flagship_naca0012_run(run_id="RUN-TAMPER-TEST")
    bundle_dir, _ = ResearchBundleExporter.export_bundle(run, output_base_dir=str(tmp_path))

    # Baseline should verify cleanly
    report_initial = ReproducibilityVerifier.verify_bundle_directory(bundle_dir)
    assert report_initial.status == ReproducibilityStatus.VERIFIED_REPRODUCIBLE

    # Tamper with conclusion.json
    conc_file = bundle_dir / "conclusion.json"
    c_data = json.loads(conc_file.read_text(encoding="utf-8"))
    c_data["tampered"] = True
    conc_file.write_text(json.dumps(c_data), encoding="utf-8")

    # Re-verify -> should fail due to SHA-256 hash mismatch
    report_tampered = ReproducibilityVerifier.verify_bundle_directory(bundle_dir)
    assert report_tampered.status == ReproducibilityStatus.REPRODUCTION_FAILED
    assert report_tampered.tamper_detected is True
    assert any("mismatch" in f.lower() for f in report_tampered.checks_failed)


def test_06_ledger_integrity_detects_cycles():
    """Verify that DAG provenance cycles are detected by ledger.verify_integrity()."""
    ledger = EvidenceLedger(ledger_id="LEDGER-CYCLE-TEST", run_id="RUN-CYCLE-1")
    rec_a = EvidenceRecord(
        evidence_id="ev-A",
        run_id="RUN-CYCLE-1",
        evidence_type=EvidenceType.QUESTION,
        source="Source A",
        source_identifier="SRC-A",
        acquisition_method="TEST",
        input_hash="hash_a_in",
        output_hash="hash_a_out",
        provenance_chain=["ev-B"],  # A depends on B
        epistemic_status=EpistemicStatus.REAL
    )
    rec_b = EvidenceRecord(
        evidence_id="ev-B",
        run_id="RUN-CYCLE-1",
        evidence_type=EvidenceType.LITERATURE_CITATION,
        source="Source B",
        source_identifier="SRC-B",
        acquisition_method="TEST",
        input_hash="hash_b_in",
        output_hash="hash_b_out",
        provenance_chain=["ev-A"],  # B depends on A (Cycle!)
        epistemic_status=EpistemicStatus.REFERENCED
    )
    ledger.append_record(rec_a)
    ledger.append_record(rec_b)

    integrity = ledger.verify_integrity()
    assert integrity.is_valid is False
    assert len(integrity.cycles_detected) > 0


def test_07_ledger_integrity_detects_orphans():
    """Verify that unreferenced disconnected records are caught as orphans."""
    ledger = EvidenceLedger(ledger_id="LEDGER-ORPHAN-TEST", run_id="RUN-ORPHAN-1")
    rec_q = EvidenceRecord(
        evidence_id="ev-q",
        run_id="RUN-ORPHAN-1",
        evidence_type=EvidenceType.QUESTION,
        source="Source Q",
        source_identifier="SRC-Q",
        acquisition_method="TEST",
        input_hash="hash_q_in",
        output_hash="hash_q_out",
        provenance_chain=[],
        epistemic_status=EpistemicStatus.REAL
    )
    rec_orphan = EvidenceRecord(
        evidence_id="ev-floating-data",
        run_id="RUN-ORPHAN-1",
        evidence_type=EvidenceType.SURFACE_COORDINATES,
        source="Disconnected source",
        source_identifier="SRC-DISCONNECTED",
        acquisition_method="TEST",
        input_hash="hash_d_in",
        output_hash="hash_d_out",
        provenance_chain=[],
        epistemic_status=EpistemicStatus.REAL
    )
    rec_conc = EvidenceRecord(
        evidence_id="ev-conc",
        run_id="RUN-ORPHAN-1",
        evidence_type=EvidenceType.RESEARCH_CONCLUSION,
        source="Source C",
        source_identifier="SRC-C",
        acquisition_method="TEST",
        input_hash="hash_c_in",
        output_hash="hash_c_out",
        provenance_chain=["ev-q"],
        epistemic_status=EpistemicStatus.REAL
    )
    ledger.append_record(rec_q)
    ledger.append_record(rec_orphan)
    ledger.append_record(rec_conc)

    integrity = ledger.verify_integrity()
    assert integrity.is_valid is False
    assert "ev-floating-data" in integrity.orphan_records


def test_08_five_tier_uncertainty_budget():
    """Verify that the 5-tier GUM uncertainty model computes correct RSS uncertainty and U_95."""
    unc = AerodynamicUncertaintyQuantifier.compute_naca0012_uncertainty(
        aoa_deg=10.0,
        gci_fine=0.008,
        surrogate_std=0.015
    )
    assert unc.status == UncertaintyStatus.QUANTIFIED
    assert unc.combined_standard_uncertainty_cl > 0.0
    assert unc.combined_expanded_uncertainty_cl_u95 > unc.combined_standard_uncertainty_cl
    assert abs(unc.combined_expanded_uncertainty_cl_u95 - 1.96 * unc.combined_standard_uncertainty_cl) < 1e-4

    # Post-stall regime test (AoA >= 12 deg) should have higher turbulence model uncertainty
    unc_stall = AerodynamicUncertaintyQuantifier.compute_naca0012_uncertainty(aoa_deg=14.0)
    assert unc_stall.model_uncertainty.turbulence_model_discrepancy_cl > unc.model_uncertainty.turbulence_model_discrepancy_cl
    assert unc_stall.combined_expanded_uncertainty_cl_u95 > unc.combined_expanded_uncertainty_cl_u95


def test_09_flagship_naca0012_passes_reproducibility_verifier():
    """Verify that the full flagship NACA 0012 run bundle passes independent reproducibility verification."""
    run = research_loop_service.execute_flagship_naca0012_run(run_id="RUN-NACA0012-AUTOTEST")
    assert run.reproducibility_verification is not None
    assert run.reproducibility_verification.get("status") == "VERIFIED_REPRODUCIBLE"
    assert run.uncertainty_assessment is not None
    assert run.grid_convergence is not None
    assert run.status.value in ["COMPLETED", "REPRODUCIBILITY_VERIFIED"]


def test_10_api_verify_reproducibility_endpoint():
    """Verify that POST /api/research/reproduce/verify returns 200 with structured audit report."""
    run = research_loop_service.execute_flagship_naca0012_run(run_id="RUN-API-VERIFY-TEST")
    response = client.post(
        "/api/research/reproduce/verify",
        json={"run_id": run.run_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["VERIFIED_REPRODUCIBLE", "PARTIALLY_REPRODUCIBLE"]
    assert "checks_passed" in data
    assert len(data["checks_passed"]) >= 6
    assert data["tamper_detected"] is False
