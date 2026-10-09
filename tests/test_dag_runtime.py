"""
Comprehensive test suite for AASI Scientific DAG Execution Runtime.
Validates topological scheduling, genuine physics solver dispatch,
dynamic data passing, failure circuit breaking, and cryptographic provenance.
"""

import pytest
from backend.scientific_language import parse_aml
from backend.scientific_compiler import compile_aml, ScientificTaskNode, ScientificTaskType, ScientificTaskDAG
from backend.scientific_runtime import execute_dag, ExecutionReport
from backend.scientific_compiler.dag import TaskExecutionState


def test_execute_investigate_dag_end_to_end():
    aml = """
    INVESTIGATE "NACA0012 Investigation Run" {
        GEOMETRY "NACA0012"
        CONDITIONS {
            alpha: 4.0 deg,
            Mach: 0.15,
            Re: 3000000.0
        }
        OBJECTIVES [CL, CD, CM]
        FIDELITY MULTI_FIDELITY
    }
    """
    program = parse_aml(aml)
    dag = compile_aml(program)[0]

    report = execute_dag(dag)
    assert isinstance(report, ExecutionReport)
    assert report.success is True
    assert report.completed_tasks == len(dag.nodes)
    assert report.failed_tasks == 0
    assert report.blocked_tasks == 0
    assert report.elapsed_wall_time_ms > 0.0
    assert len(report.provenance_hash) == 64

    # Verify individual task outputs were recorded
    panel_out = report.task_results.get("t_solver_panel")
    assert panel_out is not None
    assert "cl" in panel_out
    assert panel_out["cl"] > 0.4  # NACA 0012 at alpha=4 deg has CL ~ 0.44

    # Verify physical validation passed
    val_out = report.task_results.get("t_validate_physics")
    assert val_out is not None
    assert val_out["validation_passed"] is True

    # Verify multi-tier reconciliation occurred
    rec_out = report.task_results.get("t_reconcile")
    assert rec_out is not None
    assert rec_out["summary"]["physical_validity"] == "VERIFIED"


def test_execute_compare_dag_multi_geometry():
    aml = """
    COMPARE "Airfoil Comparison" {
        BASE "NACA0012"
        CANDIDATES ["NACA4412", "NACA2412"]
        CONDITIONS { alpha: 4.0 deg }
        METRICS [L_OVER_D]
    }
    """
    dag = compile_aml(parse_aml(aml))[0]
    report = execute_dag(dag)
    assert report.success is True
    assert report.completed_tasks == len(dag.nodes)

    rank_out = report.task_results.get("t_trade_study_rank")
    assert rank_out is not None
    assert "winner" in rank_out
    assert "results" in rank_out
    # NACA 4412 has high camber (4%), so it should produce high lift and strong L/D
    scores = rank_out["results"]
    assert len(scores) == 3


def test_execute_sweep_dag_curve_fit():
    aml = """
    SWEEP "AoA Polar Sweep" {
        GEOMETRY "NACA0012"
        VARIABLE alpha FROM 0.0 TO 8.0 STEP 2.0 deg
        CONDITIONS { Mach: 0.15 }
    }
    """
    dag = compile_aml(parse_aml(aml))[0]
    report = execute_dag(dag)
    assert report.success is True

    fit_out = report.task_results.get("t_polar_fit")
    assert fit_out is not None
    assert "cl_alpha_per_deg" in fit_out["results"]
    assert fit_out["results"]["points_evaluated"] == 5


def test_execute_validate_dag_asme_vv20():
    aml = """
    VALIDATE "NACA0012 Abbott Validation" {
        GEOMETRY "NACA0012"
        DATASET "Abbott_1945"
        TOLERANCE 0.12
    }
    """
    dag = compile_aml(parse_aml(aml))[0]
    report = execute_dag(dag)
    assert report.success is True

    vv_out = report.task_results.get("t_asme_vv20")
    assert vv_out is not None
    assert "asme_vv20_passed" in vv_out["results"]
    assert vv_out["results"]["asme_vv20_passed"] is True


def test_circuit_breaker_blocks_downstream_on_failure():
    # Build a 2-node DAG where node 1 raises an error
    dag = ScientificTaskDAG(dag_id="DAG-FAIL-TEST", mission_name="Failure Test")
    
    # Custom node with illegal geometry to force failure
    t_fail = ScientificTaskNode(
        task_id="t_fail",
        name="Invalid Task",
        task_type=ScientificTaskType.SOLVER_PANEL,
        parameters={"geometry": "", "alpha_deg": "invalid_alpha"},
    )
    t_downstream = ScientificTaskNode(
        task_id="t_downstream",
        name="Downstream Task",
        task_type=ScientificTaskType.REPORT_SYNTHESIS,
    )
    dag.add_node(t_fail)
    dag.add_node(t_downstream)
    dag.add_edge("t_fail", "t_downstream")

    report = execute_dag(dag)
    assert report.success is False
    assert report.failed_tasks == 1
    assert report.blocked_tasks == 1
    assert dag.nodes["t_downstream"].state == TaskExecutionState.BLOCKED
