"""
AASI Milestone 3: Colab Fallback & Notebook Generation Test Suite.
Tests:
- Generation of AASI_Colab_<JOB>.ipynb
- All 9 required scientific steps (environment setup, exact case retrieval,
  execution, logs, residuals, forces, manifest, SHA-256 checksums, upload-ready archive)
- Strict Anti-Fabrication Rule: The notebook must NEVER declare VERIFIED.
- Cryptographic provenance and case deck integrity.
"""

import sys
import json
import tarfile
from pathlib import Path
import pytest

WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from backend.compute.colab_session import ColabSessionPackager


# ---------------------------------------------------------------------------
# Test 1: AASI_Colab_<JOB>.ipynb Naming & Dual Alias Generation
# ---------------------------------------------------------------------------
def test_colab_notebook_named_generation(tmp_path):
    """M3 requirement: Generate AASI_Colab_<JOB>.ipynb with backward compatibility."""
    job_id = "JOB-M3-TEST-001"
    out_dir = tmp_path / job_id
    bundle = ColabSessionPackager.create_session_bundle(
        job_id=job_id,
        geometry_id="NACA 0012",
        alpha_deg=4.0,
        reynolds=3e6,
        mach=0.15,
        output_dir=out_dir,
    )

    # 1. Check named notebook exists
    named_nb = out_dir / f"AASI_Colab_{job_id}.ipynb"
    assert named_nb.exists(), f"Expected {named_nb.name} to be generated."
    assert bundle["colab_notebook_name"] == f"AASI_Colab_{job_id}.ipynb"
    assert bundle["notebook_path"] == str(named_nb)

    # 2. Check backward compatibility notebook.ipynb exists
    legacy_nb = out_dir / "notebook.ipynb"
    assert legacy_nb.exists(), "Legacy notebook.ipynb must also be maintained."
    assert bundle["legacy_notebook_path"] == str(legacy_nb)

    # Content must match
    assert named_nb.read_text(encoding="utf-8") == legacy_nb.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 2: Full 9-Step Scientific Workflow in Notebook
# ---------------------------------------------------------------------------
def test_colab_notebook_contains_all_9_scientific_steps(tmp_path):
    """Verifies that generated notebook contains all 9 required operational steps."""
    job_id = "JOB-M3-STEPS-002"
    bundle = ColabSessionPackager.create_session_bundle(
        job_id=job_id,
        geometry_id="NACA 4412",
        alpha_deg=8.0,
        reynolds=6e6,
        mach=0.15,
        output_dir=tmp_path / job_id,
    )

    nb_data = json.loads(Path(bundle["notebook_path"]).read_text(encoding="utf-8"))
    cells = nb_data["cells"]
    nb_full_text = json.dumps(nb_data)

    # Step 1: Environment Setup
    assert "openfoam10" in nb_full_text
    assert "apt-get install" in nb_full_text

    # Step 2: Exact Case Retrieval & Case Hash Verification
    assert "EXPECTED_CASE_HASH" in nb_full_text
    assert bundle["case_tar_hash"] in nb_full_text
    assert "case.tar.gz" in nb_full_text

    # Step 3: Solver Execution & Process Tracking
    assert "blockMesh" in nb_full_text
    assert "simpleFoam" in nb_full_text
    assert "log.simpleFoam" in nb_full_text

    # Step 4: Residual Extraction & Convergence Check
    assert "residual_pattern" in nb_full_text
    assert "Solving for (Ux|Uy|p|k|omega" in nb_full_text
    assert "1e-4" in nb_full_text  # Monotonic convergence threshold

    # Step 5: Aerodynamic Force Extraction
    assert "forceCoeffs.dat" in nb_full_text
    assert "CL" in nb_full_text
    assert "CD" in nb_full_text
    assert "CM" in nb_full_text

    # Step 6: Execution Manifest Generation
    assert "job_manifest.json" in nb_full_text
    assert "execution_duration_sec" in nb_full_text

    # Step 7: SHA-256 Packaging & Checksums
    assert f"results_{job_id}.tar.gz" in nb_full_text
    assert "checksums.sha256" in nb_full_text
    assert "hashlib.sha256" in nb_full_text

    # Step 8: Upload-Ready Archive & Colab Download Trigger
    assert "files.download" in nb_full_text


# ---------------------------------------------------------------------------
# Test 3: CRITICAL RULE — Notebook NEVER Declares VERIFIED
# ---------------------------------------------------------------------------
def test_colab_notebook_never_declares_verified(tmp_path):
    """
    CRITICAL TRUTH RULE: The Colab notebook must NEVER declare status: VERIFIED.
    It must state EXECUTED / USER_EXECUTED_UNVERIFIED and specify that verification
    is exclusively performed by AASI server verification upon ingestion.
    """
    job_id = "JOB-M3-ANTI-FABRICATION-003"
    bundle = ColabSessionPackager.create_session_bundle(
        job_id=job_id,
        geometry_id="NACA 0012",
        alpha_deg=6.0,
        reynolds=3e6,
        mach=0.15,
        output_dir=tmp_path / job_id,
    )

    nb_data = json.loads(Path(bundle["notebook_path"]).read_text(encoding="utf-8"))
    nb_full_text = json.dumps(nb_data)

    # 1. Must NOT declare verified status in manifest template
    assert "'status': 'EXECUTED'" in nb_full_text or '"status": "EXECUTED"' in nb_full_text
    assert "'verified': False" in nb_full_text or '"verified": false' in nb_full_text
    assert "status: VERIFIED" not in nb_full_text
    assert '"status": "VERIFIED"' not in nb_full_text
    assert "'status': 'VERIFIED'" not in nb_full_text

    # 2. Must explicitly disclaim verification
    assert "NOT VERIFIED" in nb_full_text
    assert "AASI server verification" in nb_full_text


# ---------------------------------------------------------------------------
# Test 4: Case Tarball Provenance & Integrity
# ---------------------------------------------------------------------------
def test_case_deck_contains_complete_openfoam_structure(tmp_path):
    """Confirms case.tar.gz contains all canonical OpenFOAM and identity files."""
    job_id = "JOB-M3-CASE-004"
    bundle = ColabSessionPackager.create_session_bundle(
        job_id=job_id,
        geometry_id="NACA 0012",
        alpha_deg=5.0,
        reynolds=3.5e6,
        mach=0.15,
        output_dir=tmp_path / job_id,
    )

    case_path = Path(bundle["case_path"])
    with tarfile.open(case_path, "r:gz") as tar:
        names = tar.getnames()
        expected = [
            "case_identity.json",
            "0/U",
            "0/p",
            "0/k",
            "0/omega",
            "constant/transportProperties",
            "constant/turbulenceProperties",
            "system/controlDict",
        ]
        for exp in expected:
            assert exp in names, f"Missing {exp} in generated case tarball."

        # Verify case_identity.json contents
        f = tar.extractfile("case_identity.json")
        identity = json.loads(f.read().decode("utf-8"))
        assert identity["geometry_id"] == "NACA 0012"
        assert identity["alpha_deg"] == 5.0
        assert identity["reynolds"] == 3.5e6
        assert identity["solver"] == "simpleFoam"


# ---------------------------------------------------------------------------
# Test 5: Dual Manifest & Archive Packaging in Generated Notebook
# ---------------------------------------------------------------------------
def test_notebook_dual_manifest_generation(tmp_path):
    """Ensures notebook creates both job_manifest.json and results_manifest.json."""
    job_id = "JOB-M3-DUAL-005"
    bundle = ColabSessionPackager.create_session_bundle(
        job_id=job_id,
        geometry_id="NACA 0012",
        alpha_deg=4.0,
        reynolds=3e6,
        output_dir=tmp_path / job_id,
    )
    nb_data = json.loads(Path(bundle["notebook_path"]).read_text(encoding="utf-8"))
    nb_text = json.dumps(nb_data)

    assert "job_manifest.json" in nb_text
    assert "results_manifest.json" in nb_text
    assert "checksums.sha256" in nb_text


# ---------------------------------------------------------------------------
# Test 6: Scientific Ingestion Verification of Returned Colab Archive
# ---------------------------------------------------------------------------
def test_simulated_colab_results_archive_verified_by_scientific_verifier(tmp_path):
    """
    Simulates authentic Colab execution output:
    Creates a results archive with valid OpenFOAM logs, residual decay < 1e-4,
    force polar CD > 0, and job_manifest.json (status: EXECUTED).
    Verifies that AASI ScientificResultVerifier audits and confirms VERIFIED.
    """
    from backend.science.verification import ScientificResultVerifier, VerificationStatus
    import hashlib

    job_id = "JOB-M3-COLAB-EXEC-006"
    sim_dir = tmp_path / job_id
    sim_dir.mkdir(parents=True, exist_ok=True)

    # 1. Authentic solver log with version banner and converged residuals
    solver_log_content = """
/*---------------------------------------------------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  10                                    |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.org                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
Exec   : simpleFoam
Date   : Sep 20 2026
Time   : 12:00:00
Host   : "colab-worker-gpu-01"
PID    : 1042

Time = 500
Solving for Ux, Initial residual = 0.0012, Final residual = 8.4e-05, No Iterations 3
Solving for Uy, Initial residual = 0.0009, Final residual = 6.2e-05, No Iterations 3
Solving for p, Initial residual = 0.0035, Final residual = 7.1e-05, No Iterations 5
Solving for k, Initial residual = 0.0004, Final residual = 4.5e-05, No Iterations 2
Solving for omega, Initial residual = 0.0005, Final residual = 3.9e-05, No Iterations 2
ExecutionTime = 42.1 s  ClockTime = 43 s

End
"""
    (sim_dir / "log.simpleFoam").write_text(solver_log_content, encoding="utf-8")

    # 2. Force coefficients directory
    forces_dir = sim_dir / "postProcessing" / "forceCoeffs" / "0"
    forces_dir.mkdir(parents=True, exist_ok=True)
    forces_content = """# Time  Cm  Cd  Cl  Cl(f)  Cl(r)
500  -0.015  0.0082  0.425  0.210  0.215
"""
    (forces_dir / "forceCoeffs.dat").write_text(forces_content, encoding="utf-8")

    # 3. Execution manifest strictly stating EXECUTED, never VERIFIED
    manifest = {
        "job_id": job_id,
        "geometry_id": "NACA 0012",
        "alpha_deg": 4.0,
        "reynolds": 3.0e6,
        "mach": 0.15,
        "status": "EXECUTED",
        "verified": False,
        "epistemic_class": "USER_EXECUTED_UNVERIFIED",
    }
    (sim_dir / "job_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (sim_dir / "results_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # 4. Package into results archive
    archive_path = tmp_path / f"results_{job_id}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(sim_dir / "log.simpleFoam", arcname="log.simpleFoam")
        tar.add(sim_dir / "job_manifest.json", arcname="job_manifest.json")
        tar.add(sim_dir / "results_manifest.json", arcname="results_manifest.json")
        tar.add(sim_dir / "postProcessing", arcname="postProcessing")

    # 5. Run scientific verification audit
    report = ScientificResultVerifier.verify_archive(
        archive_dir=archive_path,
        expected_case_id=job_id,
    )

    assert report.is_verified is True
    assert report.status == VerificationStatus.VERIFIED
    assert report.parsed_polars["CL"] == 0.425
    assert report.parsed_polars["CD"] == 0.0082
    assert report.parsed_polars["CM"] == -0.015
    assert report.solver_name == "OpenFOAM simpleFoam"
    assert report.solver_version == "10"


# ---------------------------------------------------------------------------
# Test 7: Anti-Fabrication Rejection on Physical Invariant Violation (CD <= 0)
# ---------------------------------------------------------------------------
def test_simulated_colab_results_archive_negative_drag_rejected(tmp_path):
    """Verifies that an archive with non-physical negative drag (CD <= 0) is rejected."""
    from backend.science.verification import ScientificResultVerifier, VerificationStatus

    job_id = "JOB-M3-PHYS-FAIL-007"
    sim_dir = tmp_path / job_id
    sim_dir.mkdir(parents=True, exist_ok=True)

    solver_log = "OpenFOAM: The Open Source CFD Toolbox\nVersion: 10\nsimpleFoam\nSolving for p, Initial residual = 0.01, Final residual = 1e-05, No Iterations 5\nEnd\n"
    (sim_dir / "log.simpleFoam").write_text(solver_log, encoding="utf-8")

    forces_dir = sim_dir / "postProcessing" / "forceCoeffs" / "0"
    forces_dir.mkdir(parents=True, exist_ok=True)
    # Non-physical negative drag
    (forces_dir / "forceCoeffs.dat").write_text("# Time Cm Cd Cl\n500 0.0 -0.005 0.50\n", encoding="utf-8")

    manifest = {"job_id": job_id, "status": "EXECUTED", "verified": False}
    (sim_dir / "job_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    archive_path = tmp_path / f"results_{job_id}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(sim_dir / "log.simpleFoam", arcname="log.simpleFoam")
        tar.add(sim_dir / "job_manifest.json", arcname="job_manifest.json")
        tar.add(sim_dir / "postProcessing", arcname="postProcessing")

    report = ScientificResultVerifier.verify_archive(archive_path, expected_case_id=job_id)
    assert report.is_verified is False
    assert report.status == VerificationStatus.INVALID
    assert any("non-positive" in r or "negative drag" in r.lower() for r in report.failure_reasons)


# ---------------------------------------------------------------------------
# Test 8: Colab Packaging and Download FastAPI Endpoints
# ---------------------------------------------------------------------------
def test_colab_fastapi_packaging_and_download_endpoints():
    """Tests the /api/compute/colab/package, /jobs/{id}/notebook, and /jobs/{id}/case endpoints."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    job_id = "JOB-API-COLAB-TEST-008"

    # 1. Package Colab bundle
    pkg_resp = client.post(
        "/api/compute/colab/package",
        json={
            "job_id": job_id,
            "geometry_id": "NACA 2412",
            "alpha_deg": 6.0,
            "reynolds": 4.5e6,
            "mach": 0.15,
        },
    )
    assert pkg_resp.status_code == 200
    data = pkg_resp.json()
    assert data["job_id"] == job_id
    assert data["colab_notebook_name"] == f"AASI_Colab_{job_id}.ipynb"
    assert "case_tar_hash" in data

    # 2. Download Notebook (.ipynb)
    nb_resp = client.get(f"/api/compute/jobs/{job_id}/notebook")
    assert nb_resp.status_code == 200
    nb_json = nb_resp.json()
    assert nb_json["nbformat"] == 4
    assert len(nb_json["cells"]) >= 8

    # 3. Download Case Tarball (.tar.gz)
    case_resp = client.get(f"/api/compute/jobs/{job_id}/case")
    assert case_resp.status_code == 200
    assert len(case_resp.content) > 100
    assert case_resp.headers["content-type"] == "application/gzip"

