"""
AASI Scientific Compiler Core.
Transforms Aerospace Mission Language (AML) AST statements into executable
Scientific Task DAGs with explicit data bindings and dependency trees.
"""

from typing import Any, Dict, List, Optional
import uuid

from backend.scientific_language.ast import (
    AMLProgram,
    AMLStatement,
    InvestigateStatement,
    CompareStatement,
    OptimizeStatement,
    ValidateStatement,
    SweepStatement,
    CharacterizeStatement,
)
from backend.scientific_compiler.dag import (
    ScientificTaskDAG,
    ScientificTaskNode,
    ScientificTaskType,
    ScientificDependencyEdge,
)
from backend.tools.contracts import EpistemicTier


class ScientificCompiler:
    """
    Translates declarative AML AST specifications into deterministic,
    optimally-ordered execution graphs.
    """

    @classmethod
    def compile_program(cls, program: AMLProgram) -> List[ScientificTaskDAG]:
        dags = []
        for i, stmt in enumerate(program.statements):
            mission_name = stmt.name or f"Mission_{i + 1}_{stmt.statement_type}"
            dag = cls.compile_statement(stmt, mission_name=mission_name)
            dags.append(dag)
        return dags

    @classmethod
    def compile_statement(cls, stmt: AMLStatement, mission_name: Optional[str] = None) -> ScientificTaskDAG:
        name = mission_name or stmt.name or f"{stmt.statement_type}_{uuid.uuid4().hex[:6]}"
        dag_id = f"DAG-{uuid.uuid4().hex[:8]}"
        dag = ScientificTaskDAG(dag_id=dag_id, mission_name=name)

        if isinstance(stmt, InvestigateStatement):
            cls._compile_investigate(stmt, dag)
        elif isinstance(stmt, CompareStatement):
            cls._compile_compare(stmt, dag)
        elif isinstance(stmt, SweepStatement):
            cls._compile_sweep(stmt, dag)
        elif isinstance(stmt, OptimizeStatement):
            cls._compile_optimize(stmt, dag)
        elif isinstance(stmt, ValidateStatement):
            cls._compile_validate(stmt, dag)
        elif isinstance(stmt, CharacterizeStatement):
            cls._compile_characterize(stmt, dag)
        else:
            raise NotImplementedError(f"Unsupported statement type: {type(stmt)}")

        dag.compute_dag_hash()
        return dag

    # -------------------------------------------------------------------------
    # INVESTIGATE Statement Compiler
    # -------------------------------------------------------------------------
    @classmethod
    def _compile_investigate(cls, stmt: InvestigateStatement, dag: ScientificTaskDAG) -> None:
        geom = stmt.geometry
        alpha = stmt.conditions.alpha_deg if stmt.conditions.alpha_deg is not None else 4.0
        mach = stmt.conditions.mach if stmt.conditions.mach is not None else 0.15
        reynolds = stmt.conditions.reynolds if stmt.conditions.reynolds is not None else 3e6

        # 1. Resolve Geometry Node
        t_geom = ScientificTaskNode(
            task_id="t_resolve_geom",
            name=f"Resolve Airfoil Geometry ({geom})",
            task_type=ScientificTaskType.RESOLVE_GEOMETRY,
            epistemic_tier=EpistemicTier.ANALYTICAL,
            parameters={"geometry": geom},
            estimated_cost_ms=5.0,
        )
        dag.add_node(t_geom)

        # 2. Query AeroDB Knowledge Base
        t_aerodb = ScientificTaskNode(
            task_id="t_query_aerodb",
            name=f"Query AeroDB Archive for {geom}",
            task_type=ScientificTaskType.QUERY_AERODB,
            epistemic_tier=EpistemicTier.DATABASE_REAL,
            parameters={"geometry": geom, "alpha": alpha, "reynolds": reynolds, "mach": mach},
            estimated_cost_ms=10.0,
        )
        dag.add_node(t_aerodb)

        # 3. Discrete Vortex Panel Method Solver
        t_panel = ScientificTaskNode(
            task_id="t_solver_panel",
            name=f"Vortex Panel Simulation ({geom} @ {alpha}°)",
            task_type=ScientificTaskType.SOLVER_PANEL,
            epistemic_tier=EpistemicTier.ANALYTICAL,
            parameters={"geometry": geom, "alpha_deg": alpha, "reynolds": reynolds, "mach": mach},
            input_bindings={"coords": "t_resolve_geom.coordinates"},
            estimated_cost_ms=15.0,
        )
        dag.add_node(t_panel)
        dag.add_edge("t_resolve_geom", "t_solver_panel")

        # 4. Multi-Fidelity Decision Gate
        t_decision = ScientificTaskNode(
            task_id="t_fidelity_decision",
            name="Evaluate Multi-Fidelity Requirements",
            task_type=ScientificTaskType.FIDELITY_DECISION,
            epistemic_tier=EpistemicTier.ANALYTICAL,
            parameters={"requested_fidelity": stmt.fidelity, "tolerance": stmt.tolerance},
            input_bindings={
                "aerodb_data": "t_query_aerodb.results",
                "panel_data": "t_solver_panel.results",
            },
            estimated_cost_ms=5.0,
        )
        dag.add_node(t_decision)
        dag.add_edge("t_query_aerodb", "t_fidelity_decision")
        dag.add_edge("t_solver_panel", "t_fidelity_decision")

        # 5. Physical Validation Gate (Conservation laws)
        t_val = ScientificTaskNode(
            task_id="t_validate_physics",
            name="Verify Conservation of Momentum & Bound Circulation",
            task_type=ScientificTaskType.VALIDATE_PHYSICS,
            epistemic_tier=EpistemicTier.ANALYTICAL,
            parameters={"tolerance": stmt.tolerance},
            input_bindings={"solver_output": "t_solver_panel.results"},
            estimated_cost_ms=5.0,
        )
        dag.add_node(t_val)
        dag.add_edge("t_solver_panel", "t_validate_physics")

        # 6. Multi-Fidelity Reconciliation
        t_reconcile = ScientificTaskNode(
            task_id="t_reconcile",
            name="Reconcile Multi-Tier Evidence with Uncertainty Bounds",
            task_type=ScientificTaskType.MULTI_FIDELITY_RECONCILE,
            epistemic_tier=EpistemicTier.DERIVED,
            input_bindings={
                "aerodb_data": "t_query_aerodb.results",
                "panel_data": "t_solver_panel.results",
                "validation_status": "t_validate_physics.validation_passed",
            },
            estimated_cost_ms=10.0,
        )
        dag.add_node(t_reconcile)
        dag.add_edge("t_fidelity_decision", "t_reconcile")
        dag.add_edge("t_validate_physics", "t_reconcile")

        # 7. Final Scientific Synthesis Report
        t_report = ScientificTaskNode(
            task_id="t_report",
            name="Compile Verifiable Scientific Investigation Report",
            task_type=ScientificTaskType.REPORT_SYNTHESIS,
            epistemic_tier=EpistemicTier.DERIVED,
            parameters={"objectives": stmt.objectives, "autonomy_level": stmt.autonomy_level},
            input_bindings={"reconciliation": "t_reconcile.summary"},
            estimated_cost_ms=10.0,
        )
        dag.add_node(t_report)
        dag.add_edge("t_reconcile", "t_report")

    # -------------------------------------------------------------------------
    # COMPARE Statement Compiler
    # -------------------------------------------------------------------------
    @classmethod
    def _compile_compare(cls, stmt: CompareStatement, dag: ScientificTaskDAG) -> None:
        all_geoms = [stmt.base_geometry] + stmt.candidate_geometries
        alpha = stmt.conditions.alpha_deg if stmt.conditions.alpha_deg is not None else 4.0
        mach = stmt.conditions.mach if stmt.conditions.mach is not None else 0.15
        reynolds = stmt.conditions.reynolds if stmt.conditions.reynolds is not None else 3e6

        solver_task_ids = []

        # Build parallel evaluation branch for each candidate
        for i, geom in enumerate(all_geoms):
            geom_tid = f"t_geom_{i}"
            solve_tid = f"t_solve_{i}"
            is_base = (i == 0)
            tag = "Base" if is_base else f"Candidate_{i}"

            t_g = ScientificTaskNode(
                task_id=geom_tid,
                name=f"Resolve Geometry: {geom} ({tag})",
                task_type=ScientificTaskType.RESOLVE_GEOMETRY,
                parameters={"geometry": geom},
            )
            dag.add_node(t_g)

            t_s = ScientificTaskNode(
                task_id=solve_tid,
                name=f"Solve Aerodynamics: {geom} ({tag})",
                task_type=ScientificTaskType.SOLVER_PANEL,
                parameters={"geometry": geom, "alpha_deg": alpha, "reynolds": reynolds, "mach": mach},
                input_bindings={"coords": f"{geom_tid}.coordinates"},
            )
            dag.add_node(t_s)
            dag.add_edge(geom_tid, solve_tid)
            solver_task_ids.append(solve_tid)

        # Comparative Trade Study Ranking Node
        t_rank = ScientificTaskNode(
            task_id="t_trade_study_rank",
            name="Rank Candidates across Objectives (L/D, Drag, Moment)",
            task_type=ScientificTaskType.TRADE_STUDY_RANK,
            parameters={
                "base_geometry": stmt.base_geometry,
                "candidates": stmt.candidate_geometries,
                "metrics": stmt.metrics,
            },
        )
        dag.add_node(t_rank)
        for stid in solver_task_ids:
            dag.add_edge(stid, "t_trade_study_rank")

        # Synthesis Report
        t_rep = ScientificTaskNode(
            task_id="t_report",
            name="Compile Comparative Trade Study Report",
            task_type=ScientificTaskType.REPORT_SYNTHESIS,
            input_bindings={"ranking": "t_trade_study_rank.results"},
        )
        dag.add_node(t_rep)
        dag.add_edge("t_trade_study_rank", "t_report")

    # -------------------------------------------------------------------------
    # SWEEP Statement Compiler
    # -------------------------------------------------------------------------
    @classmethod
    def _compile_sweep(cls, stmt: SweepStatement, dag: ScientificTaskDAG) -> None:
        geom = stmt.geometry
        pts = stmt.sweep_range.points
        mach = stmt.conditions.mach if stmt.conditions.mach is not None else 0.15
        reynolds = stmt.conditions.reynolds if stmt.conditions.reynolds is not None else 3e6

        # 1. Geometry resolution
        t_geom = ScientificTaskNode(
            task_id="t_geom",
            name=f"Resolve Geometry: {geom}",
            task_type=ScientificTaskType.RESOLVE_GEOMETRY,
            parameters={"geometry": geom},
        )
        dag.add_node(t_geom)

        # 2. Discretize parameter sweep
        t_disc = ScientificTaskNode(
            task_id="t_discretize",
            name=f"Discretize {stmt.sweep_range.variable} Sweep ({len(pts)} points)",
            task_type=ScientificTaskType.DISCRETIZE_SWEEP,
            parameters={"points": pts, "variable": stmt.sweep_range.variable},
        )
        dag.add_node(t_disc)

        # 3. Parallel simulation points
        point_task_ids = []
        for i, val in enumerate(pts):
            tid = f"t_pt_{i}"
            t_pt = ScientificTaskNode(
                task_id=tid,
                name=f"Point {i+1}: {stmt.sweep_range.variable}={val}",
                task_type=ScientificTaskType.SOLVER_PANEL,
                parameters={"geometry": geom, "alpha_deg": val, "reynolds": reynolds, "mach": mach},
                input_bindings={"coords": "t_geom.coordinates"},
            )
            dag.add_node(t_pt)
            dag.add_edge("t_geom", tid)
            dag.add_edge("t_discretize", tid)
            point_task_ids.append(tid)

        # 4. Polar Curve Fitting & Aerodynamic Derivatives
        t_fit = ScientificTaskNode(
            task_id="t_polar_fit",
            name="Fit Polar Curves and Extract Derivatives (CL_alpha, CD_min, L/D_max)",
            task_type=ScientificTaskType.POLAR_CURVE_FIT,
            parameters={"variable": stmt.sweep_range.variable, "points": pts},
        )
        dag.add_node(t_fit)
        for ptid in point_task_ids:
            dag.add_edge(ptid, "t_polar_fit")

        # 5. Report
        t_rep = ScientificTaskNode(
            task_id="t_report",
            name="Compile Aerodynamic Polar Sweep Report",
            task_type=ScientificTaskType.REPORT_SYNTHESIS,
            input_bindings={"polar_data": "t_polar_fit.results"},
        )
        dag.add_node(t_rep)
        dag.add_edge("t_polar_fit", "t_report")

    # -------------------------------------------------------------------------
    # OPTIMIZE Statement Compiler
    # -------------------------------------------------------------------------
    @classmethod
    def _compile_optimize(cls, stmt: OptimizeStatement, dag: ScientificTaskDAG) -> None:
        t_geom = ScientificTaskNode(
            task_id="t_geom",
            name=f"Resolve Baseline: {stmt.geometry}",
            task_type=ScientificTaskType.RESOLVE_GEOMETRY,
            parameters={"geometry": stmt.geometry},
        )
        dag.add_node(t_geom)

        t_opt = ScientificTaskNode(
            task_id="t_optimize",
            name=f"Iterative Optimization ({stmt.objective.direction.value} {stmt.objective.metric})",
            task_type=ScientificTaskType.OPTIMIZATION_STEP,
            parameters={
                "geometry": stmt.geometry,
                "objective": stmt.objective.model_dump(),
                "constraints": [c.model_dump() for c in stmt.constraints],
                "max_iterations": stmt.max_iterations,
                "fidelity": stmt.fidelity,
            },
        )
        dag.add_node(t_opt)
        dag.add_edge("t_geom", "t_optimize")

        t_rep = ScientificTaskNode(
            task_id="t_report",
            name="Compile Aerodynamic Optimization Report",
            task_type=ScientificTaskType.REPORT_SYNTHESIS,
            input_bindings={"opt_results": "t_optimize.results"},
        )
        dag.add_node(t_rep)
        dag.add_edge("t_optimize", "t_report")

    # -------------------------------------------------------------------------
    # VALIDATE Statement Compiler
    # -------------------------------------------------------------------------
    @classmethod
    def _compile_validate(cls, stmt: ValidateStatement, dag: ScientificTaskDAG) -> None:
        t_geom = ScientificTaskNode(
            task_id="t_geom",
            name=f"Resolve Benchmark Profile: {stmt.geometry}",
            task_type=ScientificTaskType.RESOLVE_GEOMETRY,
            parameters={"geometry": stmt.geometry},
        )
        dag.add_node(t_geom)

        t_bench = ScientificTaskNode(
            task_id="t_load_bench",
            name=f"Load Benchmark Archive ({stmt.dataset or 'Abbott_1945'})",
            task_type=ScientificTaskType.LOAD_BENCHMARK,
            parameters={"dataset": stmt.dataset or "Abbott_1945", "geometry": stmt.geometry},
        )
        dag.add_node(t_bench)

        t_sim = ScientificTaskNode(
            task_id="t_solver_sim",
            name=f"Compute Simulation for {stmt.geometry}",
            task_type=ScientificTaskType.SOLVER_PANEL,
            parameters={"geometry": stmt.geometry, "alpha_deg": 4.0},
        )
        dag.add_node(t_sim)
        dag.add_edge("t_geom", "t_solver_sim")

        t_vv = ScientificTaskNode(
            task_id="t_asme_vv20",
            name="ASME V&V 20 Benchmark Discrepancy & Validation Check",
            task_type=ScientificTaskType.ASME_VV20_CHECK,
            parameters={"criteria": stmt.criteria, "tolerance": stmt.tolerance},
            input_bindings={
                "benchmark": "t_load_bench.data",
                "simulation": "t_solver_sim.results",
            },
        )
        dag.add_node(t_vv)
        dag.add_edge("t_load_bench", "t_asme_vv20")
        dag.add_edge("t_solver_sim", "t_asme_vv20")

        t_rep = ScientificTaskNode(
            task_id="t_report",
            name="Compile ASME V&V 20 Validation Certification Report",
            task_type=ScientificTaskType.REPORT_SYNTHESIS,
            input_bindings={"vv20": "t_asme_vv20.results"},
        )
        dag.add_node(t_rep)
        dag.add_edge("t_asme_vv20", "t_report")

    # -------------------------------------------------------------------------
    # CHARACTERIZE Statement Compiler
    # -------------------------------------------------------------------------
    @classmethod
    def _compile_characterize(cls, stmt: CharacterizeStatement, dag: ScientificTaskDAG) -> None:
        sweep_stmt = SweepStatement(
            name=f"Comprehensive Characterization: {stmt.geometry}",
            geometry=stmt.geometry,
            sweep_range={
                "variable": "alpha",
                "start": -4.0,
                "end": 14.0,
                "step": 2.0,
                "unit": "deg",
            },
            fidelity=stmt.fidelity,
        )
        cls._compile_sweep(sweep_stmt, dag)
