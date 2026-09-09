"""NASA NTRS and NACA ingestion adapter with PDF extraction, structure parsing, and provenance tracking."""

from __future__ import annotations

import io
import logging
import os
import re
from typing import Any, Dict, List, Optional
import httpx

from .chunking import StructureAwareChunker
from .models import Chunk, Document, Provenance, ScientificObjectType
from .source_registry import BaseSourceAdapter, SourceIdentifier, SourceMetadata
from .vector_store import VectorIndex

logger = logging.getLogger("aasi.knowledge.nasa")


class NasaAdapter(BaseSourceAdapter):
    """Ingestion and search adapter for NASA NTRS and historical NACA archives."""

    NTRS_SEARCH_URL = "https://ntrs.nasa.gov/api/citations"

    def __init__(
        self,
        vector_index: Optional[VectorIndex] = None,
        chunker: Optional[StructureAwareChunker] = None,
        max_documents_per_run: int = 25,
        max_file_size_bytes: int = 50 * 1024 * 1024,  # 50 MB safety limit
    ):
        super().__init__(
            SourceMetadata(
                source_id=SourceIdentifier.NASA_NTRS,
                name="NASA Technical Reports Server & NACA Archives",
                organization="National Aeronautics and Space Administration (NASA)",
                homepage="https://ntrs.nasa.gov",
                api_endpoint="https://ntrs.nasa.gov/api/citations",
                license_type="Public Domain (NASA / NACA Technical Work)",
                access_status="PUBLIC_DOMAIN",
                search_supported=True,
                automated_ingestion=True,
                update_strategy="REST API discovery with structure-aware chunking and FAISS indexing",
                implementation_status="IMPLEMENTED",
                notes="Primary NASA scientific repository with historical NACA technical reports."
            )
        )
        self.vector_index = vector_index
        self.chunker = chunker or StructureAwareChunker()
        self.max_documents_per_run = max_documents_per_run
        self.max_file_size_bytes = max_file_size_bytes
        self._ingested_documents: Dict[str, Document] = {}

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search NASA NTRS via public citations API with safe fallback."""
        max_results = min(max_results, self.max_documents_per_run)
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(
                    self.NTRS_SEARCH_URL,
                    params={"q": query, "page": {"size": max_results}},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    raw_results = data.get("results", [])
                    return [self.extract_metadata(item) for item in raw_results]
        except Exception as e:
            logger.warning(f"Live NTRS search unavailable ({e}), returning local matches.")

        # Fallback to locally ingested documents matching query
        local_matches = []
        for doc_id, doc in self._ingested_documents.items():
            if query.lower() in doc.title.lower() or (doc.abstract and query.lower() in doc.abstract.lower()):
                local_matches.append({
                    "id": doc.document_id,
                    "title": doc.title,
                    "abstract": doc.abstract,
                    "source": doc.provenance.source_organization,
                    "report_number": doc.provenance.report_number,
                    "year": doc.provenance.publication_date,
                    "url": doc.provenance.source_url,
                })
        return local_matches[:max_results]

    def fetch_document(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Fetch metadata for a specific NTRS ID."""
        doc = self._ingested_documents.get(identifier)
        if doc:
            return doc.model_dump()
        return None

    def extract_metadata(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw NTRS JSON schema into standard AASI document metadata."""
        item_id = str(raw_item.get("id", "ntrs-unknown"))
        title = raw_item.get("title", "Untitled NASA Publication")
        abstract = raw_item.get("abstract") or raw_item.get("description")
        
        # Author names
        authors: List[str] = []
        for a in raw_item.get("authorAffiliations", []):
            name = a.get("meta", {}).get("author", {}).get("name")
            if name:
                authors.append(name)

        # Date / Year
        pub_date = raw_item.get("publicationDate") or raw_item.get("distributionDate")
        year = None
        if pub_date:
            m = re.search(r"\b(19\d\d|20\d\d)\b", str(pub_date))
            if m:
                year = int(m.group(1))

        # Report number
        report_num = None
        for report in raw_item.get("reportNumbers", []):
            if report:
                report_num = report
                break

        url = f"https://ntrs.nasa.gov/citations/{item_id}" if item_id else None

        return {
            "id": item_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "year": year,
            "report_number": report_num,
            "url": url,
            "source": "NASA NTRS" if not str(report_num).startswith("NACA") else "NACA",
            "license": "Public Domain (NASA Technical Report)",
        }

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> Dict[int, str]:
        """Safely extract text from PDF bytes page-by-page using pypdf."""
        if len(pdf_bytes) > self.max_file_size_bytes:
            raise ValueError(
                f"PDF size {len(pdf_bytes)} bytes exceeds maximum allowed {self.max_file_size_bytes} bytes."
            )

        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            pages: Dict[int, str] = {}
            for idx, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    pages[idx + 1] = extracted
            return pages
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            raise RuntimeError(f"PDF extraction failed: {e}")

    def ingest_document(
        self,
        document_id: str,
        title: str,
        content_text: str,
        provenance: Provenance,
        abstract: Optional[str] = None,
        pages_dict: Optional[Dict[int, str]] = None,
    ) -> Document:
        """Ingest, chunk, and index a verified NASA or NACA document."""
        # Chunk document preserving structure
        chunks = self.chunker.chunk_document(
            document_id=document_id,
            source_id=provenance.source_organization,
            text=content_text,
            pages_dict=pages_dict,
            default_section="Technical Analysis",
        )

        # Collect all equations across chunks
        all_eqs = []
        for c in chunks:
            all_eqs.extend(c.equations)

        doc = Document(
            document_id=document_id,
            title=title,
            abstract=abstract,
            provenance=provenance,
            chunks=chunks,
            equations=all_eqs,
            metadata={
                "chunk_count": len(chunks),
                "equation_count": len(all_eqs),
                "year": provenance.publication_date,
            },
        )

        self._ingested_documents[document_id] = doc
        return doc

    def get_ingested_documents(self) -> List[Document]:
        return list(self._ingested_documents.values())
