"""
AASI Phase 26 End-to-End Autonomous Remote CFD Execution Test Suite.
Tests the complete canonical user journey:
"Analyze a NACA 4412 at Re = 3e6, alpha = 6 degrees. Compare analytical theory,
existing CFD knowledge, surrogate prediction, and perform a real CFD validation if required."
"""

import pytest
from backend.agent.planner import ScientificPlanner
from backend.dataset.catalog import CFDCatalog
from backend.agent.decision_engine import FidelityDecisionEngine
from backend.compute.colab_session import ColabSessionPackager
from backend.agent.orchestrator import ProductionOrchestrator, OrchestratorState
from backend.agent.report_generator import ScientificReportGenerator
from backend.agent.scientific_answer import ScientificAnswerEngine


def test_canonical_phase26_end_to_end_investigation(tmp_path):
    """
    Simulates the full autonomous execution lifecycle for NACA 4412 at alpha=6°.
    """
    user_prompt = "Analyze a NACA 4412 at Re = 3e6, alpha = 6 degrees. Compare analytical theory, existing CFD knowledge, surrogate prediction, and perform a real CFD validation if required."

    # 1. Parse natural language objective
    spec = ScientificPlanner.parse_objective(user_prompt)
    assert spec.geometry == "NACA 4412"
    assert spec.alpha_deg == 6.0
    assert spec.reynolds == 3000000.0

    # 2. Initialize production orchestrator
    orch = ProductionOrchestrator(session_id="SESS-CANONICAL-001", objective=user_prompt)
    orch.transition_to(OrchestratorState.PLANNED, trigger="PLAN_COMPLETE")

    # 3. Search CFD knowledge fabric
    catalog = CFDCatalog()
    records = catalog.query(geometry_id="NACA 4412")
    orch.transition_to(OrchestratorState.KNOWLEDGE_SEARCH, trigger="CATALOG_QUERIED")
    assert len(records) >= 1

    # 4. Fidelity decision
    decision = FidelityDecisionEngine.evaluate(
        geometry=spec.geometry,
        alpha_deg=spec.alpha_deg,
        reynolds=spec.reynolds,
        mach=spec.mach,
        database_matches=[{"distance": 0.08}],
        surrogate_uncertainty=0.18,
        user_fidelity_req="adaptive_validation",
    )
    orch.transition_to(OrchestratorState.FIDELITY_DECISION, trigger="FIDELITY_EVALUATED")
    assert decision.is_new_cfd_required is True

    # 5. Case generation & Colab bundle packaging
    orch.transition_to(OrchestratorState.CASE_GENERATED, trigger="OPENFOAM_STAGED")
    orch.transition_to(OrchestratorState.PREFLIGHT, trigger="PREFLIGHT_PASSED")
    orch.transition_to(OrchestratorState.BACKEND_SELECTED, trigger="BACKEND_COLAB")

    job_id = "JOB-CANONICAL-NACA4412"
    bundle = ColabSessionPackager.create_session_bundle(
        job_id=job_id,
        geometry_id=spec.geometry,
        alpha_deg=spec.alpha_deg,
        reynolds=spec.reynolds,
        mach=spec.mach,
        output_dir=tmp_path / job_id,
    )
    orch.transition_to(OrchestratorState.JOB_STAGED, trigger="COLAB_BUNDLE_PACKAGED")
    assert bundle["status"] == "COLAB_BUNDLE_READY"

    # 6. User authorization handoff boundary
    orch.transition_to(OrchestratorState.USER_AUTHORIZATION_REQUIRED, trigger="AWAITING_USER_CLICK")

    # 7. Simulated return of authentic results from hardware
    orch.transition_to(OrchestratorState.RESULTS_AVAILABLE, trigger="ARCHIVE_UPLOADED")
    orch.transition_to(OrchestratorState.INGESTING, trigger="INGEST_ARCHIVE")
    orch.transition_to(OrchestratorState.VERIFYING, trigger="VERIFY_PROVENANCE")
    orch.transition_to(OrchestratorState.SCIENTIFIC_VALIDATION, trigger="ASME_VV20_PASSED")

    # 8. Compile multi-fidelity comparison
    report = ScientificReportGenerator.generate(
        experiment_id=job_id,
        objective=user_prompt,
        geometry="NACA 4412",
        alpha_deg=6.0,
        reynolds=3e6,
        mach=0.15,
        live_cfd_results={"cl": 1.0820, "cd": 0.0125, "cm": -0.09},
        database_results={"cl": 1.0800, "cd": 0.0120, "cm": -0.09},
        surrogate_results={"cl": 1.0710, "cd": 0.0132, "cm": -0.088},
        analytical_results={"cl": 1.0966, "cd": 0.0075, "cm": -0.10},
    )
    orch.transition_to(OrchestratorState.REPORT_GENERATED, trigger="REPORT_COMPILED")

    # 9. Verify discrepancies & explanations
    cl_comp = report.comparisons["CL"]
    assert cl_comp.live_cfd.value == 1.0820
    assert cl_comp.surrogate.value == 1.0710
    # Discrepancy = 1.0820 - 1.0710 = +0.0110
    assert cl_comp.cfd_surrogate_discrepancy == 0.0110

    explanation = ScientificAnswerEngine.explain_discrepancy(
        geometry="NACA 4412",
        alpha_deg=6.0,
        live_cfd_cd=0.0125,
        surrogate_cd=0.0132,
        database_cd=0.0120,
    )
    assert explanation.trust_verdict == "TRUSTWORTHY"

    # 10. Complete orchestrator run
    orch.transition_to(OrchestratorState.COMPLETE, trigger="LIFECYCLE_FINALIZED")
    assert orch.session.current_state == OrchestratorState.COMPLETE
    assert len(orch.session.history) >= 12
