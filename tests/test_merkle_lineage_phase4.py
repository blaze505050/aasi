"""
AASI Phase 4 Test Suite: Cryptographic Merkle-DAG Experiment Lineage.
Governing Doctrine: Absolute Anti-Fabrication Rule.

Validates:
1. Cryptographic node sealing & self-integrity verification.
2. Causal parent-child DAG construction across computational stages.
3. Backward recursive lineage verification back to genesis root.
4. Detection of tampered / forged inputs or metrics (anti-forgery).
5. Whole-investigation composite Merkle root computation.
6. Exportable independent audit proofs.
7. Runtime DAG execution integration (ExecutionContext Merkle chain).
"""

import pytest
from backend.science.merkle_lineage import (
    MerkleLineageGraph,
    MerkleLineageNode,
    MerkleNodeType,
    canonical_hash,
)
from backend.scientific_language import parse_aml
from backend.scientific_compiler.compiler import ScientificCompiler
from backend.scientific_runtime.executor import ScientificTaskExecutor
from backend.scientific_runtime.context import ExecutionContext


@pytest.fixture
def fresh_graph(tmp_path):
    g = MerkleLineageGraph(storage_path=tmp_path / "test_merkle.json")
    g.clear()
    return g


def test_merkle_node_creation_and_self_verification(fresh_graph):
    """Verify single node deterministic hashing and self-integrity validation."""
    node = fresh_graph.record_node(
        investigation_id="INV-TEST-001",
        stage_name="GEOMETRY_DISCRETIZATION",
        node_type=MerkleNodeType.GEOMETRY_DISCRETIZATION,
        inputs={"geometry": "NACA 0012", "points": 100},
        metrics={"max_camber": 0.0, "thickness_ratio": 0.12},
    )

    assert len(node.node_id) == 64
    assert node.verify_self_hash() is True
    assert fresh_graph.verify_node(node.node_id) is True


def test_causal_dag_construction_and_backward_trace(fresh_graph):
    """Verify multi-stage causal DAG: Genesis -> Geometry -> Mesh -> Solver -> Reconcile."""
    inv_id = "INV-FLOW-001"

    # Stage 1: Genesis Spec
    n_genesis = fresh_graph.record_node(
        investigation_id=inv_id,
        stage_name="MISSION_SPEC",
        node_type=MerkleNodeType.GENESIS_SPEC,
        inputs={"mission": "Evaluate NACA 0012 L/D at alpha=4 deg"},
    )

    # Stage 2: Geometry Discretization
    n_geom = fresh_graph.record_node(
        investigation_id=inv_id,
        stage_name="GEOMETRY_GENERATION",
        node_type=MerkleNodeType.GEOMETRY_DISCRETIZATION,
        parent_hashes=[n_genesis.node_id],
        inputs={"geometry": "NACA 0012", "chord": 1.0},
    )

    # Stage 3: Mesh Generation
    n_mesh = fresh_graph.record_node(
        investigation_id=inv_id,
        stage_name="MESH_GENERATION",
        node_type=MerkleNodeType.MESH_GENERATION,
        parent_hashes=[n_geom.node_id],
        inputs={"cells": 24000, "yplus": 0.85},
        artifacts={"blockMeshDict": canonical_hash("CGridBlockMeshContent")},
    )

    # Stage 4: CFD Solver Execution
    n_solver = fresh_graph.record_node(
        investigation_id=inv_id,
        stage_name="SOLVER_EXECUTION",
        node_type=MerkleNodeType.SOLVER_EXECUTION,
        parent_hashes=[n_mesh.node_id],
        inputs={"solver": "simpleFoam", "alpha": 4.0},
        metrics={"CL": 0.441, "CD": 0.0084, "residuals": 8.5e-5},
    )

    # Stage 5: Evidence Reconciliation
    n_reconcile = fresh_graph.record_node(
        investigation_id=inv_id,
        stage_name="EVIDENCE_RECONCILIATION",
        node_type=MerkleNodeType.EVIDENCE_RECONCILIATION,
        parent_hashes=[n_solver.node_id],
        inputs={"tolerance": 0.05},
        metrics={"discrepancy_resolved": True},
    )

    # Trace from final reconciliation back to genesis
    trace = fresh_graph.verify_lineage_trace(n_reconcile.node_id)
    assert trace["valid"] is True
    assert trace["ancestor_count"] == 5
    assert trace["investigation_id"] == inv_id


def test_tamper_detection_in_merkle_trace(fresh_graph):
    """Verify that tampering with an intermediate node breaks the cryptographic trace."""
    inv_id = "INV-TAMPER-001"

    n1 = fresh_graph.record_node(
        investigation_id=inv_id,
        stage_name="STAGE_1",
        node_type=MerkleNodeType.GENESIS_SPEC,
        inputs={"seed": 1},
    )

    n2 = fresh_graph.record_node(
        investigation_id=inv_id,
        stage_name="STAGE_2",
        node_type=MerkleNodeType.SOLVER_EXECUTION,
        parent_hashes=[n1.node_id],
        metrics={"CL": 0.50},
    )

    # Valid trace before tampering
    assert fresh_graph.verify_lineage_trace(n2.node_id)["valid"] is True

    # Tamper with n1 data without updating node_id
    n1_stored = fresh_graph.get_node(n1.node_id)
    n1_stored.metrics_digest = canonical_hash({"forged_metric": 999.0})

    # Trace must now fail with hash mismatch
    bad_trace = fresh_graph.verify_lineage_trace(n2.node_id)
    assert bad_trace["valid"] is False
    assert "mismatch" in bad_trace["reason"]
    assert bad_trace["broken_at"] == n1.node_id


def test_investigation_composite_root_and_audit_proof(fresh_graph):
    """Verify whole-investigation root digest and exportable audit proof."""
    inv_id = "INV-AUDIT-001"

    n1 = fresh_graph.record_node(
        investigation_id=inv_id,
        stage_name="STAGE_A",
        node_type=MerkleNodeType.GENESIS_SPEC,
    )
    n2 = fresh_graph.record_node(
        investigation_id=inv_id,
        stage_name="STAGE_B",
        node_type=MerkleNodeType.SOLVER_EXECUTION,
        parent_hashes=[n1.node_id],
    )

    root = fresh_graph.compute_investigation_root(inv_id)
    assert len(root) == 64

    proof = fresh_graph.export_audit_proof(n2.node_id)
    assert proof["verification"]["valid"] is True
    assert len(proof["immediate_parents"]) == 1
    assert proof["immediate_parents"][0]["node_id"] == n1.node_id
    assert proof["proof_generator"] == "AASI_MERKLE_KERNEL_v1.0"


def test_runtime_dag_execution_records_merkle_blocks():
    """Verify that compiling and executing an AML task DAG automatically seals Merkle blocks."""
    aml = """
    INVESTIGATE "NACA0012 Test" {
        GEOMETRY "NACA 0012"
        CONDITIONS {
            alpha: 4.0 deg,
            Re: 3.0e6,
            Mach: 0.15
        }
        FIDELITY MULTI_FIDELITY
        TOLERANCE 0.05
    }
    """
    program = parse_aml(aml)
    dag = ScientificCompiler.compile_statement(program.statements[0])

    ctx = ExecutionContext(
        execution_id="EXEC-MERKLE-TEST",
        dag_id=dag.dag_id,
        mission_name=dag.mission_name,
    )

    # Execute all nodes in topological stages
    stages = dag.topological_sort()
    for stage in stages:
        for tid in stage:
            node = dag.nodes[tid]
            out = ScientificTaskExecutor.execute_node(node, ctx)
            assert "merkle_node_id" in out
            assert len(out["merkle_node_id"]) == 64

    # Verify context recorded Merkle chain
    assert len(ctx.merkle_chain) == len(dag.nodes)
    final_prov = ctx.compute_final_provenance()
    assert len(final_prov) == 64
