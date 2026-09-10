"""
Tests for AASI Compute Backend Abstraction & User-Executed CFD Workflow.
"""

import os
import shutil
import pytest
from backend.compute.models import (
    ComputeBackendType,
    ComputeRequest,
    UploadedArtifactPayload,
    ExecutionStatus,
)
from backend.compute.registry import ComputeBackendRegistry
from backend.compute.user_provided import UserProvidedCaseGenerator
from backend.compute.artifacts import ArtifactIngestionService


def test_user_executed_case_generator_all_sections():
    """Verifies that UserProvidedCaseGenerator generates a complete aasi_case/ directory with all 14 README sections."""
    generator = UserProvidedCaseGenerator(base_output_dir="data/test_cases")
    req = ComputeRequest(
        case_id="TEST-USER-CASE-001",
        geometry="NACA 0012",
        mach=0.15,
        reynolds=3000000.0,
        aoa_deg=4.0,
        backend=ComputeBackendType.USER_EXECUTED
    )
    deck = generator.generate_case(req)

    assert os.path.exists(deck.case_directory)
    assert os.path.exists(deck.readme_path)
    assert os.path.exists(deck.manifest_path)
    assert os.path.exists(deck.validation_checklist_path)

    # Check that dictionaries exist
    assert os.path.exists(os.path.join(deck.case_directory, "0", "U"))
    assert os.path.exists(os.path.join(deck.case_directory, "0", "p"))
    assert os.path.exists(os.path.join(deck.case_directory, "constant", "transportProperties"))
    assert os.path.exists(os.path.join(deck.case_directory, "system", "controlDict"))
    assert os.path.exists(os.path.join(deck.case_directory, "system", "blockMeshDict"))

    # Check that scripts exist
    for sp in deck.script_paths:
        assert os.path.exists(sp)

    # Verify all 14 mandatory sections in README.md
    with open(deck.readme_path, "r", encoding="utf-8") as f:
        readme_text = f.read()

    mandatory_sections = [
        "1. Software Requirement",
        "2. OpenFOAM Version Compatibility",
        "3. Case Description",
        "4. Geometry",
        "5. Boundary Conditions",
        "6. Mesh Instructions",
        "7. Solver",
        "8. Turbulence Model",
        "9. Run Commands",
        "10. Expected Outputs",
        "11. Convergence Criteria",
        "12. Post-Processing Commands",
        "13. Files to Upload Back to AASI",
        "14. Validation Procedure"
    ]
    for sec in mandatory_sections:
        assert sec in readme_text, f"Missing mandatory README section: {sec}"

    # Clean up test output
    shutil.rmtree(deck.case_directory, ignore_errors=True)


def test_compute_registry_dispatch():
    """Tests routing through ComputeBackendRegistry."""
    registry = ComputeBackendRegistry()
    req = ComputeRequest(
        case_id="REGISTRY-TEST-001",
        geometry="NACA 0012",
        backend=ComputeBackendType.USER_EXECUTED
    )
    res = registry.dispatch(req)
    assert res["backend"] == "USER_EXECUTED"
    assert res["status"] == ExecutionStatus.AWAITING_USER_UPLOAD.value
    assert "case_deck" in res
    assert "instructions" in res
    shutil.rmtree(res["case_deck"]["case_directory"], ignore_errors=True)


def test_remote_backend_slurm_script():
    """Tests Slurm script generation for remote institutional clusters."""
    registry = ComputeBackendRegistry()
    req = ComputeRequest(
        case_id="SLURM-TEST-001",
        geometry="NACA 0012",
        backend=ComputeBackendType.REMOTE
    )
    res = registry.dispatch(req)
    assert res["backend"] == "REMOTE"
    assert "#SBATCH --job-name=aasi_SLURM-TEST-001" in res["slurm_script"]
    assert "simpleFoam" in res["slurm_script"]
    assert "cluster.nitk.ac.in" in res["ssh_command"]
    shutil.rmtree(res["case_deck"]["case_directory"], ignore_errors=True)


def test_artifact_ingestion_openfoam():
    """Tests parsing user-uploaded OpenFOAM force coefficient log."""
    service = ArtifactIngestionService()
    mock_log = """# Time        Cd            Cl            Cm
100           0.01250       0.3500        -0.010
500           0.00810       0.4350        -0.012
1000          0.00762       0.4410        -0.0123
"""
    payload = UploadedArtifactPayload(
        case_id="TEST-CASE-UPLOAD",
        solver="openfoam",
        file_name="coefficient.dat",
        file_content=mock_log
    )
    res = service.ingest_artifact(payload)
    assert res.status == "INGESTED"
    assert res.coefficients.get("cd") == pytest.approx(0.00762, abs=1e-5)
    assert res.coefficients.get("cl") == pytest.approx(0.4410, abs=1e-4)
    assert res.coefficients.get("cm") == pytest.approx(-0.0123, abs=1e-4)
    assert res.validation_status == "VALIDATED"
    assert len(res.provenance_hash) == 64


def test_artifact_ingestion_physical_bounds_warning():
    """Tests that unphysical aerodynamic values (e.g. negative drag) trigger warnings."""
    service = ArtifactIngestionService()
    bad_log = "Time  Cd  Cl  Cm\n100 -0.05 5.5 0.0"
    payload = UploadedArtifactPayload(
        case_id="BAD-TEST-CASE",
        solver="openfoam",
        file_name="coefficient.dat",
        file_content=bad_log
    )
    res = service.ingest_artifact(payload)
    assert res.validation_status in ["PHYSICAL_ANOMALY", "SUSPICIOUS_HIGH_LIFT"]
    assert any("Negative drag" in note or "exceeds" in note for note in res.validation_notes)
