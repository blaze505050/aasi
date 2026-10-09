"""
Unit and Integration Tests for Milestone 6: Multi-Fidelity Evidence Reconciliation.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Tests compliance with Section 6, 7, and 8 of 04_SCIENTIFIC_BRAIN.md:
- 9 distinct epistemic tiers
- Zero uncertainty fabrication
- Explicit discrepancy quantification with physical units
- 8 physical contradiction evaluation dimensions
- API endpoints in backend/api/routes_evidence.py
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.science.evidence import (
    DiscrepancySignificance,
    EvidenceDiscrepancy,
    EvidenceReconciliationEngine,
    EvidenceTier,
    ReconciliationReport,
    ScientificEvidenceItem,
    UncertaintyStatus,
    evidence_reconciler,
)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Epistemic Tiers Verification
# ---------------------------------------------------------------------------

def test_nine_distinct_epistemic_tiers():
    """Verify all 9 distinct epistemic tiers exist and are strictly unique."""
    tiers = list(EvidenceTier)
    assert len(tiers) == 9
    expected = {
        "USER_ASSERTION",
        "MODEL_GENERATED",
        "ANALYTICAL",
        "REFERENCE_DATA",
        "SURROGATE",
        "SIMULATED",
        "EXTERNALLY_EXECUTED",
        "VERIFIED",
        "EXPERIMENTAL",
    }
    actual = {t.value for t in tiers}
    assert actual == expected


# ---------------------------------------------------------------------------
# 2. Strict Zero Uncertainty Fabrication Rule
# ---------------------------------------------------------------------------

def test_uncertainty_fabrication_prevented():
    """Setting uncertainty when status is NOT_ESTABLISHED must raise ValueError."""
    with pytest.raises(ValueError, match="FABRICATION VIOLATION"):
        ScientificEvidenceItem(
            item_id="ev_fab_1",
            quantity="CL",
            value=0.48,
            unit="dimensionless",
            tier=EvidenceTier.MODEL_GENERATED,
            source="LLM Reasoning Claim",
            uncertainty_status=UncertaintyStatus.NOT_ESTABLISHED,
            uncertainty=0.02,  # FABRICATION! Must fail!
        )


def test_uncertainty_established_requires_value():
    """Setting status to ESTABLISHED without valid positive uncertainty must raise ValueError."""
    with pytest.raises(ValueError, match="ESTABLISHED uncertainty status requires a non-negative numerical uncertainty"):
        ScientificEvidenceItem(
            item_id="ev_est_none",
            quantity="CL",
            value=0.48,
            unit="dimensionless",
            tier=EvidenceTier.EXPERIMENTAL,
            source="Wind Tunnel",
            uncertainty_status=UncertaintyStatus.ESTABLISHED,
            uncertainty=None,  # Missing uncertainty value! Must fail!
        )

    with pytest.raises(ValueError, match="ESTABLISHED uncertainty status requires a non-negative numerical uncertainty"):
        ScientificEvidenceItem(
            item_id="ev_est_neg",
            quantity="CL",
            value=0.48,
            unit="dimensionless",
            tier=EvidenceTier.EXPERIMENTAL,
            source="Wind Tunnel",
            uncertainty_status=UncertaintyStatus.ESTABLISHED,
            uncertainty=-0.01,  # Negative uncertainty! Must fail!
        )


def test_valid_evidence_items():
    """Verify valid creation of both established and unestablished uncertainty items."""
    item_unestablished = ScientificEvidenceItem(
        item_id="ev_sim_1",
        quantity="CL",
        value=0.482,
        unit="dimensionless",
        tier=EvidenceTier.SIMULATED,
        source="OpenFOAM simpleFoam (pre-audit)",
        uncertainty_status=UncertaintyStatus.NOT_ESTABLISHED,
        uncertainty=None,
    )
    assert item_unestablished.uncertainty is None
    assert item_unestablished.uncertainty_status == UncertaintyStatus.NOT_ESTABLISHED

    item_established = ScientificEvidenceItem(
        item_id="ev_exp_1",
        quantity="CL",
        value=0.470,
        unit="dimensionless",
        tier=EvidenceTier.EXPERIMENTAL,
        source="Ladson (1988) NASA TM-4074",
        uncertainty_status=UncertaintyStatus.ESTABLISHED,
        uncertainty=0.015,
    )
    assert item_established.uncertainty == 0.015
    assert item_established.uncertainty_status == UncertaintyStatus.ESTABLISHED


# ---------------------------------------------------------------------------
# 3. Discrepancy Quantification & Units
# ---------------------------------------------------------------------------

def test_discrepancy_quantification():
    """Verify signed and relative discrepancies preserve units and compute accurately."""
    item_cfd = ScientificEvidenceItem(
        item_id="ev_cfd",
        quantity="CL",
        value=0.500,
        unit="dimensionless",
        tier=EvidenceTier.VERIFIED,
        source="OpenFOAM steady RANS (audited)",
        uncertainty_status=UncertaintyStatus.NOT_ESTABLISHED,
    )
    item_ref = ScientificEvidenceItem(
        item_id="ev_ref",
        quantity="CL",
        value=0.460,
        unit="dimensionless",
        tier=EvidenceTier.REFERENCE_DATA,
        source="NACA Report 824",
        uncertainty_status=UncertaintyStatus.NOT_ESTABLISHED,
    )

    discrepancy = evidence_reconciler.compare_pair(
        item_a=item_cfd,
        item_b=item_ref,
        geometry="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
        mach=0.15,
    )

    assert discrepancy.quantity == "CL"
    assert discrepancy.unit == "dimensionless"
    assert pytest.approx(discrepancy.absolute_difference, abs=1e-5) == 0.040
    # Relative difference relative to baseline item_b (0.460): 0.040 / 0.460 = 8.6956% -> 8.70%
    assert pytest.approx(discrepancy.relative_difference_pct, abs=1e-2) == 8.70
    assert discrepancy.significance == DiscrepancySignificance.SIGNIFICANT


def test_discrepancy_significance_levels():
    """Test NEGLIGIBLE (<2%), MODERATE (2-5%), SIGNIFICANT (5-15%), and CRITICAL (>15%)."""
    # Negligible (<2%)
    i1 = ScientificEvidenceItem(item_id="1", quantity="CD", value=0.0080, tier=EvidenceTier.VERIFIED, source="CFD")
    i2 = ScientificEvidenceItem(item_id="2", quantity="CD", value=0.0081, tier=EvidenceTier.EXPERIMENTAL, source="Tunnel")
    d_neg = evidence_reconciler.compare_pair(i1, i2)
    assert d_neg.significance == DiscrepancySignificance.NEGLIGIBLE

    # Moderate (2-5%)
    i3 = ScientificEvidenceItem(item_id="3", quantity="CD", value=0.0083, tier=EvidenceTier.EXPERIMENTAL, source="Tunnel")
    d_mod = evidence_reconciler.compare_pair(i1, i3)
    assert d_mod.significance == DiscrepancySignificance.MODERATE

    # Critical (>15%)
    i4 = ScientificEvidenceItem(item_id="4", quantity="CD", value=0.0120, tier=EvidenceTier.ANALYTICAL, source="Theory")
    d_crit = evidence_reconciler.compare_pair(i1, i4)
    assert d_crit.significance == DiscrepancySignificance.CRITICAL


# ---------------------------------------------------------------------------
# 4. Honest Uncertainty Evaluation
# ---------------------------------------------------------------------------

def test_honest_uncertainty_overlap_when_established():
    """When both items have established uncertainty, compute overlap accurately."""
    # Overlapping: Item A = 0.48 +/- 0.02 [0.46, 0.50]; Item B = 0.49 +/- 0.02 [0.47, 0.51]
    item_a = ScientificEvidenceItem(
        item_id="a",
        quantity="CL",
        value=0.48,
        tier=EvidenceTier.EXPERIMENTAL,
        source="Tunnel A",
        uncertainty_status=UncertaintyStatus.ESTABLISHED,
        uncertainty=0.02,
    )
    item_b = ScientificEvidenceItem(
        item_id="b",
        quantity="CL",
        value=0.49,
        tier=EvidenceTier.EXPERIMENTAL,
        source="Tunnel B",
        uncertainty_status=UncertaintyStatus.ESTABLISHED,
        uncertainty=0.02,
    )
    d_overlap = evidence_reconciler.compare_pair(item_a, item_b)
    assert d_overlap.uncertainty_evaluated is True
    assert d_overlap.uncertainty_overlap is True

    # Non-overlapping: Item C = 0.55 +/- 0.01 [0.54, 0.56]
    item_c = ScientificEvidenceItem(
        item_id="c",
        quantity="CL",
        value=0.55,
        tier=EvidenceTier.EXPERIMENTAL,
        source="Tunnel C",
        uncertainty_status=UncertaintyStatus.ESTABLISHED,
        uncertainty=0.01,
    )
    d_no_overlap = evidence_reconciler.compare_pair(item_a, item_c)
    assert d_no_overlap.uncertainty_evaluated is True
    assert d_no_overlap.uncertainty_overlap is False


def test_honest_uncertainty_when_not_established():
    """When either item lacks established uncertainty, do not fabricate; state unestablished."""
    item_established = ScientificEvidenceItem(
        item_id="exp",
        quantity="CL",
        value=0.48,
        tier=EvidenceTier.EXPERIMENTAL,
        source="Tunnel A",
        uncertainty_status=UncertaintyStatus.ESTABLISHED,
        uncertainty=0.02,
    )
    item_unestablished = ScientificEvidenceItem(
        item_id="surr",
        quantity="CL",
        value=0.49,
        tier=EvidenceTier.SURROGATE,
        source="Neural Operator",
        uncertainty_status=UncertaintyStatus.NOT_ESTABLISHED,
        uncertainty=None,
    )
    d = evidence_reconciler.compare_pair(item_established, item_unestablished)
    assert d.uncertainty_evaluated is False
    assert d.uncertainty_overlap is None
    assert "uncertainty intervals not evaluated" in d.uncertainty_note.lower()


# ---------------------------------------------------------------------------
# 5. Physical Contradiction Dimensions & Provenance
# ---------------------------------------------------------------------------

def test_physical_contradiction_dimensions():
    """Verify evaluation across the 8 physical contradiction dimensions."""
    item_cfd = ScientificEvidenceItem(
        item_id="cfd",
        quantity="CL",
        value=0.50,
        tier=EvidenceTier.VERIFIED,
        source="OpenFOAM k-omega SST",
    )
    item_exp = ScientificEvidenceItem(
        item_id="exp",
        quantity="CL",
        value=0.46,
        tier=EvidenceTier.EXPERIMENTAL,
        source="Wind Tunnel Measurement",
    )

    d = evidence_reconciler.compare_pair(item_cfd, item_exp)
    dims = d.physical_dimensions
    assert len(dims) == 8
    expected_dims = {
        "geometry",
        "reynolds_mach",
        "boundary_layer_transition",
        "turbulence_modeling",
        "spatial_resolution",
        "boundary_conditions",
        "measurement_uncertainty",
        "model_form",
    }
    assert set(dims.keys()) == expected_dims
    assert "transition" in dims["boundary_layer_transition"].lower()
    assert "turbulence" in dims["turbulence_modeling"].lower()


def test_reconciliation_report_provenance():
    """Verify multi-fidelity reconciliation report groups quantities and computes hash."""
    items = [
        ScientificEvidenceItem(item_id="1", quantity="CL", value=0.48, tier=EvidenceTier.EXPERIMENTAL, source="NACA TM-4074"),
        ScientificEvidenceItem(item_id="2", quantity="CL", value=0.50, tier=EvidenceTier.VERIFIED, source="OpenFOAM"),
        ScientificEvidenceItem(item_id="3", quantity="CD", value=0.0082, tier=EvidenceTier.EXPERIMENTAL, source="NACA TM-4074"),
        ScientificEvidenceItem(item_id="4", quantity="CD", value=0.0088, tier=EvidenceTier.VERIFIED, source="OpenFOAM"),
    ]

    report = evidence_reconciler.reconcile_evidence(
        evidence_items=items,
        geometry="NACA 0012",
        alpha_deg=4.0,
        reynolds=3.0e6,
    )

    assert report.provenance_hash != ""
    assert len(report.provenance_hash) == 64
    assert len(report.discrepancies) == 2  # 1 pair for CL, 1 pair for CD
    assert set(report.quantities_compared) == {"CD", "CL"}


# ---------------------------------------------------------------------------
# 6. API Route Integration Tests
# ---------------------------------------------------------------------------

def test_api_evidence_tiers(client):
    """GET /api/evidence/tiers returns all 9 distinct epistemic tiers."""
    resp = client.get("/api/evidence/tiers")
    assert resp.status_code == 200
    tiers = resp.json()
    assert len(tiers) == 9
    assert "USER_ASSERTION" in tiers
    assert "EXPERIMENTAL" in tiers
    assert "VERIFIED" in tiers


def test_api_evidence_dimensions(client):
    """GET /api/evidence/dimensions returns 8 physical dimensions."""
    resp = client.get("/api/evidence/dimensions")
    assert resp.status_code == 200
    dimensions = resp.json()
    assert len(dimensions) == 8
    dim_names = {d["dimension"] for d in dimensions}
    assert "boundary_layer_transition" in dim_names
    assert "turbulence_modeling" in dim_names


def test_api_evidence_compare(client):
    """POST /api/evidence/compare performs pairwise comparison."""
    payload = {
        "item_a": {
            "item_id": "item_cfd",
            "quantity": "CL",
            "value": 0.495,
            "unit": "dimensionless",
            "tier": "VERIFIED",
            "source": "OpenFOAM",
            "uncertainty_status": "NOT_ESTABLISHED",
        },
        "item_b": {
            "item_id": "item_exp",
            "quantity": "CL",
            "value": 0.470,
            "unit": "dimensionless",
            "tier": "EXPERIMENTAL",
            "source": "Wind tunnel",
            "uncertainty_status": "ESTABLISHED",
            "uncertainty": 0.015,
        },
        "geometry": "NACA 0012",
        "alpha_deg": 4.0,
        "reynolds": 3000000.0,
        "mach": 0.15,
    }
    resp = client.post("/api/evidence/compare", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["quantity"] == "CL"
    assert data["unit"] == "dimensionless"
    assert pytest.approx(data["absolute_difference"], abs=1e-4) == 0.025
    assert len(data["physical_dimensions"]) == 8


def test_api_evidence_reconcile(client):
    """POST /api/evidence/reconcile produces multi-fidelity report."""
    payload = {
        "items": [
            {
                "item_id": "it_1",
                "quantity": "CL",
                "value": 0.48,
                "unit": "dimensionless",
                "tier": "REFERENCE_DATA",
                "source": "NACA 824",
                "uncertainty_status": "NOT_ESTABLISHED",
            },
            {
                "item_id": "it_2",
                "quantity": "CL",
                "value": 0.50,
                "unit": "dimensionless",
                "tier": "VERIFIED",
                "source": "OpenFOAM audited",
                "uncertainty_status": "NOT_ESTABLISHED",
            },
        ],
        "geometry": "NACA 0012",
        "alpha_deg": 4.0,
        "reynolds": 3000000.0,
        "mach": 0.15,
    }
    resp = client.post("/api/evidence/reconcile", json=payload)
    assert resp.status_code == 200
    report = resp.json()
    assert report["provenance_hash"] != ""
    assert len(report["discrepancies"]) == 1
