"""
AASI Milestone 7: Scientific Memory Engine.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Section 9 of Architecture & Prompt 8:
- Stores verified results, failure investigations, assumptions, environments, and provenance.
- Provides multi-dimensional similarity retrieval over geometry, Re, Mach, AoA, solver, and target quantity.
- Enforces strict epistemic trust: Verified empirical/CFD evidence strictly holds higher trust
  and precedence over model-generated text or unverified claims.
- Preserves negative evidence (failed investigations remain searchable with failure diagnosis).
"""

from __future__ import annotations

import difflib
import hashlib
import json
import logging
import math
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import AliasChoices, BaseModel, Field, model_validator

logger = logging.getLogger("aasi.science.memory")


class MemoryEntryType(str, Enum):
    """Classification of scientific knowledge retained in memory."""
    VERIFIED_RESULT = "VERIFIED_RESULT"              # Audited CFD or experimental benchmark
    FAILED_INVESTIGATION = "FAILED_INVESTIGATION"    # Divergence, mesh crash, or physical violation (negative evidence)
    SCIENTIFIC_ASSUMPTION = "SCIENTIFIC_ASSUMPTION"  # Physical assumption (e.g. trip-wire location, 2D flow)
    ENVIRONMENT_CAPABILITY = "ENVIRONMENT_CAPABILITY"# Local runner/hardware environment fingerprint
    RECONCILED_EVIDENCE = "RECONCILED_EVIDENCE"      # Multi-fidelity discrepancy reconciliation report


class EpistemicTrustTier(str, Enum):
    """
    Epistemic trust ranking.
    Verified empirical and audited CFD results strictly hold higher trust than model-generated text.
    """
    VERIFIED_CFD = "VERIFIED_CFD"                    # Highest trust: passed 10-point audit, residuals < 1e-4
    REFERENCE_DATA = "REFERENCE_DATA"                # High trust: peer-reviewed published experimental data
    EXPERIMENTAL = "EXPERIMENTAL"                    # High trust: physical wind tunnel or flight measurement
    SURROGATE = "SURROGATE"                          # Moderate trust: neural operator / ML regression
    ANALYTICAL = "ANALYTICAL"                        # Moderate trust: theoretical potential derivation
    MODEL_GENERATED = "MODEL_GENERATED"              # Low trust: LLM generative reasoning claim
    UNVERIFIED_ASSERTION = "UNVERIFIED_ASSERTION"    # Lowest trust: unverified user assertion


def get_trust_weight(tier: EpistemicTrustTier) -> float:
    """
    Returns numeric trust coefficient.
    Verified empirical evidence strictly outranks model-generated text.
    """
    weights = {
        EpistemicTrustTier.VERIFIED_CFD: 1.00,
        EpistemicTrustTier.REFERENCE_DATA: 0.95,
        EpistemicTrustTier.EXPERIMENTAL: 0.95,
        EpistemicTrustTier.SURROGATE: 0.60,
        EpistemicTrustTier.ANALYTICAL: 0.50,
        EpistemicTrustTier.MODEL_GENERATED: 0.20,
        EpistemicTrustTier.UNVERIFIED_ASSERTION: 0.10,
    }
    return weights.get(tier, 0.10)


class ScientificMemoryEntry(BaseModel):
    """
    Unit record of scientific knowledge stored in AASI memory.
    """
    memory_id: str = Field(..., description="Unique memory identifier (e.g. MEM-JOB-1234)")
    entry_type: MemoryEntryType = Field(..., description="Type of knowledge retained")
    trust_tier: EpistemicTrustTier = Field(..., description="Epistemic trust tier")
    geometry: str = Field(..., description="Airfoil or aerodynamic body identifier (e.g. NACA 0012)")
    operating_conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Operating conditions: alpha_deg, reynolds, mach",
    )
    solver: Optional[str] = Field(default="simpleFoam", description="Computational solver or experimental facility")
    target_quantities: List[str] = Field(
        default_factory=list,
        description="Quantities evaluated (e.g. ['CL', 'CD', 'CM'])",
    )
    results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Empirical or numerical values (CL, CD, CM, Cp_min, etc.)",
    )
    failures: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Negative evidence: failure modes, error logs, and instability diagnoses",
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Documented scientific assumptions for this case",
    )
    environment: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution environment: OS, CPU, OpenFOAM version, RAM",
    )
    provenance_hash: str = Field(default="", description="Cryptographic SHA-256 state digest")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def compute_provenance_hash(self) -> str:
        """Computes deterministic cryptographic hash of this memory record."""
        payload = {
            "memory_id": self.memory_id,
            "entry_type": self.entry_type.value,
            "trust_tier": self.trust_tier.value,
            "geometry": self.geometry.strip().upper(),
            "conditions": self.operating_conditions,
            "solver": self.solver or "",
            "results": self.results,
            "failures": self.failures,
            "assumptions": sorted(self.assumptions),
        }
        raw = json.dumps(payload, sort_keys=True)
        self.provenance_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self.provenance_hash

    def to_dict(self) -> Dict[str, Any]:
        if not self.provenance_hash:
            self.compute_provenance_hash()
        return {
            "memory_id": self.memory_id,
            "entry_type": self.entry_type.value,
            "trust_tier": self.trust_tier.value,
            "trust_weight": get_trust_weight(self.trust_tier),
            "geometry": self.geometry,
            "operating_conditions": self.operating_conditions,
            "solver": self.solver,
            "target_quantities": self.target_quantities,
            "results": self.results,
            "failures": self.failures,
            "assumptions": self.assumptions,
            "environment": self.environment,
            "provenance_hash": self.provenance_hash,
            "timestamp": self.timestamp,
        }


class MemoryQuery(BaseModel):
    """Query specification for multi-dimensional similarity retrieval."""
    geometry: Optional[str] = Field(default=None, json_schema_extra={"example": "NACA 0012"})
    alpha_deg: Optional[float] = Field(default=None, json_schema_extra={"example": 4.0})
    reynolds: Optional[float] = Field(default=None, json_schema_extra={"example": 3.0e6})
    mach: Optional[float] = Field(default=None, json_schema_extra={"example": 0.15})
    solver: Optional[str] = Field(default=None, json_schema_extra={"example": "simpleFoam"})
    target_quantity: Optional[str] = Field(default=None, json_schema_extra={"example": "CL"})
    entry_type: Optional[MemoryEntryType] = Field(default=None)
    min_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    apply_trust_weight: bool = Field(
        default=True,
        description="If True, ranks by effective score (similarity * trust_weight). Verified evidence takes priority.",
    )
    limit: int = Field(default=10, ge=1, le=100)


class MemorySearchResult(BaseModel):
    """Result of a scientific memory similarity retrieval query."""
    entry: ScientificMemoryEntry
    similarity_score: float = Field(description="Raw multi-criteria physical similarity [0.0, 1.0]")
    trust_weight: float = Field(description="Epistemic trust tier coefficient [0.1, 1.0]")
    effective_score: float = Field(description="Composite score: similarity_score * trust_weight")
    dimension_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Decomposition of similarity across geometry, Re, Mach, alpha, and quantities",
    )


class ScientificMemoryEngine:
    """
    Maintains and queries AASI's long-term scientific memory.
    Features:
    - Multi-dimensional aerodynamic similarity retrieval.
    - Strict epistemic trust weighting (verified CFD outranks model-generated claims).
    - Failure memory preservation (negative evidence search).
    - Automated hydration from empirical_ledger.json.
    - Atomic persistent storage in data/scientific_memory.json.
    """

    def __init__(self, memory_file: Optional[Path] = None, ledger_file: Optional[Path] = None):
        workspace_root = Path(__file__).resolve().parent.parent.parent
        self.memory_file = memory_file or (workspace_root / "data" / "scientific_memory.json")
        self.ledger_file = ledger_file or (workspace_root / "data" / "empirical_ledger.json")
        self._entries: Dict[str, ScientificMemoryEntry] = {}
        self._load_or_hydrate()

    def _load_or_hydrate(self) -> None:
        """Loads memory from disk or hydrates from empirical_ledger.json if empty."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("entries", []):
                        entry = ScientificMemoryEntry(**item)
                        self._entries[entry.memory_id] = entry
                logger.info(f"Loaded {len(self._entries)} scientific memory entries from {self.memory_file}")
            except Exception as e:
                logger.warning(f"Failed to load memory from {self.memory_file}: {e}; re-hydrating from ledger.")
                self._entries.clear()

        # If entries is still empty, hydrate from empirical_ledger.json
        if not self._entries and self.ledger_file.exists():
            self._hydrate_from_ledger()

    def _hydrate_from_ledger(self) -> None:
        """Imports certified runs and failures from empirical_ledger.json."""
        try:
            with open(self.ledger_file, "r", encoding="utf-8") as f:
                ledger = json.load(f)
            
            count = 0
            for job_id, run in ledger.items():
                v_status = run.get("verification_status", "UNKNOWN")
                geom = run.get("geometry_identity", "UNKNOWN_GEOM")
                cond = run.get("executed_parameters") or run.get("conditions", {})
                receipt = run.get("result_receipt") or {}
                diagnosis = run.get("diagnosis")
                
                if v_status == "VERIFIED":
                    entry_type = MemoryEntryType.VERIFIED_RESULT
                    trust_tier = EpistemicTrustTier.VERIFIED_CFD
                    failures = []
                else:
                    entry_type = MemoryEntryType.FAILED_INVESTIGATION
                    trust_tier = EpistemicTrustTier.VERIFIED_CFD  # The execution attempt is empirical/verified failure
                    failures = [{"diagnosis": diagnosis or "UNSPECIFIED_FAILURE", "job_id": job_id}]

                target_quantities = sorted(list(receipt.keys())) if receipt else ["CL", "CD", "CM"]
                
                entry = ScientificMemoryEntry(
                    memory_id=f"MEM-{job_id}",
                    entry_type=entry_type,
                    trust_tier=trust_tier,
                    geometry=geom,
                    operating_conditions=cond,
                    solver="simpleFoam",
                    target_quantities=target_quantities,
                    results=receipt,
                    failures=failures,
                    assumptions=[
                        "Incompressible Reynolds-Averaged Navier-Stokes (k-omega SST)",
                        "Fully turbulent boundary layer",
                    ],
                    environment={
                        "platform": "OpenFOAM",
                        "case_hash": run.get("case_hash"),
                        "archive_hash": run.get("archive_hash"),
                    },
                )
                entry.compute_provenance_hash()
                self._entries[entry.memory_id] = entry
                count += 1
            
            logger.info(f"Successfully hydrated {count} entries into scientific memory from ledger.")
            self._save()
        except Exception as e:
            logger.error(f"Failed hydrating from ledger: {e}")

    def _save(self) -> None:
        """Persists scientific memory to disk atomically."""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.memory_file.with_suffix(".tmp")
        payload = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_entries": len(self._entries),
            "entries": [e.model_dump() for e in self._entries.values()],
        }
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(temp_file, self.memory_file)

    def add_entry(self, entry: ScientificMemoryEntry) -> ScientificMemoryEntry:
        """Stores a new memory entry with sealed cryptographic hash."""
        entry.compute_provenance_hash()
        self._entries[entry.memory_id] = entry
        self._save()

        # Synchronize with consolidated EpistemicMemoryKernel
        try:
            from backend.science.epistemic_kernel import epistemic_kernel, EpistemicRecord, EpistemicRecordType, EpistemicTrustTier
            rec_type = EpistemicRecordType.VERIFIED_RESULT if entry.entry_type == MemoryEntryType.VERIFIED_RESULT else EpistemicRecordType.FAILED_INVESTIGATION
            ep_rec = EpistemicRecord(
                record_id=entry.memory_id,
                record_type=rec_type,
                trust_tier=EpistemicTrustTier(entry.trust_tier.value),
                title=f"Record {entry.memory_id} ({entry.geometry})",
                geometry=entry.geometry,
                operating_conditions=entry.operating_conditions,
                solver=entry.solver,
                target_quantities=entry.target_quantities,
                results=entry.results,
                failures=entry.failures,
                assumptions=entry.assumptions,
                environment=entry.environment,
            )
            epistemic_kernel.store_record(ep_rec)
        except Exception:
            pass

        return entry

    def get_entry(self, memory_id: str) -> Optional[ScientificMemoryEntry]:
        """Retrieves a specific memory entry by ID."""
        return self._entries.get(memory_id)

    def list_entries(self, entry_type: Optional[MemoryEntryType] = None) -> List[ScientificMemoryEntry]:
        """Lists stored memory entries, optionally filtered by entry_type."""
        if entry_type:
            return [e for e in self._entries.values() if e.entry_type == entry_type]
        return list(self._entries.values())

    def get_failures(self, geometry: Optional[str] = None) -> List[ScientificMemoryEntry]:
        """
        Retrieves negative evidence records (failed investigations).
        Essential for avoiding known failure modes in experiment planning.
        """
        failures = [e for e in self._entries.values() if e.entry_type == MemoryEntryType.FAILED_INVESTIGATION]
        if geometry:
            geom_clean = geometry.strip().upper()
            failures = [f for f in failures if f.geometry.strip().upper() == geom_clean]
        return failures

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics on stored memory corpus."""
        by_type = {}
        by_trust = {}
        for e in self._entries.values():
            by_type[e.entry_type.value] = by_type.get(e.entry_type.value, 0) + 1
            by_trust[e.trust_tier.value] = by_trust.get(e.trust_tier.value, 0) + 1
        return {
            "total_entries": len(self._entries),
            "by_entry_type": by_type,
            "by_trust_tier": by_trust,
            "verified_results_count": by_type.get(MemoryEntryType.VERIFIED_RESULT.value, 0),
            "failed_investigations_count": by_type.get(MemoryEntryType.FAILED_INVESTIGATION.value, 0),
        }

    # -----------------------------------------------------------------------
    # Multi-Dimensional Similarity Scoring Engine
    # -----------------------------------------------------------------------

    def compute_similarity(self, query: MemoryQuery, entry: ScientificMemoryEntry) -> tuple[float, Dict[str, float]]:
        """
        Computes transparent multi-dimensional similarity score between query and entry.
        Weights:
        - Geometry: 0.30
        - Reynolds (log10): 0.25
        - Mach: 0.15
        - Angle of Attack: 0.15
        - Target Quantities: 0.15
        """
        dim_scores: Dict[str, float] = {}

        # 1. Geometry similarity (0.30)
        if query.geometry:
            q_geom = query.geometry.strip().upper()
            e_geom = entry.geometry.strip().upper()
            if q_geom == e_geom:
                s_geom = 1.0
            elif q_geom[:7] == e_geom[:7]:  # same series (e.g. NACA 00 vs NACA 00)
                s_geom = 0.85
            elif q_geom[:4] == e_geom[:4]:  # same family (NACA vs NACA)
                ratio = difflib.SequenceMatcher(None, q_geom, e_geom).ratio()
                s_geom = max(0.5, ratio)
            else:
                s_geom = difflib.SequenceMatcher(None, q_geom, e_geom).ratio() * 0.4
        else:
            s_geom = 1.0
        dim_scores["geometry"] = round(s_geom, 3)

        # 2. Reynolds number similarity in log10 space (0.25)
        e_cond = entry.operating_conditions
        e_re = float(e_cond.get("reynolds", 3.0e6))
        if query.reynolds and query.reynolds > 0 and e_re > 0:
            log_q = math.log10(query.reynolds)
            log_e = math.log10(e_re)
            diff_log = abs(log_q - log_e)
            # Full divergence if > 2 orders of magnitude apart
            s_re = max(0.0, 1.0 - (diff_log / 2.0))
        else:
            s_re = 1.0
        dim_scores["reynolds"] = round(s_re, 3)

        # 3. Mach number similarity (0.15)
        e_mach = float(e_cond.get("mach", 0.15))
        if query.mach is not None:
            diff_m = abs(query.mach - e_mach)
            # Scaling: 0.40 Mach difference yields 0 similarity
            s_mach = max(0.0, 1.0 - (diff_m / 0.40))
        else:
            s_mach = 1.0
        dim_scores["mach"] = round(s_mach, 3)

        # 4. Angle of Attack similarity (0.15)
        e_alpha = float(e_cond.get("alpha_deg", 0.0))
        if query.alpha_deg is not None:
            diff_a = abs(query.alpha_deg - e_alpha)
            # Scaling: 10 degrees difference yields 0 similarity
            s_alpha = max(0.0, 1.0 - (diff_a / 10.0))
        else:
            s_alpha = 1.0
        dim_scores["alpha"] = round(s_alpha, 3)

        # 5. Target Quantity similarity (0.15)
        if query.target_quantity:
            t_clean = query.target_quantity.strip().upper()
            quantities = {q.upper() for q in entry.target_quantities}
            if entry.results:
                quantities.update({k.upper() for k in entry.results.keys()})
            s_quant = 1.0 if t_clean in quantities else 0.0
        else:
            s_quant = 1.0
        dim_scores["target_quantity"] = round(s_quant, 3)

        # Weighted composite score
        composite = (
            0.30 * s_geom +
            0.25 * s_re +
            0.15 * s_mach +
            0.15 * s_alpha +
            0.15 * s_quant
        )
        composite = max(0.0, min(1.0, round(composite, 4)))
        return composite, dim_scores

    def search(self, query: MemoryQuery) -> List[MemorySearchResult]:
        """
        Searches memory using multi-dimensional similarity and epistemic trust ordering.
        Verified evidence strictly prioritizes over model-generated text.
        """
        results: List[MemorySearchResult] = []

        for entry in self._entries.values():
            # Filter by entry_type if specified
            if query.entry_type and entry.entry_type != query.entry_type:
                continue

            # Filter by solver if specified
            if query.solver and entry.solver:
                if query.solver.strip().lower() != entry.solver.strip().lower():
                    continue

            sim_score, dim_scores = self.compute_similarity(query, entry)

            if sim_score < query.min_similarity:
                continue

            trust_weight = get_trust_weight(entry.trust_tier)
            effective_score = round(sim_score * trust_weight if query.apply_trust_weight else sim_score, 4)

            results.append(
                MemorySearchResult(
                    entry=entry,
                    similarity_score=sim_score,
                    trust_weight=trust_weight,
                    effective_score=effective_score,
                    dimension_scores=dim_scores,
                )
            )

        # Sort: primary effective_score descending, secondary similarity_score descending
        results.sort(key=lambda r: (r.effective_score, r.similarity_score), reverse=True)
        return results[:query.limit]


# Global singleton instance
scientific_memory = ScientificMemoryEngine()
