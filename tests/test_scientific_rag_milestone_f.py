"""
Unit and Integration Tests for Milestone F: Scientific RAG Re-ranking &
Provenance-Preserving Citation.

Validates:
- Two-stage retrieval: candidate gathering + epistemic authority reranking
- Exact technical token and equation matching boost
- Redundancy and duplicate snippet suppression via Jaccard similarity
- Citation formatting with cryptographic provenance hash and epistemic badges
- KnowledgeService end-to-end literature search with reranking
- API endpoint: POST /api/knowledge/search
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.knowledge.models import RetrievalResult, Provenance, ScientificObjectType
from backend.knowledge.reranker import ScientificReranker, format_scientific_citation
from backend.knowledge.service import KnowledgeService

client = TestClient(app)


def test_scientific_reranker_exact_identifier_boost():
    """Verifies that exact technical report numbers and equations receive a relevance boost."""
    reranker = ScientificReranker()

    res_generic = RetrievalResult(
        document_id="DOC-1",
        chunk_id="CHUNK-1",
        title="General Subsonic Aerodynamics",
        source="NASA",
        authors=["Author A"],
        snippet="Discussion of lift and boundary layers over standard wings.",
        relevance=0.60,
        provenance=Provenance(source_organization="NASA", title="General Aerodynamics", publication_date="1970", content_hash="hash1"),
        object_type=ScientificObjectType.RETRIEVED_REFERENCE,
    )

    res_exact = RetrievalResult(
        document_id="DOC-2",
        chunk_id="CHUNK-2",
        title="NASA-TN-D-628 Section Characteristics",
        source="NASA",
        authors=["Critzos"],
        snippet="Measurements of NACA 0012 airfoil section across angles of attack from NASA-TN-D-628.",
        relevance=0.60,
        provenance=Provenance(source_organization="NASA", title="NASA-TN-D-628", report_number="NASA-TN-D-628", publication_date="1961", content_hash="hash2"),
        object_type=ScientificObjectType.RETRIEVED_REFERENCE,
    )

    query = "Where can I find the NASA-TN-D-628 polar data for NACA 0012?"
    reranked = reranker.rerank(query, [res_generic, res_exact], top_k=2)

    assert len(reranked) == 2
    # res_exact should be ranked first due to exact token match
    assert reranked[0].document_id == "DOC-2"
    assert reranked[0].relevance > reranked[1].relevance


def test_scientific_reranker_epistemic_authority():
    """Verifies that verified agency reports outrank preprints given identical base scores."""
    reranker = ScientificReranker()

    res_agency = RetrievalResult(
        document_id="NASA-DOC",
        chunk_id="C-1",
        title="Turbulent Boundary Layer Measurement",
        source="NASA Technical Reports Server",
        authors=["NASA Researcher"],
        snippet="Skin friction coefficient measurements in wind tunnel.",
        relevance=0.70,
        provenance=Provenance(source_organization="NASA", title="TBL Measurement", publication_date="1985", content_hash="h1"),
        object_type=ScientificObjectType.RETRIEVED_REFERENCE,
    )

    res_preprint = RetrievalResult(
        document_id="ARXIV-DOC",
        chunk_id="C-2",
        title="Turbulent Boundary Layer Modeling",
        source="arXiv Fluid Dynamics",
        authors=["Preprint Author"],
        snippet="Skin friction coefficient measurements in wind tunnel.",
        relevance=0.70,
        provenance=Provenance(source_organization="arXiv", title="TBL Modeling", publication_date="2024", content_hash="h2"),
        object_type=ScientificObjectType.RETRIEVED_REFERENCE,
    )

    query = "Turbulent boundary layer skin friction coefficient"
    reranked = reranker.rerank(query, [res_preprint, res_agency], top_k=2)

    assert reranked[0].document_id == "NASA-DOC"
    assert reranked[1].document_id == "ARXIV-DOC"


def test_scientific_reranker_redundancy_suppression():
    """Verifies that redundant snippets from the same document are filtered to promote diversity."""
    reranker = ScientificReranker()

    res_chunk1 = RetrievalResult(
        document_id="DOC-SAME",
        chunk_id="C-1",
        title="NACA 0012 Wind Tunnel Tests",
        source="NASA",
        snippet="Lift coefficient increases linearly with angle of attack until stall angle of 16 degrees.",
        relevance=0.85,
        provenance=Provenance(source_organization="NASA", title="NACA 0012", publication_date="1961", content_hash="h1"),
        object_type=ScientificObjectType.RETRIEVED_REFERENCE,
    )

    res_chunk2_duplicate = RetrievalResult(
        document_id="DOC-SAME",
        chunk_id="C-2",
        title="NACA 0012 Wind Tunnel Tests",
        source="NASA",
        snippet="Lift coefficient increases linearly with angle of attack until stall angle of 16 degrees approximately.",
        relevance=0.83,
        provenance=Provenance(source_organization="NASA", title="NACA 0012", publication_date="1961", content_hash="h2"),
        object_type=ScientificObjectType.RETRIEVED_REFERENCE,
    )

    res_chunk3_distinct = RetrievalResult(
        document_id="DOC-DISTINCT",
        chunk_id="C-3",
        title="Compressibility Effects on Airfoils",
        source="NASA",
        snippet="Transonic drag rise occurs above critical Mach number with shock formation.",
        relevance=0.75,
        provenance=Provenance(source_organization="NASA", title="Compressibility", publication_date="1975", content_hash="h3"),
        object_type=ScientificObjectType.RETRIEVED_REFERENCE,
    )

    query = "NACA 0012 lift coefficient stall"
    reranked = reranker.rerank(query, [res_chunk1, res_chunk2_duplicate, res_chunk3_distinct], top_k=2)

    # res_chunk2 should be suppressed due to high overlap with res_chunk1 from same document
    assert len(reranked) == 2
    assert reranked[0].chunk_id == "C-1"
    assert reranked[1].chunk_id == "C-3"


def test_format_scientific_citation():
    """Tests academically rigorous citation formatting with hash and epistemic badges."""
    # NASA Agency report citation
    cite_nasa = format_scientific_citation(
        title="Aerodynamic Characteristics of the NACA 0012 Airfoil",
        source="NASA Langley Research Center",
        year="1961",
        report_number="NASA-TN-D-628",
        content_hash="abc123def4567890123456789012345678901234",
        url="https://ntrs.nasa.gov/citations/19930090976",
        epistemic_classification="AGENCY_TECHNICAL_REPORT"
    )
    assert "[NASA-TN-D-628]" in cite_nasa
    assert "https://ntrs.nasa.gov" in cite_nasa
    assert "[Hash: `abc123def456`]" in cite_nasa
    assert "**[AGENCY_TECHNICAL_REPORT]**" in cite_nasa

    # arXiv preprint citation
    cite_arxiv = format_scientific_citation(
        title="Deep Learning for Transonic Shocks",
        source="arXiv / Cornell University",
        year="2024",
        report_number="2401.12345",
        content_hash="feedbeef12345678901234567890123456789012",
        url="https://arxiv.org/abs/2401.12345",
    )
    assert "**[UNVERIFIED_PREPRINT]**" in cite_arxiv


def test_knowledge_service_search_literature_reranked():
    """Verifies that KnowledgeService.search_literature() returns reranked results."""
    svc = KnowledgeService()
    results = svc.search_literature("NACA 0012 aerodynamic polars", k=3)
    assert len(results) > 0
    for r in results:
        assert 0.0 <= r.relevance <= 1.0


def test_api_knowledge_search():
    """Tests POST /api/knowledge/search endpoint."""
    res = client.post("/api/knowledge/search", json={
        "query": "NACA 0012 lift and drag",
        "k": 3
    })
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert len(data["results"]) > 0
    first = data["results"][0]
    assert "relevance" in first
    assert "provenance" in first
