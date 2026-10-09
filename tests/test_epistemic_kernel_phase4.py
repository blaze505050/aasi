"""
AASI Phase 4 Test Suite: Consolidated Epistemic Memory & Prior-Knowledge Warm Starting.
Governing Doctrine: Absolute Anti-Fabrication Rule.

Validates:
1. Unified memory loading & foundational aerodynamic seeds.
2. Multi-dimensional physical similarity retrieval (Geometry, Re, Mach, Alpha, Quantities).
3. Prior-knowledge warm starting for parameter sweeps and optimization loops.
4. Anti-fabrication guarantees (preserves bounds, never silently copies polars).
5. Parameter sweep warm-start injection in DAG execution runtime.
6. Optimization loop prior-knowledge bounds injection in DAG runtime.
7. REST API integration for warm starting and Merkle lineage.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.science.epistemic_kernel import (
    EpistemicMemoryKernel,
    EpistemicQuery,
    EpistemicRecord,
    EpistemicRecordType,
    EpistemicTrustTier,
    WarmStartProposal,
    epistemic_kernel,
)
from backend.science.merkle_lineage import MerkleNodeType, merkle_lineage
from backend.scientific_language import parse_aml
from backend.scientific_compiler.compiler import ScientificCompiler
from backend.scientific_runtime.executor import ScientificTaskExecutor
from backend.scientific_runtime.context import ExecutionContext

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Corpus Initialization & Foundational Seeds
# ---------------------------------------------------------------------------

def test_epistemic_kernel_foundational_seeds():
    """Verify kernel contains canonical aerodynamic seeds and negative evidence."""
    stats = epistemic_kernel.get_stats()
    assert stats["total_records"] >= 3
    assert stats["by_record_type"].get(EpistemicRecordType.COMPUTATIONAL_SEED.value, 0) >= 2
    assert stats["failed_investigations_count"] >= 1

    seed_4412 = epistemic_kernel.get_record("EPI-SEED-NACA4412")
    assert seed_4412 is not None
    assert seed_4412.geometry == "NACA 4412"
    assert seed_4412.mesh_parameters["yplus_target"] < 1.0
    assert seed_4412.solver_settings["relaxation_p"] == 0.7


# ---------------------------------------------------------------------------
# 2. Multi-Dimensional Similarity Retrieval
# ---------------------------------------------------------------------------

def test_multi_dimensional_similarity_search():
    """Verify multi-criteria physical similarity ranking and trust weighting."""
    query = EpistemicQuery(
        geometry="NACA 4412",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
        target_quantity="CL",
    )
    results = epistemic_kernel.search(query)
    assert len(results) > 0

    best = results[0]
    assert best.record.geometry == "NACA 4412"
    assert best.similarity_score >= 0.95
    assert best.trust_weight == 1.0  # VERIFIED_CFD


# ---------------------------------------------------------------------------
# 3. Prior-Knowledge Warm Starting
# ---------------------------------------------------------------------------

def test_warm_start_exact_match_and_mesh_reuse():
    """Verify exact match yields validated mesh parameters and solver settings."""
    ws = epistemic_kernel.get_warm_start(
        geometry="NACA 4412",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
        target_quantity="CL",
    )
    assert ws.geometry == "NACA 4412"
    assert ws.is_exact_match is True
    assert ws.similarity_score >= 0.95
    assert ws.reusable_mesh_parameters["yplus_target"] <= 1.0
    assert ws.reusable_solver_settings["relaxation_p"] == 0.7
    assert ws.reusable_solver_settings["relaxation_U"] == 0.3
    assert ws.initial_guess_cl is not None

    # Anti-fabrication guarantees
    assert any("ANTI-FABRICATION" in p for p in ws.prohibited_reuses)


def test_warm_start_deep_stall_negative_evidence():
    """Verify post-stall operating conditions trigger negative evidence warnings and repairs."""
    ws = epistemic_kernel.get_warm_start(
        geometry="NACA 0012",
        alpha_deg=18.0,
        reynolds=3.0e6,
        mach=0.15,
    )
    assert ws.geometry == "NACA 0012"
    assert len(ws.negative_evidence_warnings) > 0
    assert any("separation" in w or "High angle" in w for w in ws.negative_evidence_warnings)
    assert len(ws.recommended_repairs) > 0
    assert any("pimpleFoam" in r or "wind-tunnel" in r for r in ws.recommended_repairs)


def test_warm_start_transonic_shock_warning():
    """Verify transonic Mach numbers trigger shock separation warnings."""
    ws = epistemic_kernel.get_warm_start(
        geometry="NACA 0012",
        alpha_deg=2.0,
        reynolds=5.0e6,
        mach=0.82,
    )
    assert any("Transonic regime" in w for w in ws.negative_evidence_warnings)
    assert any("rhoSimpleFoam" in r for r in ws.recommended_repairs)


# ---------------------------------------------------------------------------
# 4. Parameter Sweep Warm Starting in DAG Runtime
# ---------------------------------------------------------------------------

def test_sweep_runtime_warm_start_injection():
    """Verify that compiling and executing a sweep statement injects warm start proposals."""
    aml = """
    SWEEP "AoA Polar" {
        GEOMETRY "NACA 0012"
        VARIABLE alpha FROM 0.0 TO 16.0 STEP 4.0 deg
        CONDITIONS {
            Mach: 0.15,
            Re: 3.0e6
        }
        RECORD [CL, CD]
        FIDELITY PANEL
    }
    """
    program = parse_aml(aml)
    dag = ScientificCompiler.compile_statement(program.statements[0])

    ctx = ExecutionContext(
        execution_id="EXEC-SWEEP-WARMSTART",
        dag_id=dag.dag_id,
        mission_name=dag.mission_name,
    )

    t_disc = dag.nodes["t_discretize"]
    out_disc = ScientificTaskExecutor.execute_node(t_disc, ctx)

    assert "warm_start_proposals" in out_disc
    assert len(out_disc["warm_start_proposals"]) == 5
    # Point 5 is alpha=16.0, must trigger stall warning
    assert out_disc["stall_warning"] is not None
    assert "High angle of attack" in out_disc["stall_warning"]
    assert len(out_disc["reusable_mesh_parameters"]) > 0


# ---------------------------------------------------------------------------
# 5. Optimization Loop Warm Starting in DAG Runtime
# ---------------------------------------------------------------------------

def test_optimization_runtime_warm_start_injection():
    """Verify iterative optimization node leverages epistemic warm starting."""
    aml = """
    OPTIMIZE "L/D Maximization" {
        GEOMETRY "NACA 0012"
        MAXIMIZE L_OVER_D
        MAX_ITERATIONS 5
        FIDELITY PANEL
    }
    """
    program = parse_aml(aml)
    dag = ScientificCompiler.compile_statement(program.statements[0])

    ctx = ExecutionContext(
        execution_id="EXEC-OPT-WARMSTART",
        dag_id=dag.dag_id,
        mission_name=dag.mission_name,
    )

    t_opt = dag.nodes["t_optimize"]
    out_opt = ScientificTaskExecutor.execute_node(t_opt, ctx)

    res = out_opt["results"]
    assert res["converged"] is True
    assert "warm_start_reusable_mesh" in res
    assert "warm_start_solver_settings" in res
    assert res["warm_start_reusable_mesh"]["yplus_target"] <= 1.0


# ---------------------------------------------------------------------------
# 6. REST API Endpoints Verification
# ---------------------------------------------------------------------------

def test_api_warm_start_endpoint():
    """Verify POST /api/v1/memory/warm-start endpoint."""
    res = client.post(
        "/api/v1/memory/warm-start",
        json={"geometry": "NACA 4412", "alpha_deg": 4.0, "reynolds": 3.0e6, "mach": 0.15},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["geometry"] == "NACA 4412"
    assert data["is_exact_match"] is True
    assert "reusable_mesh_parameters" in data
    assert "reusable_solver_settings" in data


def test_api_lineage_and_audit_proof_endpoints():
    """Verify Merkle lineage inspection and verification endpoints."""
    # 1. Record a test node in Merkle graph
    node = merkle_lineage.record_node(
        investigation_id="INV-API-TEST",
        stage_name="CFD_EVALUATION",
        node_type=MerkleNodeType.SOLVER_EXECUTION,
        inputs={"alpha": 4.0},
        metrics={"CL": 0.44},
    )

    # 2. GET /lineage/{inv_id}
    res_list = client.get(f"/api/v1/memory/lineage/INV-API-TEST")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 3. GET /lineage/node/{node_id}
    res_node = client.get(f"/api/v1/memory/lineage/node/{node.node_id}")
    assert res_node.status_code == 200
    assert res_node.json()["node_id"] == node.node_id

    # 4. GET /lineage/node/{node_id}/proof
    res_proof = client.get(f"/api/v1/memory/lineage/node/{node.node_id}/proof")
    assert res_proof.status_code == 200
    assert res_proof.json()["verification"]["valid"] is True

    # 5. POST /lineage/verify
    res_verify = client.post(
        "/api/v1/memory/lineage/verify",
        json={"node_id": node.node_id},
    )
    assert res_verify.status_code == 200
    assert res_verify.json()["valid"] is True
