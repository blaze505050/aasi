"""
AASI Phase 3: Multi-Fidelity Decision Engine & Resolution Bridge.
Connects the Scientific Task DAG runtime to the 8-level ScientificResolutionEngine
and implements deterministic fidelity escalation policies.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.science.engine import ScientificResolutionEngine
from backend.science.models import EpistemicStatus
from backend.agent.canonical_investigation import EpistemicTier
from backend.agent.investigation_lifecycle import AutonomyLevel


class AerodynamicRegime(str, Enum):
    INCOMPRESSIBLE_ATTACHED = "INCOMPRESSIBLE_ATTACHED"  # Low alpha (<10 deg), Mach < 0.3
    COMPRESSIBLE_SUBSONIC = "COMPRESSIBLE_SUBSONIC"      # Mach 0.3 - 0.7
    TRANSONIC_SHOCK = "TRANSONIC_SHOCK"                  # Mach 0.7 - 1.2, shock waves present
    SUPERSONIC = "SUPERSONIC"                            # Mach 1.2 - 5.0
    HIGH_ALPHA_STALL = "HIGH_ALPHA_STALL"                # Alpha > 12 deg, flow separation


class MultiFidelityDecision(BaseModel):
    selected_tier: EpistemicTier
    governing_regime: AerodynamicRegime
    escalation_reason: str
    requires_live_cfd: bool
    requires_human_approval: bool
    recommended_solver: str
    target_tolerance: float
    resolution_level: str


class MultiFidelityDecisionEngine:
    """
    Evaluates operating state, physical regimes, and user requirements
    to select or escalate computational fidelity across the 8-level hierarchy.
    """

    def __init__(self, resolution_engine: Optional[ScientificResolutionEngine] = None):
        self.resolution_engine = resolution_engine or ScientificResolutionEngine()

    @classmethod
    def classify_regime(cls, mach: float, alpha_deg: float) -> AerodynamicRegime:
        """Determines governing aerodynamic physical regime."""
        if abs(alpha_deg) >= 12.0:
            return AerodynamicRegime.HIGH_ALPHA_STALL
        if mach >= 1.2:
            return AerodynamicRegime.SUPERSONIC
        if mach >= 0.7:
            return AerodynamicRegime.TRANSONIC_SHOCK
        if mach >= 0.3:
            return AerodynamicRegime.COMPRESSIBLE_SUBSONIC
        return AerodynamicRegime.INCOMPRESSIBLE_ATTACHED

    def evaluate_fidelity(
        self,
        geometry: str,
        alpha_deg: float = 4.0,
        mach: float = 0.15,
        reynolds: float = 3e6,
        requested_fidelity: str = "MULTI_FIDELITY",
        tolerance: float = 0.05,
        autonomy_level: AutonomyLevel = AutonomyLevel.L3_BOUNDED,
    ) -> MultiFidelityDecision:
        regime = self.classify_regime(mach, alpha_deg)
        query_str = f"Calculate drag and lift polar for {geometry} at alpha={alpha_deg} deg, Mach={mach}, Re={reynolds}"
        
        # 1. Probe 8-level resolution hierarchy
        res_info = self.resolution_engine.resolve(query_str)
        res_level = res_info.get("resolution_level", "LEVEL 5 - ANALYTICAL")

        requires_cfd = False
        requires_approval = False
        reason = "Potential flow panel solver certified for incompressible attached flow regime."
        tier = EpistemicTier.ANALYTICAL
        solver = "Discrete Vortex Panel Method (Katz & Plotkin)"

        # 2. Check for authentic database match
        if "LEVEL 2" in res_level or "LEVEL 3" in res_level:
            tier = EpistemicTier.DATABASE_REAL
            solver = "Verified Experimental & CFD Database Catalog"
            reason = f"Authentic physical record identified in {res_level}."

        # 3. Dynamic escalation based on physical regime
        if regime in (AerodynamicRegime.TRANSONIC_SHOCK, AerodynamicRegime.HIGH_ALPHA_STALL):
            # Panel solver is physically invalid for shock waves or boundary-layer separation
            requires_cfd = True
            tier = EpistemicTier.LIVE_CFD
            solver = "OpenFOAM simpleFoam (k-omega SST)"
            reason = (
                f"Physical regime escalation: {regime.value} cannot be reliably predicted "
                f"by potential flow or thin airfoil theory. High-fidelity Navier-Stokes required."
            )
            # Check if autonomy level requires approval for live CFD dispatch
            if autonomy_level in (AutonomyLevel.L0_ADVISORY, AutonomyLevel.L1_ASSISTED):
                requires_approval = True

        elif requested_fidelity == "LIVE_CFD":
            requires_cfd = True
            tier = EpistemicTier.LIVE_CFD
            solver = "OpenFOAM simpleFoam (k-omega SST)"
            reason = "User explicitly requested high-fidelity CFD simulation."
            if autonomy_level in (AutonomyLevel.L0_ADVISORY, AutonomyLevel.L1_ASSISTED):
                requires_approval = True

        return MultiFidelityDecision(
            selected_tier=tier,
            governing_regime=regime,
            escalation_reason=reason,
            requires_live_cfd=requires_cfd,
            requires_human_approval=requires_approval,
            recommended_solver=solver,
            target_tolerance=tolerance,
            resolution_level=res_level,
        )
