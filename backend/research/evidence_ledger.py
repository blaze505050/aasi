"""
AASI Unified Scientific Evidence Ledger.

Governing Directive: Real Scientific Execution, Evidence Integrity & Independent Reproducibility.
Provides an immutable, cryptographically verifiable ledger tracking every piece of evidence,
derivation, computation, and reference supporting scientific research conclusions.
Enforces bi-directional graph traversal:
Conclusion -> Validation -> Computation -> Input -> Dataset/Source.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field


class EpistemicStatus(str, Enum):
    """Rigorous classification of epistemic certainty and origin."""
    REAL = "REAL"                          # Actually downloaded/read/parsed data or executed computation
    DERIVED = "DERIVED"                    # Numerically calculated from real physical inputs (e.g. thin-airfoil)
    REFERENCED = "REFERENCED"              # Authoritative values from peer-reviewed/NASA publications
    SIMULATED = "SIMULATED"                # Actually produced by a validated numerical solver
    SURROGATE = "SURROGATE"                # Produced by a verified trained ML/surrogate model with uncertainty
    UNAVAILABLE = "UNAVAILABLE"            # Required evidence/computation does not exist locally
    USER_EXECUTED = "USER_EXECUTED"        # Staged for external cluster/user execution
    DEMONSTRATION = "DEMONSTRATION"        # Isolated mock path; MUST NEVER be represented as scientific evidence


class EvidenceType(str, Enum):
    """Categorization of research evidence entities."""
    QUESTION = "QUESTION"
    LITERATURE_CITATION = "LITERATURE_CITATION"
    SURFACE_COORDINATES = "SURFACE_COORDINATES"
    POLAR_DATASET = "POLAR_DATASET"
    ANALYTICAL_DERIVATION = "ANALYTICAL_DERIVATION"
    SURROGATE_INFERENCE = "SURROGATE_INFERENCE"
    CFD_CASE_DECK = "CFD_CASE_DECK"
    CFD_GRID_CONVERGENCE = "CFD_GRID_CONVERGENCE"
    UNCERTAINTY_QUANTIFICATION = "UNCERTAINTY_QUANTIFICATION"
    EXPERIMENTAL_BENCHMARK = "EXPERIMENTAL_BENCHMARK"
    VALIDATION_COMPARISON = "VALIDATION_COMPARISON"
    RESEARCH_CONCLUSION = "RESEARCH_CONCLUSION"


class EvidenceRecord(BaseModel):
    """
    Immutable atomic record of a single piece of scientific evidence in AASI.
    Cryptographically tied to inputs, outputs, and provenance parents.
    """
    evidence_id: str
    run_id: str
    evidence_type: EvidenceType
    source: str
    source_identifier: str
    acquisition_method: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    input_hash: str
    output_hash: str
    provenance_chain: List[str] = Field(default_factory=list)  # Parent evidence_ids
    epistemic_status: EpistemicStatus
    reproducibility_status: str = "DETERMINISTIC"  # DETERMINISTIC, STATISTICALLY_REPRODUCIBLE, EXTERNAL_VERIFIED, NON_REPRODUCIBLE
    execution_status: str = "COMPLETED"            # COMPLETED, USER_EXECUTED_REQUIRED, FAILED, UNAVAILABLE
    license: str = "Public Domain"
    citation: Optional[str] = None
    notes: Optional[str] = None
    payload_summary: Dict[str, Any] = Field(default_factory=dict)

    def compute_record_hash(self) -> str:
        """Computes deterministic SHA-256 fingerprint of this record."""
        canonical_content = {
            "evidence_id": self.evidence_id,
            "run_id": self.run_id,
            "evidence_type": self.evidence_type.value,
            "source": self.source,
            "source_identifier": self.source_identifier,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "provenance_chain": sorted(self.provenance_chain),
            "epistemic_status": self.epistemic_status.value,
            "execution_status": self.execution_status,
            "license": self.license
        }
        raw = json.dumps(canonical_content, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class EvidenceLedger(BaseModel):
    """
    Unified machine-readable evidence ledger for a research campaign or run.
    Supports backward graph traversal, chain-of-custody verification, and Merkle fingerprinting.
    """
    ledger_id: str
    run_id: str
    records: List[EvidenceRecord] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    merkle_root: Optional[str] = None

    def append_record(self, record: EvidenceRecord) -> str:
        """Appends a new record and invalidates current Merkle root until recomputed."""
        self.records.append(record)
        self.merkle_root = self.compute_ledger_fingerprint()
        return record.evidence_id

    def get_record(self, evidence_id: str) -> Optional[EvidenceRecord]:
        """Retrieves record by its unique evidence identifier."""
        for r in self.records:
            if r.evidence_id == evidence_id:
                return r
        return None

    def list_records_by_type(self, evidence_type: EvidenceType) -> List[EvidenceRecord]:
        return [r for r in self.records if r.evidence_type == evidence_type]

    def verify_backward_chain(self, target_evidence_id: str) -> Tuple[bool, List[str], List[str]]:
        """
        Performs recursive backward graph traversal from target evidence to root inputs.
        Returns:
            (is_valid, visited_path, missing_links)
        A link is missing if a referenced parent evidence_id does not exist in the ledger.
        """
        visited: List[str] = []
        missing: List[str] = []
        seen: Set[str] = set()

        def _traverse(curr_id: str):
            if curr_id in seen:
                return
            seen.add(curr_id)
            visited.append(curr_id)

            rec = self.get_record(curr_id)
            if rec is None:
                missing.append(curr_id)
                return

            for parent_id in rec.provenance_chain:
                _traverse(parent_id)

        _traverse(target_evidence_id)
        is_valid = (len(missing) == 0) and (len(visited) > 0)
        return is_valid, visited, missing

    def compute_ledger_fingerprint(self) -> str:
        """
        Computes a cumulative cryptographic SHA-256 fingerprint across all records in insertion order.
        Any tampering or reordering immediately changes the fingerprint.
        """
        if not self.records:
            return hashlib.sha256(b"EMPTY_LEDGER").hexdigest()

        running_hash = hashlib.sha256()
        for rec in self.records:
            rec_hash = rec.compute_record_hash()
            running_hash.update(rec_hash.encode("utf-8"))
        fingerprint = running_hash.hexdigest()
        self.merkle_root = fingerprint
        return fingerprint

    def verify_integrity(self) -> EvidenceIntegrityReport:
        """
        Audits the complete evidence ledger DAG for:
        - Duplicate evidence IDs
        - Broken parent links
        - Directed cycles in provenance
        - Orphan records unreachable from conclusion
        - Ancestor validation requirement
        """
        errors = []
        dup_ids = []
        broken_links = []
        cycles = []
        orphans = []

        seen_ids = set()
        for r in self.records:
            if r.evidence_id in seen_ids:
                dup_ids.append(r.evidence_id)
                errors.append(f"Duplicate evidence ID: {r.evidence_id}")
            seen_ids.add(r.evidence_id)

        for r in self.records:
            for p_id in r.provenance_chain:
                if p_id not in seen_ids:
                    broken_links.append(f"{r.evidence_id} -> {p_id}")
                    errors.append(f"Broken provenance link: {r.evidence_id} references missing parent {p_id}")

        adj = {r.evidence_id: r.provenance_chain for r in self.records}
        visited_state: Dict[str, int] = {}

        def _dfs_cycle(node: str, path: List[str]) -> bool:
            visited_state[node] = 1
            for neighbor in adj.get(node, []):
                if neighbor in adj:
                    if visited_state.get(neighbor, 0) == 1:
                        cycle_str = " -> ".join(path + [neighbor])
                        cycles.append(cycle_str)
                        errors.append(f"Provenance cycle detected: {cycle_str}")
                        return True
                    elif visited_state.get(neighbor, 0) == 0:
                        if _dfs_cycle(neighbor, path + [neighbor]):
                            return True
            visited_state[node] = 2
            return False

        for node in adj:
            if visited_state.get(node, 0) == 0:
                _dfs_cycle(node, [node])

        conclusion_records = [r for r in self.records if r.evidence_type == EvidenceType.RESEARCH_CONCLUSION]
        has_conclusion = len(conclusion_records) > 0
        conclusion_has_val = False

        if has_conclusion:
            conc_id = conclusion_records[0].evidence_id
            _, reachable, _ = self.verify_backward_chain(conc_id)
            reachable_set = set(reachable)

            for r in self.records:
                if r.evidence_id not in reachable_set:
                    orphans.append(r.evidence_id)
                    errors.append(f"Orphan evidence record: {r.evidence_id}")

            val_types = [EvidenceType.VALIDATION_COMPARISON, EvidenceType.EXPERIMENTAL_BENCHMARK, EvidenceType.CFD_GRID_CONVERGENCE]
            val_records = [r.evidence_id for r in self.records if r.evidence_type in val_types]
            if any(v in reachable_set for v in val_records):
                conclusion_has_val = True
            else:
                errors.append("Conclusion node does not have validation ancestor.")

        is_valid = (len(errors) == 0)

        return EvidenceIntegrityReport(
            is_valid=is_valid,
            total_records=len(self.records),
            orphan_records=orphans,
            broken_parent_links=broken_links,
            cycles_detected=cycles,
            duplicate_ids=dup_ids,
            has_conclusion=has_conclusion,
            conclusion_has_validation=conclusion_has_val,
            integrity_errors=errors
        )

    def to_export_dict(self) -> Dict[str, Any]:
        """Exports full ledger representation for reproducibility bundles."""
        return {
            "ledger_id": self.ledger_id,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "merkle_root": self.compute_ledger_fingerprint(),
            "total_records": len(self.records),
            "records": [r.model_dump() for r in self.records]
        }


class EvidenceIntegrityReport(BaseModel):
    """Diagnostic report evaluating cryptographic DAG integrity of an EvidenceLedger."""
    is_valid: bool
    total_records: int
    orphan_records: List[str] = Field(default_factory=list)
    broken_parent_links: List[str] = Field(default_factory=list)
    cycles_detected: List[str] = Field(default_factory=list)
    duplicate_ids: List[str] = Field(default_factory=list)
    has_conclusion: bool = False
    conclusion_has_validation: bool = False
    integrity_errors: List[str] = Field(default_factory=list)
