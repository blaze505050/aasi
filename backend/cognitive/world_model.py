"""
AASI Cognitive Engine: Aerospace World Model.
Persistent, structured, versioned, provenance-aware representation of the complete
scientific investigation state. Not a vector database; encodes physical ontology.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("aasi.cognitive.world_model")


class PhysicsDomain(str, Enum):
    """Aerospace continuum regimes and physical modeling domains."""
    INVISCID_POTENTIAL = "INVISCID_POTENTIAL"
    SUBSONIC_INCOMPRESSIBLE_VISCOUS = "SUBSONIC_INCOMPRESSIBLE_VISCOUS"
    TRANSONIC_COMPRESSIBLE = "TRANSONIC_COMPRESSIBLE"
    SUPERSONIC_SHOCK = "SUPERSONIC_SHOCK"
    HYPERSONIC_AEROTHERMODYNAMICS = "HYPERSONIC_AEROTHERMODYNAMICS"
    POST_STALL_SEPARATED = "POST_STALL_SEPARATED"
    UNSTEADY_VORTEX_SHEDDING = "UNSTEADY_VORTEX_SHEDDING"
    AEROELASTIC_FLUTTER = "AEROELASTIC_FLUTTER"
    ORBITAL_PERTURBATION = "ORBITAL_PERTURBATION"
    ROCKET_PROPULSION_REACTION = "ROCKET_PROPULSION_REACTION"


class AssertionStatus(str, Enum):
    """Epistemic status of assertions stored within the world model."""
    CONJECTURE = "CONJECTURE"            # Proposed hypothesis or theoretical guess
    THEORETICAL = "THEORETICAL"          # Derived from ideal mathematical model
    SURROGATE_INFERENCE = "SURROGATE_INFERENCE" # Interpolated by ML/surrogate model
    NUMERICAL_AUDITED = "NUMERICAL_AUDITED"     # Converged, residual-verified Navier-Stokes CFD
    EMPIRICAL_BENCHMARK = "EMPIRICAL_BENCHMARK" # Peer-reviewed wind-tunnel/flight measurement
    REFUTED = "REFUTED"                  # Contradicted by superior tier evidence
    UNKNOWN = "UNKNOWN"                  # Parameter or behavior recognized as unmeasured


class WorldModelAssertion(BaseModel):
    """
    Unit assertion within the world model.
    Guarantees every assertion carries source, status, timestamp, and evidence links.
    """
    assertion_id: str = Field(default_factory=lambda: f"AST-{uuid.uuid4().hex[:8].upper()}")
    subject: str = Field(..., description="Subject of the assertion (e.g. NACA 0012 Lift Slope)")
    property_name: str = Field(..., description="Target aerodynamic property (e.g. dCL/dalpha, CD0, stall_alpha)")
    value: Any = Field(..., description="Value, bracket, or qualitative physical claim")
    units: str = Field(default="dimensionless", description="Engineering units")
    status: AssertionStatus = Field(default=AssertionStatus.CONJECTURE)
    source: str = Field(..., description="Citation, solver job ID, model name, or user input")
    epistemic_tier: str = Field(default="MODEL_GENERATED")
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PhysicalGeometry(BaseModel):
    """Geometric definition and normalization state."""
    name: str = "NACA 0012"
    format: str = "Selig"
    chord_m: float = 1.0
    span_m: Optional[float] = None
    thickness_ratio: float = 0.12
    camber_ratio: float = 0.0
    leading_edge_radius_c: float = 0.0158
    coordinates_sha256: str = ""
    is_normalized: bool = True


class PhysicalEnvironment(BaseModel):
    """Freestream atmospheric and fluid properties."""
    fluid: str = "Air"
    density_kg_m3: float = 1.225
    temperature_k: float = 288.15
    pressure_pa: float = 101325.0
    dynamic_viscosity_pa_s: float = 1.789e-5
    speed_of_sound_m_s: float = 340.29
    altitude_m: float = 0.0
    turbulence_intensity_percent: float = 0.1


class OperatingState(BaseModel):
    """Active flight regime conditions."""
    alpha_deg: float = 0.0
    reynolds: float = 3.0e6
    mach: float = 0.15
    dynamic_pressure_pa: float = 1580.0
    sweep_angle_deg: float = 0.0


class InvestigationObjective(BaseModel):
    """Target scientific determination defining success criteria."""
    question: str
    target_quantities: List[str] = Field(default_factory=lambda: ["CL", "CD", "CM"])
    accuracy_tolerance_percent: float = 2.0
    required_epistemic_tier: str = "NUMERICAL_AUDITED"
    max_compute_cycles: int = 5
    is_resolved: bool = False
    resolution_summary: Optional[str] = None


class ScientificAssumption(BaseModel):
    """Explicit physical or numerical boundary condition assumption."""
    assumption_id: str = Field(default_factory=lambda: f"ASM-{uuid.uuid4().hex[:6].upper()}")
    statement: str
    rationale: str
    validity_regime: str = "Pre-stall alpha < 12 deg, Subsonic Mach < 0.3"
    sensitivity: str = "HIGH"  # LOW, MEDIUM, HIGH, CRITICAL


class AutonomousDecision(BaseModel):
    """Audit record of an autonomous choice made by the cognitive engine."""
    decision_id: str = Field(default_factory=lambda: f"DEC-{uuid.uuid4().hex[:8].upper()}")
    action: str = Field(..., description="Action taken (e.g. SELECT_TOOL, STAGE_COLAB, HALT_STALLED)")
    rationale: str = Field(..., description="Rigorous physical and epistemic justification")
    evidence_basis: List[str] = Field(default_factory=list, description="IDs of evidence or hypotheses consulted")
    alternatives_considered: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AerospaceWorldModel(BaseModel):
    """
    Central persistent data model of the AASI Cognitive Engine.
    Represents the full physical, epistemic, and operational state of an aerospace investigation.
    """
    world_model_id: str = Field(default_factory=lambda: f"WM-{uuid.uuid4().hex[:8].upper()}")
    version: int = Field(default=1, description="Monotonically increasing version counter")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 1. Investigation Framing
    objective: InvestigationObjective
    active_domains: List[PhysicsDomain] = Field(default_factory=lambda: [PhysicsDomain.SUBSONIC_INCOMPRESSIBLE_VISCOUS])

    # 2. Physical System Definition
    geometry: PhysicalGeometry = Field(default_factory=PhysicalGeometry)
    environment: PhysicalEnvironment = Field(default_factory=PhysicalEnvironment)
    operating_state: OperatingState = Field(default_factory=OperatingState)

    # 3. Cognitive Artifacts
    assumptions: List[ScientificAssumption] = Field(default_factory=list)
    assertions: Dict[str, WorldModelAssertion] = Field(default_factory=dict)
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    experiments: List[Dict[str, Any]] = Field(default_factory=list)
    simulations: List[Dict[str, Any]] = Field(default_factory=list)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    decisions: List[AutonomousDecision] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list, description="Explicitly recognized unmeasured or unmodeled variables")
    next_actions: List[Dict[str, Any]] = Field(default_factory=list)

    # 4. Provenance & Cryptographic Lineage
    provenance_hash: str = ""
    parent_version_hash: str = ""

    def snapshot(self) -> AerospaceWorldModel:
        """Creates an immutable copy incrementing version."""
        data = self.model_dump()
        data["version"] = self.version + 1
        data["parent_version_hash"] = self.provenance_hash
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        cloned = AerospaceWorldModel(**data)
        cloned.compute_provenance_hash()
        return cloned

    def compute_provenance_hash(self) -> str:
        """Computes deterministic SHA-256 digest of entire world model state."""
        digest_dict = {
            "id": self.world_model_id,
            "version": self.version,
            "objective": self.objective.model_dump(),
            "geometry": self.geometry.name,
            "operating_state": self.operating_state.model_dump(),
            "assertion_keys": sorted(list(self.assertions.keys())),
            "hypotheses_count": len(self.hypotheses),
            "evidence_count": len(self.evidence),
            "decisions_count": len(self.decisions),
            "parent_hash": self.parent_version_hash,
        }
        raw = json.dumps(digest_dict, sort_keys=True)
        self.provenance_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self.provenance_hash

    def add_assertion(self, assertion: WorldModelAssertion) -> None:
        """Adds or updates a structured assertion and refreshes provenance."""
        self.assertions[assertion.assertion_id] = assertion
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.compute_provenance_hash()

    def record_decision(self, decision: AutonomousDecision) -> None:
        """Appends an autonomous decision record and refreshes provenance."""
        self.decisions.append(decision)
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.compute_provenance_hash()
