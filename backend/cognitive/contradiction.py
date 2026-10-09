"""
AASI Cognitive Engine: Contradiction Engine.
Detects, diagnoses, and synthesizes physical divergences across analytical theory,
Navier-Stokes CFD, neural surrogates, and empirical wind-tunnel records.
Refuses to classify expected model-form differences as simulation errors.
"""

from __future__ import annotations

import logging
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("aasi.cognitive.contradiction")


class ContradictionType(str, Enum):
    """Classification of root physical or numerical divergence causes."""
    MODEL_FORM_DIFFERENCE = "MODEL_FORM_DIFFERENCE"        # Inviscid potential (CD=0) vs Viscous RANS (CD>0)
    REYNOLDS_DEPENDENCE = "REYNOLDS_DEPENDENCE"            # Laminar vs turbulent boundary layer transition
    TURBULENCE_MODEL_CLOSURE = "TURBULENCE_MODEL_CLOSURE"  # k-omega SST vs Spalart-Allmaras in adverse pressure gradients
    TRANSONIC_SHOCK_DIVERGENCE = "TRANSONIC_SHOCK_DIVERGENCE" # Shock wave drag emergence above critical Mach
    POST_STALL_SEPARATION = "POST_STALL_SEPARATION"        # Massive flow detachment violating steady RANS assumptions
    FACILITY_INTERFERENCE = "FACILITY_INTERFERENCE"        # Wind-tunnel wall correction or trip-wire drag increments
    DISCRETIZATION_INSUFFICIENT = "DISCRETIZATION_INSUFFICIENT" # Coarse grid discretization error before Richardson extrapolation
    GENUINE_NUMERICAL_DEFECT = "GENUINE_NUMERICAL_DEFECT"  # Residual divergence, NaN corruption, or sign convention bug


class ContradictionRecord(BaseModel):
    """Structured report of a detected divergence between two or more physical representations."""
    contradiction_id: str = Field(default_factory=lambda: f"CON-{uuid.uuid4().hex[:8].upper()}")
    quantity: str = Field(..., description="Target aerodynamic variable (e.g. CD, CL, CM)")
    contradiction_type: ContradictionType
    source_a: str = Field(..., description="First source name (e.g. Inviscid Thin-Airfoil Theory)")
    value_a: float
    tier_a: str
    source_b: str = Field(..., description="Second source name (e.g. OpenFOAM k-omega SST RANS)")
    value_b: float
    tier_b: str
    relative_divergence_percent: float
    is_genuine_defect: bool = False
    physical_explanation: str
    governing_mechanism: str
    recommended_resolving_action: str


class CognitiveContradictionEngine:
    """Evaluates multi-source aerodynamic evidence and explains physical variance."""

    def evaluate_contradiction(
        self,
        quantity: str,
        source_a: str,
        tier_a: str,
        value_a: float,
        source_b: str,
        tier_b: str,
        value_b: float,
        geometry_name: str = "NACA 0012",
        operating_state: Optional[Dict[str, Any]] = None,
    ) -> Optional[ContradictionRecord]:
        """
        Compares two results for the same physical quantity.
        If divergence exceeds normal tolerance, evaluates root physical mechanisms.
        """
        operating_state = operating_state or {}
        alpha = float(operating_state.get("alpha_deg", 0.0))
        re = float(operating_state.get("reynolds", 3.0e6))
        m = float(operating_state.get("mach", 0.15))

        mean_val = (abs(value_a) + abs(value_b)) / 2.0
        if mean_val < 1e-6:
            return None

        rel_diff = abs(value_a - value_b) / mean_val * 100.0

        # Discrepancy under 2% is normal numerical/experimental scatter
        if rel_diff < 2.0:
            return None

        # Diagnosis Case 1: D'Alembert's Paradox (Potential flow CD=0 vs Viscous CD>0)
        if quantity.upper() == "CD" and (value_a == 0.0 or value_b == 0.0):
            return ContradictionRecord(
                quantity="CD",
                contradiction_type=ContradictionType.MODEL_FORM_DIFFERENCE,
                source_a=source_a,
                value_a=value_a,
                tier_a=tier_a,
                source_b=source_b,
                value_b=value_b,
                tier_b=tier_b,
                relative_divergence_percent=rel_diff,
                is_genuine_defect=False,
                physical_explanation=(
                    "D'Alembert's Paradox: Ideal inviscid potential flow predicts zero drag (CD = 0) "
                    "because upstream and downstream pressure distributions integrate symmetrically without friction. "
                    "Viscous RANS and physical experiments capture non-zero skin friction and boundary-layer displacement."
                ),
                governing_mechanism="Viscous boundary layer shear stress and momentum deficit in the wake.",
                recommended_resolving_action="Retain Viscous RANS or Wind-Tunnel Benchmark as ground truth; apply Squire-Young correction to potential solver.",
            )

        # Diagnosis Case 2: Post-Stall Discrepancy (Steady RANS overprediction)
        if alpha >= 14.0 and quantity.upper() == "CL":
            return ContradictionRecord(
                quantity="CL",
                contradiction_type=ContradictionType.POST_STALL_SEPARATION,
                source_a=source_a,
                value_a=value_a,
                tier_a=tier_a,
                source_b=source_b,
                value_b=value_b,
                tier_b=tier_b,
                relative_divergence_percent=rel_diff,
                is_genuine_defect=False,
                physical_explanation=(
                    f"At alpha = {alpha} deg, steady RANS turbulence models typically delay separation and overpredict CL "
                    f"relative to physical wind-tunnel benchmarks, which exhibit massive unsteady vortex shedding."
                ),
                governing_mechanism="3D unsteady vortex shedding and massive boundary layer detachment.",
                recommended_resolving_action="Execute unsteady DDES / LES or adopt empirical wind-tunnel stall polar.",
            )

        # Diagnosis Case 3: Reynolds Number Boundary Layer Transition Divergence
        if quantity.upper() == "CD" and rel_diff > 15.0:
            return ContradictionRecord(
                quantity="CD",
                contradiction_type=ContradictionType.REYNOLDS_DEPENDENCE,
                source_a=source_a,
                value_a=value_a,
                tier_a=tier_a,
                source_b=source_b,
                value_b=value_b,
                tier_b=tier_b,
                relative_divergence_percent=rel_diff,
                is_genuine_defect=False,
                physical_explanation=(
                    f"At Re = {re:.1e}, profile drag is highly sensitive to the location of boundary layer transition. "
                    f"Fully turbulent simulations trip the boundary layer at the leading edge, increasing skin friction, "
                    f"whereas natural laminar flow maintains a low-drag laminar bucket over the forward 30-50% chord."
                ),
                governing_mechanism="Laminar-to-turbulent boundary layer transition location (e^N or intermittency).",
                recommended_resolving_action="Perform transition-sensitive XFOIL e^N sweep or gamma-Re_theta CFD transition study.",
            )

        # Default Generic Physical Discrepancy
        return ContradictionRecord(
            quantity=quantity,
            contradiction_type=ContradictionType.MODEL_FORM_DIFFERENCE,
            source_a=source_a,
            value_a=value_a,
            tier_a=tier_a,
            source_b=source_b,
            value_b=value_b,
            tier_b=tier_b,
            relative_divergence_percent=rel_diff,
            is_genuine_defect=False,
            physical_explanation=f"Divergence of {rel_diff:.1f}% observed between {source_a} and {source_b} for {quantity}.",
            governing_mechanism="Multi-fidelity turbulence closure or spatial discretization difference.",
            recommended_resolving_action="Execute Richardson extrapolation or compare against Abbott & von Doenhoff empirical reference.",
        )
