"""
AASI Experiment Execution Graph.
Directed graph tracking tasks, dependencies, state transitions, and repair lineages.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import hashlib
import json


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class TaskNode(BaseModel):
    """Atomic task node in the scientific experiment graph."""
    node_id: str
    name: str
    task_type: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    output_hash: Optional[str] = None


class TaskEdge(BaseModel):
    """Directed dependency edge between tasks."""
    source: str
    target: str
    condition: Optional[str] = None


class ExperimentGraph(BaseModel):
    """
    Directed execution graph for autonomous scientific workflows.
    Tracks end-to-end task execution and retry lineages.
    """
    graph_id: str
    experiment_id: str
    nodes: Dict[str, TaskNode] = Field(default_factory=dict)
    edges: List[TaskEdge] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    parent_graph_id: Optional[str] = None

    @classmethod
    def create_default_pipeline(cls, experiment_id: str, graph_id: Optional[str] = None) -> "ExperimentGraph":
        """Builds standard autonomous scientific discovery pipeline graph."""
        gid = graph_id or f"GRAPH-{experiment_id}"
        graph = cls(graph_id=gid, experiment_id=experiment_id)

        pipeline_nodes = [
            ("parse_objective", "Parse Scientific Objective", "NLP_PARSER"),
            ("retrieve_dataset", "Retrieve Existing CFD / Polars", "RETRIEVAL"),
            ("surrogate_predict", "Evaluate AeroSurrogateV1", "SURROGATE"),
            ("fidelity_decision", "Determine Execution Fidelity", "DECISION_ENGINE"),
            ("openfoam_stage", "Generate OpenFOAM Simulation Deck", "CFD_STAGER"),
            ("colab_bundle", "Package Colab Execution Bundle", "COMPUTE_PACKAGER"),
            ("execute_cfd", "Execute CFD Solver", "SOLVER_EXECUTION"),
            ("scientific_validation", "Perform ASME V&V 20 & Physics Validation", "VALIDATION"),
            ("generate_report", "Compile Final Scientific Report", "REPORT_GENERATOR"),
        ]

        for nid, name, ttype in pipeline_nodes:
            graph.add_node(TaskNode(node_id=nid, name=name, task_type=ttype))

        # Add linear default edges
        for i in range(len(pipeline_nodes) - 1):
            graph.add_edge(pipeline_nodes[i][0], pipeline_nodes[i + 1][0])

        return graph

    def add_node(self, node: TaskNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, source: str, target: str, condition: Optional[str] = None) -> None:
        self.edges.append(TaskEdge(source=source, target=target, condition=condition))

    def update_node_status(
        self,
        node_id: str,
        status: TaskStatus,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.status = status
            if status == TaskStatus.RUNNING and not node.started_at:
                node.started_at = datetime.now(timezone.utc).isoformat()
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED]:
                node.completed_at = datetime.now(timezone.utc).isoformat()
            if outputs is not None:
                node.outputs = outputs
                # Compute SHA-256 of outputs
                canonical = json.dumps(outputs, sort_keys=True, default=str)
                node.output_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if error:
                node.error = error

    def compute_graph_hash(self) -> str:
        """Computes cryptographic digest of the entire graph state."""
        dump = self.model_dump()
        canonical = json.dumps(dump, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
