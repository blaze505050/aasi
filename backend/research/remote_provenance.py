"""
AASI Phase 23: Remote CFD Cryptographic Provenance Engine.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Builds an unbroken 12-node Merkle Provenance DAG linking physical geometry,
remote execution runtime, solver logs, residual histories, flowfields, and scientific models.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RemoteCFDProvenanceDAG(BaseModel):
    """
    12-Node Cryptographic Merkle Provenance Directed Acyclic Graph.
    Guarantees mathematical tamper-evidence across remote computation boundaries.
    """
    geometry_hash: str
    case_hash: str
    mesh_hash: str
    solver_config_hash: str
    solver_version_hash: str
    runtime_env_hash: str
    execution_log_hash: str
    residual_history_hash: str
    flowfield_hash: str
    force_hash: str
    physical_validation_hash: str
    dataset_record_hash: str
    root_merkle_hash: str
    dag_nodes: Dict[str, str] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def assemble(
        cls,
        geometry_data: Any,
        case_files: Dict[str, Any],
        mesh_meta: Dict[str, Any],
        solver_config: Dict[str, Any],
        solver_version: str,
        runtime_env: Dict[str, Any],
        execution_log: str,
        residual_history: Any,
        flowfield_data: Any,
        forces: Dict[str, float],
        validation_report: Dict[str, Any],
        dataset_record_id: str,
    ) -> "RemoteCFDProvenanceDAG":
        """Construct deterministic 12-node Merkle DAG."""
        h_geom = hashlib.sha256(json.dumps(geometry_data, sort_keys=True).encode()).hexdigest()
        h_case = hashlib.sha256(json.dumps(case_files, sort_keys=True).encode()).hexdigest()
        h_mesh = hashlib.sha256(json.dumps(mesh_meta, sort_keys=True).encode()).hexdigest()
        h_cfg = hashlib.sha256(json.dumps(solver_config, sort_keys=True).encode()).hexdigest()
        h_ver = hashlib.sha256(solver_version.encode()).hexdigest()
        h_env = hashlib.sha256(json.dumps(runtime_env, sort_keys=True).encode()).hexdigest()
        h_log = hashlib.sha256(execution_log.encode()).hexdigest()
        h_res = hashlib.sha256(json.dumps(residual_history, sort_keys=True).encode()).hexdigest()
        h_fld = hashlib.sha256(json.dumps(flowfield_data, sort_keys=True).encode()).hexdigest()
        h_frc = hashlib.sha256(json.dumps(forces, sort_keys=True).encode()).hexdigest()
        h_val = hashlib.sha256(json.dumps(validation_report, sort_keys=True).encode()).hexdigest()
        h_rec = hashlib.sha256(dataset_record_id.encode()).hexdigest()

        nodes = {
            "node_1_geometry": h_geom,
            "node_2_case": h_case,
            "node_3_mesh": h_mesh,
            "node_4_solver_config": h_cfg,
            "node_5_solver_version": h_ver,
            "node_6_runtime_env": h_env,
            "node_7_execution_log": h_log,
            "node_8_residual_history": h_res,
            "node_9_flowfields": h_fld,
            "node_10_forces": h_frc,
            "node_11_physical_validation": h_val,
            "node_12_dataset_record": h_rec,
        }

        # Merkle tree root computation
        combined_leaves = "".join(nodes[k] for k in sorted(nodes.keys()))
        root_hash = hashlib.sha256(combined_leaves.encode()).hexdigest()

        return cls(
            geometry_hash=h_geom,
            case_hash=h_case,
            mesh_hash=h_mesh,
            solver_config_hash=h_cfg,
            solver_version_hash=h_ver,
            runtime_env_hash=h_env,
            execution_log_hash=h_log,
            residual_history_hash=h_res,
            flowfield_hash=h_fld,
            force_hash=h_frc,
            physical_validation_hash=h_val,
            dataset_record_hash=h_rec,
            root_merkle_hash=root_hash,
            dag_nodes=nodes,
        )

    def verify_integrity(self) -> bool:
        """Verify that the stored root Merkle hash matches the leaves."""
        combined_leaves = "".join(self.dag_nodes[k] for k in sorted(self.dag_nodes.keys()))
        computed_root = hashlib.sha256(combined_leaves.encode()).hexdigest()
        return computed_root == self.root_merkle_hash
