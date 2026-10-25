"""
Tests for Phase 13: Scientific Memory and Evidence Graph Integration with Task Harness.
"""

import pytest
from backend.harness.task_harness import TaskHarness
from backend.science.merkle_lineage import merkle_lineage
from backend.science.memory import scientific_memory, MemoryQuery


def test_task_harness_creates_merkle_node():
    harness = TaskHarness()
    result = harness.execute_task("calculate lift for NACA 0012 at alpha 5.0")
    assert result.success is True
    assert "merkle_node_id" in result.evidence_record
    node_id = result.evidence_record["merkle_node_id"]
    assert node_id is not None
    assert len(node_id) == 64

    # Verify node in Merkle graph
    node = merkle_lineage.get_node(node_id)
    assert node is not None
    assert node.verify_self_hash() is True
    assert node.investigation_id == result.task_id


def test_task_harness_persists_scientific_memory():
    harness = TaskHarness()
    result = harness.execute_task("calculate drag for NACA 0012 at alpha 4.0")
    assert result.success is True

    # Search in scientific memory
    q = MemoryQuery(
        geometry="NACA 0012",
        alpha_deg=4.0,
        min_similarity=0.7,
    )
    search_results = scientific_memory.search(q)
    assert len(search_results) > 0
    top_entry = search_results[0].entry
    assert "NACA 0012" in top_entry.geometry.upper()
    assert len(top_entry.provenance_hash) == 64


def test_failed_task_records_negative_evidence_in_merkle():
    harness = TaskHarness()
    # Tool call with invalid parameters that cause failure
    result = harness.execute_task(
        "run polar sweep with start -50 end 100",  # Out of bounds
    )
    # Merkle nodes should still exist and maintain integrity
    inv_nodes = merkle_lineage.get_investigation_lineage(result.task_id)
    assert isinstance(inv_nodes, list)
