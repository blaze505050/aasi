"""
AASI Milestone 4: Scientific Hypothesis Engine.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Structured scientific hypotheses containing statement, evidence basis, assumptions,
prediction, candidate test, and status.
HYPOTHESES MUST NEVER BE REPRESENTED OR DISPLAYED AS ESTABLISHED FACTS.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("aasi.science.hypotheses")


class HypothesisStatus(str, Enum):
    """Epistemic lifecycle status of a scientific hypothesis."""
    PROPOSED = "PROPOSED"          # Formulated; awaiting experimental test
    TESTING = "TESTING"            # Candidate experiment staged or actively executing
    SUPPORTED = "SUPPORTED"        # Verified results match quantifiable prediction
    REFUTED = "REFUTED"            # Verified results contradict prediction
    INCONCLUSIVE = "INCONCLUSIVE"  # Results ambiguous, unconverged, or within noise threshold


class ScientificHypothesis(BaseModel):
    """
    Structured scientific hypothesis object.
    Complies strictly with Section 5 of 04_SCIENTIFIC_BRAIN.md and Milestone 4.
    Every hypothesis is fundamentally a testable conjecture, NEVER an established fact.
    """
    hypothesis_id: str = Field(default_factory=lambda: f"HYP-{uuid.uuid4().hex[:8].upper()}")
    title: str = Field(..., description="Concise human-readable title of the hypothesis")
    statement: str = Field(..., description="Physical causal claim (e.g. Boundary-layer separation causes drag rise)")
    evidence_basis: List[str] = Field(default_factory=list, description="Prior observations, literature, or data supporting the formulation")
    assumptions: List[str] = Field(default_factory=list, description="Underlying physical/numerical boundary conditions and regime limits")
    prediction: str = Field(..., description="Concrete, quantifiable, falsifiable outcome expected if hypothesis holds")
    candidate_test: str = Field(..., description="Specific experiment or simulation designed to test or falsify the hypothesis")
    status: HypothesisStatus = Field(default=HypothesisStatus.PROPOSED, description="Current epistemic evaluation status")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score [0.0, 1.0]")
    domain: str = Field(default="aerodynamics", description="Scientific domain (e.g. aerodynamics, fluid_mechanics)")
    geometry_id: Optional[str] = Field(default=None, description="Associated geometry if specific")

    # Anti-Fabrication & Epistemic Safeguards (IMMUTABLE)
    is_established_fact: bool = Field(
        default=False,
        description="Hypotheses are conjectures and can NEVER be declared established facts.",
    )
    epistemic_warning: str = Field(
        default=(
            "SCIENTIFIC HYPOTHESIS: This statement represents a testable conjecture and must "
            "NEVER be treated as an established physical fact without verified empirical proof."
        ),
        description="Mandatory epistemic disclaimer displayed with all hypothesis representations.",
    )

    # Provenance and Test Linkage
    provenance_hash: str = Field(default="", description="Cryptographic SHA-256 digest of hypothesis content")
    test_evidence: Dict[str, Any] = Field(default_factory=dict, description="Artifacts, job IDs, and measurements from candidate test")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("is_established_fact")
    @classmethod
    def enforce_never_fact(cls, v: bool) -> bool:
        if v is True:
            raise ValueError(
                "CRITICAL EPISTEMIC VIOLATION: A hypothesis can never be set as an established fact! "
                "Even supported hypotheses remain empirical conjectures subject to regime boundaries."
            )
        return False

    def compute_provenance_hash(self) -> str:
        """Computes deterministic SHA-256 hash sealing statement, assumptions, prediction, and test."""
        payload = {
            "hypothesis_id": self.hypothesis_id,
            "statement": self.statement.strip(),
            "evidence_basis": sorted(self.evidence_basis),
            "assumptions": sorted(self.assumptions),
            "prediction": self.prediction.strip(),
            "candidate_test": self.candidate_test.strip(),
            "domain": self.domain,
        }
        raw = json.dumps(payload, sort_keys=True)
        self.provenance_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self.provenance_hash

    def to_presentation_dict(self) -> Dict[str, Any]:
        """
        Formats hypothesis for UI presentation or API output.
        Guarantees that the hypothesis is clearly demarcated as a conjecture with explicit warnings.
        """
        return {
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "statement": self.statement,
            "evidence_basis": self.evidence_basis,
            "assumptions": self.assumptions,
            "prediction": self.prediction,
            "candidate_test": self.candidate_test,
            "status": self.status.value,
            "confidence": self.confidence,
            "domain": self.domain,
            "geometry_id": self.geometry_id,
            "is_established_fact": False,
            "epistemic_warning": self.epistemic_warning,
            "provenance_hash": self.provenance_hash,
            "test_evidence": self.test_evidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class HypothesisEngine:
    """
    Manages formulation, evaluation, persistence, and discrepancy analysis of scientific hypotheses.
    Enforces fail-closed validation and anti-fabrication standards.
    """

    REGISTRY_DIR = Path("data/hypotheses")

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path(".")
        self.storage_dir = self.workspace_root / self.REGISTRY_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, ScientificHypothesis] = {}
        self._load_all()

    def formulate(
        self,
        title: str,
        statement: str,
        evidence_basis: List[str],
        assumptions: List[str],
        prediction: str,
        candidate_test: str,
        domain: str = "aerodynamics",
        geometry_id: Optional[str] = None,
        confidence: float = 0.8,
        hypothesis_id: Optional[str] = None,
    ) -> ScientificHypothesis:
        """
        Formulates and registers a new structured scientific hypothesis.
        Rejects empty or non-falsifiable submissions.
        """
        if not title or not title.strip():
            raise ValueError("Hypothesis title cannot be empty.")
        if not statement or not statement.strip():
            raise ValueError("Hypothesis statement cannot be empty.")
        if not prediction or not prediction.strip():
            raise ValueError("Hypothesis prediction cannot be empty; every hypothesis must be quantifiable and falsifiable.")
        if not candidate_test or not candidate_test.strip():
            raise ValueError("Hypothesis candidate_test cannot be empty; a concrete validating experiment must be defined.")

        hid = hypothesis_id or f"HYP-{uuid.uuid4().hex[:8].upper()}"
        hyp = ScientificHypothesis(
            hypothesis_id=hid,
            title=title.strip(),
            statement=statement.strip(),
            evidence_basis=[e.strip() for e in evidence_basis if e.strip()],
            assumptions=[a.strip() for a in assumptions if a.strip()],
            prediction=prediction.strip(),
            candidate_test=candidate_test.strip(),
            domain=domain.strip().lower(),
            geometry_id=geometry_id.strip() if geometry_id else None,
            confidence=confidence,
            status=HypothesisStatus.PROPOSED,
        )
        hyp.compute_provenance_hash()
        self.save_hypothesis(hyp)
        return hyp

    def save_hypothesis(self, hypothesis: ScientificHypothesis) -> None:
        """Persists hypothesis to disk and updates in-memory registry."""
        hypothesis.updated_at = datetime.now(timezone.utc).isoformat()
        if not hypothesis.provenance_hash:
            hypothesis.compute_provenance_hash()

        self._memory_cache[hypothesis.hypothesis_id] = hypothesis
        file_path = self.storage_dir / f"{hypothesis.hypothesis_id}.json"
        file_path.write_text(hypothesis.model_dump_json(indent=2), encoding="utf-8")

    def get_hypothesis(self, hypothesis_id: str) -> Optional[ScientificHypothesis]:
        """Retrieves a hypothesis by ID."""
        if hypothesis_id in self._memory_cache:
            return self._memory_cache[hypothesis_id]

        file_path = self.storage_dir / f"{hypothesis_id}.json"
        if file_path.exists():
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                hyp = ScientificHypothesis(**data)
                self._memory_cache[hypothesis_id] = hyp
                return hyp
            except Exception as e:
                logger.error("Failed loading hypothesis %s: %s", hypothesis_id, e)
        return None

    def list_hypotheses(
        self,
        status: Optional[HypothesisStatus] = None,
        domain: Optional[str] = None,
        geometry_id: Optional[str] = None,
    ) -> List[ScientificHypothesis]:
        """Lists registered hypotheses filtered by criteria."""
        results = list(self._memory_cache.values())
        if status:
            results = [h for h in results if h.status == status]
        if domain:
            results = [h for h in results if h.domain.lower() == domain.lower()]
        if geometry_id:
            results = [h for h in results if h.geometry_id == geometry_id]
        return sorted(results, key=lambda h: h.created_at, reverse=True)

    def update_status(
        self,
        hypothesis_id: str,
        new_status: HypothesisStatus,
        evidence_summary: Optional[str] = None,
        test_job_id: Optional[str] = None,
        measured_values: Optional[Dict[str, Any]] = None,
    ) -> ScientificHypothesis:
        """
        Transitions the epistemic status of a hypothesis with recorded evidence.
        """
        hyp = self.get_hypothesis(hypothesis_id)
        if not hyp:
            raise KeyError(f"Hypothesis '{hypothesis_id}' not found.")

        hyp.status = new_status
        if test_job_id:
            hyp.test_evidence["job_id"] = test_job_id
        if evidence_summary:
            hyp.test_evidence["evaluation_summary"] = evidence_summary
        if measured_values:
            hyp.test_evidence["measured_values"] = measured_values
        hyp.test_evidence["evaluated_at"] = datetime.now(timezone.utc).isoformat()

        self.save_hypothesis(hyp)
        return hyp

    def generate_for_discrepancy(
        self,
        quantity: str,
        geometry: str,
        alpha_deg: float,
        reynolds: float,
        mach: float,
        src_a: str,
        val_a: float,
        src_b: str,
        val_b: float,
        abs_diff: float,
    ) -> List[ScientificHypothesis]:
        """
        Synthesizes physics-grounded testable hypotheses when multiple sources disagree.
        Outputs complete hypotheses with statement, evidence, assumptions, prediction, candidate test, status.
        """
        hypotheses: List[ScientificHypothesis] = []
        q_upper = quantity.upper()
        sources = {src_a.upper(), src_b.upper()}

        # 1. Inviscid Analytical vs Viscous CFD / Wind Tunnel
        if "ANALYTICAL" in sources:
            if q_upper == "CD":
                hypotheses.append(
                    self.formulate(
                        title="Viscous Boundary Layer & Form Drag Deficit",
                        statement=(
                            f"Analytical thin-airfoil theory for {geometry} neglects viscous boundary-layer "
                            f"displacement thickness and skin friction, causing an under-prediction of drag compared to {src_a if src_b == 'ANALYTICAL' else src_b}."
                        ),
                        evidence_basis=[
                            "Potential flow d'Alembert's paradox dictates zero drag in ideal inviscid flow.",
                            f"Observed drag discrepancy: Delta={abs_diff:.4f} between {src_a}={val_a} and {src_b}={val_b}.",
                            f"Airfoil {geometry} operates in viscous sublayer regime at Re={reynolds:.1e}.",
                        ],
                        assumptions=[
                            f"Chord Reynolds number Re = {reynolds:.1e}",
                            f"Incompressible regime Mach = {mach:.2f}",
                            "Clean surface without transition tripping strips",
                        ],
                        prediction=(
                            f"Including boundary-layer skin friction and momentum deficit will account for "
                            f">90% of the Delta={abs_diff:.4f} drag discrepancy, restoring CD > 0."
                        ),
                        candidate_test=(
                            f"Execute OpenFOAM simpleFoam RANS case on {geometry} at alpha={alpha_deg}°, "
                            f"Re={reynolds:.1e} with kOmegaSST turbulence model; extract friction and pressure drag components."
                        ),
                        domain="aerodynamics",
                        geometry_id=geometry,
                        confidence=0.96,
                    )
                )
            elif q_upper == "CL":
                hypotheses.append(
                    self.formulate(
                        title="Viscous Decambering & Lift Slope Attenuation",
                        statement=(
                            f"Viscous boundary-layer thickening on the suction surface of {geometry} reduces the effective aerodynamic camber, "
                            f"causing the real lift slope dCL/dalpha to fall below the theoretical inviscid 2*pi (6.28/rad)."
                        ),
                        evidence_basis=[
                            "Thin-airfoil theoretical lift slope is dCL/dalpha = 2*pi = 0.1097/deg.",
                            f"Observed lift discrepancy: Delta={abs_diff:.4f} at alpha={alpha_deg}°.",
                            "Boundary-layer growth displaces outer inviscid streamlines away from upper surface.",
                        ],
                        assumptions=[
                            f"Angle of attack alpha = {alpha_deg}°",
                            f"Chord Reynolds number Re = {reynolds:.1e}",
                            "Attached or weakly separated boundary layer",
                        ],
                        prediction=(
                            f"Evaluating effective boundary-layer displacement thickness delta*(x) will predict "
                            f"a decambered lift slope within 3% of the measured value {min(val_a, val_b):.4f}."
                        ),
                        candidate_test=(
                            f"Run 3-point AoA sweep [alpha-2°, alpha, alpha+2°] in OpenFOAM simpleFoam to evaluate "
                            f"empirical dCL/dalpha and inspect upper surface delta*(x)."
                        ),
                        domain="aerodynamics",
                        geometry_id=geometry,
                        confidence=0.92,
                    )
                )

        # 2. Live CFD vs Neural Surrogate (Smoothing in Adverse Pressure Gradient)
        if "LIVE_CFD" in sources and "SURROGATE" in sources:
            hypotheses.append(
                self.formulate(
                    title="Neural Surrogate Spatial Smoothing in Adverse Gradient",
                    statement=(
                        f"The neural surrogate model applies spatial low-pass filtering that smooths the localized "
                        f"trailing-edge adverse pressure gradient on {geometry}, producing discrepancy Delta={abs_diff:.4f} against full CFD."
                    ),
                    evidence_basis=[
                        f"Discrepancy of {abs_diff:.4f} in {quantity} between CFD ({val_a if src_a == 'LIVE_CFD' else val_b}) and Surrogate.",
                        f"Airfoil {geometry} at alpha={alpha_deg}° develops adverse pressure gradient dCp/dx > 0 near trailing edge.",
                    ],
                    assumptions=[
                        f"Angle of attack alpha = {alpha_deg}°",
                        "Surrogate architecture uses finite basis spatial smoothing",
                    ],
                    prediction=(
                        f"The surrogate error will be concentrated in regions of maximum dCp/dx near x/c > 0.70; "
                        f"refining mesh and re-training with gradient loss will reduce Delta below {abs_diff / 2:.4f}."
                    ),
                    candidate_test=(
                        f"Sample Cp distribution along suction surface from full CFD and compare point-by-point with "
                        f"surrogate field prediction to locate localized error concentration."
                    ),
                    domain="aerodynamics",
                    geometry_id=geometry,
                    confidence=0.88,
                )
            )

        # 3. Live CFD vs Database Benchmark (Turbulence Closure & Experimental Trip)
        if "LIVE_CFD" in sources and "DATABASE_REAL" in sources:
            hypotheses.append(
                self.formulate(
                    title="RANS Turbulence Closure vs Experimental Boundary Trip",
                    statement=(
                        f"The RANS k-omega SST model assumes fully turbulent boundary layer over the entire chord of {geometry}, "
                        f"whereas reference database measurements (Abbott & von Doenhoff Report 824) featured natural or trip-wire transition."
                    ),
                    evidence_basis=[
                        f"Discrepancy Delta={abs_diff:.4f} in {quantity} between CFD and Abbott & von Doenhoff benchmark.",
                        "Standard RANS simpleFoam runs without gamma-Re_theta transition modeling by default.",
                    ],
                    assumptions=[
                        f"Reynolds number Re = {reynolds:.1e}",
                        "Wind tunnel test section turbulence intensity ~ 0.1%",
                    ],
                    prediction=(
                        f"Activating a transition model or setting laminar leading edge up to experimental transition location "
                        f"will reduce predicted CD by ~15-20% and close the gap with database {min(val_a, val_b):.4f}."
                    ),
                    candidate_test=(
                        f"Run OpenFOAM with gammaReThetaFoam or evaluate laminar sub-layer extent on {geometry} "
                        f"at Re={reynolds:.1e}, alpha={alpha_deg}°."
                    ),
                    domain="aerodynamics",
                    geometry_id=geometry,
                    confidence=0.89,
                )
            )

        return hypotheses

    def _load_all(self) -> None:
        """Populates in-memory cache from registry files."""
        if not self.storage_dir.exists():
            return
        for file in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                hyp = ScientificHypothesis(**data)
                self._memory_cache[hyp.hypothesis_id] = hyp
            except Exception as e:
                logger.warning("Could not parse hypothesis file %s: %s", file.name, e)


# Global singleton instance
hypothesis_engine = HypothesisEngine()
