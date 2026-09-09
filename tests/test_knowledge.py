"""Tests for Phase 3 Scientific Knowledge Subsystem: models, provenance, chunking, embeddings, FAISS, and hybrid retrieval."""

import os
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.knowledge.chunking import StructureAwareChunker
from backend.knowledge.embeddings import FastDeterministicEmbeddingProvider
from backend.knowledge.models import Chunk, Document, Equation, Provenance, ScientificObjectType
from backend.knowledge.nasa_adapter import NasaAdapter
from backend.knowledge.retriever import HybridRetriever
from backend.knowledge.source_registry import SourceIdentifier, SourceRegistry
from backend.knowledge.vector_store import FAISSVectorIndex

client = TestClient(app)


class TestScientificModelsAndProvenance:
    """Test scientific object taxonomy, provenance integrity, and equation schemas."""

    def test_scientific_object_types_are_distinct(self):
        types = [t.value for t in ScientificObjectType]
        assert "DOCUMENT" in types
        assert "DATASET" in types
        assert "EXPERIMENT" in types
        assert "SIMULATION" in types
        assert "SURROGATE" in types
        assert "ANALYTICAL_RESULT" in types
        assert "RETRIEVED_REFERENCE" in types
        # Verify they are unique
        assert len(types) == len(set(types))

    def test_provenance_cryptographic_hash_computation(self):
        raw_text = "NACA 0012 experimental airfoil data from Langley wind tunnel."
        h1 = Provenance.compute_hash(raw_text)
        h2 = Provenance.compute_hash(raw_text)
        h3 = Provenance.compute_hash(raw_text + " modified")

        assert len(h1) == 64  # SHA-256 hex digest
        assert h1 == h2
        assert h1 != h3

    def test_provenance_model_validation(self):
        prov = Provenance(
            source_organization="NASA",
            title="Summary of Airfoil Data",
            authors=["Ira H. Abbott", "Albert E. von Doenhoff"],
            publication_date="1945",
            report_number="NACA-TR-824",
            source_url="https://ntrs.nasa.gov/citations/19930090976",
            license="Public Domain",
            discipline="Aerodynamics",
            source_type=ScientificObjectType.DOCUMENT,
            content_hash=Provenance.compute_hash("NACA-TR-824 text payload"),
        )
        assert prov.source_organization == "NASA"
        assert prov.report_number == "NACA-TR-824"
        assert prov.content_hash is not None

    def test_equation_model_with_context_and_units(self):
        eq = Equation(
            equation_id="eq-cl-1",
            equation_text="C_L = 2 * pi * alpha",
            latex=r"C_L = 2\pi\alpha",
            source_document_id="NACA-TR-460",
            page=4,
            surrounding_context="Under thin airfoil theory, the linear lift slope is expressed as C_L = 2*pi*alpha.",
            variables={"C_L": "Lift coefficient", "alpha": "Angle of attack"},
            units={"C_L": "dimensionless", "alpha": "radians"},
            extraction_confidence=0.95,
        )
        assert eq.equation_id == "eq-cl-1"
        assert eq.latex == r"C_L = 2\pi\alpha"
        assert eq.extraction_confidence >= 0.90
        assert eq.variables["C_L"] == "Lift coefficient"


class TestStructureAwareChunking:
    """Test chunking with section hierarchy and equation preservation."""

    def test_equation_extraction_from_latex(self):
        chunker = StructureAwareChunker()
        text = (
            "Section 2. Lift and Drag\n"
            "The theoretical lift coefficient for thin airfoils is given by:\n"
            "$$C_L = 2\\pi\\alpha$$\n"
            "where alpha is in radians."
        )
        eqs = chunker.extract_equations(text, document_id="doc-test", page=2)
        assert len(eqs) >= 1
        assert "C_L" in eqs[0].equation_text or "2\\pi" in (eqs[0].latex or "")

    def test_structure_aware_chunk_retention(self):
        chunker = StructureAwareChunker(max_chunk_size=300)
        doc_text = (
            "ABSTRACT\nThis report investigates boundary layer transition.\n\n"
            "EXPERIMENTAL RESULTS\nMeasurements of skin friction were recorded at Mach 0.3.\n\n"
            "CONCLUSIONS\nTransition occurs at 12 percent chord."
        )
        chunks = chunker.chunk_document(
            document_id="doc-struct-1",
            source_id="NASA",
            text=doc_text,
        )
        assert len(chunks) >= 2
        for c in chunks:
            assert c.document_id == "doc-struct-1"
            assert c.source_id == "NASA"
            assert c.content_hash is not None
            assert len(c.content_hash) == 64


class TestSourceRegistryAndAdapters:
    """Test scientific source adapters and explicit documentation of unautomated sources."""

    def test_source_registry_registration_and_metadata(self):
        reg = SourceRegistry()
        sources = reg.list_sources()
        assert len(sources) >= 6

        source_ids = [s.source_id for s in sources]
        assert SourceIdentifier.NASA_NTRS in source_ids
        assert SourceIdentifier.NACA in source_ids
        assert SourceIdentifier.ARXIV in source_ids
        assert SourceIdentifier.ESA in source_ids
        assert SourceIdentifier.ISRO in source_ids
        assert SourceIdentifier.OPEN_DATASETS in source_ids

    def test_unautomated_sources_document_reasons(self):
        reg = SourceRegistry()
        esa = reg.get(SourceIdentifier.ESA)
        isro = reg.get(SourceIdentifier.ISRO)

        assert esa is not None
        assert not esa.metadata.automated_ingestion
        assert "NOT IMPLEMENTED — REASON" in esa.metadata.implementation_status

        assert isro is not None
        assert not isro.metadata.automated_ingestion
        assert "NOT IMPLEMENTED — REASON" in isro.metadata.implementation_status

    def test_nasa_adapter_ingestion_workflow(self):
        adapter = NasaAdapter()
        prov = Provenance(
            source_organization="NASA",
            title="Transonic Aerodynamics of NACA 0012",
            publication_date="1967",
            report_number="NASA-TM-X-1361",
            content_hash=Provenance.compute_hash("NASA report content"),
        )
        doc = adapter.ingest_document(
            document_id="NASA-TM-X-1361",
            title="Transonic Aerodynamics of NACA 0012",
            content_text="The drag divergence Mach number is Mach_dd = 0.72.",
            provenance=prov,
        )
        assert doc.document_id == "NASA-TM-X-1361"
        assert len(doc.chunks) >= 1
        assert doc.provenance.report_number == "NASA-TM-X-1361"


class TestEmbeddingsAndVectorStore:
    """Test embedding vectors and FAISS vector index."""

    def test_fast_deterministic_embedding_properties(self):
        provider = FastDeterministicEmbeddingProvider(dimension=384)
        assert provider.dimension == 384

        v1 = provider.embed_query("NACA 0012 aerodynamic drag polar")
        v2 = provider.embed_query("NACA 0012 aerodynamic drag polar")
        v3 = provider.embed_query("Orbital insertion burn around Jupiter")

        assert len(v1) == 384
        assert v1 == v2  # Fully deterministic

        import numpy as np
        dot_similar = np.dot(np.array(v1), np.array(v2))
        dot_different = np.dot(np.array(v1), np.array(v3))
        assert dot_similar > dot_different

    def test_faiss_vector_index_add_and_search(self):
        import numpy as np
        idx = FAISSVectorIndex(dimension=4)
        vectors = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ], dtype=np.float32)
        metadata = [{"id": "chunk-1"}, {"id": "chunk-2"}]
        idx.add(vectors, metadata)

        assert idx.total_vectors == 2
        query = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        results = idx.search(query, k=1)
        assert len(results) == 1
        assert results[0][0]["id"] == "chunk-1"
        assert results[0][1] >= 0.99


class TestHybridRetrieverAndKnowledgeAPI:
    """Test hybrid search with semantic, keyword, and metadata filters via API."""

    def test_api_knowledge_sources_endpoint(self):
        res = client.get("/api/knowledge/sources")
        assert res.status_code == 200
        data = res.json()
        assert "sources" in data
        assert len(data["sources"]) >= 6

    def test_api_knowledge_documents_endpoint(self):
        res = client.get("/api/knowledge/documents")
        assert res.status_code == 200
        data = res.json()
        assert "documents" in data
        assert len(data["documents"]) >= 12
        # Check NACA-TR-824 exists
        doc_ids = [d["document_id"] for d in data["documents"]]
        assert "NACA-TR-824" in doc_ids

    def test_api_knowledge_document_detail_endpoint(self):
        res = client.get("/api/knowledge/documents/NACA-TR-824")
        assert res.status_code == 200
        doc = res.json()
        assert doc["document_id"] == "NACA-TR-824"
        assert "Summary of Airfoil Data" in doc["title"]
        assert doc["provenance"]["content_hash"] is not None
        assert len(doc["chunks"]) >= 1

    def test_api_knowledge_search_with_filtering(self):
        res = client.post(
            "/api/knowledge/search",
            json={
                "query": "NACA 0012 drag polar",
                "k": 3,
                "source_filter": "NACA",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["count"] >= 1
        top_hit = data["results"][0]
        assert "NACA" in top_hit["source"]
        assert "provenance" in top_hit
        assert top_hit["provenance"]["content_hash"] is not None
