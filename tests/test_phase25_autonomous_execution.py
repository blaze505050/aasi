"""
AASI Phase 25 Autonomous Scientific Execution Platform Test Suite.
Adversarial and functional validation for:
- Natural-language planner
- Experiment graph & retry lineage
- Strict state machine transitions
- Colab state disambiguation
- Fidelity decision engine
- CFD error diagnostics
- Non-mutating repair engine & retry limits
- CFD dataset knowledge fabric & lazy storage
- Path traversal and security bounds
"""

import pytest
import hashlib
import json
from pathlib import Path

from backend.agent.scientific_state import (
    ProvenanceState,
    CFDResultState,
    ColabExecutionState,
    ScientificStateMachine,
)
from backend.agent.planner import ScientificPlanner, ExperimentSpecification
from backend.agent.experiment_graph import ExperimentGraph, TaskStatus, TaskNode
from backend.agent.decision_engine import FidelityDecisionEngine, FidelityLevel
from backend.agent.diagnostics import CFDDiagnosticsEngine, CFDErrorClass
from backend.agent.repair_engine import CFDRepairEngine
from backend.agent.report_generator import ScientificReportGenerator
from backend.agent.execution_controller import AutonomousExecutionController
from backend.dataset.schema import (
    CFDRecord,
    GeometrySpec,
    FlowConditions,
    MeshMetrics,
    SolverConfig,
    SimulationResults,
    ValidationMetrics,
    ProvenanceMetadata,
)
from backend.dataset.storage import ObjectStorageBackend, MetadataStore, ScientificFeatureStore
from backend.dataset.catalog import CFDCatalog
from backend.dataset.similarity import AerodynamicSimilarity
from backend.dataset.retrieval import CFDRetrievalEngine
from backend.dataset.provenance import DatasetProvenanceGuard


# ============================================================================
# 1. Natural Language Planner Tests
# ============================================================================

def test_planner_extracts_airfoil_and_conditions():
    """Verify planner deterministically extracts parameters from natural language."""
    text = "Analyze NACA 4412 at Re=3e6 and alpha=8 degrees and determine whether the current surrogate prediction is trustworthy."
    spec = ScientificPlanner.parse_objective(text)

    assert spec.geometry == "NACA 4412"
    assert spec.alpha_deg == 8.0
    assert spec.reynolds == 3000000.0
    assert spec.mach == 0.15
    assert "CL" in spec.required_outputs
    assert spec.fidelity_requirement == "adaptive_validation"
    assert len(spec.spec_hash) == 64
    assert spec.experiment_id.startswith("EXP-AASI-")


def test_planner_default_fallbacks():
    """Verify planner provides safe aerodynamic fallbacks when parameters are omitted."""
    text = "Study aerodynamic lift and drag for NACA 0012."
    spec = ScientificPlanner.parse_objective(text)

    assert spec.geometry == "NACA 0012"
    assert spec.alpha_deg == 4.0
    assert spec.reynolds == 3000000.0
    assert spec.mach == 0.15


# ============================================================================
# 2. Experiment Graph Tests
# ============================================================================

def test_experiment_graph_creation_and_execution_updates():
    """Verify directed experiment graph construction and node state updates."""
    graph = ExperimentGraph.create_default_pipeline("EXP-TEST-001")
    assert len(graph.nodes) == 9
    assert len(graph.edges) == 8

    # Update node
    graph.update_node_status("parse_objective", TaskStatus.RUNNING)
    assert graph.nodes["parse_objective"].status == TaskStatus.RUNNING
    assert graph.nodes["parse_objective"].started_at is not None

    graph.update_node_status("parse_objective", TaskStatus.COMPLETED, outputs={"geom": "NACA 0012"})
    assert graph.nodes["parse_objective"].status == TaskStatus.COMPLETED
    assert graph.nodes["parse_objective"].output_hash is not None

    # Compute graph digest
    digest = graph.compute_graph_hash()
    assert len(digest) == 64


# ============================================================================
# 3. Scientific State Machine Tests
# ============================================================================

def test_state_machine_legal_progression():
    """Verify valid sequential progression through CFDResultState."""
    sm = ScientificStateMachine(CFDResultState.PLANNED)

    sm.transition(CFDResultState.CASE_GENERATED, trigger="MESH_OK")
    sm.transition(CFDResultState.PREFLIGHT_PASSED, trigger="PREFLIGHT_OK")
    sm.transition(CFDResultState.BUNDLE_READY, trigger="BUNDLE_OK")
    sm.transition(CFDResultState.EXECUTION_REQUESTED, trigger="SUBMIT_OK")
    sm.transition(CFDResultState.EXECUTING, trigger="SOLVER_OK")
    sm.transition(CFDResultState.RAW_RESULTS_RECEIVED, trigger="RESULTS_OK")
    sm.transition(CFDResultState.INTEGRITY_VERIFIED, trigger="INTEGRITY_OK")
    sm.transition(CFDResultState.PHYSICAL_VALIDATION, trigger="PHYSICS_OK")
    sm.transition(CFDResultState.SCIENTIFIC_VALIDATION, trigger="ASME_OK")
    sm.transition(CFDResultState.DATABASE_COMMITTED, trigger="COMMIT_OK")

    assert sm.current_state == CFDResultState.DATABASE_COMMITTED
    assert len(sm.history) == 10


def test_state_machine_rejects_illegal_transitions():
    """Fail-closed: illegal leaps directly to committed state must raise ValueError."""
    sm = ScientificStateMachine(CFDResultState.PLANNED)
    with pytest.raises(ValueError, match="Illegal state transition"):
        sm.transition(CFDResultState.DATABASE_COMMITTED, trigger="ILLEGAL_SKIP")


def test_state_machine_fail_transition():
    """Verify failure transition immediately enters FAILED state."""
    sm = ScientificStateMachine(CFDResultState.EXECUTING)
    sm.fail(reason="Residual divergence encountered")
    assert sm.current_state == CFDResultState.FAILED
    assert sm.history[-1].detail == "Residual divergence encountered"


# ============================================================================
# 4. Colab State Disambiguation Tests
# ============================================================================

def test_colab_states_distinct_and_never_collapsed():
    """Verify all Colab execution states remain separate and uncollapsed."""
    states = [
        ColabExecutionState.COLAB_BUNDLE_READY,
        ColabExecutionState.COLAB_EXECUTED,
        ColabExecutionState.RESULTS_IMPORTED,
        ColabExecutionState.RESULTS_VERIFIED,
        ColabExecutionState.EXECUTION_UNVERIFIED,
    ]
    # Verify uniqueness
    assert len(states) == len(set(states))
    assert ColabExecutionState.COLAB_BUNDLE_READY.value != ColabExecutionState.COLAB_EXECUTED.value
    assert ColabExecutionState.COLAB_EXECUTED.value != ColabExecutionState.RESULTS_IMPORTED.value
    assert ColabExecutionState.RESULTS_IMPORTED.value != ColabExecutionState.RESULTS_VERIFIED.value


# ============================================================================
# 5. Fidelity Decision Engine Tests
# ============================================================================

def test_fidelity_decision_high_match_low_uncertainty():
    """When existing CFD matches well and surrogate uncertainty is low, new CFD is not required."""
    matches = [{"distance": 0.02}]
    decision = FidelityDecisionEngine.evaluate(
        geometry="NACA 0012",
        alpha_deg=4.0,
        reynolds=3e6,
        mach=0.15,
        database_matches=matches,
        surrogate_uncertainty=0.04,
    )
    assert decision.is_new_cfd_required is False
    assert decision.selected_fidelity == FidelityLevel.DATABASE_MATCH


def test_fidelity_decision_high_uncertainty_requires_cfd():
    """When surrogate uncertainty is high or flow is outside standard bounds, new CFD is required."""
    matches = [{"distance": 0.60}]
    decision = FidelityDecisionEngine.evaluate(
        geometry="NACA 0012",
        alpha_deg=16.0,  # High post-stall angle
        reynolds=3e6,
        mach=0.15,
        database_matches=matches,
        surrogate_uncertainty=0.35,  # High uncertainty
    )
    assert decision.is_new_cfd_required is True
    assert decision.selected_fidelity == FidelityLevel.NEW_CFD_REQUIRED
    assert decision.recommended_backend == "COLAB"


def test_fidelity_decision_adaptive_validation_override():
    """When user requests adaptive validation, multi-fidelity comparison is triggered."""
    decision = FidelityDecisionEngine.evaluate(
        geometry="NACA 4412",
        alpha_deg=8.0,
        reynolds=3e6,
        mach=0.15,
        user_fidelity_req="adaptive_validation",
    )
    assert decision.is_new_cfd_required is True
    assert decision.selected_fidelity == FidelityLevel.MULTI_FIDELITY_COMPARISON


# ============================================================================
# 6. Automatic CFD Diagnostics Tests
# ============================================================================

def test_diagnostics_detects_floating_point_exception():
    report = CFDDiagnosticsEngine.diagnose(solver_log="Error: Floating point exception in solver loop. p residual: nan")
    assert report.error_class == CFDErrorClass.FLOATING_POINT_FAILURE
    assert report.confidence >= 0.90
    assert len(report.repair_candidates) > 0


def test_diagnostics_detects_divergence():
    residuals = {"p": [0.1, 0.5, 2.0, 150.0]}
    report = CFDDiagnosticsEngine.diagnose(residuals=residuals)
    assert report.error_class == CFDErrorClass.DIVERGENCE


def test_diagnostics_detects_residual_stagnation():
    # Residuals oscillating above 1e-2 for 400 iterations
    stagnated_vals = [0.015] * 350
    residuals = {"p": stagnated_vals}
    report = CFDDiagnosticsEngine.diagnose(residuals=residuals)
    assert report.error_class == CFDErrorClass.RESIDUAL_STAGNATION


def test_diagnostics_detects_negative_drag_violation():
    forces = {"cl": 0.45, "cd": -0.002}
    report = CFDDiagnosticsEngine.diagnose(forces=forces)
    assert report.error_class == CFDErrorClass.PHYSICS_GATE_VIOLATION


def test_diagnostics_detects_missing_solver():
    report = CFDDiagnosticsEngine.diagnose(solver_log="bash: simpleFoam: command not found")
    assert report.error_class == CFDErrorClass.MISSING_SOLVER


# ============================================================================
# 7. Automatic CFD Repair Engine & Retry Limits
# ============================================================================

def test_repair_engine_proposes_new_candidate_without_mutating_original():
    """Verify repair engine generates cryptographically new candidate without altering original."""
    original_spec = {"geometry": "NACA 0012", "alpha_deg": 12.0}
    original_hash = "abc123originalhash"
    diagnosis = CFDDiagnosticsEngine.diagnose(residuals={"p": [10.0, 50.0, 200.0]})

    outcome = CFDRepairEngine.propose_repair(
        original_spec=original_spec,
        original_case_hash=original_hash,
        diagnosis=diagnosis,
        current_retry_count=0,
    )

    assert outcome.status == "REPAIR_CANDIDATE_GENERATED"
    assert outcome.retries_exhausted is False
    assert outcome.candidate is not None
    assert outcome.candidate.candidate_case_hash != original_hash
    assert outcome.candidate.retry_number == 1
    assert "fvSolution_relaxation" in outcome.candidate.modifications


def test_repair_engine_exhaustion_at_max_retries():
    """Verify exceeding 3 retries transitions to HUMAN_REVIEW_REQUIRED."""
    original_spec = {"geometry": "NACA 0012", "alpha_deg": 12.0}
    original_hash = "abc123originalhash"
    diagnosis = CFDDiagnosticsEngine.diagnose(residuals={"p": [10.0, 50.0, 200.0]})

    outcome = CFDRepairEngine.propose_repair(
        original_spec=original_spec,
        original_case_hash=original_hash,
        diagnosis=diagnosis,
        current_retry_count=3,  # Already at MAX_RETRIES
    )

    assert outcome.status == "HUMAN_REVIEW_REQUIRED"
    assert outcome.retries_exhausted is True
    assert outcome.candidate is None
    assert "exhausted" in outcome.detail.lower()


# ============================================================================
# 8. Path Traversal & Security Ingestion Guard Tests
# ============================================================================

def test_provenance_guard_rejects_malicious_archive_paths():
    """Security: prevent path traversal attacks in dataset archives."""
    safe_paths = ["constant/polyMesh/points", "0/U", "system/controlDict"]
    assert DatasetProvenanceGuard.validate_archive_path_safety(safe_paths) is True

    unsafe_paths_traversal = ["../../etc/passwd", "constant/polyMesh/points"]
    assert DatasetProvenanceGuard.validate_archive_path_safety(unsafe_paths_traversal) is False

    unsafe_paths_root = ["/var/run/secret.key", "0/U"]
    assert DatasetProvenanceGuard.validate_archive_path_safety(unsafe_paths_root) is False

    unsafe_paths_windows = ["C:\\Windows\\System32\\calc.exe", "0/U"]
    assert DatasetProvenanceGuard.validate_archive_path_safety(unsafe_paths_windows) is False


# ============================================================================
# 9. CFD Knowledge Fabric (Catalog & Storage) Tests
# ============================================================================

def test_cfd_catalog_query_and_similarity(tmp_path):
    """Verify CFD catalog registers records and computes aerodynamic similarity."""
    catalog = CFDCatalog(workspace_root=tmp_path)
    records = catalog.query()
    assert len(records) >= 3

    # Similarity test
    dist_same = AerodynamicSimilarity.compute_distance(
        "NACA 0012", 4.0, 3e6, 0.15,
        "NACA 0012", 4.0, 3e6, 0.15,
    )
    assert dist_same == 0.0

    dist_diff = AerodynamicSimilarity.compute_distance(
        "NACA 0012", 4.0, 3e6, 0.15,
        "NACA 4412", 8.0, 1e6, 0.20,
    )
    assert dist_diff > 0.30


def test_object_storage_backend_lazy_retrieval(tmp_path):
    """Verify lazy storage saves binary artifacts and retrieves them on demand."""
    storage = ObjectStorageBackend(tmp_path / "artifacts")
    test_bytes = b"OpenFOAM-10 simulation forceCoeffs raw content"
    digest = storage.put_artifact("forceCoeffs.dat", test_bytes)

    assert storage.exists(digest, "forceCoeffs.dat") is True
    retrieved = storage.get_artifact(digest, "forceCoeffs.dat")
    assert retrieved == test_bytes


# ============================================================================
# 10. Autonomous Execution Controller & Multi-Fidelity Report Tests
# ============================================================================

def test_autonomous_controller_end_to_end(tmp_path):
    """Verify the entire closed-loop scientific agent executes seamlessly."""
    controller = AutonomousExecutionController(workspace_root=tmp_path)
    objective = "Analyze NACA 4412 at Re=3e6 and alpha=8 degrees with adaptive validation."

    result = controller.run_pipeline(objective, user_fidelity_req="adaptive_validation")

    assert "experiment_id" in result
    assert result["experiment_id"].startswith("EXP-AASI-")
    assert result["fidelity_decision"]["is_new_cfd_required"] is True
    assert result["colab_execution_state"] == ColabExecutionState.COLAB_BUNDLE_READY.value
    assert "report" in result

    report = result["report"]
    assert "CL" in report["comparisons"]
    cl_comp = report["comparisons"]["CL"]
    assert cl_comp["surrogate"]["value"] is not None
    assert cl_comp["analytical"]["value"] is not None
    assert cl_comp["database_real"]["value"] is not None

    # Verify provenance states
    assert cl_comp["surrogate"]["provenance"] == ProvenanceState.SURROGATE.value
    assert cl_comp["analytical"]["provenance"] == ProvenanceState.ANALYTICAL.value
    assert cl_comp["database_real"]["provenance"] == ProvenanceState.DATABASE_REAL.value


def test_report_generator_multi_fidelity_discrepancies():
    """Verify report generator calculates exact numerical discrepancies."""
    report = ScientificReportGenerator.generate(
        experiment_id="EXP-DISC-001",
        objective="Verify discrepancy calculation",
        geometry="NACA 0012",
        alpha_deg=4.0,
        reynolds=3e6,
        mach=0.15,
        live_cfd_results={"cl": 0.4350, "cd": 0.0084, "cm": 0.0},
        database_results={"cl": 0.4380, "cd": 0.0078, "cm": 0.0},
        surrogate_results={"cl": 0.4281, "cd": 0.0089, "cm": 0.001},
        analytical_results={"cl": 0.4386, "cd": 0.0062, "cm": 0.0},
    )

    cl_comp = report.comparisons["CL"]
    # CFD - Surrogate discrepancy = 0.4350 - 0.4281 = +0.0069
    assert cl_comp.cfd_surrogate_discrepancy == 0.0069
    # CFD - Analytical discrepancy = 0.4350 - 0.4386 = -0.0036
    assert cl_comp.cfd_analytical_discrepancy == -0.0036
    assert cl_comp.live_cfd.provenance == ProvenanceState.LIVE_CFD


# ============================================================================
# 11. Multi-Format Dataset Ingestion Tests
# ============================================================================

def test_dataset_ingest_csv_polar(tmp_path):
    """Verify CSV aerodynamic polar ingestion with schema validation and trust levels."""
    from backend.dataset.ingestion import DatasetIngestor, TrustLevel
    from backend.dataset.catalog import CFDCatalog
    from backend.dataset.storage import ObjectStorageBackend

    catalog = CFDCatalog(workspace_root=tmp_path)
    storage = ObjectStorageBackend(tmp_path / "artifacts")
    ingestor = DatasetIngestor(catalog=catalog, storage=storage)

    csv_content = """alpha,cl,cd,cm
-4.0,-0.41,0.0065,0.0
0.0,0.02,0.0055,0.0
4.0,0.44,0.0068,0.0
8.0,0.85,0.0092,0.0
12.0,1.21,0.0145,0.0
"""
    result = ingestor.ingest_csv_polar(
        csv_content=csv_content,
        geometry_id="NACA 0012",
        reynolds=3e6,
        mach=0.15,
        trust_level=TrustLevel.PEER_REVIEWED_BENCHMARK,
    )

    assert result.success is True
    assert result.record_id.startswith("REC-CSV-")
    assert result.content_hash is not None
    assert result.trust_level == TrustLevel.PEER_REVIEWED_BENCHMARK
    assert result.record.flow.reynolds == 3e6
    assert result.record.results.cl is not None


def test_dataset_ingest_json_benchmark(tmp_path):
    """Verify JSON benchmark dataset ingestion with optional frozen benchmark tagging."""
    from backend.dataset.ingestion import DatasetIngestor, TrustLevel
    from backend.dataset.catalog import CFDCatalog
    from backend.dataset.storage import ObjectStorageBackend

    catalog = CFDCatalog(workspace_root=tmp_path)
    storage = ObjectStorageBackend(tmp_path / "artifacts")
    ingestor = DatasetIngestor(catalog=catalog, storage=storage)

    benchmark_json = json.dumps({
        "geometry": {"geometry_id": "NACA 4412"},
        "flow": {"reynolds": 3000000.0, "mach": 0.15, "aoa_deg": 6.0},
        "mesh": {"cell_count": 52000},
        "solver": {"solver": "simpleFoam"},
        "results": {"cl": 1.0820, "cd": 0.0125, "cm": -0.09},
    })

    result = ingestor.ingest_json_benchmark(
        json_content=benchmark_json,
        dataset_name="FROZEN-AERODYNAMICS-P25",
        trust_level=TrustLevel.FROZEN_EVALUATION_BENCHMARK,
        freeze_benchmark=True,
    )

    assert result.success is True
    assert result.trust_level == TrustLevel.FROZEN_EVALUATION_BENCHMARK
    assert result.record.provenance.reproduction_bundle_id == "FROZEN_BENCHMARK"


def test_dataset_ingest_vtk_field(tmp_path):
    """Verify VTK field parsing and lazy object storage retrieval."""
    from backend.dataset.ingestion import DatasetIngestor
    from backend.dataset.catalog import CFDCatalog
    from backend.dataset.storage import ObjectStorageBackend

    catalog = CFDCatalog(workspace_root=tmp_path)
    storage = ObjectStorageBackend(tmp_path / "artifacts")
    ingestor = DatasetIngestor(catalog=catalog, storage=storage)

    valid_vtk = b"# vtk DataFile Version 3.0\nFlow velocity and pressure field\nASCII\nDATASET UNSTRUCTURED_GRID\nPOINTS 3 float\n0 0 0\n1 0 0\n0 1 0\n"
    result = ingestor.ingest_vtk_field(
        vtk_bytes=valid_vtk,
        geometry_id="NACA 0012",
        field_name="U_field.vtk",
    )

    assert result.success is True
    assert result.record_id.startswith("REC-VTK-")
    assert "vtk_digest" in result.record.results.flow_field_artifacts


def test_adversarial_corrupted_vtk_rejected(tmp_path):
    """Verify corrupted or invalid VTK files fail ingestion."""
    from backend.dataset.ingestion import DatasetIngestor
    from backend.dataset.catalog import CFDCatalog
    from backend.dataset.storage import ObjectStorageBackend

    catalog = CFDCatalog(workspace_root=tmp_path)
    storage = ObjectStorageBackend(tmp_path / "artifacts")
    ingestor = DatasetIngestor(catalog=catalog, storage=storage)

    corrupted_vtk = b"RANDOM_GARBAGE_WITHOUT_VTK_HEADER\nDATA\n"
    result = ingestor.ingest_vtk_field(
        vtk_bytes=corrupted_vtk,
        geometry_id="NACA 0012",
    )

    assert result.success is False
    assert "Invalid VTK file format" in result.error


def test_adversarial_surrogate_mislabeled_as_cfd_rejected():
    """Verify that surrogate inference values cannot be tagged as LIVE_CFD."""
    from backend.agent.report_generator import ScientificReportGenerator

    report = ScientificReportGenerator.generate(
        experiment_id="EXP-SEC-001",
        objective="Surrogate test",
        geometry="NACA 0012",
        alpha_deg=4.0,
        reynolds=3e6,
        mach=0.15,
        live_cfd_results=None,  # Live solver was not run!
        surrogate_results={"cl": 0.4350, "cd": 0.0084, "cm": 0.0},
    )

    # When live CFD is not run, live_cfd entry must remain None or UNVERIFIED
    cl_comp = report.comparisons["CL"]
    assert cl_comp.live_cfd is None
    # Surrogate must carry SURROGATE provenance, never LIVE_CFD
    assert cl_comp.surrogate.provenance == ProvenanceState.SURROGATE
    assert cl_comp.surrogate.provenance != ProvenanceState.LIVE_CFD

