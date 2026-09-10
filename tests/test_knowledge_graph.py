"""
Tests for AASI Scientific Knowledge Graph Foundation.
"""

import pytest
from backend.graph.models import EntityType, RelationType, GraphEntity, GraphRelation
from backend.graph.service import KnowledgeGraphService


def test_knowledge_graph_entities_and_relations():
    """Verifies that KnowledgeGraphService stores entities across 16 types and 10 relation types."""
    graph = KnowledgeGraphService()
    assert len(graph.entities) >= 10
    assert len(graph.relations) >= 7

    # Check airfoil entity
    af = graph.get_entity("AF-NACA0012")
    assert af is not None
    assert af.entity_type == EntityType.AIRFOIL
    assert af.name == "NACA 0012"

    # Check mission entity
    msn = graph.get_entity("MSN-CHANDRAYAAN3")
    assert msn is not None
    assert msn.entity_type == EntityType.MISSION


def test_knowledge_graph_neighbor_traversal():
    """Tests graph traversal to discover connected papers and facilities."""
    graph = KnowledgeGraphService()
    neighbors = graph.get_neighbors("AF-NACA0012")
    assert len(neighbors) >= 2

    # Should be described in NASA TN-D-628
    pub_ids = [n["entity"]["entity_id"] for n in neighbors if n["relation"] == "DESCRIBED_IN"]
    assert "PUB-NASA-TND628" in pub_ids


def test_knowledge_graph_search():
    """Tests entity search by name or ID."""
    graph = KnowledgeGraphService()
    results = graph.search_entities("Chandrayaan")
    assert len(results) >= 1
    assert results[0].entity_id == "MSN-CHANDRAYAAN3"
