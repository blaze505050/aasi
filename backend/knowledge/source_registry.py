"""Extensible scientific source registry with strict license and access handling."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceIdentifier(str, Enum):
    """Standardized identifiers for scientific literature and data sources."""
    NASA_NTRS = "NASA_NTRS"          # NASA Technical Reports Server
    NASA_DATA = "NASA_DATA"          # NASA Open Data Portal
    NACA = "NACA"                    # NACA Historical Aerodynamics (1915-1958)
    ESA = "ESA"                      # European Space Agency Technical Material
    ISRO = "ISRO"                    # Indian Space Research Organisation Public Reports
    ARXIV = "ARXIV"                  # arXiv Cornell Open Access Preprints
    OPEN_RESEARCH = "OPEN_RESEARCH"  # Open University Theses & Open Access Journals
    OPEN_DATASETS = "OPEN_DATASETS"  # Curated Open Aerodynamic / Space Datasets


class SourceMetadata(BaseModel):
    """Descriptive metadata and access parameters for a scientific source."""
    source_id: SourceIdentifier
    name: str
    organization: str
    homepage: str
    api_endpoint: Optional[str] = None
    license_type: str
    access_status: str  # OPEN, RESTRICTED, PUBLIC_DOMAIN
    search_supported: bool
    automated_ingestion: bool
    update_strategy: str
    implementation_status: str  # IMPLEMENTED, EXPERIMENTAL, NOT_IMPLEMENTED
    notes: Optional[str] = None


class BaseSourceAdapter(ABC):
    """Abstract interface that all scientific source adapters must implement."""

    def __init__(self, metadata: SourceMetadata):
        self.metadata = metadata

    @property
    def source_id(self) -> SourceIdentifier:
        return self.metadata.source_id

    @property
    def name(self) -> str:
        return self.metadata.name

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search metadata repository for documents matching query string."""
        pass

    @abstractmethod
    def fetch_document(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieve full document metadata and text/PDF payload if permitted."""
        pass

    @abstractmethod
    def extract_metadata(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize source-specific fields into standard AASI metadata."""
        pass

    def check_access_permission(self, item_id: str) -> bool:
        """Check whether the item is legally permissible for local ingestion."""
        return self.metadata.access_status in ("OPEN", "PUBLIC_DOMAIN")


class NasaNtrsAdapter(BaseSourceAdapter):
    """Adapter for NASA Technical Reports Server (NTRS)."""

    def __init__(self):
        super().__init__(
            SourceMetadata(
                source_id=SourceIdentifier.NASA_NTRS,
                name="NASA Technical Reports Server",
                organization="National Aeronautics and Space Administration (NASA)",
                homepage="https://ntrs.nasa.gov",
                api_endpoint="https://ntrs.nasa.gov/api/citations",
                license_type="Public Domain (NASA Technical Reports)",
                access_status="PUBLIC_DOMAIN",
                search_supported=True,
                automated_ingestion=True,
                update_strategy="On-demand API queries and cached technical report ingestion",
                implementation_status="IMPLEMENTED",
                notes="Primary NASA scientific publication server with open REST metadata API."
            )
        )

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        # Provided by backend.knowledge.nasa_adapter
        return []

    def fetch_document(self, identifier: str) -> Optional[Dict[str, Any]]:
        return None

    def extract_metadata(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        return raw_item


class NacaAdapter(BaseSourceAdapter):
    """Adapter for NACA (National Advisory Committee for Aeronautics) historical reports."""

    def __init__(self):
        super().__init__(
            SourceMetadata(
                source_id=SourceIdentifier.NACA,
                name="NACA Technical Reports & Memorandums",
                organization="National Advisory Committee for Aeronautics (1915-1958)",
                homepage="https://ntrs.nasa.gov/search?q=naca",
                api_endpoint="https://ntrs.nasa.gov/api/citations",
                license_type="Public Domain (US Government Work pre-1958)",
                access_status="PUBLIC_DOMAIN",
                search_supported=True,
                automated_ingestion=True,
                update_strategy="Curated historical aerodynamic corpus and NTRS historical archives",
                implementation_status="IMPLEMENTED",
                notes="Covers fundamental experimental aerodynamics, NACA 4-digit and 5-digit airfoils, and high-speed flight."
            )
        )

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        return []

    def fetch_document(self, identifier: str) -> Optional[Dict[str, Any]]:
        return None

    def extract_metadata(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        return raw_item


class ArxivAdapter(BaseSourceAdapter):
    """Adapter for arXiv Open Access Preprints in aerospace, fluid dynamics, and physics."""

    def __init__(self):
        super().__init__(
            SourceMetadata(
                source_id=SourceIdentifier.ARXIV,
                name="arXiv Aerospace & Physics Preprints",
                organization="Cornell University / arXiv.org",
                homepage="https://arxiv.org",
                api_endpoint="http://export.arxiv.org/api/query",
                license_type="Open Access (CC-BY, arXiv.org non-exclusive)",
                access_status="OPEN",
                search_supported=True,
                automated_ingestion=True,
                update_strategy="arXiv API queries for physics.flu-dyn and astro-ph",
                implementation_status="IMPLEMENTED",
                notes="Covers modern preprints in fluid dynamics, astrodynamics, and computational physics."
            )
        )

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        return []

    def fetch_document(self, identifier: str) -> Optional[Dict[str, Any]]:
        return None

    def extract_metadata(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        return raw_item


class EsaAdapter(BaseSourceAdapter):
    """Adapter for European Space Agency technical material."""

    def __init__(self):
        super().__init__(
            SourceMetadata(
                source_id=SourceIdentifier.ESA,
                name="European Space Agency Technical Publications",
                organization="European Space Agency (ESA)",
                homepage="https://www.esa.int",
                api_endpoint=None,
                license_type="ESA Open Access / Copyright ESA",
                access_status="OPEN",
                search_supported=False,
                automated_ingestion=False,
                update_strategy="Manual curation of public technical documents",
                implementation_status="NOT IMPLEMENTED — REASON: ESA does not provide a public unauthenticated REST API for bulk technical report retrieval. Ingestion requires manually curated public open-access documents.",
                notes="Future implementation will support ESA Open Access Repository via OAI-PMH."
            )
        )

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        return []

    def fetch_document(self, identifier: str) -> Optional[Dict[str, Any]]:
        return None

    def extract_metadata(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        return raw_item


class IsroAdapter(BaseSourceAdapter):
    """Adapter for Indian Space Research Organisation public technical releases."""

    def __init__(self):
        super().__init__(
            SourceMetadata(
                source_id=SourceIdentifier.ISRO,
                name="ISRO Technical Publications & Missions",
                organization="Indian Space Research Organisation (ISRO)",
                homepage="https://www.isro.gov.in",
                api_endpoint=None,
                license_type="Government of India Public Use",
                access_status="OPEN",
                search_supported=False,
                automated_ingestion=False,
                update_strategy="Manual curation of official public mission archives",
                implementation_status="NOT IMPLEMENTED — REASON: ISRO scientific publications and payload telemetry are published across distributed portal documents without an open automated query API. Automated scraping without explicit API is prohibited.",
                notes="Future implementation will support validated mission archives and open payload data."
            )
        )

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        return []

    def fetch_document(self, identifier: str) -> Optional[Dict[str, Any]]:
        return None

    def extract_metadata(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        return raw_item


class OpenDatasetsAdapter(BaseSourceAdapter):
    """Adapter for open aerospace and aerodynamic benchmarks."""

    def __init__(self):
        super().__init__(
            SourceMetadata(
                source_id=SourceIdentifier.OPEN_DATASETS,
                name="AASI Curated Open Datasets",
                organization="AASI Open Aerodynamic & Space Benchmark Catalog",
                homepage="https://github.com/blaze505050/aasi",
                api_endpoint=None,
                license_type="Public Domain / CC0 / CC-BY-4.0",
                access_status="PUBLIC_DOMAIN",
                search_supported=True,
                automated_ingestion=True,
                update_strategy="Internal dataset registry catalog with condition search",
                implementation_status="IMPLEMENTED",
                notes="Structured physical aerodynamic, flight, and CFD benchmark data."
            )
        )

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        return []

    def fetch_document(self, identifier: str) -> Optional[Dict[str, Any]]:
        return None

    def extract_metadata(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        return raw_item


class SourceRegistry:
    """Registry coordinating all registered scientific sources and adapter instances."""

    def __init__(self):
        self._adapters: Dict[SourceIdentifier, BaseSourceAdapter] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(NasaNtrsAdapter())
        self.register(NacaAdapter())
        self.register(ArxivAdapter())
        self.register(EsaAdapter())
        self.register(IsroAdapter())
        self.register(OpenDatasetsAdapter())

    def register(self, adapter: BaseSourceAdapter):
        self._adapters[adapter.source_id] = adapter

    def get(self, source_id: SourceIdentifier | str) -> Optional[BaseSourceAdapter]:
        if isinstance(source_id, str):
            try:
                source_id = SourceIdentifier(source_id)
            except ValueError:
                return None
        return self._adapters.get(source_id)

    def list_sources(self) -> List[SourceMetadata]:
        return [adapter.metadata for adapter in self._adapters.values()]
