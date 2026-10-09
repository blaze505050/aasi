"""
AASI Milestone 4: Scientific Hypotheses API Router.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Hypotheses must never be represented or displayed as established facts.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.science.hypotheses import (
    ScientificHypothesis,
    HypothesisStatus,
    hypothesis_engine,
)

router = APIRouter(prefix="/hypotheses", tags=["Scientific Hypotheses"])


class FormulateHypothesisRequest(BaseModel):
    title: str = Field(..., json_schema_extra={"example": "Viscous Boundary Layer Decambering"})
    statement: str = Field(..., json_schema_extra={"example": "Boundary layer displacement reduces effective camber and attenuates lift slope."})
    evidence_basis: List[str] = Field(default_factory=list, json_schema_extra={"example": ["Theoretical lift slope 2*pi vs measured slope ~ 5.8/rad"]})
    assumptions: List[str] = Field(default_factory=list, json_schema_extra={"example": ["Re=3e6", "Mach=0.15", "Attached boundary layer"]})
    prediction: str = Field(..., json_schema_extra={"example": "Empirical dCL/dalpha will match decambered potential prediction within 3%."})
    candidate_test: str = Field(..., json_schema_extra={"example": "Execute OpenFOAM simpleFoam AoA sweep [-2, 0, 2, 4, 6] deg."})
    domain: str = Field(default="aerodynamics")
    geometry_id: Optional[str] = Field(default=None, json_schema_extra={"example": "NACA 0012"})
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class EvaluateHypothesisRequest(BaseModel):
    status: HypothesisStatus = Field(..., description="Target status: SUPPORTED, REFUTED, or INCONCLUSIVE")
    evidence_summary: str = Field(..., description="Summary of experimental or CFD verification evidence")
    test_job_id: Optional[str] = Field(default=None, description="AASI compute job ID providing evidence")
    measured_values: Optional[Dict[str, Any]] = Field(default=None, description="Numerical polars or quantities observed")


class DiscrepancyHypothesisRequest(BaseModel):
    quantity: str = Field(default="CD", json_schema_extra={"example": "CD"})
    geometry: str = Field(default="NACA 0012", json_schema_extra={"example": "NACA 0012"})
    alpha_deg: float = Field(default=4.0, json_schema_extra={"example": 4.0})
    reynolds: float = Field(default=3e6, json_schema_extra={"example": 3e6})
    mach: float = Field(default=0.15, json_schema_extra={"example": 0.15})
    source_a: str = Field(..., json_schema_extra={"example": "ANALYTICAL"})
    value_a: float = Field(..., json_schema_extra={"example": 0.0075})
    source_b: str = Field(..., json_schema_extra={"example": "LIVE_CFD"})
    value_b: float = Field(..., json_schema_extra={"example": 0.0125})
    absolute_difference: Optional[float] = None


@router.post("", response_model=Dict[str, Any], summary="Formulate a Scientific Hypothesis")
async def formulate_hypothesis(req: FormulateHypothesisRequest) -> Dict[str, Any]:
    """
    Registers a new testable scientific hypothesis.
    Enforces that all hypotheses carry immutable is_established_fact=False and epistemic disclaimers.
    """
    try:
        hyp = hypothesis_engine.formulate(
            title=req.title,
            statement=req.statement,
            evidence_basis=req.evidence_basis,
            assumptions=req.assumptions,
            prediction=req.prediction,
            candidate_test=req.candidate_test,
            domain=req.domain,
            geometry_id=req.geometry_id,
            confidence=req.confidence,
        )
        return hyp.to_presentation_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[Dict[str, Any]], summary="List Scientific Hypotheses")
async def list_hypotheses(
    status: Optional[HypothesisStatus] = Query(None, description="Filter by hypothesis status"),
    domain: Optional[str] = Query(None, description="Filter by scientific domain"),
    geometry_id: Optional[str] = Query(None, description="Filter by geometry identifier"),
) -> List[Dict[str, Any]]:
    """Lists all registered hypotheses, annotated with epistemic warnings."""
    hypotheses = hypothesis_engine.list_hypotheses(
        status=status,
        domain=domain,
        geometry_id=geometry_id,
    )
    return [h.to_presentation_dict() for h in hypotheses]


@router.get("/{hypothesis_id}", response_model=Dict[str, Any], summary="Get Scientific Hypothesis by ID")
async def get_hypothesis(hypothesis_id: str) -> Dict[str, Any]:
    """Retrieves a specific hypothesis by its unique ID."""
    hyp = hypothesis_engine.get_hypothesis(hypothesis_id)
    if not hyp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hypothesis '{hypothesis_id}' not found.")
    return hyp.to_presentation_dict()


@router.post("/{hypothesis_id}/evaluate", response_model=Dict[str, Any], summary="Evaluate Hypothesis with Empirical Evidence")
async def evaluate_hypothesis(hypothesis_id: str, req: EvaluateHypothesisRequest) -> Dict[str, Any]:
    """
    Evaluates hypothesis against empirical simulation or experimental results.
    Transitions status to SUPPORTED, REFUTED, or INCONCLUSIVE with recorded provenance.
    Never elevates a hypothesis to an established fact.
    """
    try:
        updated = hypothesis_engine.update_status(
            hypothesis_id=hypothesis_id,
            new_status=req.status,
            evidence_summary=req.evidence_summary,
            test_job_id=req.test_job_id,
            measured_values=req.measured_values,
        )
        return updated.to_presentation_dict()
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hypothesis '{hypothesis_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/discrepancy", response_model=List[Dict[str, Any]], summary="Generate Hypotheses from Discrepancy")
async def generate_from_discrepancy(req: DiscrepancyHypothesisRequest) -> List[Dict[str, Any]]:
    """
    Synthesizes physics-grounded testable hypotheses when multiple evidence sources disagree.
    """
    abs_diff = req.absolute_difference if req.absolute_difference is not None else abs(req.value_a - req.value_b)
    hypotheses = hypothesis_engine.generate_for_discrepancy(
        quantity=req.quantity,
        geometry=req.geometry,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
        src_a=req.source_a,
        val_a=req.value_a,
        src_b=req.source_b,
        val_b=req.value_b,
        abs_diff=round(abs_diff, 5),
    )
    return [h.to_presentation_dict() for h in hypotheses]
