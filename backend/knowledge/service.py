"""Unified knowledge service coordinating retrieval, datasets, source registries, and RAG."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from .dataset_registry import DatasetRegistry
from .embeddings import EmbeddingProvider, get_embedding_provider
from .models import Dataset, Document, RetrievalResult
from .rag import ScientificRAGPipeline
from .resolution import ResultResolutionDispatcher
from .retriever import HybridRetriever
from .reranker import ScientificReranker
from .seed_corpus import build_and_index_seed_corpus
from .source_registry import SourceMetadata, SourceRegistry
from .vector_store import FAISSVectorIndex, VectorIndex

logger = logging.getLogger("aasi.knowledge.service")


class KnowledgeService:
    """Central service managing scientific knowledge ingestion, indexing, datasets, and retrieval."""

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_index: Optional[VectorIndex] = None,
    ):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.vector_index = vector_index or FAISSVectorIndex(self.embedding_provider.dimension)
        self.retriever = HybridRetriever(
            vector_index=self.vector_index,
            embedding_provider=self.embedding_provider,
        )
        self.source_registry = SourceRegistry()
        self.dataset_registry = DatasetRegistry()
        self.rag_pipeline = ScientificRAGPipeline()
        self.reranker = ScientificReranker()
        self.resolution_dispatcher = ResultResolutionDispatcher(
            dataset_registry=self.dataset_registry,
            retriever=self.retriever,
        )
        self._documents: Dict[str, Document] = {}
        self._initialized = False

    def initialize(self):
        """Initialize seed corpus and catalog."""
        if self._initialized:
            return
        docs, chunk_count = build_and_index_seed_corpus(
            vector_index=self.vector_index,
            retriever=self.retriever,
            dataset_registry=self.dataset_registry,
            embedding_provider=self.embedding_provider,
        )
        for d in docs:
            self._documents[d.document_id] = d
        self._initialized = True
        logger.info(
            f"KnowledgeService initialized: {len(self._documents)} documents, "
            f"{chunk_count} chunks, {len(self.dataset_registry.list_datasets())} datasets."
        )

    def list_sources(self) -> List[SourceMetadata]:
        return self.source_registry.list_sources()

    def search_literature(
        self,
        query: str,
        k: int = 5,
        source_filter: Optional[str] = None,
        discipline_filter: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """Two-stage hybrid dense/lexical retrieval + scientific authority reranking."""
        self.initialize()
        candidates = self.retriever.search(
            query=query,
            k=max(k * 3, 15),
            source_filter=source_filter,
            discipline_filter=discipline_filter,
            year_min=year_min,
            year_max=year_max,
        )
        return self.reranker.rerank(query=query, candidates=candidates, top_k=k)

    def get_document(self, document_id: str) -> Optional[Document]:
        self.initialize()
        return self._documents.get(document_id)

    def list_documents(self) -> List[Dict[str, Any]]:
        self.initialize()
        return [
            {
                "document_id": doc.document_id,
                "title": doc.title,
                "source": doc.provenance.source_organization,
                "authors": doc.provenance.authors,
                "year": doc.provenance.publication_date,
                "report_number": doc.provenance.report_number,
                "discipline": doc.provenance.discipline,
                "url": doc.provenance.source_url,
                "content_hash": doc.provenance.content_hash,
                "chunk_count": len(doc.chunks),
                "equation_count": len(doc.equations),
            }
            for doc in self._documents.values()
        ]

    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        self.initialize()
        return self.dataset_registry.get(dataset_id)

    def list_datasets(
        self, domain: Optional[str] = None, geometry: Optional[str] = None
    ) -> List[Dataset]:
        self.initialize()
        return self.dataset_registry.list_datasets(domain=domain, geometry=geometry)

    def query_datasets(
        self,
        geometry: str,
        mach: Optional[float] = None,
        reynolds: Optional[float] = None,
        aoa_deg: Optional[float] = None,
        domain: str = "aerodynamics",
    ) -> List[Dict[str, Any]]:
        self.initialize()
        return self.dataset_registry.query_conditions(
            geometry=geometry,
            mach=mach,
            reynolds=reynolds,
            aoa_deg=aoa_deg,
            domain=domain,
        )

    def resolve_scientific_query(self, query: str) -> Dict[str, Any]:
        """Execute the result-resolution workflow on a scientific or flight condition question."""
        self.initialize()
        return self.resolution_dispatcher.resolve(query)


# Global singleton instance for the backend
_knowledge_service_instance: Optional[KnowledgeService] = None


def get_knowledge_service() -> KnowledgeService:
    global _knowledge_service_instance
    if _knowledge_service_instance is None:
        _knowledge_service_instance = KnowledgeService()
        _knowledge_service_instance.initialize()
    return _knowledge_service_instance
