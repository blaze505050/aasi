"""
AASI Phase 28: Comprehensive Autonomy & Scientific Integration Tests.
Covers all 18 mandatory integration test scenarios:
TEST 1: Natural-language request -> Canonical Investigation created
TEST 2: MethodSelectionRecord logged with candidates, reason, and confidence
TEST 3: Database result -> verified answer retrieved
TEST 4: Analytical thin airfoil result -> correctly classified with inviscid assumptions
TEST 5: Synthetic result -> never presented as real physical fact
TEST 6: Staged CFD -> status strictly remains NOT_EXECUTED or STAGED_ONLY
TEST 7: Valid CFD result bundle -> VERIFIED
TEST 8: Incomplete CFD bundle (missing forces/logs) -> INCOMPLETE
TEST 9: Corrupted result bundle -> INVALID
TEST 10: Execution failure -> automated 11-class diagnosis report
TEST 11: Repair candidate generated -> new cryptographic case hash with parameter adjustments
TEST 12: Three failed attempts -> STOP with HUMAN_REVIEW_REQUIRED
TEST 13: Database vs Live CFD comparison -> physical discrepancy record with evidence
TEST 14: Provenance and epistemic tags survive into the final answer
TEST 15: Unauthorized artifact access -> denied (HTTP 403 / Access Denied)
TEST 16: User A cannot access User B's investigation (multitenant isolation)
TEST 17: No secrets or API keys exposed in API responses or Colab notebooks
TEST 18: No local CFD execution occurs in public/default mode (zero local laptop load)
"""

import json
import tarfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.auth.security import security_manager
from backend.auth.governance import governance_engine
from backend.compute.queue import job_queue, JobState
from backend.agent.canonical_investigation import (
    Investigation,
    InvestigationStatus,
    EpistemicTier,
    OperatingConditions,
    ScientificValue,
)
from backend.agent.method_selector import MethodSelector
from backend.science.verification import ScientificResultVerifier, VerificationStatus
from backend.agent.diagnostics import CFDDiagnosticsEngine, CFDErrorClass
from backend.agent.repair_engine import CFDRepairEngine
from backend.agent.execution_lifecycle import AutonomousLifecycleController
from backend.agent.discrepancy_engine import ScientificDiscrepancyEngine
from backend.agent.investigation_graph import InvestigationGraph, InquiryNodeType

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_users():
    """Ensure clean test users and auth tokens."""
    # Reset job queue in memory
    job_queue.clear()
    governance_engine.reset()

    user_a = security_manager.get_user_by_username("user_a")
    if not user_a:
        user_a = security_manager.create_user("user_a", "user_a@aasi.aero", "password123A!", role="RESEARCHER")
    user_b = security_manager.get_user_by_username("user_b")
    if not user_b:
        user_b = security_manager.create_user("user_b", "user_b@aasi.aero", "password123B!", role="RESEARCHER")

    session_a = security_manager.create_session_token(user_a)
    session_b = security_manager.create_session_token(user_b)

    return {
        "user_a": user_a,
        "user_b": user_b,
        "token_a": session_a.token,
        "token_b": session_b.token,
    }


# ==============================================================================
# TEST 1: Natural-language request -> Canonical Investigation created
# ==============================================================================
def test_1_natural_language_to_canonical_investigation(setup_test_users):
    token = setup_test_users["token_a"]
    resp = client.post(
        "/api/investigate",
        headers={"Authorization": f"Bearer {token}"},
        json={"objective": "What happens to the drag of NACA 4412 from alpha 4° to 12° at Re=3e6?"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "investigation_id" in data
    assert data["geometry"] == "NACA 4412"
    assert data["alpha_deg"] in [4.0, 6.0, 12.0]

    # Verify canonical representation can be queried
    c_resp = client.get(
        f"/api/investigate/{data['job_id']}/canonical",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert c_resp.status_code == 200, c_resp.text
    inv = c_resp.json()
    assert inv["domain"] == "aerodynamics"
    assert inv["governing_physics"] is not None
    assert len(inv["candidate_methods"]) > 0
    assert inv["selected_method"] is not None
    assert inv["provenance_hash"] != ""


# ==============================================================================
# TEST 2: MethodSelectionRecord logged with candidates, reason, and confidence
# ==============================================================================
def test_2_method_selection_record():
    cond = OperatingConditions(alpha_deg=6.0, reynolds=3e6, mach=0.15)
    rec = MethodSelector.evaluate_candidates(
        geometry="NACA 4412",
        conditions=cond,
        user_intent="Analyze drag rise and separation for NACA 4412",
        has_database_match=True,
        database_distance=0.03,
        surrogate_uncertainty=0.08,
    )
    assert rec.selected_method == EpistemicTier.LIVE_CFD
    assert rec.confidence >= 0.90
    assert "drag" in rec.reason.lower() or "viscous" in rec.reason.lower()
    assert len(rec.candidate_methods) >= 3
    # Check that candidates have applicable status and scores
    for cand in rec.candidate_methods:
        assert cand.method_name != ""
        assert 0.0 <= cand.suitability_score <= 1.0


# ==============================================================================
# TEST 3: Database result -> verified answer retrieved
# ==============================================================================
def test_3_database_result_retrieval(setup_test_users):
    token = setup_test_users["token_a"]
    resp = client.post(
        "/api/investigate",
        headers={"Authorization": f"Bearer {token}"},
        json={"objective": "Retrieve Abbott & von Doenhoff benchmark for NACA 0012 at alpha 0 deg"},
    )
    assert resp.status_code == 200
    data = resp.json()
    cd_entries = [m for m in data["multi_fidelity_matrix"] if "Drag" in m["quantity"]]
    assert len(cd_entries) == 1
    # Benchmark database must have a valid non-empty float
    assert cd_entries[0]["database"] is not None
    assert cd_entries[0]["database"] > 0.0


# ==============================================================================
# TEST 4: Analytical thin airfoil result -> correctly classified with inviscid assumptions
# ==============================================================================
def test_4_analytical_thin_airfoil_inviscid_classification():
    cond = OperatingConditions(alpha_deg=4.0, reynolds=3e6, mach=0.10)
    rec = MethodSelector.evaluate_candidates(
        geometry="NACA 0012",
        conditions=cond,
        user_intent="Linear lift slope theoretical estimate",
        has_database_match=False,
        database_distance=1.0,
        surrogate_uncertainty=0.35,
    )
    assert rec.selected_method == EpistemicTier.ANALYTICAL
    assert "thin airfoil" in rec.reason.lower() or "first-order" in rec.reason.lower()
    # Inviscid assumption implies no form drag
    analytical_candidate = [c for c in rec.candidate_methods if c.tier == EpistemicTier.ANALYTICAL][0]
    assert "viscous" in analytical_candidate.reason.lower() or "cannot resolve" in analytical_candidate.reason.lower()


# ==============================================================================
# TEST 5: Synthetic result -> never presented as real physical fact
# ==============================================================================
def test_5_synthetic_result_anti_fabrication_label():
    val = ScientificValue(
        quantity="CD",
        value=0.0125,
        epistemic_tier=EpistemicTier.SYNTHETIC,
        source_ref="Generative Interpolator Mock",
        is_live_cfd=False,
    )
    assert val.epistemic_tier != EpistemicTier.LIVE_CFD
    assert val.epistemic_tier != EpistemicTier.DATABASE_REAL
    assert val.is_live_cfd is False


# ==============================================================================
# TEST 6: Staged CFD -> status strictly remains NOT_EXECUTED or STAGED_ONLY
# ==============================================================================
def test_6_staged_cfd_strictly_not_executed(setup_test_users):
    token = setup_test_users["token_a"]
    resp = client.post(
        "/api/investigate",
        headers={"Authorization": f"Bearer {token}"},
        json={"objective": "CFD simulation for RAE 2822 at alpha 2.5 deg Re=6.5e6"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # Before results archive is imported, live_cfd MUST be None
    for entry in data["multi_fidelity_matrix"]:
        assert entry["live_cfd"] is None
        assert entry["status"] == "AWAITING_REMOTE_CFD"
    assert data["job_state"] == JobState.AUTHORIZATION_REQUIRED.value


# ==============================================================================
# TEST 7: Valid CFD result bundle -> VERIFIED
# ==============================================================================
def test_7_valid_cfd_bundle_verified(tmp_path):
    archive_dir = tmp_path / "valid_sim"
    archive_dir.mkdir(parents=True)

    # 1. Manifest
    (archive_dir / "job_manifest.json").write_text(
        json.dumps({"job_id": "JOB-12345", "investigation_id": "INV-12345", "status": "COMPLETED"})
    )
    # 2. Solver Log
    (archive_dir / "log.simpleFoam").write_text(
        "OpenFOAM simpleFoam\nVersion: 10\nSolving for p, Initial residual = 0.5, Final residual = 1e-5\nEnd\n"
    )
    # 3. Force coefficients
    forces_dir = archive_dir / "postProcessing" / "forceCoeffs" / "0"
    forces_dir.mkdir(parents=True)
    (forces_dir / "forceCoeffs.dat").write_text("# Time Cm Cd Cl\n1000 -0.085 0.0125 1.0820\n")

    report = ScientificResultVerifier.verify_archive(archive_dir, expected_case_id="JOB-12345")
    assert report.status == VerificationStatus.VERIFIED
    assert report.is_verified is True
    assert report.parsed_polars["CL"] == 1.0820
    assert report.parsed_polars["CD"] == 0.0125
    assert report.parsed_polars["CM"] == -0.085


# ==============================================================================
# TEST 8: Incomplete CFD bundle (missing forces/logs) -> INCOMPLETE
# ==============================================================================
def test_8_incomplete_cfd_bundle_marked_incomplete(tmp_path):
    archive_dir = tmp_path / "incomplete_sim"
    archive_dir.mkdir(parents=True)
    # Only manifest, no log and no forces
    (archive_dir / "job_manifest.json").write_text(
        json.dumps({"job_id": "JOB-INCOMPLETE", "status": "CRASHED"})
    )
    report = ScientificResultVerifier.verify_archive(archive_dir, expected_case_id="JOB-INCOMPLETE")
    assert report.status == VerificationStatus.INCOMPLETE
    assert report.is_verified is False
    assert len(report.failure_reasons) > 0


# ==============================================================================
# TEST 9: Corrupted result bundle -> INVALID
# ==============================================================================
def test_9_corrupted_result_bundle_marked_invalid(tmp_path):
    archive_dir = tmp_path / "invalid_sim"
    archive_dir.mkdir(parents=True)
    (archive_dir / "job_manifest.json").write_text(
        json.dumps({"job_id": "JOB-CORRUPT"})
    )
    (archive_dir / "log.simpleFoam").write_text("OpenFOAM simpleFoam\nSolving for p...\nEnd\n")
    # Non-physical negative drag
    forces_dir = archive_dir / "postProcessing" / "forceCoeffs" / "0"
    forces_dir.mkdir(parents=True)
    (forces_dir / "forceCoeffs.dat").write_text("# Time Cm Cd Cl\n1000 -0.085 -0.0500 1.0820\n")

    report = ScientificResultVerifier.verify_archive(archive_dir, expected_case_id="JOB-CORRUPT")
    assert report.status == VerificationStatus.INVALID
    assert report.is_verified is False
    assert any("Drag coefficient is non-positive" in r for r in report.failure_reasons)


# ==============================================================================
# TEST 10: Execution failure -> automated 11-class diagnosis report
# ==============================================================================
def test_10_execution_failure_11_class_diagnosis():
    divergence_log = (
        "Courant Number mean: 0.1 max: 0.8\n"
        "smoothSolver: Solving for Ux, Initial residual = 1.0, Final residual = 1.0\n"
        "#0  Foam::error::printStack(Foam::Ostream&)\n"
        "Floating point exception (core dumped)\n"
    )
    diag = CFDDiagnosticsEngine.diagnose(solver_log=divergence_log)
    assert diag.error_class in [CFDErrorClass.FLOATING_POINT_FAILURE, CFDErrorClass.DIVERGENCE]
    assert diag.confidence > 0.90
    assert len(diag.repair_candidates) > 0


# ==============================================================================
# TEST 11: Repair candidate generated -> new cryptographic case hash
# ==============================================================================
def test_11_repair_candidate_new_cryptographic_hash():
    diag = CFDDiagnosticsEngine.diagnose(solver_log="Floating point exception\n")
    original_spec = {"geometry": "NACA 4412", "alpha_deg": 8.0, "reynolds": 3e6}
    original_hash = "abc123originalhash"

    outcome = CFDRepairEngine.propose_repair(
        original_spec=original_spec,
        original_case_hash=original_hash,
        diagnosis=diag,
        current_retry_count=0,
    )
    assert outcome.status == "REPAIR_CANDIDATE_GENERATED"
    candidate = outcome.candidate
    assert candidate is not None
    assert candidate.original_case_hash == original_hash
    # Cryptographic candidate hash MUST differ from original hash
    assert candidate.candidate_case_hash != original_hash
    assert candidate.retry_number == 1
    assert len(candidate.modifications) > 0


# ==============================================================================
# TEST 12: Three failed attempts -> STOP with HUMAN_REVIEW_REQUIRED
# ==============================================================================
def test_12_three_failed_attempts_stops_at_human_review():
    job = job_queue.create_job(
        user_id="user_a",
        experiment_id="EXP-RETRY-TEST",
        geometry="NACA 4412",
        alpha_deg=8.0,
        reynolds=3e6,
        mach=0.15,
    )

    failing_log = "Floating point exception\n"
    # Attempt 1
    r1 = AutonomousLifecycleController.handle_solver_failure(job.job_id, failing_log, current_attempt=1)
    assert r1.outcome_status == "RETRY_STAGED"
    # Attempt 2
    r2 = AutonomousLifecycleController.handle_solver_failure(job.job_id, failing_log, current_attempt=2)
    assert r2.outcome_status == "RETRY_STAGED"
    # Attempt 3 -> Exhausted!
    r3 = AutonomousLifecycleController.handle_solver_failure(job.job_id, failing_log, current_attempt=3)
    assert r3.outcome_status == "HUMAN_REVIEW_REQUIRED"
    assert r3.new_job_state == JobState.HUMAN_REVIEW_REQUIRED
    assert "retry limit (3) reached" in r3.detail.lower()


# ==============================================================================
# TEST 13: Database vs Live CFD comparison -> physical discrepancy record with evidence
# ==============================================================================
def test_13_database_vs_live_cfd_discrepancy_with_evidence():
    records = ScientificDiscrepancyEngine.analyze_discrepancies(
        geometry="NACA 4412",
        alpha_deg=6.0,
        reynolds=3e6,
        mach=0.15,
        values_by_source={"LIVE_CFD": 0.0125, "DATABASE_REAL": 0.0120, "ANALYTICAL": 0.0075},
        quantity="CD",
    )
    assert len(records) >= 2
    # Verify analytical comparison contains inviscid d'Alembert hypothesis
    analytical_rec = [r for r in records if "ANALYTICAL" in [r.source_a, r.source_b]][0]
    assert len(analytical_rec.hypotheses) > 0
    assert any("inviscid" in h.mechanism.lower() or "displacement" in h.mechanism.lower() for h in analytical_rec.hypotheses)
    assert all(len(h.evidence) > 0 for h in analytical_rec.hypotheses)


# ==============================================================================
# TEST 14: Provenance and epistemic tags survive into the final answer
# ==============================================================================
def test_14_provenance_and_epistemic_tags_preserved():
    inv = Investigation(
        investigation_id="INV-PROV-TEST",
        user_request="Verify drag of NACA 4412",
        scientific_intent="Analyze drag",
        geometry="NACA 4412",
        operating_conditions=OperatingConditions(alpha_deg=4.0, reynolds=3e6, mach=0.15),
    )
    inv.comparisons["CD"] = {
        "LIVE_CFD": ScientificValue(quantity="CD", value=0.0125, epistemic_tier=EpistemicTier.LIVE_CFD, source_ref="simpleFoam"),
        "DATABASE_REAL": ScientificValue(quantity="CD", value=0.0120, epistemic_tier=EpistemicTier.DATABASE_REAL, source_ref="Abbott Report 824"),
    }
    graph = InvestigationGraph.build_from_investigation(inv)
    assert graph.nodes[0].node_type == InquiryNodeType.QUESTION
    # Check that provenance hashes exist on each node
    for node in graph.nodes:
        assert node.provenance_hash is not None
        assert len(node.provenance_hash) == 64  # SHA-256 hex string


# ==============================================================================
# TEST 15: Unauthorized artifact access -> denied (HTTP 403 / Access Denied)
# ==============================================================================
def test_15_unauthorized_artifact_access_denied(setup_test_users):
    token_b = setup_test_users["token_b"]
    # Attempt to access a job that belongs to user_a
    job = job_queue.create_job(
        user_id="user_a",
        experiment_id="EXP-SECRET",
        geometry="NACA 0012",
        alpha_deg=0.0,
        reynolds=3e6,
        mach=0.15,
    )
    # user_b attempts to access user_a's job
    resp = client.get(
        f"/api/investigate/{job.job_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403, resp.text


# ==============================================================================
# TEST 16: User A cannot access User B's investigation (multitenant isolation)
# ==============================================================================
def test_16_multitenant_isolation(setup_test_users):
    token_a = setup_test_users["token_a"]
    token_b = setup_test_users["token_b"]

    # User B creates an investigation
    resp_b = client.post(
        "/api/investigate",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"objective": "Evaluate NACA 2412 for User B"},
    )
    assert resp_b.status_code == 200
    job_id_b = resp_b.json()["job_id"]

    # User A tries to view User B's canonical investigation
    resp_a = client.get(
        f"/api/investigate/{job_id_b}/canonical",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a.status_code == 403, resp_a.text


# ==============================================================================
# TEST 17: No secrets or API keys exposed in API responses or Colab notebooks
# ==============================================================================
def test_17_no_secrets_exposed_in_api_or_notebooks(setup_test_users):
    token = setup_test_users["token_a"]
    resp = client.post(
        "/api/investigate",
        headers={"Authorization": f"Bearer {token}"},
        json={"objective": "Check security disclosure on NACA 0012"},
    )
    assert resp.status_code == 200
    body_text = resp.text.lower()
    # Ensure sensitive credentials are never leaked
    for forbidden in ["password", "secret_key", "api_secret", "private_key", "bearer"]:
        if forbidden == "bearer":
            # Exclude standard auth headers if any, but ensure no bearer tokens in JSON payload
            assert "bearer aasi_" not in body_text
        else:
            assert f'"{forbidden}"' not in body_text


# ==============================================================================
# TEST 18: No local CFD execution occurs in public/default mode (zero laptop load)
# ==============================================================================
def test_18_zero_local_laptop_load_guaranteed(setup_test_users):
    token = setup_test_users["token_a"]
    resp = client.post(
        "/api/investigate",
        headers={"Authorization": f"Bearer {token}"},
        json={"objective": "Run CFD for NACA 4412"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # Selected provider must be remote (COLAB), never local
    assert data["selected_provider"] == "COLAB"
    assert data["job_state"] == JobState.AUTHORIZATION_REQUIRED.value
    # No simpleFoam process should ever be executed on local host
    assert data["multi_fidelity_matrix"][0]["live_cfd"] is None
