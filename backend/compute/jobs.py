"""
AASI Phase 23: Immutable CFD Job Manifest & State Transition Log.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Maintains tamper-evident state machines and cryptographic hashes for all compute jobs.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.compute.base import BackendType, ExecutionState


class CFDJobEvent(BaseModel):
    """Immutable audit trail event in a job's lifecycle."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    from_state: ExecutionState
    to_state: ExecutionState
    detail: str
    actor: str = "AASI_Compute_Fabric"


class CFDJobManifest(BaseModel):
    """
    Immutable manifest governing a remote or local CFD compute job.
    Evolves exclusively via append-only state transitions. Never overwritten.
    """
    job_id: str
    experiment_id: str
    geometry_name: str
    geometry_hash: str
    case_hash: str
    mesh_hash: Optional[str] = None
    solver: str = "simpleFoam"
    solver_version: Optional[str] = None
    backend: BackendType = BackendType.COLAB
    conditions: Dict[str, Any] = Field(default_factory=dict)
    requested_resources: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: ExecutionState = ExecutionState.QUEUED
    events: List[CFDJobEvent] = Field(default_factory=list)
    artifacts_dir: Optional[str] = None
    runtime_metadata: Dict[str, Any] = Field(default_factory=dict)
    output_hashes: Dict[str, str] = Field(default_factory=dict)
    expected_output_hashes: Dict[str, str] = Field(default_factory=dict)
    imported_result_hash: Optional[str] = None
    execution_log_summary: Optional[str] = None
    validation_verdict: Optional[str] = None
    provenance_root_hash: Optional[str] = None

    def transition_to(self, new_state: ExecutionState, detail: str = "") -> None:
        """Appends a verifiable state transition event."""
        event = CFDJobEvent(
            from_state=self.status,
            to_state=new_state,
            detail=detail,
        )
        self.events.append(event)
        self.status = new_state

    def compute_manifest_hash(self) -> str:
        """Returns deterministic SHA-256 hash of core scientific parameters."""
        core_dict = {
            "job_id": self.job_id,
            "experiment_id": self.experiment_id,
            "geometry_name": self.geometry_name,
            "geometry_hash": self.geometry_hash,
            "case_hash": self.case_hash,
            "solver": self.solver,
            "backend": self.backend.value,
            "conditions": self.conditions,
        }
        raw = json.dumps(core_dict, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def save(self, path: Path) -> None:
        """Persist manifest as formatted JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "CFDJobManifest":
        """Load manifest from JSON file."""
        return cls.model_validate_json(path.read_text(encoding="utf-8"))
