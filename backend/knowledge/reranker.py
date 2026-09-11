"""
AASI Scientific Two-Stage Reranker & Epistemic Authority Evaluator.

Refines initial hybrid dense/lexical candidate pools using:
1. Exact equation, report number, and flow variable matching
2. Epistemic authority tier weighting (Peer-Reviewed > Agency Reports > Preprints)
3. Content redundancy suppression / Jaccard token deduplication
4. Reciprocal Rank Fusion (RRF) score combination
"""

import re
from typing import List, Dict, Any, Set, Optional, Tuple
from backend.knowledge.models import RetrievalResult, Provenance
from backend.sources.models import EpistemicClassification


class ScientificReranker:
    """Stage 2 reranker prioritizing epistemic authority and exact technical tokens."""

    AUTHORITY_WEIGHTS: Dict[str, float] = {
        "PEER_REVIEWED_LITERATURE": 1.25,
        "OFFICIAL_STANDARD": 1.25,
        "AGENCY_TECHNICAL_REPORT": 1.20,
        "STATIC_HISTORICAL_SEED": 1.10,
        "PUBLIC_COMMERCIAL_RELEASE": 0.95,
        "UNVERIFIED_PREPRINT": 0.85,
    }

    # Technical identifiers that warrant immediate exact-match elevation
    EXACT_IDENTIFIERS = [
        r"nasa-[a-z]+-[a-z0-9\-]+",
        r"naca\s*\d{4,5}",
        r"naca-[a-z]+-\d+",
        r"faa-[a-z0-9\-]+",
        r"arxiv:\d{4}\.\d{4,5}",
        r"k-omega\s*(?:sst)?",
        r"spalart-allmaras",
        r"cl\s*=\s*[-+]?\d*\.?\d+",
        r"cd\s*=\s*[-+]?\d*\.?\d+",
    ]

    def rerank(
        self,
        query: str,
        candidates: List[RetrievalResult],
        top_k: int = 5,
        diversity_threshold: float = 0.65,
    ) -> List[RetrievalResult]:
        """Reranks candidates and enforces diversity across the top-k results."""
        if not candidates:
            return []

        q_lower = query.lower()
        exact_tokens = self._extract_exact_tokens(q_lower)

        scored: List[Tuple[float, RetrievalResult]] = []

        for res in candidates:
            base_score = res.relevance
            snippet_lower = (res.snippet + " " + res.title).lower()

            # 1. Epistemic Authority Weight
            authority_mult = self._get_authority_multiplier(res)
            score = base_score * authority_mult

            # 2. Exact Technical Identifier Boost
            match_count = 0
            for token in exact_tokens:
                if token in snippet_lower:
                    match_count += 1
            if match_count > 0:
                score += min(0.35, 0.15 * match_count)

            # Cap score between 0 and 1
            final_score = round(min(1.0, max(0.0, score)), 4)
            scored.append((final_score, res))

        # Sort descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # 3. Redundancy & Diversity Suppression
        selected: List[RetrievalResult] = []
        seen_token_sets: List[Set[str]] = []

        for final_score, item in scored:
            tokens = set(re.findall(r"\b\w{4,}\b", item.snippet.lower()))
            is_redundant = False
            for seen in seen_token_sets:
                intersection = len(tokens.intersection(seen))
                union = len(tokens.union(seen))
                jaccard = (intersection / union) if union > 0 else 0.0
                if jaccard > diversity_threshold and item.document_id == selected[seen_token_sets.index(seen)].document_id:
                    is_redundant = True
                    break

            if not is_redundant:
                # Update relevance to final reranked score
                item.relevance = final_score
                selected.append(item)
                seen_token_sets.append(tokens)

            if len(selected) >= top_k:
                break

        return selected

    def _get_authority_multiplier(self, res: RetrievalResult) -> float:
        """Determines authority tier based on source, title, and provenance metadata."""
        src = (res.source or "").upper()
        title = (res.title or "").upper()
        doc_id = (res.document_id or "").upper()

        if "ARXIV" in src or "ARXIV" in doc_id or "PREPRINT" in title:
            return self.AUTHORITY_WEIGHTS["UNVERIFIED_PREPRINT"]
        if "SPACEX" in src or "COMMERCIAL" in title:
            return self.AUTHORITY_WEIGHTS["PUBLIC_COMMERCIAL_RELEASE"]
        if "NASA" in src or "NACA" in src or "ESA" in src or "ISRO" in src:
            return self.AUTHORITY_WEIGHTS["AGENCY_TECHNICAL_REPORT"]
        if "AIAA" in src or "JOURNAL" in src or "IEEE" in src:
            return self.AUTHORITY_WEIGHTS["PEER_REVIEWED_LITERATURE"]

        return 1.0

    def _extract_exact_tokens(self, query: str) -> List[str]:
        """Extracts technical codes, equations, and specific identifiers from query."""
        tokens: List[str] = []
        for pat in self.EXACT_IDENTIFIERS:
            matches = re.findall(pat, query)
            tokens.extend(matches)
        return tokens


def format_scientific_citation(
    title: str,
    source: str,
    year: Optional[Any] = None,
    report_number: Optional[str] = None,
    content_hash: Optional[str] = None,
    url: Optional[str] = None,
    epistemic_classification: Optional[str] = None,
) -> str:
    """Formats an academically rigorous citation with cryptographic hash and epistemic badge."""
    yr_str = f"({year})" if year else "(n.d.)"
    rep_str = f" [{report_number}]" if report_number else ""
    hash_str = f" [Hash: `{content_hash[:12]}`]" if content_hash else ""
    
    badge = ""
    if epistemic_classification:
        badge = f" **[{epistemic_classification}]**"
    elif "arxiv" in source.lower():
        badge = " **[UNVERIFIED_PREPRINT]**"
    elif "spacex" in source.lower():
        badge = " **[COMMERCIAL_RELEASE]**"
    elif any(k in source.lower() for k in ["nasa", "naca", "esa", "isro"]):
        badge = " **[AGENCY_TECHNICAL_REPORT]**"

    link = f"[{title}]({url})" if url else f"*{title}*"
    return f"{link} {yr_str}. {source}{rep_str}.{badge}{hash_str}"
