"""
AASI Scientific Execution Runtime Context.
Maintains state, dynamic data bindings, and cryptographic execution logs across tasks.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timezone
import hashlib
import json
from pydantic import BaseModel, Field


class ExecutionContext(BaseModel):
    """
    State container for an active DAG execution run.
    Stores completed task outputs and resolves dynamic input bindings.
    """
    execution_id: str
    dag_id: str
    mission_name: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    task_outputs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    provenance_chain: Dict[str, str] = Field(default_factory=dict)
    merkle_chain: Dict[str, str] = Field(default_factory=dict, description="task_id -> Merkle lineage node_id")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def record_task_output(self, task_id: str, outputs: Dict[str, Any], output_hash: str) -> None:
        self.task_outputs[task_id] = outputs
        self.provenance_chain[task_id] = output_hash

    def record_merkle_node(self, task_id: str, node_id: str) -> None:
        self.merkle_chain[task_id] = node_id

    def get_merkle_node_id(self, task_id: str) -> Optional[str]:
        return self.merkle_chain.get(task_id)

    def resolve_binding(self, binding_expr: str) -> Any:
        """
        Resolves an expression of form 'upstream_task_id.field_name' or 'upstream_task_id'.
        """
        if "." in binding_expr:
            upstream_id, field = binding_expr.split(".", 1)
            outputs = self.task_outputs.get(upstream_id, {})
            return outputs.get(field)
        return self.task_outputs.get(binding_expr)

    def compute_final_provenance(self) -> str:
        """Computes comprehensive SHA-256 digest over all completed tasks in this run."""
        payload = f"{self.execution_id}|{self.dag_id}|{json.dumps(self.provenance_chain, sort_keys=True)}|{json.dumps(self.merkle_chain, sort_keys=True)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
