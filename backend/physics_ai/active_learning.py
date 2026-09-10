"""
AASI Active Learning 2.0 & Candidate Registry.

Provides modular acquisition strategies, candidate lifecycle management,
parameter space coverage map generation, and conversion to CFDJobSpec.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from enum import Enum
from datetime import datetime, timezone
import hashlib
import json
import os
import numpy as np
from pydantic import BaseModel, Field

from backend.multifidelity.models import FlowConditions

if TYPE_CHECKING:
    from backend.simulation.job_spec import CFDJobSpec, SolverType, ExecutionBackend



class AcquisitionStrategy(str, Enum):
    UNCERTAINTY = "UNCERTAINTY"
    OOD_BOUNDARY = "OOD_BOUNDARY"
    SPACE_COVERAGE = "SPACE_COVERAGE"
    COST_AWARE = "COST_AWARE"


class CandidateStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    GENERATED = "GENERATED"
    EXECUTED = "EXECUTED"
    INGESTED = "INGESTED"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"


class CandidateAuditEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    from_status: Optional[CandidateStatus] = None
    to_status: CandidateStatus
    actor: str = "AASI Scientific Engine"
    rationale: str = ""


class ActiveLearningCandidateRecord(BaseModel):
    candidate_id: str
    geometry: str
    flow_conditions: FlowConditions
    acquisition_strategy: AcquisitionStrategy = AcquisitionStrategy.COST_AWARE
    status: CandidateStatus = CandidateStatus.PROPOSED
    estimated_uncertainty: float = 0.5
    ood_score: float = 0.5
    coverage_gap: float = 0.5
    estimated_cost_hours: float = 0.5
    composite_score: float = 0.5
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    scientific_rationale: str = ""
    associated_job_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    audit_trail: List[CandidateAuditEntry] = Field(default_factory=list)


class ParameterCoverageMap(BaseModel):
    geometry: str
    plane: str  # "aoa_vs_mach", "aoa_vs_reynolds", "mach_vs_reynolds"
    existing_points: List[Dict[str, Any]]
    candidate_points: List[Dict[str, Any]]
    coverage_density_pct: float
    total_samples: int



class ActiveLearning2Engine:
    """
    Advanced Active Learning Engine with modular acquisition functions
    and parameter space coverage analysis.
    """

    @classmethod
    def generate_candidates(
        cls,
        geometry: str,
        existing_points: List[Dict[str, float]],
        strategy: AcquisitionStrategy = AcquisitionStrategy.COST_AWARE,
        mach_grid: Optional[List[float]] = None,
        aoa_grid: Optional[List[float]] = None,
        reynolds_grid: Optional[List[float]] = None,
        max_candidates: int = 10,
        cost_weight: float = 0.2
    ) -> List[ActiveLearningCandidateRecord]:
        """
        Explores the parameter space and ranks candidate simulation points
        based on the selected acquisition strategy.
        """
        mach_grid = mach_grid or [0.10, 0.20, 0.35, 0.50, 0.65]
        aoa_grid = aoa_grid or [-4.0, 0.0, 4.0, 8.0, 12.0, 16.0]
        reynolds_grid = reynolds_grid or [1.0e6, 3.0e6, 6.0e6]

        candidates: List[ActiveLearningCandidateRecord] = []
        cand_idx = 1

        for m in mach_grid:
            for re_val in reynolds_grid:
                for aoa in aoa_grid:
                    # Normalized distance to nearest known training point
                    min_dist = 999.0
                    for pt in existing_points:
                        pt_m = pt.get("mach", 0.15)
                        pt_a = pt.get("aoa", pt.get("aoa_deg", 0.0))
                        pt_re = pt.get("reynolds", 3.0e6)
                        # Normalize differences
                        dm = (m - pt_m) / 0.6
                        da = (aoa - pt_a) / 20.0
                        dre = (np.log10(max(re_val, 1e4)) - np.log10(max(pt_re, 1e4))) / 2.0
                        d = float(np.sqrt(dm**2 + da**2 + dre**2))
                        if d < min_dist:
                            min_dist = d

                    # Metrics computation
                    coverage_gap = min(1.0, float(min_dist * 1.5))
                    
                    # Uncertainty: base distance + physics non-linearity near stall/transonic
                    base_unc = min(1.0, float(min_dist * 1.6))
                    if aoa >= 12.0:
                        base_unc = min(1.0, base_unc * 1.45)
                    if m >= 0.50:
                        base_unc = min(1.0, base_unc * 1.35)

                    # OOD score: higher at boundary or beyond
                    ood_score = min(3.0, float(min_dist * 2.2))

                    # Compute cost estimate (higher for high Mach and high Reynolds)
                    cost_hrs = 0.2 + (m * 0.5) + (np.log10(re_val) / 10.0) * 0.4
                    cost_norm = min(1.0, cost_hrs / 1.5)

                    # Acquisition scoring
                    if strategy == AcquisitionStrategy.UNCERTAINTY:
                        score = base_unc
                    elif strategy == AcquisitionStrategy.OOD_BOUNDARY:
                        # Peak near boundary ~ 1.5 to 2.0
                        score = 1.0 - abs(ood_score - 1.8) / 2.0
                    elif strategy == AcquisitionStrategy.SPACE_COVERAGE:
                        score = coverage_gap
                    else:  # COST_AWARE
                        score = (0.45 * base_unc + 0.25 * (ood_score / 3.0) + 0.30 * coverage_gap) - (cost_weight * cost_norm)

                    score = round(max(0.01, min(1.0, float(score))), 3)

                    # Priority threshold
                    if score >= 0.65:
                        priority = "HIGH"
                        rationale = "High scientific priority: Critical under-sampled region with significant physics complexity."
                    elif score >= 0.40:
                        priority = "MEDIUM"
                        rationale = "Moderate priority: Noticeable parameter gap with moderate solver requirement."
                    else:
                        priority = "LOW"
                        rationale = "Low priority: Region already well populated or low epistemic value."

                    cond = FlowConditions(mach=m, reynolds=re_val, aoa_deg=aoa)
                    cand_id = f"AL-CAND-{geometry.replace(' ', '')}-{cand_idx:03d}"
                    cand_record = ActiveLearningCandidateRecord(
                        candidate_id=cand_id,
                        geometry=geometry,
                        flow_conditions=cond,
                        acquisition_strategy=strategy,
                        status=CandidateStatus.PROPOSED,
                        estimated_uncertainty=round(base_unc, 3),
                        ood_score=round(ood_score, 3),
                        coverage_gap=round(coverage_gap, 3),
                        estimated_cost_hours=round(cost_hrs, 2),
                        composite_score=score,
                        priority=priority,
                        scientific_rationale=rationale,
                        audit_trail=[
                            CandidateAuditEntry(
                                to_status=CandidateStatus.PROPOSED,
                                rationale="Generated by Active Learning 2.0 acquisition planner."
                            )
                        ]
                    )
                    candidates.append(cand_record)
                    cand_idx += 1

        # Sort by composite score descending
        candidates.sort(key=lambda c: c.composite_score, reverse=True)
        return candidates[:max_candidates]

    @classmethod
    def compute_coverage_map(
        cls,
        geometry: str,
        existing_points: List[Dict[str, float]],
        candidate_points: List[ActiveLearningCandidateRecord],
        plane: str = "aoa_vs_mach"
    ) -> ParameterCoverageMap:
        """
        Projects 3D parameter space onto 2D plane to visualize sampling density.
        """
        exist_proj: List[Dict[str, float]] = []
        for pt in existing_points:
            exist_proj.append({
                "x": pt.get("aoa", pt.get("aoa_deg", 0.0)) if "aoa" in plane.split("_vs_")[0] else pt.get("mach", 0.15),
                "y": pt.get("mach", 0.15) if "mach" in plane.split("_vs_")[1] else pt.get("reynolds", 3.0e6)
            })

        cand_proj: List[Dict[str, float]] = []
        for cand in candidate_points:
            x_val = cand.flow_conditions.aoa_deg if "aoa" in plane.split("_vs_")[0] else cand.flow_conditions.mach
            y_val = cand.flow_conditions.mach if "mach" in plane.split("_vs_")[1] else cand.flow_conditions.reynolds
            cand_proj.append({"x": x_val, "y": y_val, "status": cand.status.value, "priority": cand.priority})

        total = len(exist_proj) + len(cand_proj)
        # Approximate density percentage based on domain grid bins
        density = min(100.0, round((len(exist_proj) / 50.0) * 100.0, 1))

        return ParameterCoverageMap(
            geometry=geometry,
            plane=plane,
            existing_points=exist_proj,
            candidate_points=cand_proj,
            coverage_density_pct=density,
            total_samples=total
        )

    @classmethod
    def convert_to_job_spec(
        cls,
        candidate: ActiveLearningCandidateRecord,
        solver: Any = None,
        backend: Any = None
    ) -> Any:
        """Converts an approved active learning candidate into a formal CFDJobSpec."""
        from backend.simulation.job_spec import CFDJobSpec, SolverType, ExecutionBackend
        solver = solver or SolverType.OPENFOAM
        backend = backend or ExecutionBackend.USER_EXECUTED
        job_id = f"JOB-{candidate.candidate_id}"
        spec = CFDJobSpec(
            job_id=job_id,
            objective_id=f"OBJ-{candidate.geometry}",
            geometry=candidate.geometry,
            geometry_hash=hashlib.sha256(candidate.geometry.encode()).hexdigest()[:16],
            flow_conditions=candidate.flow_conditions,

            solver=solver,
            execution_backend=backend,
            scientific_priority=round(candidate.composite_score * 10.0, 1)
        )
        return spec


class ActiveLearningCandidateRegistry:
    """In-memory candidate registry with serialization support."""

    def __init__(self, persistence_path: Optional[str] = None):
        self._candidates: Dict[str, ActiveLearningCandidateRecord] = {}
        self.persistence_path = persistence_path or "data/active_learning/candidates.json"

    def register_candidate(self, candidate: ActiveLearningCandidateRecord) -> None:
        self._candidates[candidate.candidate_id] = candidate

    def get_candidate(self, candidate_id: str) -> Optional[ActiveLearningCandidateRecord]:
        return self._candidates.get(candidate_id)

    def list_candidates(
        self,
        geometry: Optional[str] = None,
        status: Optional[CandidateStatus] = None,
        priority: Optional[str] = None
    ) -> List[ActiveLearningCandidateRecord]:
        results = list(self._candidates.values())
        if geometry:
            results = [c for c in results if c.geometry.lower() == geometry.lower()]
        if status:
            results = [c for c in results if c.status == status]
        if priority:
            results = [c for c in results if c.priority.upper() == priority.upper()]
        return results

    def update_status(
        self,
        candidate_id: str,
        new_status: CandidateStatus,
        rationale: str = "",
        actor: str = "AASI User / Researcher"
    ) -> Optional[ActiveLearningCandidateRecord]:
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            return None
        
        old_status = candidate.status
        candidate.status = new_status
        candidate.audit_trail.append(
            CandidateAuditEntry(
                from_status=old_status,
                to_status=new_status,
                actor=actor,
                rationale=rationale
            )
        )
        return candidate

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
        data = [c.model_dump() for c in self._candidates.values()]
        with open(self.persistence_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        cand = ActiveLearningCandidateRecord.model_validate(item)
                        self._candidates[cand.candidate_id] = cand
            except Exception:
                pass


# Global singleton candidate registry
active_learning_registry = ActiveLearningCandidateRegistry()
