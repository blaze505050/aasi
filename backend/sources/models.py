"""
AASI Scientific Source Federation Models.

Defines KnowledgeType (20 types), AccessMethod, SourceMetadata,
and CurrentInfoItem.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class KnowledgeType(str, Enum):
    DOCUMENT = "DOCUMENT"
    PAPER = "PAPER"
    TECHNICAL_REPORT = "TECHNICAL_REPORT"
    DATASET = "DATASET"
    EXPERIMENT = "EXPERIMENT"
    CFD_RESULT = "CFD_RESULT"
    SIMULATION = "SIMULATION"
    EQUATION = "EQUATION"
    TABLE = "TABLE"
    FIGURE = "FIGURE"
    MISSION = "MISSION"
    SPACECRAFT = "SPACECRAFT"
    ROCKET = "ROCKET"
    AIRCRAFT = "AIRCRAFT"
    MATERIAL = "MATERIAL"
    SOFTWARE = "SOFTWARE"
    NEWS = "NEWS"
    PRESS_RELEASE = "PRESS_RELEASE"
    STANDARD = "STANDARD"
    TEXTBOOK = "TEXTBOOK"
    THESIS = "THESIS"


class AccessMethod(str, Enum):
    DIRECT_API = "DIRECT_API"
    URL_REGISTRY = "URL_REGISTRY"
    METADATA_INGESTION = "METADATA_INGESTION"
    MANUAL_IMPORT = "MANUAL_IMPORT"
    RESTRICTED = "RESTRICTED"
    STATIC_SEED = "STATIC_SEED"
    METADATA_ONLY = "METADATA_ONLY"
    PUBLIC_DOWNLOAD = "PUBLIC_DOWNLOAD"
    LIVE_API = "LIVE_API"
    DISABLED = "DISABLED"


class SourceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PARTIAL = "PARTIAL"
    MANUAL_ONLY = "MANUAL_ONLY"
    PLANNED = "PLANNED"
    UNSUPPORTED = "UNSUPPORTED"


class SourceMetadata(BaseModel):
    source_id: str
    organization: str
    name: str
    category: str
    base_url: str
    access_method: AccessMethod
    license: str
    update_frequency: str
    public_access: bool
    citation_policy: str
    content_types: List[KnowledgeType]
    status: SourceStatus
    notes: Optional[str] = None


class CurrentInfoCategory(str, Enum):
    LAUNCHES = "launches"
    MISSIONS = "missions"
    SPACECRAFT = "spacecraft"
    ROCKET_TESTS = "rocket_tests"
    DISCOVERIES = "discoveries"
    ASTRONOMY = "astronomy"
    ASTROPHYSICS = "astrophysics"
    SPACE_WEATHER = "space_weather"
    AEROSPACE_RESEARCH = "aerospace_research"
    AGENCY_UPDATES = "agency_updates"


class CurrentInfoItem(BaseModel):
    item_id: str
    title: str
    organization: str
    category: CurrentInfoCategory
    summary: str
    source_url: str
    published_at: str
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    age_days: int = 0
    freshness_status: str = "STALE_STATIC_SEED"
    acquisition_method: str = "STATIC_SEED_INDEX"
    label: str = "CURRENT_INFORMATION"
    provenance_hash: str


# --- First-Class Provenance & Source Fabric Models ---

class EpistemicClassification(str, Enum):
    PEER_REVIEWED_LITERATURE = "PEER_REVIEWED_LITERATURE"
    AGENCY_TECHNICAL_REPORT = "AGENCY_TECHNICAL_REPORT"
    PUBLIC_COMMERCIAL_RELEASE = "PUBLIC_COMMERCIAL_RELEASE"
    STATIC_HISTORICAL_SEED = "STATIC_HISTORICAL_SEED"
    OFFICIAL_STANDARD = "OFFICIAL_STANDARD"
    UNVERIFIED_PREPRINT = "UNVERIFIED_PREPRINT"


class CommercialPublicityStatus(str, Enum):
    PUBLICLY_VERIFIED_INFORMATION = "PUBLICLY_VERIFIED_INFORMATION"
    PROPRIETARY_UNAVAILABLE = "PROPRIETARY_UNAVAILABLE"


class ProvenanceVerificationLevel(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    METADATA_VERIFIED = "METADATA_VERIFIED"
    RAW_BYTE_VERIFIED = "RAW_BYTE_VERIFIED"
    CONTENT_VERIFIED = "CONTENT_VERIFIED"


class ProvenanceChain(BaseModel):
    """Rigorous cryptographic provenance chain tracking document authenticity.
    
    Explicitly separates metadata string hashes from true raw artifact byte hashes.
    """
    metadata_descriptor_hash: str = Field(
        ...,
        description="SHA-256 hash of author, title, publication date metadata string."
    )
    raw_artifact_hash: Optional[str] = Field(
        None,
        description="Cryptographic SHA-256 hash of the downloaded PDF/file bytes. Null if not downloaded."
    )
    extracted_content_hash: Optional[str] = Field(
        None,
        description="Cryptographic SHA-256 hash of the normalized extracted text or tabular data."
    )
    retrieval_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of retrieval."
    )
    parser_version: Optional[str] = Field(
        "aasi-parser-v1.0",
        description="Version identifier of the ingestion parser."
    )
    verification_level: ProvenanceVerificationLevel = Field(
        default=ProvenanceVerificationLevel.METADATA_VERIFIED,
        description="Proven verifiable depth of this artifact."
    )


class DocumentFragment(BaseModel):
    """A granular, citable section or table from a verified source document."""
    fragment_id: str
    document_id: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    content: str
    content_hash: str
    fragment_type: str = "TEXT"  # TEXT, TABLE, FIGURE, EQUATION


class SourceDocument(BaseModel):
    """Canonical scientific document representation in the AASI source fabric."""
    document_id: str
    source_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    organization: str
    publication_date: str
    url: str
    license: str
    access_method: AccessMethod
    epistemic_classification: EpistemicClassification = EpistemicClassification.AGENCY_TECHNICAL_REPORT
    commercial_status: Optional[CommercialPublicityStatus] = None
    abstract: Optional[str] = None
    doi: Optional[str] = None
    report_number: Optional[str] = None
    provenance_chain: ProvenanceChain
    fragments: List[DocumentFragment] = Field(default_factory=list)
