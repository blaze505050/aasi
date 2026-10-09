"""
AASI Scientific Execution DAG Model.
Defines strongly-typed nodes, dependency edges, execution states,
and provenance tracking for compiled scientific investigations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone
import hashlib
import json
from pydantic import BaseModel, Field

from backend.tools.contracts import EpistemicTier


class TaskExecutionState(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"


class ScientificTaskType(str, Enum):
    # Geometry & Setup
    RESOLVE_GEOMETRY = "RESOLVE_GEOMETRY"
    DISCRETIZE_SWEEP = "DISCRETIZE_SWEEP"
    # Knowledge & Database
    QUERY_AERODB = "QUERY_AERODB"
    KNOWLEDGE_SEARCH = "KNOWLEDGE_SEARCH"
    LOAD_BENCHMARK = "LOAD_BENCHMARK"
    # Computational Solvers
    SOLVER_PANEL = "SOLVER_PANEL"
    SOLVER_SURROGATE = "SOLVER_SURROGATE"
    SOLVER_CFD_RANS = "SOLVER_CFD_RANS"
    # Verification & Validation
    VALIDATE_PHYSICS = "VALIDATE_PHYSICS"
    GRID_CONVERGENCE = "GRID_CONVERGENCE"
    ASME_VV20_CHECK = "ASME_VV20_CHECK"
    # Cross-Fidelity & Synthesis
    FIDELITY_DECISION = "FIDELITY_DECISION"
    MULTI_FIDELITY_RECONCILE = "MULTI_FIDELITY_RECONCILE"
    TRADE_STUDY_RANK = "TRADE_STUDY_RANK"
    POLAR_CURVE_FIT = "POLAR_CURVE_FIT"
    OPTIMIZATION_STEP = "OPTIMIZATION_STEP"
    REPORT_SYNTHESIS = "REPORT_SYNTHESIS"


class ScientificTaskNode(BaseModel):
    """
    Atomic executable computational task in a scientific DAG.
    """
    task_id: str
    name: str
    task_type: ScientificTaskType
    epistemic_tier: EpistemicTier = EpistemicTier.ANALYTICAL
    state: TaskExecutionState = TaskExecutionState.PENDING
    
    # Input parameter requirements and dynamic dependencies
    parameters: Dict[str, Any] = Field(default_factory=dict)
    input_bindings: Dict[str, str] = Field(
        default_factory=dict,
        description="Maps input_param_name -> 'upstream_task_id.output_field'"
    )
    
    # Execution metrics and results
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: float = 0.0
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    provenance_hash: Optional[str] = None
    
    # Cost estimation
    estimated_cost_ms: float = 10.0


class ScientificDependencyEdge(BaseModel):
    """
    Directed dependency between an upstream prerequisite and downstream consumer.
    """
    source_task_id: str
    target_task_id: str
    is_data_dependency: bool = True
    condition: Optional[str] = None


class ScientificTaskDAG(BaseModel):
    """
    Executable Directed Acyclic Graph representing a compiled scientific mission.
    """
    dag_id: str
    mission_name: str
    description: str = ""
    nodes: Dict[str, ScientificTaskNode] = Field(default_factory=dict)
    edges: List[ScientificDependencyEdge] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provenance_hash: str = ""

    def add_node(self, node: ScientificTaskNode) -> None:
        self.nodes[node.task_id] = node

    def add_edge(self, source: str, target: str, is_data: bool = True, condition: Optional[str] = None) -> None:
        if source not in self.nodes:
            raise ValueError(f"Source task '{source}' not in DAG")
        if target not in self.nodes:
            raise ValueError(f"Target task '{target}' not in DAG")
        self.edges.append(ScientificDependencyEdge(
            source_task_id=source,
            target_task_id=target,
            is_data_dependency=is_data,
            condition=condition,
        ))

    def get_predecessors(self, task_id: str) -> List[str]:
        return [e.source_task_id for e in self.edges if e.target_task_id == task_id]

    def get_successors(self, task_id: str) -> List[str]:
        return [e.target_task_id for e in self.edges if e.source_task_id == task_id]

    def get_in_degrees(self) -> Dict[str, int]:
        degrees = {nid: 0 for nid in self.nodes}
        for e in self.edges:
            degrees[e.target_task_id] += 1
        return degrees

    def topological_sort(self) -> List[List[str]]:
        """
        Computes parallel execution stages using Kahn's algorithm.
        Returns a list of stages, where each stage contains tasks that can execute concurrently.
        """
        in_degree = self.get_in_degrees()
        ready_queue = [nid for nid, deg in in_degree.items() if deg == 0]
        stages: List[List[str]] = []
        visited = set()

        while ready_queue:
            current_stage = list(ready_queue)
            stages.append(current_stage)
            next_queue = []

            for task_id in current_stage:
                visited.add(task_id)
                for successor in self.get_successors(task_id):
                    in_degree[successor] -= 1
                    if in_degree[successor] == 0:
                        next_queue.append(successor)

            ready_queue = next_queue

        if len(visited) != len(self.nodes):
            unvisited = set(self.nodes.keys()) - visited
            raise ValueError(f"Cycle detected in Scientific DAG! Unresolved tasks: {unvisited}")

        return stages

    def compute_dag_hash(self) -> str:
        """Computes deterministic SHA-256 fingerprint of the DAG topology and specifications."""
        structure = {
            "dag_id": self.dag_id,
            "nodes": {nid: {"type": n.task_type.value, "params": n.parameters} for nid, n in sorted(self.nodes.items())},
            "edges": [(e.source_task_id, e.target_task_id) for e in sorted(self.edges, key=lambda x: (x.source_task_id, x.target_task_id))],
        }
        digest = hashlib.sha256(json.dumps(structure, sort_keys=True).encode("utf-8")).hexdigest()
        self.provenance_hash = digest
        return digest
