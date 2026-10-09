"""
AASI Phase 26 Error Recovery Test Suite.
Verifies diagnostics and automatic non-mutating repair across all 11 error classes:
1. Residual divergence
2. Floating point exception
3. Bad mesh quality
4. Non-convergence / residual stagnation
5. Courant-number instability
6. Boundary-condition inconsistency
7. Missing field
8. Solver executable missing
9. Time-step instability
10. Linear solver failure
11. Turbulence-model instability
"""

import pytest
from backend.agent.diagnostics import CFDDiagnosticsEngine, CFDErrorClass
from backend.agent.repair_engine import CFDRepairEngine


def test_diagnostics_all_11_error_classes():
    """Verify diagnostic detection across all 11 failure types."""
    # 1. Missing solver
    d1 = CFDDiagnosticsEngine.diagnose(solver_log="bash: simpleFoam: command not found")
    assert d1.error_class == CFDErrorClass.MISSING_SOLVER

    # 2. Missing field
    d2 = CFDDiagnosticsEngine.diagnose(solver_log="cannot find file \"0/nut\"")
    assert d2.error_class == CFDErrorClass.MISSING_FIELD

    # 3. Courant instability
    d3 = CFDDiagnosticsEngine.diagnose(solver_log="Courant Number mean: 0.12 max: 14.85")
    assert d3.error_class == CFDErrorClass.COURANT_INSTABILITY

    # 4. Floating point exception
    d4 = CFDDiagnosticsEngine.diagnose(solver_log="Floating point exception in solver loop. p residual: nan")
    assert d4.error_class == CFDErrorClass.FLOATING_POINT_FAILURE

    # 5. Turbulence instability
    d5 = CFDDiagnosticsEngine.diagnose(solver_log="bounding k, min: -1.2e-5 max: 10.0")
    assert d5.error_class == CFDErrorClass.TURBULENCE_INSTABILITY

    # 6. Linear solver failure
    d6 = CFDDiagnosticsEngine.diagnose(solver_log="GAMG: failed to converge in 100 iterations")
    assert d6.error_class == CFDErrorClass.LINEAR_SOLVER_FAILURE

    # 7. Time step instability
    d7 = CFDDiagnosticsEngine.diagnose(solver_log="time step too large, aborting run")
    assert d7.error_class == CFDErrorClass.TIME_STEP_INSTABILITY

    # 8. Residual divergence
    d8 = CFDDiagnosticsEngine.diagnose(residuals={"p": [0.1, 5.0, 150.0]})
    assert d8.error_class == CFDErrorClass.DIVERGENCE

    # 9. Residual stagnation
    stagnant_vals = [0.015] * 350
    d9 = CFDDiagnosticsEngine.diagnose(residuals={"p": stagnant_vals})
    assert d9.error_class == CFDErrorClass.RESIDUAL_STAGNATION

    # 10. Mesh quality failure
    d10 = CFDDiagnosticsEngine.diagnose(mesh_log="checkMesh: non-orthogonality > 70 degrees, mesh invalid")
    assert d10.error_class == CFDErrorClass.MESH_QUALITY_FAILURE

    # 11. Invalid boundary condition
    d11 = CFDDiagnosticsEngine.diagnose(solver_log="patch not found in polyMesh/boundary")
    assert d11.error_class == CFDErrorClass.INVALID_BOUNDARY_CONDITION


def test_repair_engine_proposes_tailored_modifications():
    """Verify repair engine generates specific fixes for Courant and linear solver failures."""
    spec = {"geometry": "NACA 4412", "alpha_deg": 6.0}
    orig_hash = "hash12345678"

    # Test Courant fix
    d_courant = CFDDiagnosticsEngine.diagnose(solver_log="Courant Number mean: 0.1 max: 12.0")
    outcome_c = CFDRepairEngine.propose_repair(spec, orig_hash, d_courant, current_retry_count=0)
    assert outcome_c.status == "REPAIR_CANDIDATE_GENERATED"
    assert outcome_c.candidate.candidate_case_hash != orig_hash
    assert "controlDict_maxCo" in outcome_c.candidate.modifications

    # Test Linear solver fix
    d_linear = CFDDiagnosticsEngine.diagnose(solver_log="GAMG: failed to converge in 100 iterations")
    outcome_l = CFDRepairEngine.propose_repair(spec, orig_hash, d_linear, current_retry_count=1)
    assert outcome_l.status == "REPAIR_CANDIDATE_GENERATED"
    assert outcome_l.candidate.retry_number == 2
    assert outcome_l.candidate.modifications.get("fvSolution_solvers_p") == "PCG"


def test_repair_exhaustion_boundary():
    """Verify strict fail-closed boundary: MAX_RETRIES = 3 -> HUMAN_REVIEW_REQUIRED."""
    spec = {"geometry": "NACA 4412", "alpha_deg": 6.0}
    orig_hash = "hash12345678"
    d_div = CFDDiagnosticsEngine.diagnose(residuals={"p": [10.0, 50.0, 500.0]})

    outcome = CFDRepairEngine.propose_repair(spec, orig_hash, d_div, current_retry_count=3)
    assert outcome.status == "HUMAN_REVIEW_REQUIRED"
    assert outcome.retries_exhausted is True
    assert outcome.candidate is None
