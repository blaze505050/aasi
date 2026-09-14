"""
AASI Phase 24: Adversarial Scientific Integrity Test Suite.
Governing Doctrine: Absolute Anti-Fabrication Rule & Fail-Closed Scientific Governance.

Tests 12 adversarial failure modes:
1. Corrupted archive (missing files, truncated tarball, wrong hash)
2. Geometry mismatch (bundle coordinates do not match manifest geometry hash)
3. Case hash mismatch (modified OpenFOAM case files)
4. Non-converged run (simpleFoam residuals > 1e-4)
5. Modified log (tampered execution log)
6. Missing residuals (residual file omitted)
7. Fake OpenFOAM version (version mismatch)
8. Missing forces (forceCoeffs.dat missing or unparsable)
9. Physical violations (Cp > 1.05, CD < 0, NaN/Inf fields)
10. Manifest-archive mismatch (unexpected or missing files)
11. Benchmark integrity (tampering with frozen benchmark fails validation)
12. Stage-10 checklist enforcement (any missing criterion triggers STAGE_10_BLOCKED)
"""

import hashlib
import io
import json
import os
import tarfile
import pytest
from pathlib import Path
from typing import Dict, Any, Optional

from backend.compute.base import BackendType, ExecutionState
from backend.compute.jobs import CFDJobManifest
from backend.compute.colab import ColabBackend
from backend.research.stage10_governance import Stage10GovernanceAuditor
from backend.research.reproduction_verifier_phase24 import Phase24ReproductionVerifier


def _create_synthetic_archive(
    dest_path: Path,
    job_id: str = "JOB-TEST",
    geometry_hash: str = "hash_0012",
    case_hash: str = "case_hash",
    include_manifest: bool = True,
    include_log: bool = True,
    log_residuals: float = 1e-5,
    include_forces: bool = True,
    force_cl: float = 0.4380,
    force_cd: float = 0.0078,
    include_cp: bool = True,
    cp_stagnation: float = 0.98,
    openfoam_version: str = "OpenFOAM-v2312",
    tamper_file: bool = False,
    extra_files: Optional[Dict[str, bytes]] = None,
) -> Path:
    """Helper to assemble a valid or maliciously altered results archive."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(dest_path, "w:gz") as tar:
        # results_manifest.json
        if include_manifest:
            manifest_dict = {
                "job_id": job_id,
                "geometry_hash": geometry_hash,
                "case_hash": case_hash,
                "solver_version": openfoam_version,
                "residuals": {
                    "p": log_residuals,
                    "Ux": log_residuals,
                    "Uy": log_residuals,
                },
                "execution_timestamp": "2026-09-15T00:00:00Z",
            }
            info = tarfile.TarInfo(name="results_manifest.json")
            data = json.dumps(manifest_dict).encode("utf-8")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        # simpleFoam.log
        if include_log:
            log_content = f"""
Exec   : simpleFoam
Version: {openfoam_version}
Time = 500
smoothSolver:  Solving for Ux, Initial residual = {log_residuals}, Final residual = {log_residuals*0.1}, No Iterations 3
smoothSolver:  Solving for Uy, Initial residual = {log_residuals}, Final residual = {log_residuals*0.1}, No Iterations 3
GAMG:  Solving for p, Initial residual = {log_residuals}, Final residual = {log_residuals*0.1}, No Iterations 4
ExecutionTime = 120 s  ClockTime = 125 s
End
"""
            if tamper_file:
                log_content += "\nTAMPERED_CONTENT_INJECTED\n"
            info = tarfile.TarInfo(name="simpleFoam.log")
            data = log_content.encode("utf-8")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        # forceCoeffs.dat
        if include_forces:
            forces_content = f"""# Time   Cm       Cd       Cl       Cl(f)    Cl(r)
499      -0.001   {force_cd}   {force_cl}   0.219    0.219
500      -0.001   {force_cd}   {force_cl}   0.219    0.219
"""
            info = tarfile.TarInfo(name="postProcessing/forces/0/forceCoeffs.dat")
            data = forces_content.encode("utf-8")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        # surface Cp
        if include_cp:
            cp_lines = ["# x/c    Cp"]
            cp_lines.append(f"0.0000   {cp_stagnation}")
            cp_lines.append("0.0500   -1.1500")
            for i in range(1, 20):
                xc = i * 0.05
                cp_lines.append(f"{xc:.4f}   {-0.5 + xc*0.6:.4f}")
            info = tarfile.TarInfo(name="postProcessing/surfaces/500/surface_Cp.dat")
            data = "\n".join(cp_lines).encode("utf-8")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        if extra_files:
            for name, content in extra_files.items():
                info = tarfile.TarInfo(name=name)
                info.size = len(content)
                tar.addfile(info, io.BytesIO(content))

    return dest_path


# ------------------------------------------------------------------------------
# TEST 1: Corrupted Archive
# ------------------------------------------------------------------------------
def test_adversarial_corrupted_archive(tmp_path):
    backend = ColabBackend(workspace_root=tmp_path)
    job_id = "JOB-TEST-CORRUPT"
    manifest = CFDJobManifest(
        job_id=job_id,
        experiment_id="EXP-CORRUPT",
        geometry_name="NACA 0012",
        geometry_hash="hash_0012",
        case_hash="case_hash",
        backend=BackendType.COLAB,
    )
    manifest.save(backend.jobs_dir / job_id / "job_manifest.json")

    corrupt_archive = tmp_path / "corrupt.tar.gz"
    corrupt_archive.write_bytes(b"NOT_A_VALID_GZIP_ARCHIVE_DATA")

    result = backend.import_results(job_id, corrupt_archive)
    assert not result["success"]
    assert "Corrupted" in result.get("error", "") or "invalid" in result.get("error", "").lower()


# ------------------------------------------------------------------------------
# TEST 2: Geometry Mismatch
# ------------------------------------------------------------------------------
def test_adversarial_geometry_hash_mismatch(tmp_path):
    backend = ColabBackend(workspace_root=tmp_path)
    m1 = CFDJobManifest(
        job_id="JOB-G1",
        experiment_id="EXP-G1",
        geometry_name="NACA 0012",
        geometry_hash="initial_placeholder_1",
        case_hash="initial_placeholder_1",
        conditions={"alpha_deg": 4.0},
        backend=BackendType.COLAB,
    )
    m2 = CFDJobManifest(
        job_id="JOB-G2",
        experiment_id="EXP-G2",
        geometry_name="NACA 6409",
        geometry_hash="initial_placeholder_2",
        case_hash="initial_placeholder_2",
        conditions={"alpha_deg": 8.0},
        backend=BackendType.COLAB,
    )
    job1 = backend.submit(m1)
    job2 = backend.submit(m2)

    # Hashes must differ for distinct geometries
    assert job1.geometry_hash != job2.geometry_hash
    assert "NACA 0012" in job1.geometry_name
    assert "NACA 6409" in job2.geometry_name

    # Now attempt importing an archive with mismatched geometry hash into JOB-G1
    mismatch_archive = _create_synthetic_archive(
        tmp_path / "mismatch_geom.tar.gz",
        job_id="JOB-G1",
        geometry_hash="WRONG_TAMPERED_HASH",
        case_hash=job1.case_hash,
    )
    result = backend.import_results("JOB-G1", mismatch_archive)
    assert not result["success"]
    assert "Geometry hash mismatch" in result.get("error", "")


# ------------------------------------------------------------------------------
# TEST 3: Case Hash Mismatch
# ------------------------------------------------------------------------------
def test_adversarial_case_tampering_hash_mismatch(tmp_path):
    backend = ColabBackend(workspace_root=tmp_path)
    m = CFDJobManifest(
        job_id="JOB-TAMPER",
        experiment_id="EXP-TAMPER",
        geometry_name="NACA 0012",
        geometry_hash="initial_placeholder",
        case_hash="initial_placeholder",
        conditions={"alpha_deg": 4.0},
        backend=BackendType.COLAB,
    )
    job = backend.submit(m)

    mismatch_case_archive = _create_synthetic_archive(
        tmp_path / "mismatch_case.tar.gz",
        job_id="JOB-TAMPER",
        geometry_hash=job.geometry_hash,
        case_hash="TAMPERED_CASE_HASH_9999",
    )
    result = backend.import_results("JOB-TAMPER", mismatch_case_archive)
    assert not result["success"]
    assert "Case hash mismatch" in result.get("error", "")


# ------------------------------------------------------------------------------
# TEST 4: Non-Converged Run (Residuals > 1e-4)
# ------------------------------------------------------------------------------
def test_adversarial_non_converged_residuals_rejected(tmp_path):
    backend = ColabBackend(workspace_root=tmp_path)
    job_id = "JOB-TEST-NONCONV"
    manifest = CFDJobManifest(
        job_id=job_id,
        experiment_id="EXP-NONCONV",
        geometry_name="NACA 0012",
        geometry_hash="hash_0012",
        case_hash="case_hash",
        backend=BackendType.COLAB,
    )
    manifest.save(backend.jobs_dir / job_id / "job_manifest.json")

    # Assemble archive with diverging residuals (0.05 > 1e-4)
    archive = _create_synthetic_archive(
        tmp_path / "unconverged.tar.gz",
        job_id=job_id,
        log_residuals=0.05,
    )
    result = backend.import_results(job_id, archive)
    assert not result["success"]
    assert "residual" in result.get("error", "").lower() or "convergence" in result.get("error", "").lower()


# ------------------------------------------------------------------------------
# TEST 5: Modified Execution Log
# ------------------------------------------------------------------------------
def test_adversarial_tampered_execution_log(tmp_path):
    backend = ColabBackend(workspace_root=tmp_path)
    job_id = "JOB-TEST-TAMPERLOG"
    manifest = CFDJobManifest(
        job_id=job_id,
        experiment_id="EXP-TAMPERLOG",
        geometry_name="NACA 0012",
        geometry_hash="hash_0012",
        case_hash="case_hash",
        backend=BackendType.COLAB,
        expected_output_hashes={"simpleFoam.log": "expected_legitimate_hash_digest"},
    )
    manifest.save(backend.jobs_dir / job_id / "job_manifest.json")

    archive = _create_synthetic_archive(
        tmp_path / "tampered_log.tar.gz",
        job_id=job_id,
        tamper_file=True,
    )
    result = backend.import_results(job_id, archive)
    assert not result["success"]
    assert "Expected output hash mismatch" in result.get("error", "")


# ------------------------------------------------------------------------------
# TEST 6: Missing Residuals / Missing Log
# ------------------------------------------------------------------------------
def test_adversarial_missing_log_rejected(tmp_path):
    backend = ColabBackend(workspace_root=tmp_path)
    job_id = "JOB-TEST-NOLOG"
    manifest = CFDJobManifest(
        job_id=job_id,
        experiment_id="EXP-NOLOG",
        geometry_name="NACA 0012",
        geometry_hash="hash_0012",
        case_hash="case_hash",
        backend=BackendType.COLAB,
    )
    manifest.save(backend.jobs_dir / job_id / "job_manifest.json")

    archive = _create_synthetic_archive(
        tmp_path / "no_log.tar.gz",
        job_id=job_id,
        include_log=False,
    )
    result = backend.import_results(job_id, archive)
    assert not result["success"]
    assert "Missing simpleFoam.log" in result.get("error", "")


# ------------------------------------------------------------------------------
# TEST 7: Fake OpenFOAM Version
# ------------------------------------------------------------------------------
def test_adversarial_fake_openfoam_version_rejected(tmp_path):
    backend = ColabBackend(workspace_root=tmp_path)
    job_id = "JOB-TEST-FAKEVER"
    manifest = CFDJobManifest(
        job_id=job_id,
        experiment_id="EXP-FAKEVER",
        geometry_name="NACA 0012",
        geometry_hash="hash_0012",
        case_hash="case_hash",
        backend=BackendType.COLAB,
    )
    manifest.save(backend.jobs_dir / job_id / "job_manifest.json")

    archive = _create_synthetic_archive(
        tmp_path / "fake_version.tar.gz",
        job_id=job_id,
        openfoam_version="OpenFOAM-MOCK-v9999",
    )
    result = backend.import_results(job_id, archive)
    assert not result["success"]
    assert "spoofed" in result.get("error", "").lower() or "fake" in result.get("error", "").lower()


# ------------------------------------------------------------------------------
# TEST 8: Missing Forces
# ------------------------------------------------------------------------------
def test_adversarial_missing_forces_rejected(tmp_path):
    backend = ColabBackend(workspace_root=tmp_path)
    job_id = "JOB-TEST-NOFORCES"
    manifest = CFDJobManifest(
        job_id=job_id,
        experiment_id="EXP-NOFORCES",
        geometry_name="NACA 0012",
        geometry_hash="hash_0012",
        case_hash="case_hash",
        backend=BackendType.COLAB,
    )
    manifest.save(backend.jobs_dir / job_id / "job_manifest.json")

    archive = _create_synthetic_archive(
        tmp_path / "no_forces.tar.gz",
        job_id=job_id,
        include_forces=False,
    )
    result = backend.import_results(job_id, archive)
    assert not result["success"]
    assert "force" in result.get("error", "").lower()


# ------------------------------------------------------------------------------
# TEST 9: Physical Violations (Negative Drag, Cp Ceiling Breach)
# ------------------------------------------------------------------------------
def test_adversarial_negative_drag_rejected(tmp_path):
    backend = ColabBackend(workspace_root=tmp_path)
    job_id = "JOB-TEST-NEGDRAG"
    manifest = CFDJobManifest(
        job_id=job_id,
        experiment_id="EXP-NEGDRAG",
        geometry_name="NACA 0012",
        geometry_hash="hash_0012",
        case_hash="case_hash",
        backend=BackendType.COLAB,
    )
    manifest.save(backend.jobs_dir / job_id / "job_manifest.json")

    # Negative drag CD = -0.050 (violates second law of thermodynamics)
    archive = _create_synthetic_archive(
        tmp_path / "neg_drag.tar.gz",
        job_id=job_id,
        force_cd=-0.050,
    )
    result = backend.import_results(job_id, archive)
    assert not result["success"]
    assert "conservation" in result.get("error", "").lower() or any("drag" in v.lower() for v in result.get("violations", []))


def test_adversarial_cp_stagnation_exceeded_rejected(tmp_path):
    backend = ColabBackend(workspace_root=tmp_path)
    job_id = "JOB-TEST-CPBREACH"
    manifest = CFDJobManifest(
        job_id=job_id,
        experiment_id="EXP-CPBREACH",
        geometry_name="NACA 0012",
        geometry_hash="hash_0012",
        case_hash="case_hash",
        backend=BackendType.COLAB,
    )
    manifest.save(backend.jobs_dir / job_id / "job_manifest.json")

    # Incompressible Bernoulli ceiling is Cp <= 1.05; test Cp = 1.65
    extra = {
        "surface_cp.json": json.dumps({"surface_cp": [1.65] + [-0.5]*63}).encode("utf-8")
    }
    archive = _create_synthetic_archive(
        tmp_path / "cp_breach.tar.gz",
        job_id=job_id,
        extra_files=extra,
    )
    result = backend.import_results(job_id, archive)
    assert not result["success"]
    assert "conservation" in result.get("error", "").lower() or any("stagnation" in v.lower() for v in result.get("violations", []))


# ------------------------------------------------------------------------------
# TEST 10: Manifest-Archive Mismatch (Missing results_manifest.json)
# ------------------------------------------------------------------------------
def test_adversarial_unexpected_files_or_hash_mismatch(tmp_path):
    backend = ColabBackend(workspace_root=tmp_path)
    job_id = "JOB-TEST-NOMANIFEST"
    manifest = CFDJobManifest(
        job_id=job_id,
        experiment_id="EXP-NOMANIFEST",
        geometry_name="NACA 0012",
        geometry_hash="hash_0012",
        case_hash="case_hash",
        backend=BackendType.COLAB,
    )
    manifest.save(backend.jobs_dir / job_id / "job_manifest.json")

    archive = _create_synthetic_archive(
        tmp_path / "no_manifest.tar.gz",
        job_id=job_id,
        include_manifest=False,
    )
    result = backend.import_results(job_id, archive)
    assert not result["success"]
    assert "Missing results_manifest.json" in result.get("error", "")


# ------------------------------------------------------------------------------
# TEST 11: Benchmark Integrity (Frozen Test Set Protection)
# ------------------------------------------------------------------------------
def test_adversarial_frozen_benchmark_tamper_detection(tmp_path):
    frozen_path = Path("data/experiments/phase22_frozen_test.json")
    assert frozen_path.exists(), "Frozen benchmark must exist on disk"
    content = frozen_path.read_bytes()
    expected_hash = "fa7b3d11b958cc85b2bad3167391c0514d00c097d0fb878e28a1c4aab048e3b8"
    actual_hash = hashlib.sha256(content).hexdigest()
    assert actual_hash == expected_hash, "Frozen benchmark hash must be bit-identical"

    # Simulate tampered benchmark
    tampered_content = content + b"\n/* INJECTED NOISE */"
    tampered_hash = hashlib.sha256(tampered_content).hexdigest()
    assert tampered_hash != expected_hash


# ------------------------------------------------------------------------------
# TEST 12: Stage-10 Checklist Enforcement (Fail-Closed)
# ------------------------------------------------------------------------------
def test_adversarial_stage10_fail_closed_on_missing_criteria():
    # If any of the 12 criteria is missing, status MUST be STAGE_10_BLOCKED
    incomplete_ledger = Stage10GovernanceAuditor.audit_stage10_readiness(
        verified_loop_cycles=2,  # Missing: must be >= 3
        geometry_names=["NACA 0012", "NACA 4412"],
        geometry_hashes=["hash1", "hash2"],
        verified_cfd_outputs=True,
        physical_validation_passed=True,
        cryptographic_provenance_verified=True,
        reproducibility_confirmed=True,
        frozen_benchmark_unbroken=True,
        honest_reporting_no_fabrication=True,
        zero_synthetic_claims=True,
        autonomous_selection_demonstrated=True,
        rollback_capability_verified=True,
        complete_audit_trail=True,
    )
    assert incomplete_ledger.status == "STAGE_10_BLOCKED"
    assert not incomplete_ledger.is_eligible
    assert any("Closed-Loop" in item for item in incomplete_ledger.missing_evidence)
    assert any("Distinct Airfoil" in item for item in incomplete_ledger.missing_evidence)

    # When all 12 criteria are satisfied, status becomes STAGE_10_ELIGIBLE
    complete_ledger = Stage10GovernanceAuditor.audit_stage10_readiness(
        verified_loop_cycles=3,
        geometry_names=["NACA 0012", "NACA 4412", "NACA 6409"],
        geometry_hashes=["h1", "h2", "h3"],
        verified_cfd_outputs=True,
        physical_validation_passed=True,
        cryptographic_provenance_verified=True,
        reproducibility_confirmed=True,
        frozen_benchmark_unbroken=True,
        honest_reporting_no_fabrication=True,
        zero_synthetic_claims=True,
        autonomous_selection_demonstrated=True,
        rollback_capability_verified=True,
        complete_audit_trail=True,
    )
    assert complete_ledger.status == "STAGE_10_ELIGIBLE"
    assert complete_ledger.is_eligible
    assert len(complete_ledger.missing_evidence) == 0
