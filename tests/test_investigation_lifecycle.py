"""
Comprehensive test suite for AASI Formal Investigation Lifecycle & Autonomy Governance.
Tests state machine rules, envelope boundary breaches, approval gates, and cryptographic auditing.
"""

import pytest
from backend.agent.investigation_lifecycle import (
    AutonomyLevel,
    AutonomyEnvelope,
    LifecycleStage,
    InvestigationLifecycleManager,
)
from backend.agent.canonical_investigation import Investigation, OperatingConditions


def test_valid_lifecycle_progression():
    mgr = InvestigationLifecycleManager(investigation_id="INV-TEST-001")
    assert mgr.current_stage == LifecycleStage.DRAFT

    e1 = mgr.transition(LifecycleStage.FORMULATED, trigger="USER_QUERY_PARSED")
    assert mgr.current_stage == LifecycleStage.FORMULATED
    assert e1.provenance_hash != ""

    e2 = mgr.transition(LifecycleStage.STAGED, trigger="SOLVER_CASE_PREPARED")
    assert mgr.current_stage == LifecycleStage.STAGED

    e3 = mgr.transition(LifecycleStage.EXECUTING, trigger="LOCAL_EXECUTION_DISPATCHED")
    assert mgr.current_stage == LifecycleStage.EXECUTING

    e4 = mgr.transition(LifecycleStage.VERIFYING, trigger="OUTPUT_INGESTED")
    assert mgr.current_stage == LifecycleStage.VERIFYING

    e5 = mgr.transition(LifecycleStage.SYNTHESIZING, trigger="PHYSICAL_CHECKS_PASSED")
    assert mgr.current_stage == LifecycleStage.SYNTHESIZING

    e6 = mgr.transition(LifecycleStage.CONCLUDED, trigger="REPORT_GENERATED")
    assert mgr.current_stage == LifecycleStage.CONCLUDED
    assert len(mgr.history) == 6


def test_illegal_lifecycle_transition_raises():
    mgr = InvestigationLifecycleManager(investigation_id="INV-ILLEGAL-001")
    # Cannot jump directly from DRAFT to EXECUTING
    with pytest.raises(ValueError, match="Illegal transition"):
        mgr.transition(LifecycleStage.EXECUTING, trigger="PREMATURE_RUN")


def test_autonomy_envelope_compute_budget_breach():
    envelope = AutonomyEnvelope(
        level=AutonomyLevel.L3_BOUNDED,
        max_compute_seconds=100.0,
        max_iterations=5,
    )
    mgr = InvestigationLifecycleManager(investigation_id="INV-BUDGET-001", envelope=envelope)
    mgr.transition(LifecycleStage.FORMULATED, trigger="FORMULATION_DONE")

    # Record excess compute time
    mgr.record_resource_usage(compute_seconds=120.0)

    # Next transition should be diverted to HUMAN_INTERVENTION_REQUIRED due to envelope breach
    evt = mgr.transition(LifecycleStage.STAGED, trigger="STAGE_CASE")
    assert mgr.current_stage == LifecycleStage.HUMAN_INTERVENTION_REQUIRED
    assert "ENVELOPE_BREACH" in evt.trigger


def test_autonomy_gated_action_requires_human_approval():
    envelope = AutonomyEnvelope(
        level=AutonomyLevel.L3_BOUNDED,
        require_human_approval_for=["CLOUD_DISPATCH"],
    )
    mgr = InvestigationLifecycleManager(investigation_id="INV-GATE-001", envelope=envelope)
    mgr.transition(LifecycleStage.FORMULATED, trigger="FORMULATION_DONE")

    # Attempt cloud dispatch without human operator
    evt = mgr.transition(
        LifecycleStage.STAGED,
        trigger="STAGING_CASE",
        actor="AI_AGENT",
        action_tag="CLOUD_DISPATCH",
    )
    assert mgr.current_stage == LifecycleStage.HUMAN_INTERVENTION_REQUIRED
    assert "GATED_ACTION" in evt.trigger

    # Human operator resolves the intervention
    evt2 = mgr.transition(
        LifecycleStage.STAGED,
        trigger="OPERATOR_AUTHORIZED_CLOUD_RUN",
        actor="HUMAN_OPERATOR",
    )
    assert mgr.current_stage == LifecycleStage.STAGED


def test_canonical_investigation_model_integration():
    inv = Investigation(
        investigation_id="INV-MODEL-001",
        user_request="Analyze NACA 2412 at 4 degrees AoA",
        scientific_intent="Baseline aerodynamic polar",
        geometry="NACA2412",
        operating_conditions=OperatingConditions(alpha_deg=4.0),
    )
    assert inv.lifecycle_stage == LifecycleStage.FORMULATED
    assert inv.autonomy_envelope.level == AutonomyLevel.L3_BOUNDED

    hash_val = inv.update_provenance()
    assert len(hash_val) == 64
