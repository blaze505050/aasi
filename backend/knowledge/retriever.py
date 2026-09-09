"""Hybrid scientific retriever combining semantic embeddings, exact keyword matching, and metadata filtering."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
import numpy as np

from .embeddings import EmbeddingProvider, get_embedding_provider
from .models import Chunk, Provenance, RetrievalResult, ScientificObjectType
from .vector_store import VectorIndex


class HybridRetriever:
    """Combines FAISS vector similarity, exact technical token matching, and metadata filters."""

    def __init__(
        self,
        vector_index: VectorIndex,
        embedding_provider: Optional[EmbeddingProvider] = None,
        semantic_weight: float = 0.55,
        keyword_weight: float = 0.45,
    ):
        self.vector_index = vector_index
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self._chunks: Dict[str, Chunk] = {}

    def register_chunk(self, chunk: Chunk):
        """Register a chunk in memory for exact keyword retrieval and metadata checks."""
        self._chunks[chunk.chunk_id] = chunk

    def register_chunks(self, chunks: List[Chunk]):
        for c in chunks:
            self.register_chunk(c)

    def _keyword_score(self, query: str, text: str) -> float:
        """Compute lexical matching score emphasizing exact technical aerospace keywords."""
        query_terms = re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", query.lower())
        if not query_terms:
            return 0.0

        text_lower = text.lower()
        score = 0.0
        total_weight = 0.0

        # Technical identifiers that warrant heavy exact-match boosting
        technical_keywords = {
            "naca", "0012", "0015", "4412", "mach", "reynolds", "rans", "navier-stokes",
            "hohmann", "delta-v", "reentry", "hypersonic", "spalart-allmaras", "k-omega",
            "drag", "lift", "pitching", "moment", "boundary", "layer", "pressure", "cp"
        }

        for term in query_terms:
            w = 2.5 if term in technical_keywords else 1.0
            total_weight += w

            # Exact phrase or term match
            count = text_lower.count(term)
            if count > 0:
                # Sublinear term frequency saturation
                score += w * min(1.0, 0.5 + 0.2 * count)

        return (score / total_weight) if total_weight > 0 else 0.0

    def search(
        self,
        query: str,
        k: int = 5,
        source_filter: Optional[str] = None,
        discipline_filter: Optional[str] = None,
        object_type_filter: Optional[ScientificObjectType] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """Perform hybrid search with metadata filtering."""
        if not query.strip():
            return []

        # 1. Semantic search via Vector Index
        q_vec = np.array(self.embedding_provider.embed_query(query), dtype=np.float32)
        # Search larger candidate pool to accommodate subsequent metadata filtering
        candidate_k = max(k * 4, 20)
        semantic_matches = self.vector_index.search(q_vec, k=candidate_k)

        candidates: Dict[str, Dict[str, Any]] = {}
        for meta, s_score in semantic_matches:
            c_id = meta.get("chunk_id")
            if not c_id:
                continue
            candidates[c_id] = {
                "metadata": meta,
                "semantic_score": max(0.0, float(s_score)),
                "keyword_score": 0.0,
            }

        # 2. Lexical scoring over candidate pool and registered chunks
        for c_id, chunk in self._chunks.items():
            k_score = self._keyword_score(query, chunk.content)
            if k_score > 0:
                if c_id in candidates:
                    candidates[c_id]["keyword_score"] = k_score
                else:
                    candidates[c_id] = {
                        "metadata": {
                            "chunk_id": chunk.chunk_id,
                            "document_id": chunk.document_id,
                            "source": chunk.source_id,
                            "page": chunk.page,
                            "title": chunk.metadata.get("title", ""),
                            "year": chunk.metadata.get("year"),
                            "provenance": chunk.metadata.get("provenance", {}),
                            "content": chunk.content,
                            "equations": [eq.model_dump() for eq in chunk.equations],
                        },
                        "semantic_score": 0.0,
                        "keyword_score": k_score,
                    }

        # 3. Filter by metadata and compute combined score
        results: List[RetrievalResult] = []
        for c_id, data in candidates.items():
            meta = data["metadata"]

            # Source filter
            if source_filter:
                item_src = meta.get("source", "").lower()
                if source_filter.lower() not in item_src:
                    continue

            # Year filter
            item_year = meta.get("year")
            if item_year is not None:
                try:
                    yr = int(item_year)
                    if year_min and yr < year_min:
                        continue
                    if year_max and yr > year_max:
                        continue
                except (ValueError, TypeError):
                    pass

            prov_dict = meta.get("provenance", {})
            if discipline_filter:
                item_disc = prov_dict.get("discipline", "").lower()
                if discipline_filter.lower() not in item_disc:
                    continue

            # Calculate hybrid combined score
            sem_score = data["semantic_score"]
            key_score = data["keyword_score"]
            combined_score = (
                self.semantic_weight * sem_score + self.keyword_weight * key_score
            )

            # Ensure provenance object
            if isinstance(prov_dict, Provenance):
                prov = prov_dict
            elif isinstance(prov_dict, dict) and prov_dict:
                prov = Provenance(**prov_dict)
            else:
                prov = Provenance(
                    source_organization=meta.get("source", "Unknown"),
                    title=meta.get("title", "Untitled Technical Report"),
                    authors=meta.get("authors", []),
                    publication_date=str(meta.get("year", "Unknown")),
                    source_url=meta.get("url"),
                    report_number=meta.get("report_number"),
                    content_hash=Provenance.compute_hash(meta.get("content", "")),
                )

            snippet = meta.get("content", "")[:350]
            if len(meta.get("content", "")) > 350:
                snippet += "..."

            results.append(
                RetrievalResult(
                    document_id=meta.get("document_id", "doc-unknown"),
                    chunk_id=c_id,
                    title=meta.get("title", "Untitled Technical Report"),
                    source=meta.get("source", "Unknown"),
                    authors=meta.get("authors", []),
                    year=meta.get("year"),
                    page=meta.get("page"),
                    snippet=snippet,
                    url=meta.get("url"),
                    relevance=round(combined_score, 4),
                    provenance=prov,
                    object_type=ScientificObjectType.RETRIEVED_REFERENCE,
                )
            )

        # Sort descending by relevance score
        results.sort(key=lambda r: r.relevance, reverse=True)
        return results[:k]
