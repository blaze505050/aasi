"""
AASI Phase 28: Canonical Autonomous Investigation Architecture.
Represents the unified scientific investigation aggregate containing all 24 conceptual elements:
user_request, scientific_intent, assumptions, domain, objectives,
geometry, operating_conditions, governing_physics, candidate_methods,
selected_method, fidelity_level, required_data, dataset_sources,
computational_plan, execution_plan, execution_status, artifacts,
validation, uncertainty, comparisons, discrepancies, repairs,
conclusions, provenance.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.agent.scientific_state import ProvenanceState, EpistemicTier
from backend.agent.investigation_lifecycle import (
    AutonomyLevel,
    AutonomyEnvelope,
    LifecycleStage,
    InvestigationLifecycleManager,
)


class InvestigationStatus(str, Enum):
    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    RETRIEVING_DATA = "RETRIEVING_DATA"
    SELECTING_METHOD = "SELECTING_METHOD"
    STAGING_COMPUTATION = "STAGING_COMPUTATION"
    AWAITING_EXECUTION = "AWAITING_EXECUTION"
    COMPUTING = "COMPUTING"
    INGESTING = "INGESTING"
    VALIDATING = "VALIDATING"
    INVESTIGATING = "INVESTIGATING"
    SYNTHESIZING = "SYNTHESIZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


class OperatingConditions(BaseModel):
    alpha_deg: float = 4.0
    alpha_range: Optional[List[float]] = None
    reynolds: float = 3_000_000.0
    mach: float = 0.15
    temperature_k: float = 288.15
    pressure_pa: float = 101325.0
    density_kg_m3: float = 1.225
    kinematic_viscosity_m2_s: float = 1.48e-5


class SweepStatus(str, Enum):
    """Provenance state of a single angle-of-attack sweep point."""
    REQUESTED = "REQUESTED"     # User asked for this alpha
    STAGED = "STAGED"           # OpenFOAM case deck was generated
    EXECUTED = "EXECUTED"       # Solver was run externally; log exists
    VERIFIED = "VERIFIED"       # Results imported and passed verification
    PARTIAL = "PARTIAL"         # Solver ran but did not converge
    NOT_EXECUTED = "NOT_EXECUTED"  # Never sent to solver


class SweepPointRecord(BaseModel):
    """Provenance record for a single alpha point in a sweep."""
    alpha_deg: float
    status: SweepStatus = SweepStatus.REQUESTED
    job_id: Optional[str] = None
    case_hash: Optional[str] = None
    cl: Optional[float] = None
    cd: Optional[float] = None
    cm: Optional[float] = None
    archive_hash: Optional[str] = None
    verification_status: Optional[str] = None


class MethodCandidate(BaseModel):
    method_name: str
    tier: EpistemicTier
    applicable: bool
    suitability_score: float
    reason: str
    limitations: List[str] = Field(default_factory=list)


class MethodSelectionRecord(BaseModel):
    candidate_methods: List[MethodCandidate] = Field(default_factory=list)
    selected_method: EpistemicTier
    reason: str
    confidence: float
    required_evidence: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    fallback_method: Optional[EpistemicTier] = None


class NextExperimentProposal(BaseModel):
    proposal_id: str
    objective: str
    variable_to_change: str
    expected_information_gained: str
    reason: str
    dependency: str
    execution_requirements: Dict[str, Any] = Field(default_factory=dict)


class PhysicalValidationRecord(BaseModel):
    passed: bool = False
    drag_positive: bool = True
    stagnation_pressure_bounded: bool = True
    lift_slope_physical: bool = True
    residuals_converged: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class DiscrepancyHypothesis(BaseModel):
    hypothesis_id: str
    mechanism: str
    description: str
    evidence: List[str] = Field(default_factory=list)
    plausibility: float = 1.0


class DiscrepancyRecord(BaseModel):
    quantity: str
    source_a: str
    value_a: Optional[float]
    source_b: str
    value_b: Optional[float]
    absolute_difference: Optional[float] = None
    relative_difference_pct: Optional[float] = None
    hypotheses: List[DiscrepancyHypothesis] = Field(default_factory=list)
    structured_hypotheses: List[Any] = Field(default_factory=list)


class RepairRecord(BaseModel):
    attempt: int
    original_case_hash: str
    repaired_case_hash: str
    error_diagnosed: str
    parameter_modifications: Dict[str, Any] = Field(default_factory=dict)
    outcome: str


class ScientificValue(BaseModel):
    quantity: str
    value: Optional[float] = None
    units: str = "dimensionless"
    epistemic_tier: EpistemicTier
    uncertainty: Optional[float] = None
    source_ref: str
    is_live_cfd: bool = False


class Investigation(BaseModel):
    """
    Canonical Investigation Aggregate.
    Ties together the complete 24-element research lifecycle.
    """
    investigation_id: str
    user_request: str
    scientific_intent: str
    assumptions: List[str] = Field(default_factory=list)
    domain: str = "aerodynamics"
    objectives: List[str] = Field(default_factory=list)

    # Scientific Hypotheses (Milestone 4)
    hypotheses: List[Any] = Field(default_factory=list)

    # Geometry & Physics
    geometry: str
    operating_conditions: OperatingConditions
    governing_physics: str = "Incompressible Reynolds-Averaged Navier-Stokes (k-omega SST)"

    # Method & Fidelity
    candidate_methods: List[MethodCandidate] = Field(default_factory=list)
    selected_method: Optional[MethodSelectionRecord] = None
    fidelity_level: str = "MULTI_FIDELITY_COMPARISON"

    # Data & Plans
    required_data: List[str] = Field(default_factory=lambda: ["CL", "CD", "CM", "Cp"])
    dataset_sources: List[str] = Field(default_factory=list)
    computational_plan: Dict[str, Any] = Field(default_factory=dict)
    execution_plan: Dict[str, Any] = Field(default_factory=dict)
    execution_status: InvestigationStatus = InvestigationStatus.UNDERSTANDING
    lifecycle_stage: LifecycleStage = LifecycleStage.FORMULATED
    autonomy_envelope: AutonomyEnvelope = Field(default_factory=AutonomyEnvelope)

    # Execution artifacts
    job_id: Optional[str] = None
    artifacts: Dict[str, str] = Field(default_factory=dict)

    # Verification & Validation
    validation: Optional[PhysicalValidationRecord] = None
    uncertainty: Dict[str, float] = Field(default_factory=dict)

    # Multi-Fidelity Comparisons & Discrepancies
    comparisons: Dict[str, Dict[str, ScientificValue]] = Field(default_factory=dict)
    discrepancies: List[DiscrepancyRecord] = Field(default_factory=list)
    evidence_reconciliation: Optional[Dict[str, Any]] = None

    # Error recovery
    repairs: List[RepairRecord] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3

    # Conclusions & Provenance
    conclusions: List[str] = Field(default_factory=list)
    next_experiments: List[NextExperimentProposal] = Field(default_factory=list)
    candidate_experiments: List[Any] = Field(default_factory=list)
    alpha_sweep: List[float] = Field(default_factory=list)
    sweep_evaluations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    reused_memory_notes: List[str] = Field(default_factory=list)
    provenance_hash: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def update_provenance(self) -> str:
        """Compute cryptographic hash of investigation state."""
        payload = f"{self.investigation_id}:{self.user_request}:{self.geometry}:{self.execution_status.value}:{len(self.comparisons)}:{len(self.repairs)}:{len(self.next_experiments)}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.provenance_hash = digest
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return digest
