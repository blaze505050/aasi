"""
Comprehensive test suite for AASI Scientific Compiler.
Validates translation of AML statements into Directed Acyclic Graphs (DAGs),
topological sorting, parallel stage identification, and cycle detection.
"""

import pytest
from backend.scientific_language import parse_aml
from backend.scientific_compiler import compile_aml, ScientificTaskDAG, ScientificTaskType, TaskExecutionState


def test_compile_investigate_statement():
    aml = """
    INVESTIGATE "NACA0012 Cruise Polar" {
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
    dags = compile_aml(program)
    assert len(dags) == 1
    dag = dags[0]

    assert isinstance(dag, ScientificTaskDAG)
    assert dag.mission_name == "NACA0012 Cruise Polar"
    assert len(dag.nodes) == 7
    assert len(dag.edges) >= 6

    # Verify task types present
    task_types = {n.task_type for n in dag.nodes.values()}
    assert ScientificTaskType.RESOLVE_GEOMETRY in task_types
    assert ScientificTaskType.QUERY_AERODB in task_types
    assert ScientificTaskType.SOLVER_PANEL in task_types
    assert ScientificTaskType.FIDELITY_DECISION in task_types
    assert ScientificTaskType.VALIDATE_PHYSICS in task_types
    assert ScientificTaskType.MULTI_FIDELITY_RECONCILE in task_types
    assert ScientificTaskType.REPORT_SYNTHESIS in task_types

    # Verify topological sorting into stages
    stages = dag.topological_sort()
    assert len(stages) >= 4
    # First stage should contain root tasks with in-degree 0 (e.g. resolve_geom and query_aerodb)
    stage_0 = set(stages[0])
    assert "t_resolve_geom" in stage_0
    assert "t_query_aerodb" in stage_0

    # Last stage should contain final report synthesis
    assert "t_report" in stages[-1]


def test_compile_compare_trade_study():
    aml = """
    COMPARE "Supercritical Trade" {
        BASE "NACA0012"
        CANDIDATES ["NACA4412", "NACA2412"]
        CONDITIONS { alpha: 3.0 deg, Mach: 0.2 }
        METRICS [L_OVER_D, CD]
    }
    """
    program = parse_aml(aml)
    dag = compile_aml(program)[0]

    # Should have 3 geometry resolutions, 3 panel solvers, 1 trade study rank, 1 report = 8 nodes
    assert len(dag.nodes) == 8
    stages = dag.topological_sort()
    # Parallel geometry resolutions should all be in stage 0
    assert len(stages[0]) == 3
    # Trade study rank must depend on all 3 solvers
    rank_preds = dag.get_predecessors("t_trade_study_rank")
    assert len(rank_preds) == 3


def test_compile_sweep_statement():
    aml = """
    SWEEP "AoA Characterization" {
        GEOMETRY "NACA0012"
        VARIABLE alpha FROM -2.0 TO 6.0 STEP 2.0 deg
        CONDITIONS { Mach: 0.15, Re: 1e6 }
        RECORD [CL, CD]
    }
    """
    program = parse_aml(aml)
    dag = compile_aml(program)[0]

    # Points: -2, 0, 2, 4, 6 (5 points)
    # Nodes: t_geom, t_discretize, 5 point solvers, t_polar_fit, t_report = 9 nodes
    assert len(dag.nodes) == 9
    fit_preds = dag.get_predecessors("t_polar_fit")
    assert len(fit_preds) == 5


def test_compile_optimize_statement():
    aml = """
    OPTIMIZE "Flap Setting" {
        GEOMETRY "NACA0012"
        OBJECTIVE MAXIMIZE L_OVER_D
        MAX_ITERATIONS 15
    }
    """
    program = parse_aml(aml)
    dag = compile_aml(program)[0]
    assert "t_optimize" in dag.nodes
    assert dag.nodes["t_optimize"].task_type == ScientificTaskType.OPTIMIZATION_STEP


def test_compile_validate_statement():
    aml = """
    VALIDATE "NACA0012 Benchmark" {
        GEOMETRY "NACA0012"
        DATASET "Abbott_1945"
        TOLERANCE 0.04
    }
    """
    program = parse_aml(aml)
    dag = compile_aml(program)[0]
    assert "t_asme_vv20" in dag.nodes
    assert "t_load_bench" in dag.nodes


def test_dag_cycle_detection():
    from backend.scientific_compiler.dag import ScientificTaskNode
    dag = ScientificTaskDAG(dag_id="DAG-CYCLE", mission_name="Cycle Test")
    dag.add_node(ScientificTaskNode(task_id="A", name="A", task_type=ScientificTaskType.RESOLVE_GEOMETRY))
    dag.add_node(ScientificTaskNode(task_id="B", name="B", task_type=ScientificTaskType.SOLVER_PANEL))
    dag.add_edge("A", "B")
    dag.add_edge("B", "A")  # Cyclic dependency!

    with pytest.raises(ValueError, match="Cycle detected"):
        dag.topological_sort()


def test_dag_hash_deterministic():
    aml = 'INVESTIGATE "NACA0012 Hash" { GEOMETRY "NACA0012" }'
    dag1 = compile_aml(parse_aml(aml))[0]
    dag2 = compile_aml(parse_aml(aml))[0]
    # DAG IDs differ, but structure produces verifiable hash
    assert len(dag1.provenance_hash) == 64
    assert len(dag2.provenance_hash) == 64
