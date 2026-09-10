"""
Tests for Phase 6 Dataset Authenticity Audit.

Verifies that:
- Local disk datasets are audited honestly
- DATASET-AUTHENTIC-AIRFOILS-V1 is classified as VERIFIED with real sample files
- Metadata-only records (e.g. DATASET-AIRFRANS-1K, NASA-CRM) are honestly flagged as METADATA_ONLY
- No false claims or hallucinated experimental polars are accepted.
"""

import pytest
from backend.datasets.audit import DatasetAuditService
from backend.datasets.audit_models import AuditStatusEnum, DatasetAuditSummary


def test_audit_authentic_airfoils():
    service = DatasetAuditService()
    result = service.audit_dataset("DATASET-AUTHENTIC-AIRFOILS-V1")
    assert result.dataset_id == "DATASET-AUTHENTIC-AIRFOILS-V1"
    assert result.overall_status == AuditStatusEnum.VERIFIED
    assert result.sample_count_actual >= 1000
    assert result.physical_sanity_status == "VALID"
    assert len(result.errors) == 0


def test_audit_metadata_only_datasets():
    service = DatasetAuditService()
    result = service.audit_dataset("DATASET-AIRFRANS-1K")
    assert result.dataset_id == "DATASET-AIRFRANS-1K"
    assert result.overall_status == AuditStatusEnum.METADATA_ONLY
    assert any("not present locally" in w for w in result.warnings)



def test_audit_summary_totals():
    summary = DatasetAuditService().audit_all()
    assert isinstance(summary, DatasetAuditSummary)
    assert summary.total_datasets_audited >= 4
    assert summary.verified_count >= 1
    assert summary.metadata_only_count >= 3
    assert summary.invalid_count == 0
