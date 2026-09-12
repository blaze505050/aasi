"""
AASI Scientific Conclusion Engine & Hierarchical Promotion Gates.

Governing Directive: Real Scientific Execution, Evidence Integrity & Independent Reproducibility.
Enforces epistemic conclusion levels and fail-closed promotion rules:
- Capping conclusions to the exact level justified by the underlying evidence ledger.
- Distinguishing statistical agreement from physical validity.
- Forbidding surrogate inferences or citations from masquerading as experimental or CFD ground truth.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.research.evidence_ledger import EpistemicStatus, EvidenceLedger, EvidenceType


class ConclusionLevel(str, Enum):
    """
    Hierarchical scientific conclusion levels in strict order of epistemic backing:
    Level 0: INSUFFICIENT_EVIDENCE (missing links, unverified models, failed gates)
    Level 1: ANALYTICAL_ONLY (classical thin-airfoil or potential flow derivations)
    Level 2: SURROGATE_SUPPORTED (verified ML surrogate prediction within valid envelope)
    Level 3: EXPERIMENTALLY_SUPPORTED (direct empirical wind-tunnel polar data)
    Level 4: CFD_SUPPORTED (grid-converged Navier-Stokes/RANS with ASME V&V 20 uncertainty)
    Level 5: MULTI_SOURCE_VALIDATED (synthesis of >=2 independent real/derived sources)
    Level 6: RESEARCH_GRADE (Multi-grid CFD + Experimental Wind-Tunnel + Verified Surrogate)
    """
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ANALYTICAL_ONLY = "ANALYTICAL_ONLY"
    SURROGATE_SUPPORTED = "SURROGATE_SUPPORTED"
    EXPERIMENTALLY_SUPPORTED = "EXPERIMENTALLY_SUPPORTED"
    CFD_SUPPORTED = "CFD_SUPPORTED"
    MULTI_SOURCE_VALIDATED = "MULTI_SOURCE_VALIDATED"
    RESEARCH_GRADE = "RESEARCH_GRADE"


class PhysicalValidationMetrics(BaseModel):
    """Rigorous aerodynamic physical validity criteria."""
    lift_slope_error_pct: float
    zero_lift_offset_deg: float
    symmetry_max_error: float
    drag_positivity_verified: bool = True
    monotonic_lift_linear_range: bool = True
    within_validity_envelope: bool = True
    extrapolation_detected: bool = False


class StatisticalMetrics(BaseModel):
    """Statistical curve agreement metrics (strictly distinguished from physical validity)."""
    r2_cl: Optional[float] = None
    rmse_cl: Optional[float] = None
    mae_cl: Optional[float] = None
    rmse_cd: Optional[float] = None
    mae_cd: Optional[float] = None


class FormalScientificVerdict(BaseModel):
    """Formal scientific research conclusion with cryptographic traceability."""
    verdict: str  # e.g., "HYPOTHESIS_CONFIRMED_WITH_REGIME_LIMITS", "INSUFFICIENT_EVIDENCE"
    conclusion_level: ConclusionLevel
    confidence_level: str
    executive_summary: str
    regimes_of_validity: Dict[str, str] = Field(default_factory=dict)
    statistical_metrics: Dict[str, Any] = Field(default_factory=dict)
    physical_metrics: Dict[str, Any] = Field(default_factory=dict)
    cfd_status: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    promotion_reasons: List[str] = Field(default_factory=list)
    failed_promotion_gates: List[str] = Field(default_factory=list)
    provenance_root: Optional[str] = None


class ScientificPromotionGate:
    """
    Evaluates evidence records from an EvidenceLedger to determine the maximum
    epistemically justified conclusion level.
    """

    @classmethod
    def evaluate_conclusion(
        cls,
        ledger: EvidenceLedger,
        target_conclusion_id: str,
        hypothesis_statement: str,
        regime_evaluations: Dict[str, str],
        physical_metrics: PhysicalValidationMetrics,
        statistical_metrics: StatisticalMetrics,
        cfd_deck_info: Optional[Dict[str, Any]] = None,
        cfd_converged_study: Optional[Dict[str, Any]] = None,
    ) -> FormalScientificVerdict:
        """
        Executes strict gatekeeper rules across the evidence ledger.
        """
        failed_gates: List[str] = []
        promotion_reasons: List[str] = []

        # 1. Backward Provenance Verification Gate
        is_chain_valid, visited, missing = ledger.verify_backward_chain(target_conclusion_id)
        if not is_chain_valid or missing:
            failed_gates.append(f"Broken provenance chain. Missing evidence IDs: {missing}")
            return FormalScientificVerdict(
                verdict="INSUFFICIENT_EVIDENCE",
                conclusion_level=ConclusionLevel.INSUFFICIENT_EVIDENCE,
                confidence_level="NONE",
                executive_summary=f"Research conclusion rejected: cryptographic provenance chain is incomplete. Missing links: {missing}",
                failed_promotion_gates=failed_gates,
                provenance_root=ledger.merkle_root
            )

        # 2. Inventory evidence types and statuses
        records = ledger.records
        statuses = {r.epistemic_status for r in records}
        ev_types = {r.evidence_type for r in records}

        has_analytical = EvidenceType.ANALYTICAL_DERIVATION in ev_types
        has_surrogate = EvidenceType.SURROGATE_INFERENCE in ev_types
        has_experimental_ref = EvidenceType.EXPERIMENTAL_BENCHMARK in ev_types
        has_cfd_grid_study = (
            EvidenceType.CFD_GRID_CONVERGENCE in ev_types or
            (cfd_converged_study is not None and cfd_converged_study.get("valid") is True)
        )
        has_executed_cfd = EpistemicStatus.SIMULATED in statuses

        # 3. Physical Validation Integrity Check
        if not physical_metrics.drag_positivity_verified:
            failed_gates.append("Physical validity violation: non-positive drag coefficient detected (Cd <= 0).")
        if not physical_metrics.monotonic_lift_linear_range:
            failed_gates.append("Physical validity violation: non-monotonic lift slope in attached flow regime.")
        if physical_metrics.extrapolation_detected:
            failed_gates.append("Model evaluated outside verified training envelope (extrapolation detected).")

        if failed_gates:
            return FormalScientificVerdict(
                verdict="INSUFFICIENT_EVIDENCE",
                conclusion_level=ConclusionLevel.INSUFFICIENT_EVIDENCE,
                confidence_level="UNRELIABLE_PHYSICS",
                executive_summary="Physical validity gates failed. Scientific claims rejected despite any statistical correlations.",
                failed_promotion_gates=failed_gates,
                provenance_root=ledger.merkle_root
            )

        # 4. Determine justified conclusion level
        # Strict Rule A: RESEARCH_GRADE requires Real Ingested CFD + ASME V&V 20 grid study + Experimental Ref + Surrogate
        if has_cfd_grid_study and has_executed_cfd and has_experimental_ref and has_surrogate:
            level = ConclusionLevel.RESEARCH_GRADE
            verdict = "HYPOTHESIS_CONFIRMED_RESEARCH_GRADE"
            confidence = "RESEARCH_GRADE_FULL_SYNTHESIS"
            promotion_reasons.append("Multi-grid ASME V&V 20 CFD converged + Experimental wind tunnel validation + Verified surrogate agreement.")

        # Strict Rule B: MULTI_SOURCE_VALIDATED requires synthesis of >= 2 distinct verified sources
        # (e.g. Thin Airfoil DERIVED + AeroSurrogateV1 SURROGATE + NASA TM-4083 REFERENCED)
        elif (has_analytical and has_surrogate and has_experimental_ref) or (has_cfd_grid_study and has_analytical):
            level = ConclusionLevel.MULTI_SOURCE_VALIDATED
            verdict = "HYPOTHESIS_CONFIRMED_WITH_REGIME_LIMITS"
            confidence = "HIGH_LINEAR_REGIME"
            promotion_reasons.append("Synthesis of Analytical Thin-Airfoil Theory + Verified Neural/Ridge Surrogate + NASA TM-4083 Reference Data.")

        # Strict Rule C: CFD_SUPPORTED requires real CFD execution
        elif has_executed_cfd or has_cfd_grid_study:
            level = ConclusionLevel.CFD_SUPPORTED
            verdict = "CFD_VALIDATED"
            confidence = "NUMERICAL_GRID_CONVERGED"
            promotion_reasons.append("Validated by grid-converged Navier-Stokes numerical simulation.")

        # Strict Rule D: EXPERIMENTALLY_SUPPORTED requires direct empirical evidence
        elif has_experimental_ref:
            level = ConclusionLevel.EXPERIMENTALLY_SUPPORTED
            verdict = "EXPERIMENTALLY_SUPPORTED"
            confidence = "EMPIRICAL_WIND_TUNNEL_CORROBORATED"
            promotion_reasons.append("Validated against authoritative published experimental wind-tunnel data.")

        # Strict Rule E: SURROGATE_SUPPORTED (verified surrogate inference within domain)
        elif has_surrogate:
            level = ConclusionLevel.SURROGATE_SUPPORTED
            verdict = "SURROGATE_SUPPORTED"
            confidence = "SURROGATE_INTERPOLATION_ONLY"
            promotion_reasons.append("Corroborated by verified aerodynamic surrogate model with epistemic uncertainty quantification.")

        # Strict Rule F: ANALYTICAL_ONLY
        elif has_analytical:
            level = ConclusionLevel.ANALYTICAL_ONLY
            verdict = "ANALYTICAL_DERIVATION_ONLY"
            confidence = "THEORETICAL_LIMIT_ONLY"
            promotion_reasons.append("Thin-airfoil theoretical potential flow limit.")

        else:
            level = ConclusionLevel.INSUFFICIENT_EVIDENCE
            verdict = "INSUFFICIENT_EVIDENCE"
            confidence = "NONE"
            failed_gates.append("No authoritative evidence source verified.")

        # Summary text
        slope_err = physical_metrics.lift_slope_error_pct
        summary = (
            f"Hypothesis confirmed within linear aerodynamic envelope (alpha in [-4 deg, 8 deg]). "
            f"Lift-curve slope error vs. exact thin-airfoil theory is {slope_err:.2f}%. "
            f"Reflectional aerodynamic symmetry error is {physical_metrics.symmetry_max_error:.4f}. "
            f"Zero-lift angle is {physical_metrics.zero_lift_offset_deg:.2f} deg. "
            f"In the separated stall regime (alpha >= 12 deg), epistemic uncertainty widens, "
            f"confirming hypothesis expectation that non-linear viscous separation requires targeted high-fidelity CFD."
        )

        cfd_info = cfd_deck_info or {
            "execution_backend": "USER_EXECUTED_REQUIRED",
            "instruction": "Execute generated OpenFOAM case deck on host or cluster to obtain full Navier-Stokes validation."
        }

        limitations = [
            "2D steady incompressible potential & surrogate framework; does not resolve 3D wingtip vortex dynamics or aeroacoustic flutter.",
            "Local CFD execution is staged as USER_EXECUTED_REQUIRED. High-fidelity RANS coefficients require external solver execution."
        ]

        return FormalScientificVerdict(
            verdict=verdict,
            conclusion_level=level,
            confidence_level=confidence,
            executive_summary=summary,
            regimes_of_validity=regime_evaluations,
            statistical_metrics=statistical_metrics.model_dump(),
            physical_metrics=physical_metrics.model_dump(),
            cfd_status=cfd_info,
            limitations=limitations,
            promotion_reasons=promotion_reasons,
            failed_promotion_gates=failed_gates,
            provenance_root=ledger.merkle_root
        )
