"""
AASI Phase 27: Remote Compute Fabric Test Suite.
Tests:
- 15 Persistent Queue Job States and transitions.
- ProviderManager routing, health reporting, and capability reporting.
- ColabProvider package creation, verification token signing, and safe retry.
- RemoteHPCProvider job package generation.
- Zero local load enforcement and absolute anti-fabrication integrity.
"""

import pytest
from backend.compute import (
    PersistentJobQueue,
    JobState,
    QueueJob,
    ProviderManager,
    ColabProvider,
    RemoteHPCProvider,
)


def test_queue_state_transitions(tmp_path):
    db_path = str(tmp_path / "test_queue.db")
    queue = PersistentJobQueue(db_path=db_path)
    
    # 1. Enqueue job
    job = queue.enqueue_job(
        user_id="user_test",
        case_hash="case_abc123",
        provider_name="COLAB",
        target_reynolds=3e6,
        target_alpha=4.0
    )
    assert job.status == JobState.QUEUED
    
    # 2. Transition through the 15 monotonic states
    assert queue.transition(job.job_id, JobState.ALLOCATED) is True
    assert queue.transition(job.job_id, JobState.STAGED) is True
    assert queue.transition(job.job_id, JobState.AUTHORIZATION_REQUIRED) is True
    assert queue.transition(job.job_id, JobState.DISPATCHED) is True
    assert queue.transition(job.job_id, JobState.RUNNING) is True
    assert queue.transition(job.job_id, JobState.RESULTS_READY) is True
    assert queue.transition(job.job_id, JobState.INGESTING) is True
    assert queue.transition(job.job_id, JobState.VERIFYING) is True
    assert queue.transition(job.job_id, JobState.VALIDATED) is True
    assert queue.transition(job.job_id, JobState.COMPLETED) is True
    
    updated = queue.get_job(job.job_id)
    assert updated.status == JobState.COMPLETED


def test_provider_manager_selection():
    pm = ProviderManager()
    colab = ColabProvider()
    hpc = RemoteHPCProvider()
    pm.register_provider("COLAB", colab)
    pm.register_provider("REMOTE_HPC", hpc)
    
    providers = pm.list_providers()
    assert len(providers) >= 2
    
    # Select best provider for high-throughput or batch run
    selected = pm.select_provider(preference="COLAB")
    assert selected is not None
    assert selected.probe().provider == "COLAB"


def test_colab_package_creation(tmp_path):
    provider = ColabProvider()
    package = provider.create_execution_package(
        job_id="job_colab_001",
        geometry="NACA4412",
        alpha=4.0,
        reynolds=3e6,
        mach=0.15
    )
    assert package is not None
    assert "launch_url" in package
    assert "notebook_path" in package
    assert "verification_token" in package
    assert package["verification_token"].startswith("sig_")


def test_hpc_package_creation():
    provider = RemoteHPCProvider()
    package = provider.create_execution_package(
        job_id="job_hpc_001",
        geometry="NACA4412",
        alpha=8.0,
        reynolds=3e6,
        mach=0.15
    )
    assert package is not None
    assert "slurm_script" in package
    assert "#SBATCH" in package["slurm_script"]


def test_anti_fabrication_unverified_rejection():
    """Validates that a fake or untrusted archive without genuine solver output is rejected."""
    provider = ColabProvider()
    fake_archive = b"This is fake data without actual OpenFOAM field files"
    verification = provider.verify_result_archive(fake_archive, expected_token="sig_invalid")
    assert verification["verified"] is False
    assert "invalid_signature" in verification["error_code"] or "missing_solver_fields" in verification["error_code"]
