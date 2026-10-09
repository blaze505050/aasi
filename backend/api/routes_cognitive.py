"""
AASI Cognitive Engine: FastAPI Routes.
Exposes cognitive investigation sessions, AerospaceWorldModel snapshots,
hypothesis evaluations, adversarial critiques, investigation graphs, and
autonomous goal-driven campaign loops with Merkle lineage sealing.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.cognitive.hypothesis_engine import CognitiveHypothesisEngine, StructuredHypothesis
from backend.cognitive.critic import ScientificCritic, HypothesisCritique
from backend.cognitive.memory import cognitive_memory_engine
from backend.cognitive.orchestrator import AutonomyLevel, cognitive_orchestrator
from backend.cognitive.tools import scientific_tool_registry

router = APIRouter(prefix="/cognitive", tags=["Cognitive Engine"])


class CognitiveInvestigateRequest(BaseModel):
    question: str = Field(..., description="Scientific aerospace question to investigate")
    geometry_name: str = Field(default="NACA 0012", description="Target airfoil or body")
    alpha_deg: float = Field(default=0.0, description="Angle of attack in degrees")
    reynolds: float = Field(default=3.0e6, description="Reynolds number")
    mach: float = Field(default=0.15, description="Mach number")
    autonomy_level: AutonomyLevel = Field(default=AutonomyLevel.LEVEL_4, description="Human governance tier")
    max_cycles: int = Field(default=3, description="Maximum cognitive cycles")


@router.post("/investigate")
async def start_cognitive_investigation(req: CognitiveInvestigateRequest) -> Dict[str, Any]:
    """Initializes and runs a bounded closed-loop scientific investigation."""
    session = cognitive_orchestrator.create_session(
        question=req.question,
        geometry_name=req.geometry_name,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
        autonomy_level=req.autonomy_level,
        max_cycles=req.max_cycles,
    )
    # Run the cycle
    completed_session = cognitive_orchestrator.run_investigation(session.session_id)
    return {
        "status": "SUCCESS",
        "session": completed_session.model_dump(),
    }


@router.get("/session/{session_id}")
async def get_cognitive_session(session_id: str) -> Dict[str, Any]:
    """Retrieves full session data, world model, hypotheses, and timeline."""
    session = cognitive_orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return session.model_dump()


@router.get("/session/{session_id}/graph")
async def get_investigation_graph(session_id: str) -> Dict[str, Any]:
    """
    Returns an inspectable, clickable node-link graph of the scientific investigation:
    Question -> Hypotheses -> Experiments -> Tool Execution -> Verification -> Decision
    """
    session = cognitive_orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    nodes = []
    links = []

    # Node 1: Question
    nodes.append({
        "id": "node-question",
        "type": "QUESTION",
        "label": session.question,
        "status": "ACTIVE",
    })

    # Nodes: Hypotheses
    for i, h in enumerate(session.active_hypotheses):
        h_id = f"node-hyp-{h.hypothesis_id}"
        nodes.append({
            "id": h_id,
            "type": "HYPOTHESIS",
            "label": h.title,
            "status": h.status.value if hasattr(h.status, "value") else str(h.status),
            "details": h.mechanism,
            "merkle_node_id": h.merkle_node_id,
        })
        links.append({"source": "node-question", "target": h_id, "relation": "GENERATED_FOR"})

    # Nodes: Experiments
    for i, exp in enumerate(session.candidate_experiments):
        exp_id = f"node-exp-{exp.experiment_id}"
        nodes.append({
            "id": exp_id,
            "type": "EXPERIMENT",
            "label": exp.title,
            "status": "PLANNED",
            "utility": exp.utility.composite_utility,
        })
        for target_h in exp.target_hypotheses:
            links.append({"source": f"node-hyp-{target_h}", "target": exp_id, "relation": "DISCRIMINATES"})

    # Node: Execution & Verification
    if session.executed_results:
        exec_node_id = "node-exec-01"
        nodes.append({
            "id": exec_node_id,
            "type": "VERIFICATION",
            "label": "Numerical Verification Audit",
            "status": "VERIFIED" if session.stopping_reason != "NO_SAFE_ACTION" else "FAILED",
        })
        if session.candidate_experiments:
            links.append({"source": f"node-exp-{session.candidate_experiments[0].experiment_id}", "target": exec_node_id, "relation": "EXECUTED_AND_AUDITED"})

    # Node: Decision
    decision_node_id = "node-decision"
    nodes.append({
        "id": decision_node_id,
        "type": "DECISION",
        "label": f"Resolution: {session.stopping_reason.value if session.stopping_reason else 'IN_PROGRESS'}",
        "status": session.current_state.value,
        "root_provenance_hash": session.world_model.provenance_hash,
    })
    if session.executed_results:
        links.append({"source": "node-exec-01", "target": decision_node_id, "relation": "INFORMED"})

    return {
        "session_id": session_id,
        "nodes": nodes,
        "links": links,
    }


class HypothesizeRequest(BaseModel):
    question: str
    geometry_name: str = "NACA 0012"
    alpha_deg: float = 4.0
    reynolds: float = 3.0e6
    mach: float = 0.15


@router.post("/hypothesize", response_model=List[StructuredHypothesis], summary="Generate Competing Hypotheses")
async def generate_hypotheses(req: HypothesizeRequest) -> List[StructuredHypothesis]:
    """Generates competing, falsifiable hypotheses with Merkle lineage linkage."""
    engine = CognitiveHypothesisEngine()
    return engine.generate_competing_hypotheses(
        question=req.question,
        geometry_name=req.geometry_name,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
    )


class CritiqueRequest(BaseModel):
    hypothesis: StructuredHypothesis
    geometry_name: str = "NACA 0012"
    alpha_deg: float = 4.0
    reynolds: float = 3.0e6
    mach: float = 0.15


@router.post("/critique", response_model=HypothesisCritique, summary="Adversarial Scientific Critique")
async def critique_hypothesis(req: CritiqueRequest) -> HypothesisCritique:
    """Executes adversarial inspection and prescribes repairs from Epistemic Memory."""
    critic = ScientificCritic()
    return critic.critique_hypothesis(
        hypothesis=req.hypothesis,
        geometry_name=req.geometry_name,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
    )


@router.get("/tools")
async def list_cognitive_tools() -> List[Dict[str, Any]]:
    """Lists registered scientific instruments and their MCP-compliant schemas."""
    return [t.model_dump() for t in scientific_tool_registry.list_tools()]


@router.get("/skills")
async def list_scientific_skills() -> List[Dict[str, Any]]:
    """Lists reusable scientific engineering skills available in the library."""
    return [s.model_dump() for s in cognitive_memory_engine._skills.values()]
