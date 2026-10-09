"""
AASI Scientific Execution Runtime Package.
Provides topological task scheduling, genuine computational physics dispatch,
and cryptographic provenance tracking.
"""

from typing import Optional
from backend.scientific_compiler.dag import ScientificTaskDAG
from backend.scientific_runtime.context import ExecutionContext
from backend.scientific_runtime.executor import ScientificTaskExecutor, TaskExecutionError
from backend.scientific_runtime.scheduler import ScientificDAGScheduler, ExecutionReport


def execute_dag(dag: ScientificTaskDAG, context: Optional[ExecutionContext] = None) -> ExecutionReport:
    """Executes a ScientificTaskDAG topologically to completion."""
    return ScientificDAGScheduler.execute(dag, context=context)


__all__ = [
    "execute_dag",
    "ScientificDAGScheduler",
    "ScientificTaskExecutor",
    "ExecutionContext",
    "ExecutionReport",
    "TaskExecutionError",
]
