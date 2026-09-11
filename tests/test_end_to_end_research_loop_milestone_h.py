"""
Milestone H Verification Tests: End-to-End Autonomous Simulation-Research Loop & System Cohesion.

Validates the full scientific intelligence pipeline:
1. Research campaign planning & active learning candidate selection
2. Hardware-aware fail-closed compute routing
3. Standalone user CFD case deck generation (Allrun, Allrun.bat, manifest, checklist)
4. Artifact ingestion, convergence QC, and ASME V&V 20 Richardson extrapolation
5. Deterministic CPU surrogate retraining with cryptographic provenance
6. Scientific literature RAG with epistemic tier ranking and formal provenance citations
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.research.service import research_loop_service
from backend.compute.hardware_matrix import hardware_matrix_manager
from backend.compute.models import ComputeRequest, ComputeBackendType, UploadedArtifactPayload
from backend.compute.registry import ComputeBackendRegistry
from backend.physics_ai.train_surrogate import SurrogateTrainer
from backend.physics_ai.checkpoints import CheckpointManager
from backend.knowledge.service import KnowledgeService


def test_end_to_end_autonomous_scientific_research_loop():
    # -------------------------------------------------------------
    # Step 1: Autonomous Research Planning & Active Learning
    # -------------------------------------------------------------
    campaign = research_loop_service.plan_campaign("OBJ-AERO-001", max_cases=3)
    assert campaign is not None
    assert campaign.objective_id == "OBJ-AERO-001"
    assert len(campaign.candidate_jobs) > 0
    candidate_job = campaign.candidate_jobs[0]
    assert candidate_job.geometry == "NACA 0012"
    assert candidate_job.flow_conditions.reynolds > 0

    # -------------------------------------------------------------
    # Step 2: Hardware-Aware Task Routing (Fail-Closed)
    # -------------------------------------------------------------
    routing_decision = hardware_matrix_manager.route_task(
        task_type="CFD_2D",
        mesh_cells=125_000,
        dimension="2D",
        solver="openfoam",
    )
    # On this workstation without native OpenFOAM binaries or with 125k cells > 50k safe quota,
    # it must route to USER_EXECUTED fail-closed rather than crashing or faking execution
    assert routing_decision.recommended_backend == ComputeBackendType.USER_EXECUTED
    assert routing_decision.allowed_locally is False
    assert len(routing_decision.resource_bottlenecks) > 0

    # -------------------------------------------------------------
    # Step 3: Standalone OpenFOAM User-Executed Case Deck Generation
    # -------------------------------------------------------------
    registry = ComputeBackendRegistry()
    compute_req = ComputeRequest(
        case_id="e2e-research-case-001",
        geometry="NACA 0012",
        solver="openfoam",
        backend=ComputeBackendType.USER_EXECUTED,
        mach=candidate_job.flow_conditions.mach,
        reynolds=candidate_job.flow_conditions.reynolds,
        aoa_deg=candidate_job.flow_conditions.aoa_deg,
    )
    dispatch_res = registry.dispatch(compute_req)
    assert dispatch_res["backend"] == "USER_EXECUTED"
    assert dispatch_res["status"] == "AWAITING_USER_UPLOAD"
    case_deck = dispatch_res["case_deck"]
    case_dir = case_deck["case_directory"]

    # Verify canonical execution scripts were generated
    assert os.path.exists(os.path.join(case_dir, "Allrun"))
    assert os.path.exists(os.path.join(case_dir, "Allrun.bat"))
    assert os.path.exists(os.path.join(case_dir, "manifest.json"))
    assert os.path.exists(os.path.join(case_dir, "validation_checklist.md"))

    # -------------------------------------------------------------
    # Step 4: External Simulation Artifact Ingestion & QC
    # -------------------------------------------------------------
    sample_openfoam_log = """# OpenFOAM simpleFoam log and forceCoeffs output
Time = 200
Solving for Ux, Initial residual = 0.00008, Final residual = 0.000009
Solving for Uy, Initial residual = 0.00007, Final residual = 0.000008
Solving for p, Initial residual = 0.00005, Final residual = 0.000006
SIMPLE solution converged in 200 iterations
End

# Time         Cd             Cs             Cl             CmRoll         CmPitch        CmYaw
0              0.08500        0.00000        0.12000        0.00000        -0.01000       0.00000
50             0.04200        0.00000        0.31000        0.00000        -0.01200       0.00000
100            0.02100        0.00000        0.45000        0.00000        -0.01400       0.00000
150            0.01820        0.00000        0.48500        0.00000        -0.01480       0.00000
200            0.01810        0.00000        0.48620        0.00000        -0.01490       0.00000
"""
    payload = UploadedArtifactPayload(
        case_id="e2e-research-case-001",
        solver="openfoam",
        file_name="forceCoeffs.dat",
        file_content=sample_openfoam_log,
        conditions={
            "mach": candidate_job.flow_conditions.mach,
            "aoa": candidate_job.flow_conditions.aoa_deg,
            "reynolds": candidate_job.flow_conditions.reynolds,
        },
    )
    ingestion = registry.artifact_service.ingest_artifact(payload)
    assert ingestion.status == "INGESTED"
    assert ingestion.converged is True
    assert ingestion.iterations == 200
    assert pytest.approx(ingestion.coefficients["cl"], rel=1e-3) == 0.4862
    assert pytest.approx(ingestion.coefficients["cd"], rel=1e-3) == 0.0181
    assert len(ingestion.provenance_hash) == 64  # SHA-256 hex string

    # -------------------------------------------------------------
    # Step 5: ASME V&V 20 Grid Convergence Study Verification
    # -------------------------------------------------------------
    r_fine = registry.artifact_service.ingest_artifact(UploadedArtifactPayload(
        case_id="E2E-GRID-FINE", file_name="res.csv", file_content="Time,Cl,Cd\n100,0.4320,0.010", solver="csv"
    ))
    r_med = registry.artifact_service.ingest_artifact(UploadedArtifactPayload(
        case_id="E2E-GRID-MED", file_name="res.csv", file_content="Time,Cl,Cd\n100,0.4280,0.011", solver="csv"
    ))
    r_coarse = registry.artifact_service.ingest_artifact(UploadedArtifactPayload(
        case_id="E2E-GRID-COARSE", file_name="res.csv", file_content="Time,Cl,Cd\n100,0.4200,0.013", solver="csv"
    ))

    gci_eval = registry.artifact_service.evaluate_mesh_convergence_study(
        fine_result=r_fine, medium_result=r_med, coarse_result=r_coarse, metric="cl"
    )
    assert gci_eval["valid"] is True
    gci = gci_eval["gci_result"]
    assert gci["apparent_order_p"] > 0.0
    assert gci["gci_fine_pct"] < 5.0
    assert gci["is_in_asymptotic_range"] is True

    # -------------------------------------------------------------
    # Step 6: Deterministic Surrogate Training with Crypto Provenance
    # -------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp_dir:
        from backend.physics_ai.train_surrogate import train_and_export_surrogate
        res = train_and_export_surrogate(
            output_dir=tmp_dir,
            export_to_checkpoints=False,
            epochs=3,
            seed=42,
        )
        assert res["checksum"] is not None
        assert "checkpoint_path" in res
        ckpt_path = res["checkpoint_path"]
        assert os.path.exists(ckpt_path)

        # Verify cryptographic integrity
        valid, sha, msg = CheckpointManager.verify_checkpoint_integrity(
            ckpt_path,
            expected_sha256=res["checksum"],
        )
        assert valid is True
        assert sha == res["checksum"]

    # -------------------------------------------------------------
    # Step 7: Scientific RAG Retrieval with Provenance Citation
    # -------------------------------------------------------------
    knowledge = KnowledgeService()
    rag_results = knowledge.search_literature(
        query="NACA 0012 experimental stall boundary TM-4083",
        k=3,
    )
    assert len(rag_results) > 0
    top_doc = rag_results[0]
    assert 0.0 <= top_doc.relevance <= 1.0
    assert top_doc.provenance.source_organization != ""


def test_api_full_scientific_cycle():
    client = TestClient(app)

    # 1. Inspect Hardware Capabilities
    res = client.get("/api/system/capabilities")
    assert res.status_code == 200
    assert "safe_max_local_mesh_cells" in res.json()

    # 2. Plan Research Campaign
    plan_res = client.post("/api/research/campaigns/plan?objective_id=OBJ-AERO-001&max_cases=2")
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    assert plan_data["objective_id"] == "OBJ-AERO-001"

    # 3. Generate User Case Deck
    deck_res = client.post(
        "/api/compute/generate-case",
        json={
            "case_id": "api-e2e-001",
            "geometry": "NACA 0012",
            "solver": "openfoam",
            "backend": "USER_EXECUTED",
            "mach": 0.15,
            "aoa_deg": 6.0,
            "reynolds": 3000000.0,
        },
    )
    assert deck_res.status_code == 200
    assert deck_res.json()["backend"] == "USER_EXECUTED"

    # 4. Ingest Simulation Output
    sample_csv = "Iteration,Drag_Cd,Lift_Cl,Pitch_Cm\n1,0.05,0.2,-0.01\n50,0.019,0.52,-0.015\n"
    ingest_res = client.post(
        "/api/compute/upload-artifact",
        json={
            "case_id": "api-e2e-001",
            "solver": "su2",
            "file_name": "history.csv",
            "file_content": sample_csv,
            "conditions": {"mach": 0.15, "aoa": 6.0},
        },
    )
    assert ingest_res.status_code == 200
    assert ingest_res.json()["status"] == "INGESTED"

    # 5. Scientific Literature Search with Reranking
    lit_res = client.post(
        "/api/knowledge/search",
        json={
            "query": "NACA 0012 aerodynamic polars",
            "k": 3,
        },
    )
    assert lit_res.status_code == 200
    assert "results" in lit_res.json()
    assert len(lit_res.json()["results"]) > 0
