"""
AASI Real arXiv Preprints Connector.

Connects to the official arXiv Atom/XML API (http://export.arxiv.org/api/query)
to query real aerospace, fluid dynamics, and computational physics preprints.
Strictly classifies all records as UNVERIFIED_PREPRINT.
Includes polite rate limiting and robust offline/timeout fallback.
"""

import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from backend.sources.base_connector import BaseSourceConnector
from backend.sources.models import (
    AccessMethod,
    EpistemicClassification,
    KnowledgeType,
    SourceStatus,
    SourceDocument,
    ProvenanceChain,
    ProvenanceVerificationLevel,
)


class ArxivSourceConnector(BaseSourceConnector):
    """Real arXiv API connector for aerodynamics, fluid dynamics, and computational physics."""

    API_URL = "http://export.arxiv.org/api/query"
    RATE_LIMIT_DELAY_SEC = 3.0  # Respect arXiv 3s politeness guideline
    ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

    def __init__(self, timeout_sec: float = 5.0):
        super().__init__(
            source_id="ARXIV_AERO",
            name="arXiv Fluid Dynamics & Aerospace Preprints",
            organization="arXiv / Cornell University",
            category="CFD",
            base_url="https://export.arxiv.org/api",
            access_method=AccessMethod.DIRECT_API,
            epistemic_classification=EpistemicClassification.UNVERIFIED_PREPRINT,
            license="arXiv Non-exclusive License / CC-BY",
            citation_policy="Cite arXiv identifier and author preprint; explicitly note non-peer-reviewed status",
            content_types=[KnowledgeType.PAPER, KnowledgeType.DOCUMENT],
            status=SourceStatus.ACTIVE,
            notes="Live direct query to arXiv API. Preprints are strictly classified as UNVERIFIED_PREPRINT.",
        )
        self.timeout_sec = timeout_sec
        self._last_request_time: float = 0.0
        self._offline_mode: bool = False

    def _enforce_rate_limit(self):
        """Enforces at least 3 seconds between consecutive external arXiv calls."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY_SEC:
            time.sleep(self.RATE_LIMIT_DELAY_SEC - elapsed)
        self._last_request_time = time.time()

    def search(self, query: str, limit: int = 10, **kwargs) -> List[SourceDocument]:
        """Search arXiv by keyword or categories.
        
        Falls back cleanly to OFFLINE_FALLBACK if network is unreachable,
        never crashing and never fabricating fake preprints.
        """
        self.total_queries += 1
        self.last_query_time = datetime.now(timezone.utc).isoformat()

        # Build clean query targeting aerospace/fluid mechanics if generic
        q_clean = query.strip()
        if not q_clean:
            q_clean = "aerodynamics OR fluid dynamics"
        
        # We search across fluid dynamics (physics.flu-dyn) and computational physics (physics.comp-ph)
        search_query = f"all:{q_clean} AND (cat:physics.flu-dyn OR cat:physics.comp-ph OR cat:math.NA)"
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max(1, min(limit, 25)),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        url = f"{self.API_URL}?{urllib.parse.urlencode(params)}"

        try:
            self._enforce_rate_limit()
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AASI-Scientific-Agent/1.0 (mailto:research@aasi.local)"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                if resp.status != 200:
                    self.total_errors += 1
                    self.last_status = f"HTTP_{resp.status}"
                    return []
                xml_data = resp.read()

            self.last_status = "ONLINE_OK"
            return self._parse_atom_feed(xml_data)

        except Exception as e:
            # Explicit fail-closed / offline fallback: never fabricate papers
            self.total_errors += 1
            self.last_status = f"OFFLINE_FALLBACK: {type(e).__name__}"
            return []

    def fetch(self, document_id: str) -> Optional[SourceDocument]:
        """Fetch a specific arXiv paper by ID (e.g. '2301.01234' or 'ARXIV:2301.01234')."""
        clean_id = document_id.replace("ARXIV:", "").strip()
        url = f"{self.API_URL}?id_list={urllib.parse.quote(clean_id)}"
        try:
            self._enforce_rate_limit()
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AASI-Scientific-Agent/1.0 (mailto:research@aasi.local)"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                if resp.status != 200:
                    return None
                docs = self._parse_atom_feed(resp.read())
                return docs[0] if docs else None
        except Exception as e:
            self.last_status = f"OFFLINE_FALLBACK: {type(e).__name__}"
            return None

    def _parse_atom_feed(self, xml_bytes: bytes) -> List[SourceDocument]:
        """Parses arXiv Atom XML into strongly typed SourceDocuments."""
        root = ET.fromstring(xml_bytes)
        documents: List[SourceDocument] = []

        for entry in root.findall("atom:entry", self.ATOM_NS):
            id_elem = entry.find("atom:id", self.ATOM_NS)
            title_elem = entry.find("atom:title", self.ATOM_NS)
            summary_elem = entry.find("atom:summary", self.ATOM_NS)
            published_elem = entry.find("atom:published", self.ATOM_NS)

            raw_id = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
            arxiv_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id
            doc_id = f"ARXIV:{arxiv_id}"

            title = " ".join((title_elem.text or "").strip().split())
            abstract = " ".join((summary_elem.text or "").strip().split())
            pub_date = (published_elem.text or "")[:10]

            authors: List[str] = []
            for author in entry.findall("atom:author", self.ATOM_NS):
                name_elem = author.find("atom:name", self.ATOM_NS)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            # Cryptographic provenance chain
            meta_hash = self.build_metadata_hash(doc_id, title, pub_date)
            chain = ProvenanceChain(
                metadata_descriptor_hash=meta_hash,
                raw_artifact_hash=None,
                extracted_content_hash=None,
                verification_level=ProvenanceVerificationLevel.METADATA_VERIFIED,
            )

            doc = SourceDocument(
                document_id=doc_id,
                source_id=self.source_id,
                title=title,
                authors=authors,
                organization="arXiv",
                publication_date=pub_date,
                url=raw_id if raw_id.startswith("http") else f"https://arxiv.org/abs/{arxiv_id}",
                license=self.license,
                access_method=AccessMethod.DIRECT_API,
                epistemic_classification=EpistemicClassification.UNVERIFIED_PREPRINT,
                abstract=abstract,
                doi=None,
                report_number=arxiv_id,
                provenance_chain=chain,
            )
            documents.append(doc)

        return documents
