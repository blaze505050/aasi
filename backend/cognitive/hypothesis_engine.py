"""
AASI Cognitive Engine: Structured Hypothesis Engine.
Generates competing, falsifiable scientific hypotheses for aerospace phenomena.
Guarantees: Hypotheses are testable conjectures, NEVER established facts.
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

logger = logging.getLogger("aasi.cognitive.hypothesis_engine")


class CognitiveHypothesisStatus(str, Enum):
    """Rigorous epistemic lifecycle status of a scientific hypothesis."""
    PROPOSED = "PROPOSED"                    # Formulated; awaiting experimental test
    UNTESTED = "UNTESTED"                    # Staged without execution
    SUPPORTED = "SUPPORTED"                  # Verified physical evidence matches quantifiable prediction
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED" # Matches within macro-trend but exhibits local discrepancy
    CONTRADICTED = "CONTRADICTED"            # Verified evidence directly violates prediction
    REJECTED = "REJECTED"                    # Falsified by fundamental physical law or audited benchmark


class FalsificationCriterion(BaseModel):
    """Quantifiable metric or threshold that would compel hypothesis rejection."""
    quantity: str = Field(..., description="Target variable (e.g. CD, CL_max, dCL/da)")
    condition: str = Field(..., description="Condition indicating falsification (e.g. CD > 0.015, dCL/da < 0)")
    threshold_value: float
    unit: str = "dimensionless"
    physical_rationale: str = Field(..., description="Why this threshold invalidates the postulated mechanism")


class StructuredHypothesis(BaseModel):
    """
    Epistemic unit representing a testable aerospace conjecture.
    Compliance with Section 4 of Cognitive Engine Specification.
    """
    hypothesis_id: str = Field(default_factory=lambda: f"HYP-{uuid.uuid4().hex[:8].upper()}")
    title: str = Field(..., description="Concise physical title")
    statement: str = Field(..., description="Physical causal claim")
    mechanism: str = Field(..., description="Detailed aerodynamic mechanism explaining the phenomenon")
    predictions: Dict[str, Any] = Field(..., description="Quantifiable predicted variables (e.g. {'CL': 0.65, 'CD': 0.0085})")
    required_evidence: List[str] = Field(..., description="Evidence types required to confirm or falsify (e.g. ['RANS_CFD', 'WIND_TUNNEL'])")
    supporting_evidence: List[str] = Field(default_factory=list, description="IDs of corroborating evidence")
    contradicting_evidence: List[str] = Field(default_factory=list, description="IDs of conflicting evidence")
    assumptions: List[str] = Field(default_factory=list, description="Underlying physical assumptions")
    testability: str = Field(default="HIGH", description="Feasibility of numerical or empirical verification (LOW, MEDIUM, HIGH)")
    status: CognitiveHypothesisStatus = Field(default=CognitiveHypothesisStatus.PROPOSED)
    falsification_criteria: List[FalsificationCriterion] = Field(default_factory=list)
    competing_with: List[str] = Field(default_factory=list, description="IDs of mutually exclusive competing hypotheses")
    merkle_node_id: Optional[str] = Field(default=None, description="Linked cryptographic Merkle lineage node ID")
    provenance_hash: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def compute_provenance_hash(self) -> str:
        payload = {
            "id": self.hypothesis_id,
            "statement": self.statement,
            "mechanism": self.mechanism,
            "predictions": self.predictions,
            "status": self.status.value,
            "merkle_node_id": self.merkle_node_id or "",
        }
        raw = json.dumps(payload, sort_keys=True)
        self.provenance_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self.provenance_hash


class CognitiveHypothesisEngine:
    """Generates competing aerospace hypotheses tailored to geometry, regime, and question."""

    def generate_competing_hypotheses(
        self,
        question: str,
        geometry_name: str,
        alpha_deg: float,
        reynolds: float,
        mach: float,
        target_quantities: Optional[List[str]] = None,
    ) -> List[StructuredHypothesis]:
        """
        Generates at least 2 competing, falsifiable hypotheses.
        Never forces a single hypothesis to be universally true.
        """
        target_quantities = target_quantities or ["CL", "CD"]
        hypotheses: List[StructuredHypothesis] = []

        is_transonic = mach >= 0.70
        is_high_alpha = alpha_deg >= 12.0
        is_low_re = reynolds < 5.0e5

        # Case 1: Transonic / Supercritical drag divergence
        if is_transonic:
            h1 = StructuredHypothesis(
                title=f"Shock-Induced Boundary Layer Separation on {geometry_name}",
                statement=f"Transonic drag rise at Mach {mach} is dominated by a strong normal shock inducing boundary layer separation.",
                mechanism="Supersonic expansion over the upper suction crest terminates in a normal shock wave with local Mach > 1.2, triggering adverse pressure gradient stall downstream.",
                predictions={"CD": 0.0250, "shock_location_x_c": 0.55, "wave_drag_significant": True},
                required_evidence=["TRANSONIC_RANS_CFD", "SCHLIEREN_BENCHMARK"],
                assumptions=["Fully turbulent boundary layer", "Isentropic freestream"],
                falsification_criteria=[
                    FalsificationCriterion(
                        quantity="CD",
                        condition="CD < 0.0120",
                        threshold_value=0.0120,
                        physical_rationale="If CD remains below 0.0120, no significant wave drag or shock separation is occurring.",
                    )
                ],
            )
            h2 = StructuredHypothesis(
                title=f"Subcritical Compression without Massive Shock Separation on {geometry_name}",
                statement=f"Drag rise at Mach {mach} is governed primarily by profile boundary layer thickening with weak, non-separating compression.",
                mechanism="Airfoil curvature produces an isentropic or weak shock (local Mach < 1.1) insufficient to detach the boundary layer prior to the trailing edge.",
                predictions={"CD": 0.0115, "shock_location_x_c": 0.70, "wave_drag_significant": False},
                required_evidence=["TRANSONIC_RANS_CFD", "SURFACE_CP_MEASUREMENTS"],
                assumptions=["Supercritical section design maintains shockless recompression"],
                falsification_criteria=[
                    FalsificationCriterion(
                        quantity="CD",
                        condition="CD > 0.0200",
                        threshold_value=0.0200,
                        physical_rationale="If CD exceeds 0.0200, strong shock losses are definitively present.",
                    )
                ],
            )
            h1.competing_with = [h2.hypothesis_id]
            h2.competing_with = [h1.hypothesis_id]
            hypotheses.extend([h1, h2])

        # Case 2: High Angle of Attack / Pre-Stall / Post-Stall
        elif is_high_alpha:
            h1 = StructuredHypothesis(
                title=f"Trailing-Edge Boundary Layer Separation Stall on {geometry_name}",
                statement=f"At alpha = {alpha_deg} deg, lift loss is caused by progressive boundary layer detachment advancing from the trailing edge forward.",
                mechanism="Adverse pressure gradient over the aft suction surface overcomes wall shear stress, causing recirculating separation bubble that thickens the wake.",
                predictions={"CL": 1.10, "CD": 0.0450, "separation_onset_x_c": 0.60},
                required_evidence=["RANS_PRESSURE_DISTRIBUTION", "SHEAR_STRESS_AUDIT"],
                assumptions=["2D steady flow", "Spalart-Allmaras or k-omega SST closure is valid"],
                falsification_criteria=[
                    FalsificationCriterion(
                        quantity="CL",
                        condition="CL > 1.35",
                        threshold_value=1.35,
                        physical_rationale="If CL exceeds 1.35, flow remains fully attached and unseparated.",
                    )
                ],
            )
            h2 = StructuredHypothesis(
                title=f"Leading-Edge Laminar Separation Bubble Burst on {geometry_name}",
                statement=f"At alpha = {alpha_deg} deg, stall is precipitated abruptly by the bursting of a short laminar separation bubble near the leading edge.",
                mechanism="Extreme suction peak near x/c < 0.05 forces laminar detachment; failure of turbulent reattachment triggers catastrophic total chord separation.",
                predictions={"CL": 0.85, "CD": 0.0800, "separation_onset_x_c": 0.05},
                required_evidence=["TRANSITION_SENSITIVE_CFD", "HIGH_RESOLUTION_GRID"],
                assumptions=["Free transition at low freestream turbulence intensity"],
                falsification_criteria=[
                    FalsificationCriterion(
                        quantity="CL",
                        condition="CL > 1.20",
                        threshold_value=1.20,
                        physical_rationale="A bubble burst collapses lift below 1.0; maintaining CL > 1.20 disproves catastrophic leading-edge burst.",
                    )
                ],
            )
            h1.competing_with = [h2.hypothesis_id]
            h2.competing_with = [h1.hypothesis_id]
            hypotheses.extend([h1, h2])

        # Case 3: Standard Subsonic Linear / Attached Cruise
        else:
            h1 = StructuredHypothesis(
                title=f"Attached Boundary Layer with Viscous Form Drag on {geometry_name}",
                statement=f"At alpha = {alpha_deg} deg, Re = {reynolds:.1e}, flow is fully attached with linear lift slope dCL/dalpha ~ 2*pi.",
                mechanism="Mild adverse pressure gradient is sustained by turbulent boundary layer. Drag is dominated by skin friction plus Squire-Young displacement thickness.",
                predictions={"CL": round(0.11 * alpha_deg, 4) if "0012" in geometry_name else round(0.11 * (alpha_deg + 2.0), 4), "CD": 0.0075},
                required_evidence=["PANEL_SOLVER_WITH_VISCOUS_CORRECTION", "RANS_CFD"],
                assumptions=["No flow separation", "Linear thin-airfoil theory valid with boundary layer correction"],
                falsification_criteria=[
                    FalsificationCriterion(
                        quantity="CD",
                        condition="CD > 0.0180",
                        threshold_value=0.0180,
                        physical_rationale="Attached flow drag for this Re cannot exceed 0.0180 without gross separation or trip anomalies.",
                    )
                ],
            )
            h2 = StructuredHypothesis(
                title=f"Laminar Separation Bubble Drag Penalty on {geometry_name}",
                statement=f"At alpha = {alpha_deg} deg, Re = {reynolds:.1e}, transitional laminar separation bubble increases profile drag beyond attached estimates.",
                mechanism="Laminar flow separates under favorable-to-adverse transition, forms a transitional bubble before reattachment, elevating pressure drag.",
                predictions={"CL": round(0.10 * alpha_deg, 4), "CD": 0.0125},
                required_evidence=["XFOIL_E_N_TRANSITION", "EXPERIMENTAL_POLAR"],
                assumptions=["Transition not artificially tripped at leading edge"],
                falsification_criteria=[
                    FalsificationCriterion(
                        quantity="CD",
                        condition="CD < 0.0080",
                        threshold_value=0.0080,
                        physical_rationale="Presence of a transitional bubble inevitably elevates CD above 0.0080 at this Reynolds number.",
                    )
                ],
            )
            h1.competing_with = [h2.hypothesis_id]
            h2.competing_with = [h1.hypothesis_id]
            hypotheses.extend([h1, h2])

        # Link generated hypotheses to Merkle Lineage Graph and Epistemic Memory
        from backend.science.merkle_lineage import MerkleNodeType, merkle_lineage
        from backend.science.epistemic_kernel import epistemic_kernel

        warm_start = epistemic_kernel.get_warm_start(
            geometry=geometry_name,
            alpha_deg=alpha_deg,
            reynolds=reynolds,
            mach=mach,
        )

        for h in hypotheses:
            if warm_start.negative_evidence_warnings:
                h.assumptions.extend(warm_start.negative_evidence_warnings)

            # Record Merkle block for the hypothesis formulation
            m_node = merkle_lineage.record_node(
                investigation_id=f"HYP-DAG-{geometry_name.replace(' ', '')}",
                stage_name=f"HYPOTHESIS_FORMULATION: {h.title}",
                node_type=MerkleNodeType.GENESIS_SPEC,
                parent_hashes=[warm_start.parent_merkle_hash] if warm_start.parent_merkle_hash else [],
                inputs={"geometry": geometry_name, "alpha_deg": alpha_deg, "reynolds": reynolds, "mach": mach, "question": question},
                metrics=h.predictions,
                metadata={"mechanism": h.mechanism, "testability": h.testability},
            )
            h.merkle_node_id = m_node.node_id
            h.compute_provenance_hash()

        logger.info("Generated %d competing hypotheses for %s at alpha=%.1f", len(hypotheses), geometry_name, alpha_deg)
        return hypotheses

    def evaluate_hypothesis_against_evidence(
        self,
        hypothesis: StructuredHypothesis,
        evidence_results: Dict[str, Any],
    ) -> CognitiveHypothesisStatus:
        """
        Evaluates a hypothesis against verified numerical/empirical metrics.
        Systematically checks falsification criteria before assessing support.
        """
        cl_actual = evidence_results.get("CL", evidence_results.get("cl"))
        cd_actual = evidence_results.get("CD", evidence_results.get("cd"))

        # Check explicit falsification criteria
        for crit in hypothesis.falsification_criteria:
            val = cd_actual if crit.quantity.upper() == "CD" else cl_actual
            if val is not None:
                if ">" in crit.condition and val > crit.threshold_value:
                    hypothesis.status = CognitiveHypothesisStatus.CONTRADICTED
                    hypothesis.contradicting_evidence.append(f"Falsified by {crit.quantity}={val:.4f} > {crit.threshold_value}")
                    return hypothesis.status
                elif "<" in crit.condition and val < crit.threshold_value:
                    hypothesis.status = CognitiveHypothesisStatus.CONTRADICTED
                    hypothesis.contradicting_evidence.append(f"Falsified by {crit.quantity}={val:.4f} < {crit.threshold_value}")
                    return hypothesis.status

        # Evaluate closeness of prediction
        cl_pred = hypothesis.predictions.get("CL")
        cd_pred = hypothesis.predictions.get("CD")

        cl_match = True if (cl_pred is None or cl_actual is None or abs(cl_pred - cl_actual) < 0.15) else False
        cd_match = True if (cd_pred is None or cd_actual is None or abs(cd_pred - cd_actual) < 0.005) else False

        if cl_match and cd_match:
            hypothesis.status = CognitiveHypothesisStatus.SUPPORTED
            hypothesis.supporting_evidence.append(f"Verified solver output matches predictions (CL={cl_actual}, CD={cd_actual})")
        elif cl_match or cd_match:
            hypothesis.status = CognitiveHypothesisStatus.PARTIALLY_SUPPORTED
            hypothesis.supporting_evidence.append(f"Macro trend consistent but local deviation observed")
        else:
            hypothesis.status = CognitiveHypothesisStatus.CONTRADICTED
            hypothesis.contradicting_evidence.append(f"Prediction mismatch (Predicted CL={cl_pred}, CD={cd_pred}; Actual CL={cl_actual}, CD={cd_actual})")

        hypothesis.compute_provenance_hash()
        return hypothesis.status
