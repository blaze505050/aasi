"""
AASI Phase 26 Scientific Answer & Discovery Test Suite.
Verifies epistemic labeling (FACT, MEASURED, COMPUTED, PREDICTED, INFERRED),
inquiry DAG generation, and discovery recommendation scoring.
"""

import pytest
from backend.agent.scientific_answer import (
    ScientificAnswerEngine,
    EpistemicLabel,
)
from backend.agent.investigation_graph import (
    InvestigationGraph,
    InquiryNodeType,
    AutonomousDiscoveryEngine,
)


def test_scientific_answer_discrepancy_explanation():
    """Verify answer engine breaks down drag discrepancies with explicit epistemic tags."""
    explanation = ScientificAnswerEngine.explain_discrepancy(
        geometry="NACA 4412",
        alpha_deg=8.0,
        live_cfd_cd=0.0182,
        surrogate_cd=0.0145,
        database_cd=0.0180,
    )

    assert "NACA 4412" in explanation.question
    assert explanation.trust_verdict in ["TRUSTWORTHY", "CONDITIONAL"]
    assert len(explanation.epistemic_statements) >= 3

    labels = [s.epistemic_label for s in explanation.epistemic_statements]
    assert EpistemicLabel.COMPUTED in labels
    assert EpistemicLabel.PREDICTED in labels
    assert EpistemicLabel.MEASURED in labels
    assert EpistemicLabel.FACT in labels


def test_scientific_answer_trustworthiness_evaluation():
    """Verify answer engine evaluates trustworthiness based on CFD presence and distance."""
    # When CFD is verified
    exp_trust = ScientificAnswerEngine.explain_trustworthiness(
        geometry="NACA 4412",
        alpha_deg=6.0,
        has_verified_cfd=True,
        mahalanobis_distance=0.4,
        residual_converged=True,
    )
    assert exp_trust.trust_verdict == "TRUSTWORTHY"

    # When OOD without CFD
    exp_untrust = ScientificAnswerEngine.explain_trustworthiness(
        geometry="NACA 4412",
        alpha_deg=18.0,
        has_verified_cfd=False,
        mahalanobis_distance=2.5,
        residual_converged=False,
    )
    assert exp_untrust.trust_verdict == "UNTRUSTWORTHY"


def test_investigation_graph_generation():
    """Verify natural language question expands into structured 11-node inquiry DAG."""
    q = "Investigate why NACA 4412 drag increases around alpha 8 degrees."
    graph = InvestigationGraph.create_from_question(q, geometry="NACA 4412", alpha_deg=8.0)

    assert len(graph.nodes) == 11
    node_types = [n.node_type for n in graph.nodes]
    assert node_types[0] == InquiryNodeType.QUESTION
    assert node_types[1] == InquiryNodeType.KNOWLEDGE_SEARCH
    assert node_types[2] == InquiryNodeType.HYPOTHESIS
    assert node_types[-1] == InquiryNodeType.CONCLUSION


def test_autonomous_discovery_recommendation():
    """Verify next experiment recommendation is clearly labeled as AI inference."""
    rec = AutonomousDiscoveryEngine.propose_next_experiment(explored_geometries=["NACA 0012", "NACA 4412"])

    assert rec.candidate_geometry not in ["NACA 0012", "NACA 4412"]
    assert rec.acquisition_score > 0.0
    assert rec.epistemic_label == "INFERRED"
    assert "recommends" in rec.recommendation_rationale.lower()
