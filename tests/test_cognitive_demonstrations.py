"""
AASI Cognitive Engine: Demonstrations Test Suite.
Validates that all 4 canonical demonstrations run deterministically and satisfy physical criteria.
"""

from backend.cognitive.demonstrations import (
    run_demo_1_naca0012_re6e6_alpha6,
    run_demo_2_naca4412_alpha20_safe_failure,
    run_demo_3_naca0012_alpha0_dalembert_contradiction,
    run_demo_4_reynolds_scaling_investigation,
)


def test_demo_1_closed_loop_discovery():
    res = run_demo_1_naca0012_re6e6_alpha6()
    assert res["final_state"] == "COMPLETED"
    assert res["stopping_reason"] == "QUESTION_RESOLVED"
    assert len(res["winning_hypothesis"]) >= 1
    assert res["provenance_hash"] != ""


def test_demo_2_safe_failure_and_extrapolation_detection():
    res = run_demo_2_naca4412_alpha20_safe_failure()
    assert res["final_state"] == "STALLED"
    assert res["stopping_reason"] == "INSUFFICIENT_RESOURCES"
    assert res["extrapolation_risk"] == "SEVERE"
    assert len(res["unknowns"]) >= 1
    # Critical invariant: Zero fabricated tool executions allowed
    assert res["executed_tool_count"] == 0


def test_demo_3_dalembert_contradiction():
    res = run_demo_3_naca0012_alpha0_dalembert_contradiction()
    assert res["contradiction_type"] == "MODEL_FORM_DIFFERENCE"
    assert res["is_genuine_defect"] is False
    assert "D'Alembert's Paradox" in res["physical_explanation"]


def test_demo_4_reynolds_scaling():
    res = run_demo_4_reynolds_scaling_investigation()
    assert res["verified_trend"] is True
    assert res["cd_higher"] < res["cd_baseline"]
    assert "boundary layer" in res["physical_explanation"]
