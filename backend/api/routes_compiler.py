"""
AASI Phase 2: Scientific Compiler & DAG Execution API Router.
Exposes endpoints for compiling AML code into task DAGs and executing them
with deterministic dependency resolution and cryptographic provenance.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.scientific_language import parse_aml, validate_aml
from backend.scientific_compiler import compile_aml, ScientificTaskDAG
from backend.scientific_runtime import execute_dag, ExecutionReport

router = APIRouter(prefix="/compiler", tags=["Scientific Compiler & DAG Runtime"])


class CompileRequest(BaseModel):
    source: str = Field(..., description="AML source code string")


class CompiledDAGSummary(BaseModel):
    dag_id: str
    mission_name: str
    node_count: int
    edge_count: int
    stages_count: int
    stages: List[List[str]]
    nodes: Dict[str, Any]
    edges: List[Any]
    provenance_hash: str


class CompileResponse(BaseModel):
    success: bool
    dags: List[CompiledDAGSummary] = Field(default_factory=list)
    total_missions: int = 0
    error: Optional[str] = None


class ExecuteRequest(BaseModel):
    source: str = Field(..., description="AML source code string")


class ExecuteResponse(BaseModel):
    success: bool
    mission_name: str
    execution_id: str
    dag_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    blocked_tasks: int
    elapsed_wall_time_ms: float
    stages_executed: int
    results: Dict[str, Any] = Field(default_factory=dict)
    provenance_hash: str
    error_summary: Optional[str] = None


@router.post("/compile", response_model=CompileResponse)
def compile_aml_endpoint(req: CompileRequest):
    """
    Compiles declarative AML code into executable Scientific Task DAGs.
    """
    try:
        prog = parse_aml(req.source)
        val = validate_aml(prog)
        if not val.is_valid:
            err_details = "; ".join(e.message for e in val.errors)
            return CompileResponse(success=False, error=f"Semantic validation failed: {err_details}")

        raw_dags = compile_aml(prog)
        dag_list = raw_dags if isinstance(raw_dags, list) else [raw_dags]

        summaries = []
        for d in dag_list:
            stages = d.topological_sort()
            summaries.append(CompiledDAGSummary(
                dag_id=d.dag_id,
                mission_name=d.mission_name,
                node_count=len(d.nodes),
                edge_count=len(d.edges),
                stages_count=len(stages),
                stages=stages,
                nodes={nid: n.model_dump() for nid, n in d.nodes.items()},
                edges=[e.model_dump() for e in d.edges],
                provenance_hash=d.provenance_hash,
            ))

        return CompileResponse(
            success=True,
            dags=summaries,
            total_missions=len(summaries),
        )
    except Exception as e:
        return CompileResponse(success=False, error=str(e))


@router.post("/execute", response_model=ExecuteResponse)
def compile_and_execute_endpoint(req: ExecuteRequest):
    """
    Compiles AML code and executes the scientific task graph to completion.
    """
    try:
        prog = parse_aml(req.source)
        val = validate_aml(prog)
        if not val.is_valid:
            err_details = "; ".join(e.message for e in val.errors)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Validation failed: {err_details}")

        raw_dags = compile_aml(prog)
        dags = raw_dags if isinstance(raw_dags, list) else [raw_dags]
        if not dags:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No executable missions found in AML script")

        # Execute first compiled DAG
        dag = dags[0]
        report = execute_dag(dag)

        return ExecuteResponse(
            success=report.success,
            mission_name=report.mission_name,
            execution_id=report.execution_id,
            dag_id=report.dag_id,
            total_tasks=report.total_tasks,
            completed_tasks=report.completed_tasks,
            failed_tasks=report.failed_tasks,
            blocked_tasks=report.blocked_tasks,
            elapsed_wall_time_ms=report.elapsed_wall_time_ms,
            stages_executed=report.stages_executed,
            results=report.task_results,
            provenance_hash=report.provenance_hash,
            error_summary=report.error_summary,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
