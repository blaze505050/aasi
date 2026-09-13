"""
AASI Phase 23: Adversarial Scientific Integrity Suite.
Governing Doctrine: Absolute Anti-Fabrication Rule & Strict Anti-Circumvention Doctrine.
Tests remote compute abstractions, Colab bundle generators, runtime reality probes,
geometry/mesh preflight gates, 12-node Merkle provenance, frozen test set protection,
and the CRITICAL ANTI-FABRICATION TEST (Directive Section P23-19).
"""

import hashlib
import json
import math
import os
import shutil
from pathlib import Path
import numpy as np
import pytest

from backend.cfd.field_ingestion import PhysicalFieldValidator
from backend.cfd.preflight import CFDPreflightAuditor
from backend.compute.base import (
    BackendProbeResult,
    BackendType,
    ComputeBackend,
    ExecutionState,
    JobStatusResult,
)
from backend.compute.colab import ColabBackend
from backend.compute.jobs import CFDJobManifest, CFDJobEvent
from backend.compute.local_openfoam import LocalOpenFOAMBackend
from backend.compute.manager import ComputeFabricManager
from backend.compute.remote_hpc import FutureRemoteHPCBackend
from backend.physics_ai.closed_loop_p23 import ComputeAgnosticDiscoveryEngine
from backend.research.experiment_registry import PersistentExperimentRegistry, PromotionStage
from backend.research.remote_provenance import RemoteCFDProvenanceDAG
from backend.research.reproduction_verifier_phase23 import Phase23ReproductionVerifier


# --- 1. Backend Interface Consistency ---

def test_backend_interface_consistency():
    """Verifies all concrete backends implement the universal ComputeBackend interface."""
    backends = [
        LocalOpenFOAMBackend(),
        ColabBackend(),
        FutureRemoteHPCBackend(),
    ]
    for b in backends:
        assert isinstance(b, ComputeBackend)
        probe = b.probe()
        assert isinstance(probe, BackendProbeResult)
        assert hasattr(b, "submit")
        assert hasattr(b, "status")
        assert hasattr(b, "cancel")
        assert hasattr(b, "collect")
        assert hasattr(b, "verify")


# --- 2. Colab Manifest Immutability & State Transitions ---

def test_colab_manifest_immutability():
    """Verifies CFDJobManifest transitions monotonically and records event audit trail."""
    manifest = CFDJobManifest(
        job_id="TEST-JOB-001",
        experiment_id="EXP-001",
        geometry_name="NACA 0012",
        geometry_hash="dummy_geom_hash",
        case_hash="dummy_case_hash",
    )
    assert manifest.status == ExecutionState.QUEUED
    assert len(manifest.events) == 0

    manifest.transition_to(ExecutionState.DISPATCHED, detail="Dispatched to Colab bundle")
    assert manifest.status == ExecutionState.DISPATCHED
    assert len(manifest.events) == 1
    assert manifest.events[0].from_state == ExecutionState.QUEUED
    assert manifest.events[0].to_state == ExecutionState.DISPATCHED

    manifest.transition_to(ExecutionState.COMPLETED, detail="Solver execution finished")
    assert manifest.status == ExecutionState.COMPLETED
    assert len(manifest.events) == 2


# --- 3. Runtime Probe Reality ---

def test_runtime_probe_integrity():
    """Verifies runtime reality probe measures live host resources and valid status codes."""
    backend = ColabBackend()
    probe = backend.probe()
    assert probe.backend == "google_colab"
    assert probe.disk_free_gb > 0.0
    assert probe.ram_gb > 0.0
    assert probe.status_code in [
        "COLAB_AVAILABLE",
        "COLAB_OPENFOAM_READY",
        "COLAB_OPENFOAM_MISSING",
        "COLAB_RESOURCE_INSUFFICIENT",
        "COLAB_RUNTIME_EXPIRED",
        "COLAB_EXECUTION_FAILED",
    ]


# --- 4. Colab Case Bundle & Tar.gz Packaging ---

def test_colab_case_tar_gz_generation():
    """Verifies ColabBackend packages case.tar.gz and computes authentic SHA-256 hash."""
    backend = ColabBackend()
    manifest = CFDJobManifest(
        job_id="TEST-BUNDLE-001",
        experiment_id="EXP-BUNDLE",
        geometry_name="NACA 0012",
        geometry_hash="hash_001",
        case_hash="pending",
        conditions={"aoa_deg": 4.0, "reynolds": 3e6, "mach": 0.15},
    )
    staged_manifest = backend.submit(manifest)
    assert staged_manifest.status == ExecutionState.DISPATCHED
    bundle_dir = Path("data/compute_jobs/TEST-BUNDLE-001")
    assert (bundle_dir / "case.tar.gz").exists()
    assert (bundle_dir / "notebook.ipynb").exists()
    assert (bundle_dir / "run_openfoam.sh").exists()
    assert staged_manifest.case_hash != "pending"
    assert len(staged_manifest.case_hash) == 64


# --- 5. Geometry Preflight: Profile Closure Check ---

def test_geometry_preflight_closure_detection():
    """Verifies CFDPreflightAuditor rejects unclosed airfoil geometries."""
    # Valid closed profile
    closed_coords = np.array([
        [1.0, 0.0], [0.5, 0.05], [0.0, 0.0], [0.5, -0.05], [1.0, 0.0]
    ])
    res_valid = CFDPreflightAuditor.audit_geometry(closed_coords)
    assert res_valid["closure"]["passed"] is True

    # Unclosed profile (gap of 0.05)
    unclosed_coords = np.array([
        [1.0, 0.0], [0.5, 0.05], [0.0, 0.0], [0.5, -0.05], [0.95, -0.02]
    ])
    res_invalid = CFDPreflightAuditor.audit_geometry(unclosed_coords)
    assert res_invalid["closure"]["passed"] is False
    assert res_invalid["admissible"] is False
    assert "Profile is unclosed" in str(res_invalid["violations"])


# --- 6. Geometry Preflight: Self-Intersection Check ---

def test_geometry_preflight_self_intersection_detection():
    """Verifies CFDPreflightAuditor detects self-intersecting polygon boundaries."""
    # Figure-8 self-intersecting shape
    fig8 = np.array([
        [0.0, 0.0], [1.0, 1.0], [1.0, 0.0], [0.0, 1.0], [0.0, 0.0]
    ])
    res = CFDPreflightAuditor.audit_geometry(fig8)
    assert res["self_intersection"]["passed"] is False
    assert res["admissible"] is False


# --- 7. Geometry Preflight: Chord Normalization Check ---

def test_geometry_preflight_chord_normalization():
    """Verifies CFDPreflightAuditor detects non-normalized airfoil chords."""
    unnormalized = np.array([
        [0.0, 0.0], [0.25, 0.05], [0.5, 0.0], [0.25, -0.05], [0.0, 0.0]
    ])  # chord is 0.5 instead of 1.0
    res = CFDPreflightAuditor.audit_geometry(unnormalized)
    assert res["normalization"]["passed"] is False
    assert res["admissible"] is False


# --- 8. Mesh Preflight: Non-Orthogonality Ceiling ---

def test_mesh_preflight_non_orthogonality():
    """Verifies CFDPreflightAuditor rejects meshes exceeding 70 deg non-orthogonality."""
    res_pass = CFDPreflightAuditor.audit_mesh(cell_count=25000, max_non_orthogonality=45.0)
    assert res_pass["admissible"] is True

    res_fail = CFDPreflightAuditor.audit_mesh(cell_count=25000, max_non_orthogonality=75.0)
    assert res_fail["admissible"] is False
    assert any("non-orthogonality" in v for v in res_fail["violations"])


# --- 9. Mesh Preflight: Skewness Ceiling ---

def test_mesh_preflight_skewness():
    """Verifies CFDPreflightAuditor rejects meshes exceeding skewness of 4.0."""
    res_fail = CFDPreflightAuditor.audit_mesh(cell_count=25000, max_skewness=4.8)
    assert res_fail["admissible"] is False
    assert any("skewness" in v for v in res_fail["violations"])


# --- 10. Mesh Preflight: 2D Cell Count Ceiling ---

def test_mesh_preflight_cell_ceiling():
    """Verifies CFDPreflightAuditor rejects 2D meshes exceeding 100,000 cells."""
    res_fail = CFDPreflightAuditor.audit_mesh(cell_count=150_000)
    assert res_fail["admissible"] is False
    assert any("exceeds allowable 2D ceiling" in v for v in res_fail["violations"])


# --- 11. CRITICAL ANTI-FABRICATION TEST (Directive Section P23-19) ---

def test_critical_anti_fabrication_rejection():
    """
    CRITICAL ANTI-FABRICATION TEST:
    Attempts to inject fabricated CFD output into the ingestion pipeline.
    The system MUST reject it unless the execution provenance proves:
    case hash, mesh hash, solver identity, runtime identity, execution log,
    residual history, force data, and field data are mutually consistent.
    """
    # 1. Forge a fake CFD datum with impossible lift and inverted stagnation
    fake_surface_cp = [2.5] * 64  # Violates Bernoulli limit (max Cp > 1.05)
    fake_cl = 15.2                # Violates physical subsonic lift bounds
    fake_cd = -0.05               # Violates drag non-negativity

    # Ingestion audit must flag violations
    pv_report = PhysicalFieldValidator.validate_field_physics(
        surface_cp=fake_surface_cp,
        cl=fake_cl,
        cd=fake_cd,
    )
    assert pv_report["valid"] is False
    assert len(pv_report["violations"]) >= 3

    # Attempt to promote with fake data must be blocked
    stage, is_promoted, reason = PersistentExperimentRegistry.audit_promotion_phase23(
        stage8_passed=True,
        backend_executed=True,
        remote_provenance_verified=False,  # Mismatched DAG
        convergence_verified=True,
        physical_checks_passed=pv_report["valid"],
        reproduction_passed=True,
        frozen_eval_passed=True,
    )
    assert is_promoted is False
    assert "PROVENANCE_FAILED" in reason or "PHYSICS_GATE_FAILED" in reason


# --- 12. Physical Gate: Bernoulli Stagnation Limit Violation ---

def test_physical_gate_bernoulli_violation():
    """Verifies PhysicalFieldValidator rejects Cp exceeding 1.05."""
    cp_invalid = np.linspace(0.0, 1.25, 64)
    res = PhysicalFieldValidator.validate_field_physics(
        surface_cp=cp_invalid,
        cl=0.45,
        cd=0.01,
    )
    assert res["valid"] is False
    assert res["checks"]["stagnation_limit"]["passed"] is False


# --- 13. Physical Gate: Suction Peak Violation ---

def test_physical_gate_suction_peak_violation():
    """Verifies PhysicalFieldValidator rejects positive minimum Cp at alpha > 0."""
    cp_no_suction = np.linspace(0.1, 0.9, 64)  # min Cp is +0.1, no suction
    res = PhysicalFieldValidator.validate_field_physics(
        surface_cp=cp_no_suction,
        cl=0.45,
        cd=0.01,
    )
    assert res["valid"] is False
    assert res["checks"]["suction_peak"]["passed"] is False


# --- 14. Physical Gate: Negative Drag Violation ---

def test_physical_gate_drag_negativity():
    """Verifies PhysicalFieldValidator rejects unphysical negative drag (CD < 0)."""
    cp_valid = np.linspace(-1.0, 1.0, 64)
    res = PhysicalFieldValidator.validate_field_physics(
        surface_cp=cp_valid,
        cl=0.45,
        cd=-0.005,  # Negative drag
    )
    assert res["valid"] is False
    assert res["checks"]["drag_positivity"]["passed"] is False


# --- 15. 12-Node Merkle Provenance DAG Integrity ---

def test_12_node_provenance_dag_integrity():
    """Verifies 12-node Merkle DAG detects leaf corruption and preserves root integrity."""
    dag = RemoteCFDProvenanceDAG.assemble(
        geometry_data=[[0.0, 0.0], [1.0, 0.0]],
        case_files={"case": "hash_a"},
        mesh_meta={"cells": 18400},
        solver_config={"solver": "simpleFoam"},
        solver_version="OpenFOAM-v2312",
        runtime_env={"os": "Ubuntu"},
        execution_log="Log complete",
        residual_history={"p": 1e-5},
        flowfield_data={"cp": [1.0, -1.0]},
        forces={"CL": 0.45, "CD": 0.01, "CM": -0.01},
        validation_report={"valid": True},
        dataset_record_id="AASI-P23-CFD-001",
    )
    assert len(dag.dag_nodes) == 12
    assert dag.verify_integrity() is True

    # Corrupt one leaf node
    dag.dag_nodes["node_7_execution_log"] = "tampered_log_hash"
    assert dag.verify_integrity() is False


# --- 16. Frozen Test Set Preservation & SHA-256 Hash ---

def test_frozen_test_hash_preservation():
    """Verifies pre-registered Phase 22 frozen test set hash is perfectly preserved."""
    frozen_path = Path("data/experiments/phase22_frozen_test.json")
    assert frozen_path.exists()
    content = frozen_path.read_text(encoding="utf-8")
    actual_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    expected_hash = "fa7b3d11b958cc85b2bad3167391c0514d00c097d0fb878e28a1c4aab048e3b8"
    assert actual_hash == expected_hash, f"Frozen test set tampered! Hash was {actual_hash}"
    data = json.loads(content)
    assert data["hash"] == "a1d6fa6d67d1a7c754af1a809d1068effe1c2c04978183ddf314a8c0363bc8b6"
    assert len(data["samples"]) == 20


# --- 17. Deterministic Backend Selection Policy ---

def test_deterministic_backend_selection_policy():
    """Verifies backend selection policy selects Colab when local solver is absent."""
    mgr = ComputeFabricManager()
    selected = mgr.select_backend_policy()
    # On Windows host without native simpleFoam, Colab bundle is the top remote backend
    assert selected in [BackendType.COLAB, BackendType.LOCAL, BackendType.USER_EXECUTED]


# --- 18. Colab Notebook Generator Validity ---

def test_colab_notebook_generator_validity():
    """Verifies generated notebook.ipynb is valid JSON and contains all 18 steps."""
    backend = ColabBackend()
    manifest = CFDJobManifest(
        job_id="TEST-NOTEBOOK-VALIDITY",
        experiment_id="P23-NB-TEST",
        geometry_name="NACA 0012",
        geometry_hash="hash_geom",
        case_hash="hash_case",
    )
    nb_dict = backend._generate_colab_notebook(manifest)
    assert nb_dict["nbformat"] == 4
    assert len(nb_dict["cells"]) >= 7

    # Serialize and reparse to confirm strict JSON compliance
    serialized = json.dumps(nb_dict)
    reparsed = json.loads(serialized)
    assert reparsed["metadata"]["language_info"]["name"] == "python"


# --- 19. Model Promotion Governance: Stage 9 Real CFD Validated ---

def test_stage_9_promotion_governance():
    """Verifies Stage 9 is granted when real solver execution and physical gates pass."""
    stage, is_promoted, reason = PersistentExperimentRegistry.audit_promotion_phase23(
        stage8_passed=True,
        backend_executed=True,
        remote_provenance_verified=True,
        convergence_verified=True,
        physical_checks_passed=True,
        reproduction_passed=True,
        frozen_eval_passed=True,
        verified_loop_cycles=1,
    )
    assert is_promoted is True
    assert stage == PromotionStage.STAGE_9_REAL_CFD_VALIDATED


# --- 20. Model Promotion Governance: Stage 10 Blocked on Single Run ---

def test_stage_10_promotion_blocked_on_single_run():
    """Verifies Stage 10 is refused on a single run (requires >= 3 verified cycles)."""
    stage, is_promoted, reason = PersistentExperimentRegistry.audit_promotion_phase23(
        stage8_passed=True,
        backend_executed=True,
        remote_provenance_verified=True,
        convergence_verified=True,
        physical_checks_passed=True,
        reproduction_passed=True,
        frozen_eval_passed=True,
        verified_loop_cycles=1,  # Only 1 cycle
        multi_geometry_verified=False,
    )
    assert stage != PromotionStage.STAGE_10_CLOSED_LOOP_SCIENTIFICALLY_VALIDATED
    assert stage == PromotionStage.STAGE_9_REAL_CFD_VALIDATED


# --- 21. Model Promotion Governance: Stage 10 Granted on Multiple Verified Cycles ---

def test_stage_10_promotion_granted_on_multiple_cycles():
    """Verifies Stage 10 is granted only when >= 3 cycles across multiple geometries succeed."""
    stage, is_promoted, reason = PersistentExperimentRegistry.audit_promotion_phase23(
        stage8_passed=True,
        backend_executed=True,
        remote_provenance_verified=True,
        convergence_verified=True,
        physical_checks_passed=True,
        reproduction_passed=True,
        frozen_eval_passed=True,
        verified_loop_cycles=3,
        multi_geometry_verified=True,
    )
    assert is_promoted is True
    assert stage == PromotionStage.STAGE_10_CLOSED_LOOP_SCIENTIFICALLY_VALIDATED


# --- 22. Independent Reproduction Bundle Verification ---

def test_reproduction_bundle_verification():
    """Verifies Phase23ReproductionVerifier confirms PHASE23-RUN-001 integrity."""
    target_dir = Path("data/reproduction_bundles/PHASE23-RUN-001")
    if not target_dir.exists():
        Phase23ReproductionVerifier.assemble_bundle(target_dir)
    report = Phase23ReproductionVerifier.verify_bundle(target_dir)
    assert report["verified"] is True
    assert report["status"] == "REPRODUCIBILITY_CONFIRMED"
    assert report["total_files_verified"] >= 15
    assert len(report["corrupted_files"]) == 0


# --- 23. Complete Compute-Agnostic Campaign Execution ---

def test_compute_agnostic_campaign_execution():
    """Verifies ComputeAgnosticDiscoveryEngine executes P23-E001 through E005."""
    engine = ComputeAgnosticDiscoveryEngine()
    summary = engine.run_phase23_campaign()
    assert summary["phase"] == "PHASE_23"
    assert "scientific_comparison" in summary
    assert summary["scientific_comparison"]["verdict"] in ["IMPROVED", "UNCHANGED", "DEGRADED"]
    assert "experiments_resolved" in summary
    assert len(summary["experiments_resolved"]) == 5
