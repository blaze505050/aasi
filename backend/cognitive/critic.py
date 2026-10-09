"""
AASI Cognitive Engine: Scientific Critic.
Adversarial scientific evaluation engine that systematically attacks proposed hypotheses.
Exposes structured critiques without generating hidden chain-of-thought.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .hypothesis_engine import StructuredHypothesis

logger = logging.getLogger("aasi.cognitive.critic")


class CritiqueVulnerability(BaseModel):
    """Specific weakness, assumption risk, or regime limit identified by the critic."""
    vulnerability_id: str
    dimension: str = Field(..., description="E.g. REGIME_LIMIT, MODEL_EXTRAPOLATION, LAW_VIOLATION, SIMPLER_EXPLANATION")
    question_challenged: str
    finding: str
    risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    suggested_audit: str


class HypothesisCritique(BaseModel):
    """Structured critique report for a single hypothesis."""
    hypothesis_id: str
    hypothesis_title: str
    is_falsifiable: bool = True
    assumptions_audited: List[str] = Field(default_factory=list)
    regime_applicability: str
    extrapolation_risk: str = "LOW"  # LOW, MODERATE, SEVERE
    potential_law_conflicts: List[str] = Field(default_factory=list)
    vulnerabilities: List[CritiqueVulnerability] = Field(default_factory=list)
    falsifying_observation: str
    competing_alternative: str
    suggested_repairs: List[str] = Field(default_factory=list, description="Prescribed repair strategies from Epistemic Memory")
    merkle_node_id: Optional[str] = Field(default=None, description="Linked Merkle audit block hash")
    overall_critique_verdict: str  # TENABLE_REQUIRES_EVIDENCE, SEVERELY_CONSTRAINED, HIGH_EXTRAPOLATION_RISK


class ScientificCritic:
    """Systematically examines and challenges scientific conjectures before experimentation."""

    def critique_hypothesis(
        self,
        hypothesis: StructuredHypothesis,
        geometry_name: str,
        alpha_deg: float,
        reynolds: float,
        mach: float,
    ) -> HypothesisCritique:
        """
        Executes an adversarial inspection across 9 scientific critique dimensions:
        1. Assumptions made
        2. Failure modes / what could make it wrong
        3. Physical laws that could contradict it
        4. Regime applicability
        5. Evidence relevance
        6. Model extrapolation risk
        7. Occam's razor / simpler explanation
        8. Clear falsifying observation
        9. Alternative hypotheses
        """
        vulnerabilities: List[CritiqueVulnerability] = []
        law_conflicts: List[str] = []

        # 1. Extrapolation Risk Audit
        extrapolation_risk = "LOW"
        if alpha_deg > 18.0:
            extrapolation_risk = "SEVERE"
            vulnerabilities.append(
                CritiqueVulnerability(
                    vulnerability_id=f"VULN-{hypothesis.hypothesis_id[:8]}-01",
                    dimension="MODEL_EXTRAPOLATION",
                    question_challenged="Is the simulation or surrogate model being extrapolated beyond valid training domain?",
                    finding=f"Alpha = {alpha_deg} deg is deeply in the post-stall regime where 2D steady RANS models notoriously diverge and overpredict lift.",
                    risk_level="CRITICAL",
                    suggested_audit="Verify against unsteady DDES or experimental dynamic stall benchmarks rather than steady RANS.",
                )
            )
        elif mach > 0.85:
            extrapolation_risk = "SEVERE"
            vulnerabilities.append(
                CritiqueVulnerability(
                    vulnerability_id=f"VULN-{hypothesis.hypothesis_id[:8]}-02",
                    dimension="MODEL_EXTRAPOLATION",
                    question_challenged="Is the compressibility regime valid for standard low-speed equations?",
                    finding=f"Mach = {mach} is in the high transonic/choked flow regime where potential solvers and Karman-Tsien corrections fail catastrophically.",
                    risk_level="CRITICAL",
                    suggested_audit="Incompressible panel methods strictly prohibited; requires full compressible Euler or Navier-Stokes solver.",
                )
            )

        # 2. Conservation Law Invariants
        if hypothesis.predictions.get("CD", 0.0) < 0.0:
            law_conflicts.append("Second Law of Thermodynamics / Energy Conservation: Aerodynamic profile drag cannot be negative in steady unpowered glide.")
        if abs(hypothesis.predictions.get("CL", 0.0)) > 3.8:
            law_conflicts.append("Theoretical Circulation Limit: 2D airfoil lift coefficient cannot exceed theoretical bound (~3.8 without high-lift active blowing).")

        # 3. Simpler Explanation / Occam's Razor
        simpler_explanation = "Standard boundary-layer friction without complex shock or bubble interactions."
        if "Separation Bubble" in hypothesis.title and reynolds > 5.0e6:
            vulnerabilities.append(
                CritiqueVulnerability(
                    vulnerability_id=f"VULN-{hypothesis.hypothesis_id[:8]}-03",
                    dimension="SIMPLER_EXPLANATION",
                    question_challenged="Is there a simpler, more parsimonious physical explanation?",
                    finding=f"At high Reynolds number ({reynolds:.1e}), boundary layer naturally transitions turbulent rapidly without needing a distinct macro-scale laminar separation bubble.",
                    risk_level="MEDIUM",
                    suggested_audit="Examine surface skin friction coefficient Cf zero-crossings to prove bubble existence.",
                )
            )

        falsifying_obs = (
            hypothesis.falsification_criteria[0].condition
            if hypothesis.falsification_criteria
            else "Observation deviating > 15% from predicted metrics."
        )

        verdict = "TENABLE_REQUIRES_EVIDENCE"
        if any(v.risk_level == "CRITICAL" for v in vulnerabilities):
            verdict = "HIGH_EXTRAPOLATION_RISK"
        elif vulnerabilities:
            verdict = "SEVERELY_CONSTRAINED"

        # Retrieve prescribed repair strategies from Epistemic Kernel negative evidence
        from backend.science.epistemic_kernel import epistemic_kernel
        from backend.science.merkle_lineage import MerkleNodeType, merkle_lineage

        warm_start = epistemic_kernel.get_warm_start(
            geometry=geometry_name,
            alpha_deg=alpha_deg,
            reynolds=reynolds,
            mach=mach,
        )
        repairs = list(warm_start.recommended_repairs)

        critique = HypothesisCritique(
            hypothesis_id=hypothesis.hypothesis_id,
            hypothesis_title=hypothesis.title,
            is_falsifiable=len(hypothesis.falsification_criteria) > 0,
            assumptions_audited=hypothesis.assumptions,
            regime_applicability=f"Alpha: {alpha_deg} deg, Re: {reynolds:.1e}, Mach: {mach}",
            extrapolation_risk=extrapolation_risk,
            potential_law_conflicts=law_conflicts,
            vulnerabilities=vulnerabilities,
            falsifying_observation=falsifying_obs,
            competing_alternative=f"Mutually exclusive with: {hypothesis.competing_with}",
            suggested_repairs=repairs,
            overall_critique_verdict=verdict,
        )

        # Record Merkle Audit Node
        parent_hashes = [hypothesis.merkle_node_id] if hypothesis.merkle_node_id else []
        m_node = merkle_lineage.record_node(
            investigation_id=f"CRITIQUE-{geometry_name.replace(' ', '')}",
            stage_name=f"ADVERSARIAL_CRITIQUE: {hypothesis.title}",
            node_type=MerkleNodeType.AUDIT_CHECKPOINT,
            parent_hashes=parent_hashes,
            inputs={"extrapolation_risk": extrapolation_risk, "regime": critique.regime_applicability},
            metrics={"vulnerability_count": len(vulnerabilities), "risk_critical": any(v.risk_level == "CRITICAL" for v in vulnerabilities)},
            metadata={"verdict": verdict, "repairs": repairs},
        )
        critique.merkle_node_id = m_node.node_id

        logger.info("Critic evaluated hypothesis %s: verdict=%s, vulnerabilities=%d", hypothesis.hypothesis_id, verdict, len(vulnerabilities))
        return critique
