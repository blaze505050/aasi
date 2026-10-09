"""
AASI Milestone 6: Multi-Fidelity Evidence Reconciliation API Router.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Endpoints to compare heterogeneous evidence across 9 distinct epistemic tiers,
strictly disallowing fabricated uncertainty, calculating discrepancies with units,
and auditing across the 8 physical contradiction dimensions.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.science.evidence import (
    EvidenceDiscrepancy,
    EvidenceReconciliationEngine,
    EvidenceTier,
    ReconciliationReport,
    ScientificEvidenceItem,
    UncertaintyStatus,
    evidence_reconciler,
)

router = APIRouter(prefix="/evidence", tags=["Evidence Reconciliation"])


class CompareTwoEvidenceRequest(BaseModel):
    item_a: ScientificEvidenceItem
    item_b: ScientificEvidenceItem
    geometry: str = Field(default="NACA 0012", json_schema_extra={"example": "NACA 0012"})
    alpha_deg: float = Field(default=4.0, json_schema_extra={"example": 4.0})
    reynolds: float = Field(default=3.0e6, json_schema_extra={"example": 3.0e6})
    mach: float = Field(default=0.15, json_schema_extra={"example": 0.15})


class ReconcileEvidenceRequest(BaseModel):
    items: List[ScientificEvidenceItem]
    geometry: str = Field(default="NACA 0012", json_schema_extra={"example": "NACA 0012"})
    alpha_deg: float = Field(default=4.0, json_schema_extra={"example": 4.0})
    reynolds: float = Field(default=3.0e6, json_schema_extra={"example": 3.0e6})
    mach: float = Field(default=0.15, json_schema_extra={"example": 0.15})


@router.post("/compare", response_model=EvidenceDiscrepancy, summary="Compare Pair of Evidence Items")
async def compare_evidence_pair(req: CompareTwoEvidenceRequest) -> EvidenceDiscrepancy:
    """
    Compares two heterogeneous evidence items.
    Calculates discrepancy with explicit units, audits uncertainty overlap honestly
    (or flags that uncertainty is not established), and analyzes the 8 physical contradiction dimensions.
    """
    try:
        return evidence_reconciler.compare_pair(
            item_a=req.item_a,
            item_b=req.item_b,
            geometry=req.geometry,
            alpha_deg=req.alpha_deg,
            reynolds=req.reynolds,
            mach=req.mach,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reconcile", response_model=ReconciliationReport, summary="Reconcile Multi-Fidelity Evidence Set")
async def reconcile_evidence_set(req: ReconcileEvidenceRequest) -> ReconciliationReport:
    """
    Reconciles a set of multi-fidelity evidence items across all common quantities.
    Computes pairwise discrepancies, honest uncertainty evaluation, and Merkle provenance hash.
    """
    if len(req.items) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 evidence items are required for reconciliation.",
        )
    return evidence_reconciler.reconcile_evidence(
        evidence_items=req.items,
        geometry=req.geometry,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
    )


@router.get("/tiers", response_model=Dict[str, str], summary="List Epistemic Evidence Tiers")
async def get_evidence_tiers() -> Dict[str, str]:
    """
    Returns the 9 distinct epistemic tiers defined in Section 6 of 04_SCIENTIFIC_BRAIN.md.
    These tiers are strictly kept separate and never merged.
    """
    return {
        EvidenceTier.USER_ASSERTION.value: "Stated by human operator (unverified assertion)",
        EvidenceTier.MODEL_GENERATED.value: "LLM reasoning claim or generative scientific text",
        EvidenceTier.ANALYTICAL.value: "Theoretical derivation (e.g. thin-airfoil theory, inviscid potential flow)",
        EvidenceTier.REFERENCE_DATA.value: "Peer-reviewed published experimental or standard dataset (e.g. NACA Report 824)",
        EvidenceTier.SURROGATE.value: "Neural operator, deep surrogate, or ML regression prediction",
        EvidenceTier.SIMULATED.value: "Raw numerical CFD calculation before formal verification audit",
        EvidenceTier.EXTERNALLY_EXECUTED.value: "External execution (e.g. Colab/cluster) awaiting verification audit",
        EvidenceTier.VERIFIED.value: "CFD passing 10-point audit, residuals < 1e-4, ASME V&V 20 standards",
        EvidenceTier.EXPERIMENTAL.value: "Physical wind tunnel or flight test measurement with documented facility conditions",
    }


@router.get("/dimensions", response_model=List[Dict[str, str]], summary="List Physical Contradiction Dimensions")
async def get_contradiction_dimensions() -> List[Dict[str, str]]:
    """
    Returns the 8 physical contradiction evaluation dimensions from Section 8 of 04_SCIENTIFIC_BRAIN.md.
    """
    return [
        {"dimension": "geometry", "description": "Airfoil coordinates, leading-edge radius, trailing-edge thickness, surface roughness"},
        {"dimension": "reynolds_mach", "description": "Reynolds number and Mach number scaling, compressibility effects"},
        {"dimension": "boundary_layer_transition", "description": "Free transition (e^N) vs fixed trip wire location"},
        {"dimension": "turbulence_modeling", "description": "RANS (Spalart-Allmaras, k-omega SST) vs LES vs DNS assumptions"},
        {"dimension": "spatial_resolution", "description": "Grid convergence, y+ wall resolution, boundary layer refinement"},
        {"dimension": "boundary_conditions", "description": "Farfield placement, blockage correction, wind tunnel wall interference"},
        {"dimension": "measurement_uncertainty", "description": "Pressure tap resolution, balance calibration, thermal drift"},
        {"dimension": "model_form", "description": "Boussinesq hypothesis limitation, 2D vs 3D end-wall effects, unsteady separation"},
    ]


# Phase 3 Enhancements: Multi-Fidelity Decision & Direct Investigation Reconciliation

class EvaluateFidelityRequest(BaseModel):
    geometry: str = "NACA0012"
    alpha_deg: float = 4.0
    mach: float = 0.15
    reynolds: float = 3e6
    requested_fidelity: str = "MULTI_FIDELITY"
    tolerance: float = 0.05
    autonomy_level: str = "L3_BOUNDED"


class ReconcileInvestigationRequest(BaseModel):
    geometry: str = "NACA0012"
    panel_results: Optional[Dict[str, Any]] = None
    aerodb_results: Optional[Dict[str, Any]] = None
    benchmark_results: Optional[Dict[str, Any]] = None
    cfd_results: Optional[Dict[str, Any]] = None


@router.post("/evaluate-fidelity", summary="Evaluate Aerodynamic Regime & 8-Level Hierarchy Fidelity")
async def evaluate_fidelity_endpoint(req: EvaluateFidelityRequest):
    """
    Evaluates physical regime (stall, transonic shock, attached subsonic)
    and selects or escalates computational tier via the 8-level hierarchy.
    """
    from backend.science.multifidelity_bridge import MultiFidelityDecisionEngine
    from backend.agent.investigation_lifecycle import AutonomyLevel

    engine = MultiFidelityDecisionEngine()
    autonomy = getattr(AutonomyLevel, req.autonomy_level.upper(), AutonomyLevel.L3_BOUNDED)
    decision = engine.evaluate_fidelity(
        geometry=req.geometry,
        alpha_deg=req.alpha_deg,
        mach=req.mach,
        reynolds=req.reynolds,
        requested_fidelity=req.requested_fidelity,
        tolerance=req.tolerance,
        autonomy_level=autonomy,
    )
    return decision.model_dump()


@router.post("/reconcile-investigation", summary="Reconcile Multi-Fidelity Investigation Results")
async def reconcile_investigation_endpoint(req: ReconcileInvestigationRequest):
    """
    Reconciles analytical, database, simulation, and experimental findings.
    Enforces the Absolute Anti-Fabrication Rule for uncertainty and flags contradictions.
    """
    from backend.science.evidence_bridge import PhysicalEvidenceBridge

    summary = PhysicalEvidenceBridge.reconcile_investigation_results(
        geometry=req.geometry,
        panel_results=req.panel_results,
        aerodb_results=req.aerodb_results,
        benchmark_results=req.benchmark_results,
        cfd_results=req.cfd_results,
    )
    return summary.model_dump()
