"""AASI Scientific Knowledge & Dataset Subsystem.

Provides provenance-tracked document ingestion, scientific object modeling,
vector storage, hybrid retrieval, two-stage reranking, and dataset registries.
"""

from .models import (
    ScientificObjectType,
    Provenance,
    Equation,
    Chunk,
    Document,
    CFDClassification,
    CFDDataModel,
    Dataset,
    Citation,
    RetrievalResult,
)
from .reranker import ScientificReranker, format_scientific_citation
from .service import KnowledgeService

__all__ = [
    "ScientificObjectType",
    "Provenance",
    "Equation",
    "Chunk",
    "Document",
    "CFDClassification",
    "CFDDataModel",
    "Dataset",
    "Citation",
    "RetrievalResult",
    "ScientificReranker",
    "format_scientific_citation",
    "KnowledgeService",
]
