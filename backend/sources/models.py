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
    label: str = "CURRENT_INFORMATION"
    provenance_hash: str
