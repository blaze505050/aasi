"""
AASI Phase 4: Merkle-DAG Experiment Lineage & Provenance Kernel.
Governing Doctrine: Absolute Anti-Fabrication Rule.

Provides cryptographic Merkle-DAG experiment lineage tracking:
- Every computational stage (Geometry, Mesh, Solver, Verification, Reconciliation) produces an immutable Merkle block.
- Child stages cryptographically bind parent hashes, establishing an unforgeable causal DAG.
- Tracks input digests, code/tool digests, artifact digests, and metric digests.
- Enables autonomous end-to-end auditability and verification back to genesis parameters.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("aasi.science.merkle")


class MerkleNodeType(str, Enum):
    """Classification of Merkle DAG lineage nodes."""
    GENESIS_SPEC = "GENESIS_SPEC"                  # Initial problem formulation / mission intent
    GEOMETRY_DISCRETIZATION = "GEOMETRY_DISCRETIZATION"  # Surface point coordinate generation
    MESH_GENERATION = "MESH_GENERATION"            # Computational grid generation / blockMeshDict
    SOLVER_EXECUTION = "SOLVER_EXECUTION"          # Live or panel solver aerodynamic solve
    EVIDENCE_RECONCILIATION = "EVIDENCE_RECONCILIATION"  # Cross-fidelity physical reconciliation
    DERIVED_ANALYSIS = "DERIVED_ANALYSIS"          # Polar curve fit, derivatives, trade-study rank
    WARM_START_SEED = "WARM_START_SEED"            # Seed from verified prior memory
    AUDIT_CHECKPOINT = "AUDIT_CHECKPOINT"          # ASME V&V 20 / GCI certification seal


def canonical_hash(payload: Any) -> str:
    """Computes deterministic SHA-256 digest of canonicalized JSON."""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class MerkleLineageNode(BaseModel):
    """
    Immutable node in the cryptographic experiment lineage Merkle DAG.
    """
    node_id: str = Field(..., description="Cryptographic SHA-256 node hash")
    investigation_id: str = Field(..., description="Associated investigation identifier")
    stage_name: str = Field(..., description="Stage or task name (e.g. SOLVER_CFD_RANS)")
    node_type: MerkleNodeType = Field(..., description="Classification of this computational step")
    parent_hashes: List[str] = Field(default_factory=list, description="List of parent node SHA-256 hashes in the DAG")
    input_digest: str = Field(..., description="SHA-256 hash of all input parameters and bindings")
    code_digest: str = Field(..., description="SHA-256 hash of solver/tool implementation fingerprint")
    artifact_digests: Dict[str, str] = Field(
        default_factory=dict,
        description="Named artifact digests (e.g. {'blockMeshDict': 'hash...', 'forces.dat': 'hash...'}})",
    )
    metrics_digest: str = Field(..., description="SHA-256 hash of output numerical metrics (CL, CD, residuals)")
    epistemic_tier: str = Field(default="VERIFIED", description="Epistemic trust tier of this stage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Human-readable provenance metadata")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        investigation_id: str,
        stage_name: str,
        node_type: MerkleNodeType,
        parent_hashes: Optional[List[str]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        code_identifier: str = "AASI_KERNEL_v1.0",
        artifacts: Optional[Dict[str, str]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        epistemic_tier: str = "VERIFIED",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MerkleLineageNode:
        """Constructs and computes cryptographic seal for a new Merkle lineage node."""
        parents = sorted(list(parent_hashes or []))
        in_digest = canonical_hash(inputs or {})
        c_digest = canonical_hash({"code_id": code_identifier})
        art_digests = artifacts or {}
        met_digest = canonical_hash(metrics or {})

        block_seal = canonical_hash({
            "investigation_id": investigation_id,
            "stage_name": stage_name,
            "node_type": node_type.value,
            "parent_hashes": parents,
            "input_digest": in_digest,
            "code_digest": c_digest,
            "artifact_digests": {k: art_digests[k] for k in sorted(art_digests.keys())},
            "metrics_digest": met_digest,
            "epistemic_tier": epistemic_tier,
        })

        return cls(
            node_id=block_seal,
            investigation_id=investigation_id,
            stage_name=stage_name,
            node_type=node_type,
            parent_hashes=parents,
            input_digest=in_digest,
            code_digest=c_digest,
            artifact_digests=art_digests,
            metrics_digest=met_digest,
            epistemic_tier=epistemic_tier,
            metadata=metadata or {},
        )

    @property
    def node_hash(self) -> str:
        """Alias returning cryptographic node ID digest."""
        return self.node_id

    def verify_self_hash(self) -> bool:
        """Verifies cryptographic integrity of this node."""
        expected = canonical_hash({
            "investigation_id": self.investigation_id,
            "stage_name": self.stage_name,
            "node_type": self.node_type.value,
            "parent_hashes": sorted(self.parent_hashes),
            "input_digest": self.input_digest,
            "code_digest": self.code_digest,
            "artifact_digests": {k: self.artifact_digests[k] for k in sorted(self.artifact_digests.keys())},
            "metrics_digest": self.metrics_digest,
            "epistemic_tier": self.epistemic_tier,
        })
        return self.node_id == expected


class MerkleLineageGraph:
    """
    Cryptographic Merkle DAG engine tracking causal experiment lineage across all stages.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        workspace_root = Path(__file__).resolve().parent.parent.parent
        self.storage_path = storage_path or (workspace_root / "data" / "merkle_lineage.json")
        self._nodes: Dict[str, MerkleLineageNode] = {}
        self._investigation_index: Dict[str, List[str]] = {}
        self._load()

    def _load(self) -> None:
        """Loads persistent lineage graph from disk."""
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("nodes", []):
                    node = MerkleLineageNode(**item)
                    self._nodes[node.node_id] = node
                    self._investigation_index.setdefault(node.investigation_id, []).append(node.node_id)
            logger.info("Loaded %d Merkle lineage nodes from %s", len(self._nodes), self.storage_path)
        except Exception as e:
            logger.warning("Failed loading Merkle lineage from %s: %s", self.storage_path, e)

    def _save(self) -> None:
        """Persists Merkle lineage graph atomically with Windows file-lock resilience."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_nodes": len(self._nodes),
            "nodes": [n.model_dump() for n in self._nodes.values()],
        }
        for attempt in range(5):
            temp_file = self.storage_path.with_name(f"{self.storage_path.stem}_{uuid.uuid4().hex[:6]}.tmp")
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                os.replace(temp_file, self.storage_path)
                return
            except PermissionError:
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except Exception:
                        pass
                if attempt == 4:
                    with open(self.storage_path, "w", encoding="utf-8") as f:
                        json.dump(payload, f, indent=2)
                    return
                time.sleep(0.05)

    def record_node(
        self,
        investigation_id: str,
        stage_name: str,
        node_type: MerkleNodeType,
        parent_hashes: Optional[List[str]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        code_identifier: str = "AASI_KERNEL_v1.0",
        artifacts: Optional[Dict[str, str]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        epistemic_tier: str = "VERIFIED",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MerkleLineageNode:
        """
        Creates, seals, indexes, and persists an immutable Merkle lineage node.
        """
        node = MerkleLineageNode.create(
            investigation_id=investigation_id,
            stage_name=stage_name,
            node_type=node_type,
            parent_hashes=parent_hashes,
            inputs=inputs,
            code_identifier=code_identifier,
            artifacts=artifacts,
            metrics=metrics,
            epistemic_tier=epistemic_tier,
            metadata=metadata,
        )

        self._nodes[node.node_id] = node
        self._investigation_index.setdefault(investigation_id, []).append(node.node_id)
        self._save()
        return node

    @property
    def node_count(self) -> int:
        """Returns total number of sealed Merkle lineage blocks."""
        return len(self._nodes)

    def get_node(self, node_id: str) -> Optional[MerkleLineageNode]:
        """Retrieves a node by its SHA-256 hash."""
        return self._nodes.get(node_id)

    def get_investigation_lineage(self, investigation_id: str) -> List[MerkleLineageNode]:
        """Retrieves all Merkle nodes for an investigation in recording order."""
        node_ids = self._investigation_index.get(investigation_id, [])
        return [self._nodes[nid] for nid in node_ids if nid in self._nodes]

    def get_investigation_nodes(self, investigation_id: str) -> List[MerkleLineageNode]:
        """Alias for get_investigation_lineage."""
        return self.get_investigation_lineage(investigation_id)

    def get_parents(self, node_id: str) -> List[MerkleLineageNode]:
        """Returns direct parent nodes in the DAG."""
        node = self.get_node(node_id)
        if not node:
            return []
        return [self._nodes[ph] for ph in node.parent_hashes if ph in self._nodes]

    def get_children(self, node_id: str) -> List[MerkleLineageNode]:
        """Returns downstream nodes that depend directly on this node."""
        children = []
        for n in self._nodes.values():
            if node_id in n.parent_hashes:
                children.append(n)
        return children

    def verify_node(self, node_id: str) -> bool:
        """Verifies self-integrity of a node."""
        node = self.get_node(node_id)
        if not node:
            return False
        return node.verify_self_hash()

    def verify_lineage_trace(self, node_id: str) -> Dict[str, Any]:
        """
        Performs recursive backward trace verifying that every ancestor node
        is uncorrupted and that parent hashes match actual existing blocks.
        """
        node = self.get_node(node_id)
        if not node:
            return {"valid": False, "reason": f"Node {node_id} not found", "ancestor_count": 0}

        visited = set()
        to_visit = [node_id]
        ancestors_verified = 0

        while to_visit:
            curr_id = to_visit.pop(0)
            if curr_id in visited:
                continue
            visited.add(curr_id)

            curr_node = self.get_node(curr_id)
            if not curr_node:
                return {
                    "valid": False,
                    "reason": f"Missing ancestor node with hash {curr_id}",
                    "broken_at": curr_id,
                    "ancestor_count": ancestors_verified,
                }

            if not curr_node.verify_self_hash():
                return {
                    "valid": False,
                    "reason": f"Hash mismatch in node {curr_id} (data corrupted or forged)",
                    "broken_at": curr_id,
                    "ancestor_count": ancestors_verified,
                }

            ancestors_verified += 1
            for p_hash in curr_node.parent_hashes:
                if p_hash not in visited:
                    to_visit.append(p_hash)

        return {
            "valid": True,
            "root_node_id": node_id,
            "investigation_id": node.investigation_id,
            "ancestor_count": ancestors_verified,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    def compute_investigation_root(self, investigation_id: str) -> str:
        """
        Computes a single root Merkle digest summarizing all nodes in the investigation.
        """
        nodes = self.get_investigation_lineage(investigation_id)
        if not nodes:
            return hashlib.sha256(f"EMPTY_INVESTIGATION:{investigation_id}".encode("utf-8")).hexdigest()

        node_hashes = [n.node_id for n in nodes]
        return canonical_hash({
            "investigation_id": investigation_id,
            "node_count": len(nodes),
            "lineage_hashes": node_hashes,
        })

    def export_audit_proof(self, node_id: str) -> Dict[str, Any]:
        """
        Exports a complete cryptographic audit receipt for independent verification.
        """
        trace = self.verify_lineage_trace(node_id)
        node = self.get_node(node_id)
        if not node:
            return {"error": f"Node {node_id} not found"}

        ancestors = []
        for p_hash in node.parent_hashes:
            p_node = self.get_node(p_hash)
            if p_node:
                ancestors.append({
                    "node_id": p_node.node_id,
                    "stage_name": p_node.stage_name,
                    "node_type": p_node.node_type.value,
                    "timestamp": p_node.timestamp,
                })

        return {
            "node": node.model_dump(),
            "verification": trace,
            "immediate_parents": ancestors,
            "proof_generator": "AASI_MERKLE_KERNEL_v1.0",
            "proof_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def clear(self) -> None:
        """Resets the lineage graph (for testing)."""
        self._nodes.clear()
        self._investigation_index.clear()
        if self.storage_path.exists():
            try:
                self.storage_path.unlink()
            except Exception:
                pass


# Global singleton instance
merkle_lineage = MerkleLineageGraph()
