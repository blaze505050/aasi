"""
AASI Phase 26 Google Colab Workflow & Monitor Test Suite.
Verifies compliant one-click session packaging, notebook synthesis,
state disambiguation, and monitor event streams.
"""

import pytest
import json
import tarfile
import io
from pathlib import Path
from backend.compute.colab_session import ColabSessionPackager
from backend.compute.monitor import (
    RemoteExecutionMonitor,
    ExecutionMilestone,
    CoarseState,
)


def test_colab_session_bundle_synthesis(tmp_path):
    """Verify Colab session generates manifest, notebook, and valid case tarball."""
    job_id = "JOB-TEST-COLAB-001"
    bundle = ColabSessionPackager.create_session_bundle(
        job_id=job_id,
        geometry_id="NACA 4412",
        alpha_deg=6.0,
        reynolds=3e6,
        mach=0.15,
        output_dir=tmp_path / job_id,
    )

    assert bundle["status"] == "COLAB_BUNDLE_READY"
    assert Path(bundle["manifest_path"]).exists()
    assert Path(bundle["case_path"]).exists()
    assert Path(bundle["notebook_path"]).exists()

    # Verify manifest
    manifest_data = json.loads(Path(bundle["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest_data["job_id"] == job_id
    assert manifest_data["geometry_id"] == "NACA 4412"
    assert manifest_data["execution_policy"] == "COLAB_USER_AUTHORIZED_ONE_CLICK"

    # Verify notebook content
    nb_data = json.loads(Path(bundle["notebook_path"]).read_text(encoding="utf-8"))
    assert len(nb_data["cells"]) >= 4
    # Check that commands are included (no manual copy required)
    nb_text = json.dumps(nb_data)
    assert "openfoam10" in nb_text
    assert "simpleFoam" in nb_text
    assert "results.tar.gz" in nb_text

    # Verify case.tar.gz contains 0/, constant/, system/
    with tarfile.open(bundle["case_path"], "r:gz") as tar:
        names = tar.getnames()
        assert "0/U" in names
        assert "0/p" in names
        assert "constant/transportProperties" in names
        assert "system/controlDict" in names


def test_colab_state_disambiguation():
    """Verify distinct Colab execution states are never collapsed."""
    from backend.agent.scientific_state import ColabExecutionState

    states = [
        ColabExecutionState.COLAB_BUNDLE_READY,
        ColabExecutionState.COLAB_EXECUTED,
        ColabExecutionState.RESULTS_IMPORTED,
        ColabExecutionState.RESULTS_VERIFIED,
        ColabExecutionState.EXECUTION_UNVERIFIED,
    ]

    # Verify distinctness
    values = [s.value for s in states]
    assert len(values) == len(set(values))
    assert ColabExecutionState.COLAB_BUNDLE_READY != ColabExecutionState.COLAB_EXECUTED
    assert ColabExecutionState.COLAB_EXECUTED != ColabExecutionState.RESULTS_IMPORTED
    assert ColabExecutionState.RESULTS_IMPORTED != ColabExecutionState.RESULTS_VERIFIED


def test_remote_execution_monitor_progression():
    """Verify monitor records milestones and sets coarse fallbacks."""
    job_id = "JOB-MONITOR-001"
    rec = RemoteExecutionMonitor.register_job(job_id, backend="GOOGLE_COLAB")
    assert rec.coarse_state == CoarseState.USER_ACTION_REQUIRED
    assert rec.current_milestone == ExecutionMilestone.QUEUED

    # Update event
    event = RemoteExecutionMonitor.record_event(
        job_id=job_id,
        milestone=ExecutionMilestone.SOLVER_RUNNING,
        description="simpleFoam iterative solve active",
        progress_pct=60,
    )
    assert event.milestone == ExecutionMilestone.SOLVER_RUNNING

    status = RemoteExecutionMonitor.get_job_status(job_id)
    assert status.current_milestone == ExecutionMilestone.SOLVER_RUNNING
    assert status.coarse_state == CoarseState.RUNNING
    assert status.progress_pct == 60

    # Complete
    RemoteExecutionMonitor.record_event(
        job_id=job_id,
        milestone=ExecutionMilestone.VERIFIED,
        description="Results verified successfully",
        progress_pct=100,
    )
    final_status = RemoteExecutionMonitor.get_job_status(job_id)
    assert final_status.coarse_state == CoarseState.COMPLETED
    assert final_status.progress_pct == 100
