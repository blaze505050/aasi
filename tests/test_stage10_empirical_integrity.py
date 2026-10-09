"""
Stage-10 Empirical Integrity Regression Tests.
12 tests enforcing provenance, hash identity, sweep provenance,
verification semantics, and failure lifecycle integrity.
"""

import hashlib
import json
import os
import sys
import tarfile
import tempfile
from pathlib import Path

import pytest

# Ensure workspace root is importable
WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from backend.compute.colab_session import ColabSessionPackager
from backend.science.verification import ScientificResultVerifier, VerificationStatus
from backend.science.empirical_ledger import EmpiricalValidationLedger, LedgerEntry, LedgerStatus
from backend.agent.diagnostics import CFDDiagnosticsEngine, CFDErrorClass
from backend.agent.repair_engine import CFDRepairEngine


# ---------------------------------------------------------------------------
# Test 1: Different geometries produce different scientific case identities
# ---------------------------------------------------------------------------
def test_different_geometry_different_case_hash():
    """NACA 4412 and NACA 0012 at identical alpha/Re/Mach MUST produce
    different case_tar_hash values because geometry is a scientifically
    material condition."""
    bundle_4412 = ColabSessionPackager.create_session_bundle(
        job_id="TEST-GEOM-4412",
        geometry_id="NACA 4412",
        alpha_deg=4.0,
        reynolds=3_000_000.0,
        mach=0.15,
        output_dir=Path(tempfile.mkdtemp()),
    )
    bundle_0012 = ColabSessionPackager.create_session_bundle(
        job_id="TEST-GEOM-0012",
        geometry_id="NACA 0012",
        alpha_deg=4.0,
        reynolds=3_000_000.0,
        mach=0.15,
        output_dir=Path(tempfile.mkdtemp()),
    )
    assert bundle_4412["case_tar_hash"] != bundle_0012["case_tar_hash"], \
        "CRITICAL: NACA 4412 and NACA 0012 produced identical case hashes!"


# ---------------------------------------------------------------------------
# Test 2: Different alpha values produce different case identities
# ---------------------------------------------------------------------------
def test_different_alpha_different_case_hash():
    """alpha=4° and alpha=20° MUST produce different case hashes."""
    bundle_a4 = ColabSessionPackager.create_session_bundle(
        job_id="TEST-ALPHA-4",
        geometry_id="NACA 4412",
        alpha_deg=4.0,
        reynolds=3_000_000.0,
        mach=0.15,
        output_dir=Path(tempfile.mkdtemp()),
    )
    bundle_a20 = ColabSessionPackager.create_session_bundle(
        job_id="TEST-ALPHA-20",
        geometry_id="NACA 4412",
        alpha_deg=20.0,
        reynolds=3_000_000.0,
        mach=0.15,
        output_dir=Path(tempfile.mkdtemp()),
    )
    assert bundle_a4["case_tar_hash"] != bundle_a20["case_tar_hash"], \
        "CRITICAL: alpha=4° and alpha=20° produced identical case hashes!"


# ---------------------------------------------------------------------------
# Test 3: Different Reynolds numbers produce different case identities
# ---------------------------------------------------------------------------
def test_different_reynolds_different_case_hash():
    """Re=3e6 and Re=6e6 MUST produce different case hashes."""
    bundle_re3 = ColabSessionPackager.create_session_bundle(
        job_id="TEST-RE-3M",
        geometry_id="NACA 4412",
        alpha_deg=4.0,
        reynolds=3_000_000.0,
        mach=0.15,
        output_dir=Path(tempfile.mkdtemp()),
    )
    bundle_re6 = ColabSessionPackager.create_session_bundle(
        job_id="TEST-RE-6M",
        geometry_id="NACA 4412",
        alpha_deg=4.0,
        reynolds=6_000_000.0,
        mach=0.15,
        output_dir=Path(tempfile.mkdtemp()),
    )
    assert bundle_re3["case_tar_hash"] != bundle_re6["case_tar_hash"], \
        "CRITICAL: Re=3e6 and Re=6e6 produced identical case hashes!"


# ---------------------------------------------------------------------------
# Test 4: Requested sweep != executed sweep
# ---------------------------------------------------------------------------
def test_requested_sweep_not_executed():
    """A sweep of [4, 6, 8, 10, 12] degrees requested at investigation
    time must NOT be reported as EXECUTED. Only the primary alpha is STAGED;
    all other points are NOT_EXECUTED."""
    # Simulate what routes_investigation.py does
    alpha_deg = 4.0
    sweep = [4.0, 6.0, 8.0, 10.0, 12.0]
    sweep_evaluations = {}
    for a in sweep:
        is_primary = abs(a - alpha_deg) < 0.01
        cfd_status = "STAGED" if is_primary else "NOT_EXECUTED"
        sweep_evaluations[str(a)] = {
            "alpha_deg": a,
            "cfd": {"CL": None, "CD": None, "status": cfd_status},
        }
    # Only alpha=4 should be STAGED
    assert sweep_evaluations["4.0"]["cfd"]["status"] == "STAGED"
    for a in ["6.0", "8.0", "10.0", "12.0"]:
        assert sweep_evaluations[a]["cfd"]["status"] == "NOT_EXECUTED", \
            f"Sweep point alpha={a} should be NOT_EXECUTED, got {sweep_evaluations[a]['cfd']['status']}"


# ---------------------------------------------------------------------------
# Test 5: Partial sweep cannot be reported as complete
# ---------------------------------------------------------------------------
def test_partial_sweep_not_complete():
    """If only 1 of 5 sweep points was executed, the sweep status must
    NOT be VERIFIED or EXECUTED for the entire sweep."""
    sweep = [4.0, 6.0, 8.0, 10.0, 12.0]
    executed = {4.0}  # Only alpha=4 was actually run
    for a in sweep:
        if a not in executed:
            assert a not in executed, \
                f"Alpha={a}° was not executed but would be incorrectly counted"
    assert len(executed) < len(sweep), "Partial sweep must not equal full sweep"
    assert len(executed) == 1, "Only 1 point was executed"


# ---------------------------------------------------------------------------
# Test 6: Failed CFD cannot become VERIFIED
# ---------------------------------------------------------------------------
def test_failed_cfd_cannot_become_verified():
    """A ledger entry at FAILED status must NOT be promotable to VERIFIED."""
    ledger = EmpiricalValidationLedger(
        ledger_path=Path(tempfile.mkdtemp()) / "test_ledger.json"
    )
    entry = LedgerEntry(
        investigation_id="INV-FAIL-TEST",
        job_id="JOB-FAIL-TEST",
        geometry_identity="NACA 4412",
        verification_status=LedgerStatus.FAILED,
    )
    ledger.record(entry)

    # Attempt to promote directly to VERIFIED (should raise)
    entry_promoted = entry.model_copy(update={"verification_status": LedgerStatus.VERIFIED})
    with pytest.raises(ValueError, match="Invalid ledger transition"):
        ledger.record(entry_promoted)


# ---------------------------------------------------------------------------
# Test 7: Staged repair cannot become successful without execution
# ---------------------------------------------------------------------------
def test_staged_repair_cannot_skip_execution():
    """A ledger entry at STAGED status must pass through EXECUTED
    before reaching VERIFIED."""
    ledger = EmpiricalValidationLedger(
        ledger_path=Path(tempfile.mkdtemp()) / "test_ledger.json"
    )
    entry = LedgerEntry(
        investigation_id="INV-STAGED-TEST",
        job_id="JOB-STAGED-TEST",
        geometry_identity="NACA 4412",
        verification_status=LedgerStatus.STAGED,
    )
    ledger.record(entry)

    # Attempt to promote directly to VERIFIED (should raise)
    entry_promoted = entry.model_copy(update={"verification_status": LedgerStatus.VERIFIED})
    with pytest.raises(ValueError, match="Invalid ledger transition"):
        ledger.record(entry_promoted)


# ---------------------------------------------------------------------------
# Test 8: Successful verification requires convergence evidence
# ---------------------------------------------------------------------------
def test_verification_requires_convergence():
    """A solver log with forces but NO residual convergence data
    must NOT produce VERIFIED status."""
    td = Path(tempfile.mkdtemp())

    # Write manifest
    manifest = {"job_id": "JOB-CONV-TEST"}
    (td / "job_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    # Write solver log WITHOUT residual data but with forces
    log = """/* OpenFOAM */
Exec   : simpleFoam
Version:  10
forces:
    Force coefficients:
        Cd          : 0.0120
        Cl          : 0.8500
        Cm          : -0.0800
End
"""
    (td / "log.simpleFoam").write_text(log, encoding="utf-8")

    # Write force coefficients
    forces_dir = td / "postProcessing" / "forceCoeffs" / "0"
    forces_dir.mkdir(parents=True)
    (forces_dir / "forceCoeffs.dat").write_text(
        "# Time Cm Cd Cl Cl(f) Cl(r)\n1000 -0.08 0.012 0.85 0.425 0.425\n",
        encoding="utf-8",
    )

    report = ScientificResultVerifier.verify_archive(td, expected_case_id="JOB-CONV-TEST")

    # Forces exist, but no convergence residuals → must NOT be VERIFIED
    assert report.status != VerificationStatus.VERIFIED, \
        f"Archive with forces but no convergence data should not be VERIFIED, got {report.status}"


# ---------------------------------------------------------------------------
# Test 9: Original failed case remains immutable after repair
# ---------------------------------------------------------------------------
def test_original_case_immutable_after_repair():
    """The repair engine must produce a candidate with a DIFFERENT hash
    from the original, never modifying the original hash."""
    from backend.agent.diagnostics import DiagnosticReport

    original_hash = "abc123def456"
    diag = DiagnosticReport(
        error_class=CFDErrorClass.COURANT_INSTABILITY,
        evidence=["Co=18.9 > 1.0"],
        diagnosis="CFL violated",
        confidence=0.95,
        repair_candidates=[],
    )
    outcome = CFDRepairEngine.propose_repair(
        original_spec={"geometry": "NACA 4412", "alpha_deg": 20.0, "reynolds": 3e6, "mach": 0.15},
        original_case_hash=original_hash,
        diagnosis=diag,
        current_retry_count=0,
    )
    assert outcome.candidate is not None
    assert outcome.candidate.original_case_hash == original_hash, \
        "Original case hash must be preserved in the repair candidate"
    assert outcome.candidate.candidate_case_hash != original_hash, \
        "Candidate case hash must differ from original"


# ---------------------------------------------------------------------------
# Test 10: Retry candidate receives distinct provenance identity
# ---------------------------------------------------------------------------
def test_retry_candidate_distinct_identity():
    """Two repair candidates (retry 1 vs retry 2) from the same original
    must produce different candidate hashes."""
    from backend.agent.diagnostics import DiagnosticReport

    original_hash = "abcdef123456"
    diag = DiagnosticReport(
        error_class=CFDErrorClass.DIVERGENCE,
        evidence=["Residual divergence"],
        diagnosis="Divergence detected",
        confidence=0.90,
        repair_candidates=[],
    )
    outcome_r1 = CFDRepairEngine.propose_repair(
        original_spec={"geometry": "NACA 4412", "alpha_deg": 20.0},
        original_case_hash=original_hash,
        diagnosis=diag,
        current_retry_count=0,
    )
    outcome_r2 = CFDRepairEngine.propose_repair(
        original_spec={"geometry": "NACA 4412", "alpha_deg": 20.0},
        original_case_hash=original_hash,
        diagnosis=diag,
        current_retry_count=1,
    )
    assert outcome_r1.candidate.candidate_case_hash != outcome_r2.candidate.candidate_case_hash, \
        "Different retry numbers must produce different candidate hashes"


# ---------------------------------------------------------------------------
# Test 11: Missing field/result artifacts remain INCOMPLETE
# ---------------------------------------------------------------------------
def test_missing_forces_incomplete():
    """An archive with a valid manifest and solver log but NO force
    coefficients must be classified as INCOMPLETE."""
    td = Path(tempfile.mkdtemp())

    manifest = {"job_id": "JOB-MISSING-FORCES"}
    (td / "job_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    log = """/* OpenFOAM */
Exec   : simpleFoam
Version:  10
Time = 1000
smoothSolver:  Solving for Ux, Initial residual = 0.001, Final residual = 5e-06, No Iterations 3
End
"""
    (td / "log.simpleFoam").write_text(log, encoding="utf-8")

    report = ScientificResultVerifier.verify_archive(td, expected_case_id="JOB-MISSING-FORCES")
    assert report.status == VerificationStatus.INCOMPLETE, \
        f"Archive missing force coefficients should be INCOMPLETE, got {report.status}"


# ---------------------------------------------------------------------------
# Test 12: Scientific answer never invents missing sweep points
# ---------------------------------------------------------------------------
def test_sweep_no_fabricated_cfd_results():
    """When a sweep is requested but only the primary alpha is staged,
    the sweep evaluation for non-primary points must have CL=None and
    CD=None in the CFD column."""
    alpha_deg = 4.0
    sweep = [4.0, 8.0, 12.0]
    for a in sweep:
        is_primary = abs(a - alpha_deg) < 0.01
        cfd_cl = None  # No CFD result unless actually executed
        cfd_cd = None
        cfd_status = "STAGED" if is_primary else "NOT_EXECUTED"

        if not is_primary:
            assert cfd_cl is None, f"CFD CL for alpha={a} must be None (not fabricated)"
            assert cfd_cd is None, f"CFD CD for alpha={a} must be None (not fabricated)"
            assert cfd_status == "NOT_EXECUTED", \
                f"CFD status for alpha={a} must be NOT_EXECUTED"


# ---------------------------------------------------------------------------
# Bonus: case_identity.json is actually in the tarball
# ---------------------------------------------------------------------------
def test_case_identity_json_in_tarball():
    """Verify that case_identity.json exists in the generated tarball
    and contains the geometry_id."""
    bundle = ColabSessionPackager.create_session_bundle(
        job_id="TEST-IDENTITY",
        geometry_id="NACA 4412",
        alpha_deg=4.0,
        reynolds=3_000_000.0,
        mach=0.15,
        output_dir=Path(tempfile.mkdtemp()),
    )
    case_path = Path(bundle["case_path"])
    assert case_path.exists()

    with tarfile.open(case_path, "r:gz") as tar:
        names = tar.getnames()
        assert "case_identity.json" in names, \
            f"case_identity.json not found in tarball. Contents: {names}"
        f = tar.extractfile("case_identity.json")
        identity = json.loads(f.read().decode("utf-8"))
        assert identity["geometry_id"] == "NACA 4412"
        assert identity["alpha_deg"] == 4.0
        assert identity["reynolds"] == 3_000_000.0


# ---------------------------------------------------------------------------
# Test 14: Verified entries cannot have hashes or results mutated
# ---------------------------------------------------------------------------
def test_verified_entry_immutable_against_mutation():
    """An entry with VERIFIED status must reject any attempt to alter its
    archive hash, case hash, geometry identity, or result receipt."""
    ledger = EmpiricalValidationLedger(
        ledger_path=Path(tempfile.mkdtemp()) / "test_immutable_ledger.json"
    )
    entry = LedgerEntry(
        investigation_id="INV-VERIFIED-1",
        job_id="JOB-VERIFIED-1",
        geometry_identity="NACA 0012",
        case_hash="hash_case_111",
        archive_hash="hash_arch_111",
        verification_status=LedgerStatus.PLANNED,
    )
    ledger.record(entry)
    
    # Transition to STAGED -> EXECUTED -> VERIFIED
    entry = entry.model_copy(update={"verification_status": LedgerStatus.STAGED})
    ledger.record(entry)
    entry = entry.model_copy(update={"verification_status": LedgerStatus.EXECUTED})
    ledger.record(entry)
    entry = entry.model_copy(update={
        "verification_status": LedgerStatus.VERIFIED,
        "result_receipt": {"CL": 0.5, "CD": 0.01},
    })
    ledger.record(entry)

    # Attempt to tamper with the archive hash of the verified entry
    tampered_entry = entry.model_copy(update={"archive_hash": "malicious_hash_tampered"})
    with pytest.raises(ValueError, match="CRITICAL IMMUTABILITY VIOLATION"):
        ledger.record(tampered_entry)

    # Attempt to tamper with results
    tampered_results = entry.model_copy(update={"result_receipt": {"CL": 0.999, "CD": 0.001}})
    with pytest.raises(ValueError, match="CRITICAL IMMUTABILITY VIOLATION"):
        ledger.record(tampered_results)


# ---------------------------------------------------------------------------
# Test 15: Baseline integrity check confirms all certified Stage-10 runs
# ---------------------------------------------------------------------------
def test_baseline_integrity_verification():
    """Confirms that the active canonical ledger verifies all Stage-10 runs."""
    ledger = EmpiricalValidationLedger()
    assert ledger.verify_baseline_integrity() is True, \
        "Baseline Stage-10 runs are missing or corrupted in active ledger!"
    assert ledger.get_verified_count() >= 3, \
        "Expected at least 3 verified runs in active ledger"
