"""
AASI Dataset Authenticity Audit Models.

Pydantic schemas representing rigorous authenticity, existence, licensing,
and numerical sanity audit findings across registered physical datasets.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class AuditStatusEnum(str, Enum):
    """Honest authenticity status of an audited physical dataset."""
    VERIFIED = "VERIFIED"                  # Raw data exists locally, validated schema & physical bounds
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"  # Raw data exists with minor missing metadata or subset
    METADATA_ONLY = "METADATA_ONLY"        # Registry entry exists, but raw payload not downloaded locally
    UNAVAILABLE = "UNAVAILABLE"            # Remote source unreachable or decommissioned
    INVALID = "INVALID"                    # Data exists but fails schema, checksum, or physical sanity
    DEMO_DATA = "DEMO_DATA"                # Illustrative synthetic/mock payload for testing only


class DiscrepancyReport(BaseModel):
    """Detailed record of a discrepancy identified during audit."""
    field_name: str
    declared_value: Any
    actual_value: Any
    severity: str = "WARNING"  # INFO, WARNING, ERROR
    explanation: str


class DatasetAuditResult(BaseModel):
    """Comprehensive audit result for a single registered dataset."""
    dataset_id: str
    dataset_name: str
    source_url: Optional[str] = None
    source_type: str = "PUBLIC_ARCHIVE"
    access_status: str = "ACCESSIBLE"
    download_status: str = "NOT_DOWNLOADED"  # LOCAL_EXISTS, NOT_DOWNLOADED, DOWNLOAD_FAILED
    local_path: Optional[str] = None
    size_bytes_actual: Optional[int] = None
    sample_count_declared: Optional[int] = None
    sample_count_actual: Optional[int] = None
    geometry_count_actual: Optional[int] = None
    license_status: str = "VERIFIED_OPEN"    # VERIFIED_OPEN, RESTRICTED, UNKNOWN, MISMATCH
    license_declared: str = ""
    license_actual: str = ""
    provenance_status: str = "DOCUMENTED"     # DOCUMENTED, PARTIAL, MISSING
    missing_values_count: int = 0
    duplicate_samples_count: int = 0
    invalid_records_count: int = 0
    nan_inf_count: int = 0
    unit_status: str = "SPECIFIED"            # SPECIFIED, PARTIAL, UNKNOWN
    schema_status: str = "CONFORMANT"         # CONFORMANT, NON_CONFORMANT
    physical_sanity_status: str = "VALID"     # VALID, BOUNDARY_VIOLATION, SUSPICIOUS
    overall_status: AuditStatusEnum = AuditStatusEnum.METADATA_ONLY
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    audited_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DatasetAuditSummary(BaseModel):
    """Repository-wide dataset layer audit summary."""
    total_datasets_audited: int
    verified_count: int
    partially_verified_count: int
    metadata_only_count: int
    demo_data_count: int
    invalid_count: int
    unavailable_count: int
    audited_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    results: List[DatasetAuditResult] = Field(default_factory=list)
