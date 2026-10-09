"""
AASI Milestone 5: Experiment Planner Test Suite.
Tests:
- All 7 mandatory fields present in candidate experiment proposals
- Transparent multi-criteria heuristic scoring breakdown
- Anti-optimality rule: Refuses to claim mathematical optimality
- Cryptographic provenance hashing and tamper resistance
- Candidate generation and prioritization across aerodynamic regimes
- Staging candidate experiments into reproducible execution bundles
- FastAPI control plane endpoints
- InvestigationGraph integration
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.science.planner import (
    CandidateExperiment,
    CandidateStatus,
    CostTier,
    ExperimentCostEstimate,
    HeuristicExperimentScorer,
    ExperimentPlanner,
)
from backend.main import app


# ---------------------------------------------------------------------------
# Test 1: All 7 Mandatory Fields Present in Candidate Experiment
# ---------------------------------------------------------------------------
def test_candidate_experiment_has_all_seven_mandatory_fields():
    """Milestone 5 requirement: question, changed_parameters, method, expected_information, cost_estimate, dependencies, rationale."""
    cost = ExperimentCostEstimate(
        regime="MODERATE_REGIME (approx 5-15 minutes)",
        estimated_cells=120_000,
        estimated_memory_gb=0.82,
        wall_clock_bracket="< 10 minutes",
        cost_tier=CostTier.FREE_COLAB,
    )
    cand = CandidateExperiment(
        experiment_id="EXP-TEST-001",
        question="Does boundary-layer separation induce stall onset on NACA 0012 between alpha=10° and 14°?",
        changed_parameters={"alpha_sweep": [10.0, 12.0, 14.0], "reynolds": 3e6, "mach": 0.15},
        method="OpenFOAM simpleFoam RANS (kOmegaSST)",
        expected_information="Precise stall angle alpha_stall, maximum lift coefficient CL_max, and post-stall drag divergence.",
        cost_estimate=cost,
        dependencies=["baseline_mesh_verification", "baseline_polar_verified"],
        rationale="Operating at alpha=8° approaches the non-linear lift curve peak; mapping [10°, 12°, 14°] bounds separation.",
        geometry_id="NACA 0012",
    )

    # 1. Check all 7 mandatory fields
    assert "stall onset" in cand.question
    assert cand.changed_parameters["alpha_sweep"] == [10.0, 12.0, 14.0]
    assert "simpleFoam" in cand.method
    assert "CL_max" in cand.expected_information
    assert cand.cost_estimate.estimated_cells == 120_000
    assert len(cand.dependencies) == 2
    assert "separation" in cand.rationale

    # 2. Check reason alias in presentation dictionary
    p_dict = cand.to_presentation_dict()
    assert p_dict["reason"] == cand.rationale
    assert p_dict["status"] == "CANDIDATE"


# ---------------------------------------------------------------------------
# Test 2: Cost Estimate Structure
# ---------------------------------------------------------------------------
def test_cost_estimate_structure():
    """Verifies that cost estimate contains regime, cell count, memory, duration, and tier."""
    cost = ExperimentCostEstimate(
        regime="RAPID_REGIME (< 5 minutes)",
        estimated_cells=65_000,
        estimated_memory_gb=0.45,
        wall_clock_bracket="< 5 minutes",
        cost_tier=CostTier.FREE_LOCAL,
    )
    assert cost.regime.startswith("RAPID_REGIME")
    assert cost.estimated_cells == 65_000
    assert cost.estimated_memory_gb == 0.45
    assert cost.cost_tier == CostTier.FREE_LOCAL


# ---------------------------------------------------------------------------
# Test 3: Transparent Heuristic Scoring Arithmetic & Breakdown
# ---------------------------------------------------------------------------
def test_transparent_heuristic_scoring():
    """
    Verifies transparent multi-criteria formula:
    S = clamp(0.35*D + 0.30*R + 0.25*U - 0.15*C, 0.0, 1.0).
    """
    score, breakdown = HeuristicExperimentScorer.score(
        discrepancy_factor=0.8,
        regime_factor=0.9,
        uncertainty_factor=0.6,
        cost_penalty_factor=0.2,
    )
    # Expected: 0.35*0.8 (0.28) + 0.30*0.9 (0.27) + 0.25*0.6 (0.15) - 0.15*0.2 (0.03) = 0.67
    assert 0.665 <= score <= 0.675
    assert breakdown["final_score"] == score
    assert breakdown["weights"]["w_discrepancy"] == 0.35
    assert breakdown["weights"]["w_regime"] == 0.30
    assert breakdown["weights"]["w_uncertainty"] == 0.25
    assert breakdown["weights"]["w_cost_penalty"] == 0.15
    assert "formula" in breakdown
    assert "optimality_notice" in breakdown

    # Clamping tests
    high_score, _ = HeuristicExperimentScorer.score(1.0, 1.0, 1.0, 0.0)
    assert high_score <= 1.0
    low_score, _ = HeuristicExperimentScorer.score(0.0, 0.0, 0.0, 1.0)
    assert low_score == 0.0


# ---------------------------------------------------------------------------
# Test 4: Anti-Optimality Rule — Refuses to Claim Mathematical Optimality
# ---------------------------------------------------------------------------
def test_anti_optimality_disclaimer_present():
    """
    CRITICAL RULE: The planner must NOT claim mathematically optimal experiment selection.
    Every proposal must carry an explicit disclaimer.
    """
    cost = ExperimentCostEstimate(
        regime="RAPID_REGIME (< 5 minutes)",
        estimated_cells=100_000,
        estimated_memory_gb=0.75,
        wall_clock_bracket="< 5 minutes",
        cost_tier=CostTier.FREE_LOCAL,
    )
    cand = CandidateExperiment(
        question="What is the surface pressure distribution?",
        changed_parameters={"post_processing": ["surfacePressure"]},
        method="OpenFOAM simpleFoam",
        expected_information="Detailed Cp profile",
        cost_estimate=cost,
        rationale="Cp reveals localized suction peak",
    )

    assert "does NOT claim global mathematical optimality" in cand.optimality_claim
    assert "HEURISTIC_SELECTION" in cand.optimality_claim

    p_dict = cand.to_presentation_dict()
    assert "optimality_claim" in p_dict
    assert "does NOT claim global mathematical optimality" in p_dict["optimality_claim"]


# ---------------------------------------------------------------------------
# Test 5: Provenance Hashing and Tamper Resistance
# ---------------------------------------------------------------------------
def test_candidate_provenance_hashing():
    """Verifies that cryptographic hash seals candidate experiment parameters deterministically."""
    cost = ExperimentCostEstimate(
        regime="RAPID", estimated_cells=100_000, estimated_memory_gb=0.75,
        wall_clock_bracket="< 5 min", cost_tier=CostTier.FREE_LOCAL
    )
    cand1 = CandidateExperiment(
        experiment_id="EXP-HASH-001",
        question="Test Question",
        changed_parameters={"alpha": 6.0},
        method="simpleFoam",
        expected_information="Info 1",
        cost_estimate=cost,
        dependencies=["dep1"],
        rationale="Rationale 1",
    )
    hash1 = cand1.compute_provenance_hash()
    assert len(hash1) == 64

    # Identical candidate yields identical hash
    cand2 = CandidateExperiment(
        experiment_id="EXP-HASH-001",
        question="Test Question",
        changed_parameters={"alpha": 6.0},
        method="simpleFoam",
        expected_information="Info 1",
        cost_estimate=cost,
        dependencies=["dep1"],
        rationale="Rationale 1",
    )
    assert cand2.compute_provenance_hash() == hash1

    # Altered parameters yield distinct hash
    cand3 = CandidateExperiment(
        experiment_id="EXP-HASH-001",
        question="Test Question",
        changed_parameters={"alpha": 8.0},  # changed
        method="simpleFoam",
        expected_information="Info 1",
        cost_estimate=cost,
        dependencies=["dep1"],
        rationale="Rationale 1",
    )
    assert cand3.compute_provenance_hash() != hash1


# ---------------------------------------------------------------------------
# Test 6: Candidate Generation & Heuristic Prioritization
# ---------------------------------------------------------------------------
def test_generate_candidate_experiments_prioritization():
    """
    Verifies that ExperimentPlanner generates physical candidate experiments
    and sorts them descending by transparent heuristic score.
    """
    planner = ExperimentPlanner()
    candidates = planner.generate_candidates(
        geometry="NACA 0012",
        alpha_deg=8.0,
        reynolds=3.0e6,
        mach=0.15,
        has_verified_cfd=True,
    )

    assert len(candidates) >= 4

    # 1. Sorted descending by heuristic score
    scores = [c.heuristic_score for c in candidates]
    assert scores == sorted(scores, reverse=True)

    # 2. Verify diversity of physical questions
    questions = [c.question for c in candidates]
    assert any("stall" in q.lower() or "separation" in q.lower() for q in questions)
    assert any("sublayer" in q.lower() or "y+" in q.lower() for q in questions)
    assert any("transition" in q.lower() for q in questions)
    assert any("surface pressure" in q.lower() or "cp" in q.lower() for q in questions)


# ---------------------------------------------------------------------------
# Test 7: Staging Candidate Experiment into Compute Bundle
# ---------------------------------------------------------------------------
def test_stage_candidate_experiment(tmp_path):
    """Verifies that a candidate experiment can be staged into an execution bundle (M5 -> M3 link)."""
    planner = ExperimentPlanner()
    candidates = planner.generate_candidates(geometry="NACA 4412", alpha_deg=6.0, reynolds=3e6)
    target_cand = candidates[0]
    assert target_cand.status == CandidateStatus.CANDIDATE

    from backend.compute.colab_session import ColabSessionPackager
    job_id = f"JOB-{target_cand.experiment_id}"
    out_dir = tmp_path / job_id
    bundle = ColabSessionPackager.create_session_bundle(
        job_id=job_id,
        geometry_id=target_cand.geometry_id or "NACA 4412",
        alpha_deg=6.0,
        reynolds=3e6,
        output_dir=out_dir,
    )
    target_cand.status = CandidateStatus.STAGED

    assert target_cand.status == CandidateStatus.STAGED
    assert (out_dir / f"AASI_Colab_{job_id}.ipynb").exists()
    assert (out_dir / "case.tar.gz").exists()


# ---------------------------------------------------------------------------
# Test 8: FastAPI Planner Endpoints
# ---------------------------------------------------------------------------
def test_fastapi_planner_endpoints():
    """Tests the /api/planner REST endpoints."""
    client = TestClient(app)

    # 1. POST /api/planner/candidates
    resp = client.post(
        "/api/planner/candidates",
        json={
            "geometry": "NACA 0012",
            "alpha_deg": 6.0,
            "reynolds": 3.0e6,
            "mach": 0.15,
            "has_verified_cfd": False,
        },
    )
    assert resp.status_code == 200
    candidates = resp.json()
    assert len(candidates) >= 4

    top_cand = candidates[0]
    exp_id = top_cand["experiment_id"]
    assert "question" in top_cand
    assert "changed_parameters" in top_cand
    assert "method" in top_cand
    assert "expected_information" in top_cand
    assert "cost_estimate" in top_cand
    assert "dependencies" in top_cand
    assert "rationale" in top_cand
    assert "reason" in top_cand
    assert "optimality_claim" in top_cand
    assert "heuristic_score" in top_cand

    # 2. GET /api/planner/candidates
    list_resp = client.get("/api/planner/candidates")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 4

    # 3. GET /api/planner/candidates/{id}
    get_resp = client.get(f"/api/planner/candidates/{exp_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["experiment_id"] == exp_id

    # 4. POST /api/planner/candidates/{id}/stage
    stage_resp = client.post(
        f"/api/planner/candidates/{exp_id}/stage",
        json={"destination": "COLAB"},
    )
    assert stage_resp.status_code == 200
    stage_data = stage_resp.json()
    assert stage_data["status"] == "STAGED"
    assert "bundle" in stage_data


# ---------------------------------------------------------------------------
# Test 9: InvestigationGraph Integration
# ---------------------------------------------------------------------------
def test_investigation_graph_candidate_experiments_rendering():
    """Verifies that InvestigationGraph properly renders candidate experiments with non-executed tags."""
    from backend.agent.canonical_investigation import Investigation, OperatingConditions
    from backend.agent.investigation_graph import InvestigationGraph, InquiryNodeType

    cost = ExperimentCostEstimate(
        regime="RAPID", estimated_cells=100_000, estimated_memory_gb=0.75,
        wall_clock_bracket="< 5 min", cost_tier=CostTier.FREE_LOCAL
    )
    cand = CandidateExperiment(
        experiment_id="EXP-GRAPH-009",
        question="Does suction peak collapse at alpha=16°?",
        changed_parameters={"alpha_deg": 16.0},
        method="OpenFOAM simpleFoam",
        expected_information="Cp minimum and separation extent",
        cost_estimate=cost,
        dependencies=["baseline_mesh_ok"],
        rationale="Stall onset investigation",
        heuristic_score=0.72,
    )

    inv = Investigation(
        investigation_id="INV-PLAN-001",
        user_request="Investigate stall onset mechanisms on NACA 0012.",
        scientific_intent="Stall exploration",
        geometry="NACA 0012",
        operating_conditions=OperatingConditions(alpha_deg=8.0),
        candidate_experiments=[cand],
    )

    graph = InvestigationGraph.build_from_investigation(inv)
    exp_nodes = [n for n in graph.nodes if n.node_type == InquiryNodeType.NEXT_EXPERIMENT]
    assert len(exp_nodes) >= 1

    found_cand_node = False
    for n in exp_nodes:
        if "EXP-GRAPH-009" in n.title:
            found_cand_node = True
            assert "Question:" in n.content
            assert "Method: OpenFOAM simpleFoam" in n.content
            assert "Heuristic Score: 0.720" in n.content
            assert "PROPOSAL ONLY - NOT EXECUTED" in n.content
    assert found_cand_node, "Expected candidate experiment node in investigation graph."
