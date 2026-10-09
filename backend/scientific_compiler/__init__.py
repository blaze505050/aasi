"""
AASI Scientific Compiler Package.
Compiles Aerospace Mission Language (AML) code into deterministic,
parallelized Scientific Task DAGs.
"""

from typing import List, Union
from backend.scientific_language.ast import AMLProgram, AMLStatement
from backend.scientific_compiler.dag import (
    ScientificTaskDAG,
    ScientificTaskNode,
    ScientificDependencyEdge,
    ScientificTaskType,
    TaskExecutionState,
)
from backend.scientific_compiler.compiler import ScientificCompiler


def compile_aml(item: Union[AMLProgram, AMLStatement]) -> Union[ScientificTaskDAG, List[ScientificTaskDAG]]:
    """Compiles an AML AST program or statement into executable Scientific Task DAG(s)."""
    if isinstance(item, AMLProgram):
        return ScientificCompiler.compile_program(item)
    return ScientificCompiler.compile_statement(item)


__all__ = [
    "compile_aml",
    "ScientificCompiler",
    "ScientificTaskDAG",
    "ScientificTaskNode",
    "ScientificDependencyEdge",
    "ScientificTaskType",
    "TaskExecutionState",
]
