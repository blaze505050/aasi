"""
AASI Phase 21: CFD Execution Registry.
Governing Rule: Absolute Anti-Fabrication Rule.
Maintains persistent, immutable records of all prepared, staged, and executed CFD simulations.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import time

from backend.cfd.solver_interface import CFDExecutionResult


class CFDExecutionRegistry:
    """Persistent ledger for CFD runs."""

    def __init__(self, registry_file: Optional[Path] = None):
        self.registry_file = registry_file or Path("data/cases/cfd_registry.json")
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.registry_file.exists():
            self._write_records([])

    def _read_records(self) -> List[Dict[str, Any]]:
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_records(self, records: List[Dict[str, Any]]) -> None:
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def register_run(self, result: CFDExecutionResult) -> Dict[str, Any]:
        """Register a simulation run record immutably."""
        records = self._read_records()
        record_id = result.run_id

        # Check if record already exists
        for rec in records:
            if rec.get("run_id") == record_id:
                return rec

        record = {
            "run_id": record_id,
            "case_name": result.case_name,
            "case_dir": result.case_dir,
            "solver_mode": result.solver_mode.value if hasattr(result.solver_mode, "value") else str(result.solver_mode),
            "solver_name": result.solver_name,
            "solver_version": result.solver_version,
            "exit_code": result.exit_code,
            "status": result.status,
            "convergence_state": (
                result.convergence_state.value
                if hasattr(result.convergence_state, "value")
                else str(result.convergence_state)
            ),
            "physical_state": (
                result.physical_state.value
                if hasattr(result.physical_state, "value")
                else str(result.physical_state)
            ),
            "execution_time_sec": result.execution_time_sec,
            "residuals": result.residuals,
            "forces": result.forces,
            "convergence_evidence": result.convergence_evidence,
            "physical_checks": result.physical_checks,
            "provenance_hash": result.provenance_hash,
            "error_message": result.error_message,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        records.append(record)
        self._write_records(records)
        return record

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve run by ID."""
        records = self._read_records()
        for rec in records:
            if rec.get("run_id") == run_id:
                return rec
        return None

    def list_runs(self) -> List[Dict[str, Any]]:
        """List all CFD records."""
        return self._read_records()
