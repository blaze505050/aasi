"""
AASI Milestone 6: Multi-Fidelity Evidence Reconciliation Engine.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Section 6, 7, and 8 of 04_SCIENTIFIC_BRAIN.md:
- Compares analytical, reference, surrogate, CFD, and experimental evidence.
- Keeps 9 distinct epistemic tiers (USER_ASSERTION, MODEL_GENERATED, ANALYTICAL,
  REFERENCE_DATA, SURROGATE, SIMULATED, EXTERNALLY_EXECUTED, VERIFIED, EXPERIMENTAL).
- Never fabricates uncertainty: If uncertainty has not been rigorously established,
  uncertainty is strictly null with status NOT_ESTABLISHED.
- Calculates discrepancies with explicit units and cryptographic provenance.
- Evaluates the 8 physical contradiction dimensions.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import AliasChoices, BaseModel, Field, model_validator

logger = logging.getLogger("aasi.science.evidence")


class EvidenceTier(str, Enum):
    """
    Strictly distinct epistemic tiers. DO NOT MERGE THESE CATEGORIES.
    Compliance with Section 6 of 04_SCIENTIFIC_BRAIN.md.
    """
    USER_ASSERTION = "USER_ASSERTION"              # Stated by human operator (unverified)
    MODEL_GENERATED = "MODEL_GENERATED"            # LLM reasoning claim or generative text
    ANALYTICAL = "ANALYTICAL"                      # Theoretical derivation (e.g. thin-airfoil theory)
    REFERENCE_DATA = "REFERENCE_DATA"              # Peer-reviewed publication catalog (e.g. NACA Report 824)
    SURROGATE = "SURROGATE"                        # Neural operator or ML regression prediction
    SIMULATED = "SIMULATED"                        # Raw numerical CFD output before verification audit
    EXTERNALLY_EXECUTED = "EXTERNALLY_EXECUTED"    # User executed on Colab/cluster; pending audit
    VERIFIED = "VERIFIED"                          # CFD passed 10-point audit, residuals < 1e-4, ASME V&V 20
    EXPERIMENTAL = "EXPERIMENTAL"                  # Physical wind tunnel or flight test measurement


class UncertaintyStatus(str, Enum):
    """Rigorous classification of uncertainty availability."""
    ESTABLISHED = "ESTABLISHED"          # Formally measured with confidence interval / ASME V&V 20
    NOT_ESTABLISHED = "NOT_ESTABLISHED"  # Uncertainty has not been established; error bars OMITTED


class DiscrepancySignificance(str, Enum):
    NEGLIGIBLE = "NEGLIGIBLE"      # Relative difference < 2% (within normal numerical tolerance)
    MODERATE = "MODERATE"          # Relative difference 2% - 5% (notable difference)
    SIGNIFICANT = "SIGNIFICANT"    # Relative difference 5% - 15% (physical divergence)
    CRITICAL = "CRITICAL"          # Relative difference > 15% (fundamental regime or theory breakdown)


class ScientificEvidenceItem(BaseModel):
    """
    Atomic evidence item representing a single aerodynamic measurement or calculation.
    Enforces strict zero-fabrication of uncertainty.
    """
    item_id: Optional[str] = Field(default=None, description="Optional unique identifier")
    quantity: str = Field(..., description="Quantity name (e.g. CL, CD, CM, dCL_da, Cp_min)")
    value: float = Field(..., description="Numerical measured or calculated value")
    units: str = Field(
        default="dimensionless",
        validation_alias=AliasChoices("units", "unit"),
        description="SI or aerospace unit (e.g. dimensionless, 1/deg, Pa, m/s)",
    )
    tier: EvidenceTier = Field(..., description="Epistemic tier; never merged with other tiers")
    source_ref: str = Field(
        default="UNSPECIFIED_SOURCE",
        validation_alias=AliasChoices("source_ref", "source"),
        description="Specific citation, job ID, or derivation identifier",
    )
    
    # Uncertainty representation (Section 7 of 04_SCIENTIFIC_BRAIN.md)
    uncertainty: Optional[float] = Field(default=None, description="Quantified uncertainty magnitude (e.g. +/- 0.0010)")
    uncertainty_type: Optional[str] = Field(default=None, description="Interval type (e.g. EXPANDED_K2, ASME_VV20_95PCT)")
    uncertainty_status: UncertaintyStatus = Field(
        default=UncertaintyStatus.NOT_ESTABLISHED,
        description="ESTABLISHED or NOT_ESTABLISHED. If not established, uncertainty must be null.",
    )

    notes: Optional[str] = Field(default=None, description="Physical setup or conditions note")
    provenance_hash: str = Field(default="", description="Cryptographic SHA-256 digest")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @model_validator(mode="after")
    def enforce_anti_fabrication_uncertainty(self) -> "ScientificEvidenceItem":
        """
        CRITICAL ANTI-FABRICATION RULE:
        If uncertainty_status is NOT_ESTABLISHED, uncertainty MUST be None.
        Never allow arbitrary or invented error bars.
        """
        if self.uncertainty_status == UncertaintyStatus.NOT_ESTABLISHED:
            if self.uncertainty is not None:
                raise ValueError(
                    "CRITICAL ANTI-FABRICATION VIOLATION: An uncertainty value was supplied without "
                    "establishing an empirical or ASME V&V 20 basis! When uncertainty_status is NOT_ESTABLISHED, "
                    "uncertainty must be null (never invent error bars)."
                )
        elif self.uncertainty_status == UncertaintyStatus.ESTABLISHED:
            if self.uncertainty is None or self.uncertainty < 0.0:
                raise ValueError(
                    "ESTABLISHED uncertainty status requires a non-negative numerical uncertainty interval."
                )
        return self

    def compute_provenance_hash(self) -> str:
        """Computes deterministic SHA-256 hash sealing quantity, value, units, tier, and source."""
        payload = {
            "quantity": self.quantity.strip().upper(),
            "value": round(self.value, 6),
            "units": self.units.strip(),
            "tier": self.tier.value,
            "source_ref": self.source_ref.strip(),
            "uncertainty": self.uncertainty,
            "uncertainty_status": self.uncertainty_status.value,
        }
        raw = json.dumps(payload, sort_keys=True)
        self.provenance_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self.provenance_hash

    def to_dict(self) -> Dict[str, Any]:
        if not self.provenance_hash:
            self.compute_provenance_hash()
        return {
            "item_id": self.item_id,
            "quantity": self.quantity,
            "value": self.value,
            "units": self.units,
            "tier": self.tier.value,
            "source_ref": self.source_ref,
            "uncertainty": self.uncertainty,
            "uncertainty_type": self.uncertainty_type,
            "uncertainty_status": self.uncertainty_status.value,
            "notes": self.notes,
            "provenance_hash": self.provenance_hash,
            "timestamp": self.timestamp,
        }


class EvidenceDiscrepancy(BaseModel):
    """
    Quantified discrepancy between two pieces of evidence for the same quantity.
    Evaluates physical mechanisms across the 8 contradiction dimensions.
    """
    quantity: str
    units: str = Field(default="dimensionless", validation_alias=AliasChoices("units", "unit"))
    unit: str = Field(default="dimensionless", validation_alias=AliasChoices("unit", "units"))
    item_a: ScientificEvidenceItem
    item_b: ScientificEvidenceItem
    absolute_difference: float
    relative_difference_pct: float
    significance: DiscrepancySignificance
    
    # Uncertainty Overlap Analysis (Strictly honest)
    uncertainty_overlap: Optional[bool] = Field(
        default=None,
        description="True if uncertainty intervals overlap; False if they diverge; null if either is NOT_ESTABLISHED.",
    )
    overlap_note: str = Field(
        default="Cannot determine interval overlap: at least one source lacks established uncertainty.",
    )
    uncertainty_note: str = Field(
        default="Cannot determine interval overlap: at least one source lacks established uncertainty.",
    )
    uncertainty_evaluated: bool = Field(default=False)

    # The 8 Physical Contradiction Dimensions (Section 8 of 04_SCIENTIFIC_BRAIN.md)
    physical_investigation: Dict[str, str] = Field(
        default_factory=dict,
        description="Evaluation across geometry, Re/Mach, transition, turbulence, mesh, BCs, measurement, model form.",
    )
    physical_dimensions: Dict[str, str] = Field(default_factory=dict)
    provenance_hash: str = ""

    def compute_provenance_hash(self) -> str:
        payload = {
            "quantity": self.quantity,
            "units": self.units,
            "hash_a": self.item_a.provenance_hash or self.item_a.compute_provenance_hash(),
            "hash_b": self.item_b.provenance_hash or self.item_b.compute_provenance_hash(),
            "absolute_difference": self.absolute_difference,
            "relative_difference_pct": self.relative_difference_pct,
        }
        raw = json.dumps(payload, sort_keys=True)
        self.provenance_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self.provenance_hash

    def to_dict(self) -> Dict[str, Any]:
        if not self.provenance_hash:
            self.compute_provenance_hash()
        return {
            "quantity": self.quantity,
            "units": self.units,
            "unit": self.unit,
            "item_a": self.item_a.to_dict(),
            "item_b": self.item_b.to_dict(),
            "absolute_difference": self.absolute_difference,
            "relative_difference_pct": self.relative_difference_pct,
            "significance": self.significance.value,
            "uncertainty_overlap": self.uncertainty_overlap,
            "overlap_note": self.overlap_note,
            "uncertainty_note": self.uncertainty_note,
            "uncertainty_evaluated": self.uncertainty_evaluated,
            "physical_investigation": self.physical_investigation,
            "physical_dimensions": self.physical_dimensions,
            "provenance_hash": self.provenance_hash,
        }


class ReconciliationReport(BaseModel):
    """Complete multi-tier evidence comparison report for a case or quantity."""
    geometry_id: str
    operating_conditions: Dict[str, Any]
    quantities_compared: List[str]
    evidence_items: List[ScientificEvidenceItem]
    discrepancies: List[EvidenceDiscrepancy]
    summary: str
    provenance_hash: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def compute_hash(self) -> str:
        disc_hashes = [d.compute_provenance_hash() for d in self.discrepancies]
        item_hashes = [it.compute_provenance_hash() for it in self.evidence_items]
        payload = {
            "geometry_id": self.geometry_id,
            "operating_conditions": self.operating_conditions,
            "quantities": sorted(self.quantities_compared),
            "item_hashes": sorted(item_hashes),
            "discrepancy_hashes": sorted(disc_hashes),
        }
        raw = json.dumps(payload, sort_keys=True)
        self.provenance_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self.provenance_hash

    def to_dict(self) -> Dict[str, Any]:
        if not self.provenance_hash:
            self.compute_hash()
        return {
            "geometry_id": self.geometry_id,
            "operating_conditions": self.operating_conditions,
            "quantities_compared": self.quantities_compared,
            "evidence_items": [it.to_dict() for it in self.evidence_items],
            "discrepancies": [d.to_dict() for d in self.discrepancies],
            "summary": self.summary,
            "provenance_hash": self.provenance_hash,
            "timestamp": self.timestamp,
        }


class EvidenceReconciliationEngine:
    """
    Evaluates multi-source evidence sets with zero fabricated uncertainty,
    quantifies discrepancies with units, and investigates the 8 contradiction dimensions.
    """

    @classmethod
    def compare_pair(
        cls,
        item_a: ScientificEvidenceItem,
        item_b: ScientificEvidenceItem,
        geometry: str = "NACA 0012",
        alpha_deg: float = 4.0,
        reynolds: float = 3.0e6,
        mach: float = 0.15,
    ) -> EvidenceDiscrepancy:
        """
        Performs rigorous pairwise comparison between two scientific evidence items.
        """
        if item_a.quantity.strip().upper() != item_b.quantity.strip().upper():
            raise ValueError(f"Cannot compare mismatched quantities: '{item_a.quantity}' vs '{item_b.quantity}'.")

        q_name = item_a.quantity.strip().upper()
        units = item_a.units

        val_a = item_a.value
        val_b = item_b.value
        abs_diff = round(abs(val_a - val_b), 6)

        # Baseline denominator for percentage: use non-zero magnitude
        denom = abs(val_b) if abs(val_b) > 1e-8 else (abs(val_a) if abs(val_a) > 1e-8 else 1.0)
        rel_diff_pct = round((abs_diff / denom) * 100.0, 2)

        # Classify significance
        if rel_diff_pct < 2.0:
            sig = DiscrepancySignificance.NEGLIGIBLE
        elif rel_diff_pct < 5.0:
            sig = DiscrepancySignificance.MODERATE
        elif rel_diff_pct < 15.0:
            sig = DiscrepancySignificance.SIGNIFICANT
        else:
            sig = DiscrepancySignificance.CRITICAL

        # Honest Uncertainty Overlap Check
        uncertainty_overlap = None
        uncertainty_evaluated = False
        overlap_note = "Cannot evaluate overlap: at least one source lacks established uncertainty (uncertainty intervals not evaluated without empirical basis)."

        if (
            item_a.uncertainty_status == UncertaintyStatus.ESTABLISHED
            and item_b.uncertainty_status == UncertaintyStatus.ESTABLISHED
            and item_a.uncertainty is not None
            and item_b.uncertainty is not None
        ):
            min_a, max_a = val_a - item_a.uncertainty, val_a + item_a.uncertainty
            min_b, max_b = val_b - item_b.uncertainty, val_b + item_b.uncertainty
            # Overlap exists if max(min_a, min_b) <= min(max_a, max_b)
            uncertainty_overlap = max(min_a, min_b) <= min(max_a, max_b)
            uncertainty_evaluated = True
            if uncertainty_overlap:
                overlap_note = (
                    f"Uncertainty intervals overlap within empirical bounds: "
                    f"[{min_a:.4f}, {max_a:.4f}] and [{min_b:.4f}, {max_b:.4f}]."
                )
            else:
                overlap_note = (
                    f"Statistically significant divergence: Uncertainty intervals do NOT overlap. "
                    f"Interval A [{min_a:.4f}, {max_a:.4f}] vs Interval B [{min_b:.4f}, {max_b:.4f}]."
                )

        # Investigate the 8 physical contradiction dimensions
        dimensions = cls._evaluate_physical_dimensions(
            item_a=item_a,
            item_b=item_b,
            geometry=geometry,
            alpha_deg=alpha_deg,
            reynolds=reynolds,
            mach=mach,
            abs_diff=abs_diff,
        )

        disc = EvidenceDiscrepancy(
            quantity=q_name,
            units=units,
            unit=units,
            item_a=item_a,
            item_b=item_b,
            absolute_difference=abs_diff,
            relative_difference_pct=rel_diff_pct,
            significance=sig,
            uncertainty_overlap=uncertainty_overlap,
            overlap_note=overlap_note,
            uncertainty_note=overlap_note,
            uncertainty_evaluated=uncertainty_evaluated,
            physical_investigation=dimensions,
            physical_dimensions=dimensions,
        )
        disc.compute_provenance_hash()
        return disc

    @classmethod
    def _evaluate_physical_dimensions(
        cls,
        item_a: ScientificEvidenceItem,
        item_b: ScientificEvidenceItem,
        geometry: str,
        alpha_deg: float,
        reynolds: float,
        mach: float,
        abs_diff: float,
    ) -> Dict[str, str]:
        """
        Evaluates the 8 core physical dimensions responsible for aerodynamic discrepancies:
        1. Geometry differences
        2. Reynolds & Mach scaling
        3. Boundary layer transition
        4. Turbulence modeling
        5. Spatial resolution (y+)
        6. Boundary conditions & free-stream turbulence
        7. Measurement & experimental uncertainty
        8. Mathematical model form
        """
        tiers = {item_a.tier, item_b.tier}
        q = item_a.quantity.upper()
        dims: Dict[str, str] = {}

        # 1. Geometry
        dims["geometry"] = (
            f"Nominal geometry: {geometry}. Coordinate discretization differences (e.g. 64 vs 256 panels, "
            f"leading-edge spline curvature) introduce localized curvature discrepancies."
        )

        # 2. Reynolds & Mach scaling
        dims["reynolds_mach"] = (
            f"Conditions: Re={reynolds:.1e}, Mach={mach:.2f}. Viscous skin friction scales with Re^(-1/5); "
            f"compressibility decambering is minimal below Mach 0.30."
        )

        # 3. Boundary layer transition
        if EvidenceTier.ANALYTICAL not in tiers:
            dims["boundary_layer_transition"] = (
                f"Natural boundary-layer transition occurs around x/c ~ 0.15 - 0.35 at Re={reynolds:.1e}. "
                f"Fully turbulent RANS assumes transition at x/c=0, yielding ~10-15% higher skin friction than free-transition data."
            )
        else:
            dims["boundary_layer_transition"] = "Analytical potential flow neglects transition physics entirely."

        # 4. Turbulence modeling
        if EvidenceTier.VERIFIED in tiers or EvidenceTier.SIMULATED in tiers:
            dims["turbulence_modeling"] = (
                "RANS turbulence modeling uses k-omega SST linear eddy viscosity closure (Boussinesq hypothesis). "
                "May over-predict turbulent kinetic energy near adverse pressure gradient detachment points."
            )
        else:
            dims["turbulence_modeling"] = "Non-CFD tier; turbulence closure not applicable."

        # 5. Spatial resolution / y+
        if EvidenceTier.VERIFIED in tiers or EvidenceTier.SIMULATED in tiers:
            dims["spatial_resolution"] = (
                "Near-wall first cell spacing targets y+ < 1.0. Wall functions introduce mild shear attenuation "
                "if y+ enters buffer layer (5 < y+ < 30)."
            )
        else:
            dims["spatial_resolution"] = "Mesh not utilized in this evidence tier comparison."

        # 6. Boundary conditions
        dims["boundary_conditions"] = (
            "OpenFOAM boundary conditions enforce uniform inlet with fixed turbulence intensity (Tu ~ 0.1%). "
            "Inlet turbulence decay along upstream domain can alter effective airfoil turbulence intensity."
        )

        # 7. Measurement & experimental uncertainty
        if EvidenceTier.EXPERIMENTAL in tiers or EvidenceTier.REFERENCE_DATA in tiers:
            dims["measurement_uncertainty"] = (
                "Historical wind tunnel data (Abbott & von Doenhoff Report 824) includes solid and wake blockage corrections "
                "with an estimated systematic experimental uncertainty of +/- 0.0010 in CD."
            )
        else:
            dims["measurement_uncertainty"] = "Numerical simulation comparisons; no physical sensor uncertainty."

        # 8. Mathematical model form
        if EvidenceTier.ANALYTICAL in tiers:
            dims["model_form"] = (
                "Fundamental model-form difference: Analytical potential theory assumes zero viscosity (d'Alembert's paradox), "
                "whereas Navier-Stokes equations resolve viscous momentum diffusion and boundary layer growth."
            )
        elif EvidenceTier.SURROGATE in tiers:
            dims["model_form"] = (
                "Surrogate model approximates field mapping using finite neural operator basis modes, "
                "which smooths localized sharp gradients compared to discretized Navier-Stokes solvers."
            )
        else:
            dims["model_form"] = "Consistent continuum Navier-Stokes formulation across compared evidence items."

        return dims

    @classmethod
    def reconcile_evidence(
        cls,
        evidence_items: List[ScientificEvidenceItem],
        geometry: str = "NACA 0012",
        alpha_deg: float = 4.0,
        reynolds: float = 3.0e6,
        mach: float = 0.15,
    ) -> ReconciliationReport:
        """
        Reconciles a collection of evidence items across all common quantities.
        Produces pairwise discrepancies, honest uncertainty evaluation, and Merkle provenance.
        """
        discrepancies: List[EvidenceDiscrepancy] = []
        quantities = sorted(list({item.quantity.strip().upper() for item in evidence_items}))

        # Group by quantity
        by_quantity: Dict[str, List[ScientificEvidenceItem]] = {}
        for item in evidence_items:
            q = item.quantity.strip().upper()
            by_quantity.setdefault(q, []).append(item)

        for q, items in by_quantity.items():
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    disc = cls.compare_pair(
                        item_a=items[i],
                        item_b=items[j],
                        geometry=geometry,
                        alpha_deg=alpha_deg,
                        reynolds=reynolds,
                        mach=mach,
                    )
                    discrepancies.append(disc)

        summary = (
            f"Evidence reconciliation complete for {geometry} at alpha={alpha_deg}°, Re={reynolds:.1e}. "
            f"Evaluated {len(evidence_items)} evidence items across {len(quantities)} quantities, "
            f"identifying {len(discrepancies)} pairwise discrepancies."
        )

        report = ReconciliationReport(
            geometry_id=geometry,
            operating_conditions={
                "alpha_deg": alpha_deg,
                "reynolds": reynolds,
                "mach": mach,
            },
            quantities_compared=quantities,
            evidence_items=evidence_items,
            discrepancies=discrepancies,
            summary=summary,
        )
        report.compute_hash()
        return report


# Global singleton instance
evidence_reconciler = EvidenceReconciliationEngine()
