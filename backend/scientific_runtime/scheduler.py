"""
AASI Deterministic Scientific DAG Execution Scheduler.
Executes ScientificTaskDAG instances according to topological dependencies,
enforcing anti-fabrication gates and generating cryptographic audit chains.
"""

from typing import Any, Dict, List, Optional
import time
from datetime import datetime, timezone
import uuid
import hashlib
import json
from pydantic import BaseModel, Field

from backend.scientific_compiler.dag import (
    ScientificTaskDAG,
    ScientificTaskNode,
    TaskExecutionState,
)
from backend.scientific_runtime.context import ExecutionContext
from backend.scientific_runtime.executor import ScientificTaskExecutor


class ExecutionReport(BaseModel):
    execution_id: str
    dag_id: str
    mission_name: str
    success: bool
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    blocked_tasks: int
    elapsed_wall_time_ms: float
    stages_executed: int
    task_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    provenance_hash: str = ""
    error_summary: Optional[str] = None


class ScientificDAGScheduler:
    """
    Executes a ScientificTaskDAG topologically with full provenance verification.
    """

    @classmethod
    def execute(cls, dag: ScientificTaskDAG, context: Optional[ExecutionContext] = None) -> ExecutionReport:
        t_start = time.perf_counter()
        exec_id = f"RUN-{uuid.uuid4().hex[:8]}"

        ctx = context or ExecutionContext(
            execution_id=exec_id,
            dag_id=dag.dag_id,
            mission_name=dag.mission_name,
        )

        stages = dag.topological_sort()
        has_failure = False
        error_msgs = []

        for stage_idx, stage_tasks in enumerate(stages):
            for task_id in stage_tasks:
                node = dag.nodes[task_id]

                # 1. Prerequisite verification
                predecessors = dag.get_predecessors(task_id)
                failed_preds = [p for p in predecessors if dag.nodes[p].state in (TaskExecutionState.FAILED, TaskExecutionState.BLOCKED)]
                
                if failed_preds:
                    node.state = TaskExecutionState.BLOCKED
                    node.error = f"Blocked by failed predecessor(s): {failed_preds}"
                    continue

                # 2. Execution
                node.state = TaskExecutionState.RUNNING
                node.started_at = datetime.now(timezone.utc).isoformat()
                node_t0 = time.perf_counter()

                try:
                    outputs = ScientificTaskExecutor.execute_node(node, ctx)
                    node_dur = (time.perf_counter() - node_t0) * 1000.0

                    node.outputs = outputs
                    node.duration_ms = round(node_dur, 2)
                    node.completed_at = datetime.now(timezone.utc).isoformat()
                    node.state = TaskExecutionState.COMPLETED

                    # Compute SHA-256 digest of node output
                    out_hash = hashlib.sha256(
                        json.dumps(outputs, sort_keys=True, default=str).encode("utf-8")
                    ).hexdigest()
                    node.provenance_hash = out_hash

                    # Record in context
                    ctx.record_task_output(task_id, outputs, out_hash)

                except Exception as e:
                    node_dur = (time.perf_counter() - node_t0) * 1000.0
                    node.duration_ms = round(node_dur, 2)
                    node.completed_at = datetime.now(timezone.utc).isoformat()
                    node.state = TaskExecutionState.FAILED
                    node.error = str(e)
                    has_failure = True
                    error_msgs.append(f"Task '{task_id}' failed: {str(e)}")

        total_elapsed = (time.perf_counter() - t_start) * 1000.0
        final_hash = ctx.compute_final_provenance()

        # Aggregate task state counts
        completed = sum(1 for n in dag.nodes.values() if n.state == TaskExecutionState.COMPLETED)
        failed = sum(1 for n in dag.nodes.values() if n.state == TaskExecutionState.FAILED)
        blocked = sum(1 for n in dag.nodes.values() if n.state == TaskExecutionState.BLOCKED)

        return ExecutionReport(
            execution_id=exec_id,
            dag_id=dag.dag_id,
            mission_name=dag.mission_name,
            success=not has_failure,
            total_tasks=len(dag.nodes),
            completed_tasks=completed,
            failed_tasks=failed,
            blocked_tasks=blocked,
            elapsed_wall_time_ms=round(total_elapsed, 2),
            stages_executed=len(stages),
            task_results=ctx.task_outputs,
            provenance_hash=final_hash,
            error_summary="; ".join(error_msgs) if error_msgs else None,
        )
