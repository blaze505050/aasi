"""
Comprehensive test suite for Phase 3 Physical Evidence Reconciliation.
Tests multi-tier data ingestion, strict anti-fabrication uncertainty rule,
contradiction flagging, and cryptographic audit hashing.
"""

import pytest
from backend.science.evidence_bridge import (
    PhysicalEvidenceBridge,
    EvidenceReconciliationSummary,
)
from backend.science.evidence import ScientificEvidenceItem, EvidenceTier, UncertaintyStatus


def test_reconcile_investigation_results():
    summary = PhysicalEvidenceBridge.reconcile_investigation_results(
        geometry="NACA0012",
        panel_results={"CL": 0.485, "CD": 0.0075, "CM": -0.001},
        aerodb_results={"cl": 0.44, "cd": 0.0062, "source": "Abbott Report 824 Archive"},
        benchmark_results={"reference_cl": 0.44, "reference_cd": 0.0062, "uncertainty_pct": 2.5},
    )

    assert isinstance(summary, EvidenceReconciliationSummary)
    assert summary.items_count >= 4
    assert summary.physical_consensus_valid is True
    assert summary.consensus_cl is not None
    assert summary.consensus_cd is not None
    assert summary.consensus_ld is not None
    assert len(summary.provenance_hash) == 64

    # Discrepancy between panel solver (0.485) and experimental (0.44)
    assert len(summary.discrepancies) >= 1
    cl_disc = summary.discrepancies[0]
    assert cl_disc["quantity"] == "CL"
    assert cl_disc["delta"] > 0.0


def test_anti_fabrication_rule_for_uncertainty():
    # Attempting to assign uncertainty without an empirical basis must fail
    with pytest.raises(ValueError, match="ANTI-FABRICATION VIOLATION"):
        ScientificEvidenceItem(
            quantity="CL",
            value=0.45,
            tier=EvidenceTier.ANALYTICAL,
            uncertainty=0.01,  # ILLEGAL: uncertainty provided with NOT_ESTABLISHED
            uncertainty_status=UncertaintyStatus.NOT_ESTABLISHED,
        )


def test_detect_physical_contradiction_negative_drag():
    # If a data source returns non-positive drag, it must be flagged as a physical violation
    summary = PhysicalEvidenceBridge.reconcile_investigation_results(
        geometry="NACA0012",
        panel_results={"CL": 0.5, "CD": -0.002},  # Physically impossible negative drag
    )
    assert summary.physical_consensus_valid is False
    assert len(summary.contradictions) >= 1
    assert any("CD <= 0.0" in c for c in summary.contradictions)
