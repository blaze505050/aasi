"""
AASI Phase 3: Physical Evidence Reconciliation Bridge.
Wraps the Milestone 6 EvidenceReconciliationEngine to reconcile multi-tier data,
evaluate numerical discrepancies, flag physical contradictions, and compute provenance digests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import math
from datetime import datetime, timezone
import hashlib
import json
from pydantic import BaseModel, Field

from backend.science.evidence import (
    EvidenceReconciliationEngine,
    ScientificEvidenceItem,
    EvidenceTier,
    UncertaintyStatus,
    DiscrepancySignificance,
    EvidenceDiscrepancy,
    ReconciliationReport,
)


class EvidenceReconciliationSummary(BaseModel):
    geometry: str
    reconciliation_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    items_count: int
    discrepancies: List[Dict[str, Any]] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    has_critical_discrepancy: bool = False
    physical_consensus_valid: bool = True
    consensus_cl: Optional[float] = None
    consensus_cd: Optional[float] = None
    consensus_ld: Optional[float] = None
    provenance_hash: str = ""


class PhysicalEvidenceBridge:
    """
    Coordinates multi-source data ingestion and runs rigorous discrepancy
    and contradiction audits across epistemic tiers.
    """

    @classmethod
    def reconcile_investigation_results(
        cls,
        geometry: str,
        panel_results: Optional[Dict[str, Any]] = None,
        aerodb_results: Optional[Dict[str, Any]] = None,
        benchmark_results: Optional[Dict[str, Any]] = None,
        cfd_results: Optional[Dict[str, Any]] = None,
    ) -> EvidenceReconciliationSummary:
        engine = EvidenceReconciliationEngine()
        evidence_items: List[ScientificEvidenceItem] = []

        # 1. Ingest Discrete Vortex Panel Method results (ANALYTICAL)
        if panel_results:
            cl = panel_results.get("CL", panel_results.get("cl"))
            cd = panel_results.get("CD", panel_results.get("cd"))
            cm = panel_results.get("CM", panel_results.get("cm"))
            if cl is not None:
                evidence_items.append(ScientificEvidenceItem(
                    quantity="CL",
                    value=float(cl),
                    tier=EvidenceTier.ANALYTICAL,
                    source_ref="Discrete Vortex Panel Solver (Katz & Plotkin)",
                    uncertainty=None,
                    uncertainty_status=UncertaintyStatus.NOT_ESTABLISHED,
                ))
            if cd is not None:
                evidence_items.append(ScientificEvidenceItem(
                    quantity="CD",
                    value=float(cd),
                    tier=EvidenceTier.ANALYTICAL,
                    source_ref="Discrete Vortex Panel Solver (Profile Drag Approx)",
                    uncertainty=None,
                    uncertainty_status=UncertaintyStatus.NOT_ESTABLISHED,
                ))

        # 2. Ingest AeroDB verified records (REFERENCE_DATA)
        if aerodb_results and aerodb_results.get("cl") is not None:
            cl = aerodb_results.get("cl")
            cd = aerodb_results.get("cd")
            src = aerodb_results.get("source", "AeroDB Verified Archive")
            if cl is not None:
                evidence_items.append(ScientificEvidenceItem(
                    quantity="CL",
                    value=float(cl),
                    tier=EvidenceTier.REFERENCE_DATA,
                    source_ref=str(src),
                    uncertainty=None,
                    uncertainty_status=UncertaintyStatus.NOT_ESTABLISHED,
                ))
            if cd is not None:
                evidence_items.append(ScientificEvidenceItem(
                    quantity="CD",
                    value=float(cd),
                    tier=EvidenceTier.REFERENCE_DATA,
                    source_ref=str(src),
                    uncertainty=None,
                    uncertainty_status=UncertaintyStatus.NOT_ESTABLISHED,
                ))

        # 3. Ingest Experimental Benchmarks (EXPERIMENTAL) with ASME V&V 20 uncertainty if provided
        if benchmark_results:
            b_cl = benchmark_results.get("reference_cl", benchmark_results.get("cl"))
            b_cd = benchmark_results.get("reference_cd", benchmark_results.get("cd"))
            u_pct = benchmark_results.get("uncertainty_pct")
            src = benchmark_results.get("dataset", "Abbott & von Doenhoff Report 824")

            if b_cl is not None:
                u_val = float(b_cl) * (u_pct / 100.0) if u_pct else None
                u_stat = UncertaintyStatus.ESTABLISHED if u_val is not None else UncertaintyStatus.NOT_ESTABLISHED
                evidence_items.append(ScientificEvidenceItem(
                    quantity="CL",
                    value=float(b_cl),
                    tier=EvidenceTier.EXPERIMENTAL,
                    source_ref=str(src),
                    uncertainty=u_val,
                    uncertainty_type="ASME_VV20_95PCT" if u_val else None,
                    uncertainty_status=u_stat,
                ))
            if b_cd is not None:
                u_val = float(b_cd) * (u_pct / 100.0) if u_pct else None
                u_stat = UncertaintyStatus.ESTABLISHED if u_val is not None else UncertaintyStatus.NOT_ESTABLISHED
                evidence_items.append(ScientificEvidenceItem(
                    quantity="CD",
                    value=float(b_cd),
                    tier=EvidenceTier.EXPERIMENTAL,
                    source_ref=str(src),
                    uncertainty=u_val,
                    uncertainty_type="ASME_VV20_95PCT" if u_val else None,
                    uncertainty_status=u_stat,
                ))

        # 4. Compute Discrepancies using EvidenceReconciliationEngine
        report = EvidenceReconciliationEngine.reconcile_evidence(
            evidence_items=evidence_items,
            geometry=geometry,
        )

        discrepancies = []
        for disc in report.discrepancies:
            discrepancies.append({
                "quantity": disc.quantity,
                "source_a": f"{disc.item_a.tier.value} ({disc.item_a.value})",
                "source_b": f"{disc.item_b.tier.value} ({disc.item_b.value})",
                "delta": disc.absolute_difference,
                "relative_diff_pct": disc.relative_difference_pct,
                "significance": disc.significance.value,
            })

        # Physical Contradiction Checks
        contradictions = []
        for item in evidence_items:
            if item.quantity == "CD" and item.value <= 0.0:
                contradictions.append(f"Physical violation in {item.source_ref}: CD <= 0.0 ({item.value})")

        # Consensus value determination
        consensus_cl = None
        consensus_cd = None
        for item in evidence_items:
            if item.quantity == "CL":
                consensus_cl = item.value
            elif item.quantity == "CD":
                consensus_cd = item.value

        consensus_ld = (consensus_cl / consensus_cd) if (consensus_cl and consensus_cd and consensus_cd > 0) else None

        # Hash computation
        payload = f"{geometry}:{len(evidence_items)}:{len(discrepancies)}:{len(contradictions)}:{consensus_cl}:{consensus_cd}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        return EvidenceReconciliationSummary(
            geometry=geometry,
            items_count=len(evidence_items),
            discrepancies=discrepancies,
            contradictions=contradictions,
            has_critical_discrepancy=any(d.get("significance") == "CRITICAL" for d in discrepancies),
            physical_consensus_valid=len(contradictions) == 0,
            consensus_cl=round(consensus_cl, 4) if consensus_cl else None,
            consensus_cd=round(consensus_cd, 5) if consensus_cd else None,
            consensus_ld=round(consensus_ld, 2) if consensus_ld else None,
            provenance_hash=digest,
        )
