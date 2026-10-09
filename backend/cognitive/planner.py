"""
AASI Cognitive Engine: Experiment Planner & Information-Gain Engine.
Designs discriminating experiments to rigorously test competing hypotheses.
Calculates multi-criteria experimental utility with transparent, deterministic metrics.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .hypothesis_engine import StructuredHypothesis

logger = logging.getLogger("aasi.cognitive.planner")


class ExperimentUtilityMetrics(BaseModel):
    """
    Transparent, explainable multi-criteria utility metrics.
    Refuses arbitrary black-box scores.
    """
    scientific_value: float = Field(..., ge=0.0, le=1.0, description="Significance of target aerodynamic determination")
    hypothesis_discrimination: float = Field(..., ge=0.0, le=1.0, description="Power to decisively confirm H1 and falsify H2")
    expected_information_gain_bits: float = Field(..., ge=0.0, description="Expected Shannon entropy reduction regarding state")
    computational_cost_index: float = Field(..., ge=0.1, description="Relative cost index: 1.0=Panel/Analytical, 5.0=RANS, 20.0=LES")
    execution_risk: float = Field(..., ge=0.0, le=1.0, description="Likelihood of solver divergence, mesh distortion, or timeout")
    verification_difficulty: float = Field(..., ge=0.0, le=1.0, description="Complexity of required numerical/experimental audit")
    composite_utility: float = Field(..., description="Deterministic ratio balancing discrimination against cost and risk")
    utility_breakdown: str = Field(..., description="Machine-readable textual derivation of the utility score")


class CognitiveCandidateExperiment(BaseModel):
    """Structured proposal for an experiment designed to resolve competing hypotheses."""
    experiment_id: str = Field(default_factory=lambda: f"EXP-{uuid.uuid4().hex[:8].upper()}")
    title: str
    target_hypotheses: List[str] = Field(..., description="IDs of hypotheses this experiment is designed to test")
    tool_required: str = Field(..., description="Required instrument (e.g. OpenFOAM_simpleFoam, DiscreteVortexPanel, AbbottCatalog)")
    operating_parameters: Dict[str, Any] = Field(..., description="Geometry, alpha, Re, Mach, mesh parameters")
    fidelity_level: str = Field(..., description="ANALYTICAL, SURROGATE, RANS_STEADY, RANS_UNSTEADY, BENCHMARK_LOOKUP")
    expected_outcome_if_h1: str
    expected_outcome_if_h2: str
    utility: ExperimentUtilityMetrics
    is_safe_to_execute_locally: bool = True
    requires_human_approval: bool = False


class CognitiveExperimentPlanner:
    """Plans and ranks discriminating scientific experiments using explicit information-gain logic."""

    def plan_discriminating_experiments(
        self,
        hypotheses: List[StructuredHypothesis],
        geometry_name: str,
        alpha_deg: float,
        reynolds: float,
        mach: float,
        has_local_openfoam: bool = False,
    ) -> List[CognitiveCandidateExperiment]:
        """
        Formulates candidates across available fidelity tiers and ranks them by composite utility:
        U = (Discrimination * ScientificValue * InfoGain) / (Cost * (1 + Risk))
        """
        hyp_ids = [h.hypothesis_id for h in hypotheses]
        candidates: List[CognitiveCandidateExperiment] = []

        is_transonic = mach >= 0.70
        is_high_alpha = alpha_deg >= 12.0

        # Candidate 1: Rapid In-Memory / Viscous Panel Screening (Low Cost, High Immediate Value)
        cost_panel = 1.0
        risk_panel = 0.05
        disc_panel = 0.65 if not is_transonic else 0.20
        sci_val_panel = 0.70
        info_panel = 1.40
        u_panel = round((disc_panel * sci_val_panel * info_panel) / (cost_panel * (1.0 + risk_panel)), 4)

        candidates.append(
            CognitiveCandidateExperiment(
                title=f"Discrete Vortex Panel Solver with Boundary Layer Correction ({geometry_name})",
                target_hypotheses=hyp_ids,
                tool_required="DiscreteVortexPanelSolver",
                operating_parameters={
                    "geometry": geometry_name,
                    "alpha_deg": alpha_deg,
                    "reynolds": reynolds,
                    "mach": mach,
                    "n_panels": 120,
                },
                fidelity_level="ANALYTICAL_WITH_VISCOUS_CORRECTION",
                expected_outcome_if_h1="Linear lift slope with Squire-Young skin friction drag (~0.008)",
                expected_outcome_if_h2="Incapable of capturing massive separation or shock detachment directly",
                utility=ExperimentUtilityMetrics(
                    scientific_value=sci_val_panel,
                    hypothesis_discrimination=disc_panel,
                    expected_information_gain_bits=info_panel,
                    computational_cost_index=cost_panel,
                    execution_risk=risk_panel,
                    verification_difficulty=0.10,
                    composite_utility=u_panel,
                    utility_breakdown=f"({disc_panel} * {sci_val_panel} * {info_panel}) / ({cost_panel} * 1.05) = {u_panel}",
                ),
                is_safe_to_execute_locally=True,
                requires_human_approval=False,
            )
        )

        # Candidate 2: Validated Empirical Literature / Reference Polar Catalog Lookup
        cost_cat = 0.5
        risk_cat = 0.0
        disc_cat = 0.90
        sci_val_cat = 0.95
        info_cat = 2.10
        u_cat = round((disc_cat * sci_val_cat * info_cat) / (cost_cat * 1.0), 4)

        candidates.append(
            CognitiveCandidateExperiment(
                title=f"Peer-Reviewed Wind-Tunnel Reference Data Audit ({geometry_name})",
                target_hypotheses=hyp_ids,
                tool_required="ScientificKnowledgeCatalog",
                operating_parameters={
                    "geometry": geometry_name,
                    "reynolds": reynolds,
                    "target_source": "NACA Report 824 / Abbott & von Doenhoff",
                },
                fidelity_level="BENCHMARK_LOOKUP",
                expected_outcome_if_h1="Empirical polar confirms attached baseline CL and CD within +/- 2%",
                expected_outcome_if_h2="Empirical polar reveals premature drag bucket or separation discrepancy",
                utility=ExperimentUtilityMetrics(
                    scientific_value=sci_val_cat,
                    hypothesis_discrimination=disc_cat,
                    expected_information_gain_bits=info_cat,
                    computational_cost_index=cost_cat,
                    execution_risk=risk_cat,
                    verification_difficulty=0.05,
                    composite_utility=u_cat,
                    utility_breakdown=f"({disc_cat} * {sci_val_cat} * {info_cat}) / 0.5 = {u_cat}",
                ),
                is_safe_to_execute_locally=True,
                requires_human_approval=False,
            )
        )

        # Candidate 3: High-Fidelity Structured C-Grid Navier-Stokes CFD (OpenFOAM simpleFoam)
        cost_cfd = 8.0
        risk_cfd = 0.35 if is_high_alpha else 0.15
        disc_cfd = 0.95
        sci_val_cfd = 0.98
        info_cfd = 2.85
        u_cfd = round((disc_cfd * sci_val_cfd * info_cfd) / (cost_cfd * (1.0 + risk_cfd)), 4)

        candidates.append(
            CognitiveCandidateExperiment(
                title=f"Conformal 6-Block C-Grid RANS Simulation (OpenFOAM k-omega SST, {geometry_name})",
                target_hypotheses=hyp_ids,
                tool_required="OpenFOAM_simpleFoam_CGrid",
                operating_parameters={
                    "geometry": geometry_name,
                    "alpha_deg": alpha_deg,
                    "reynolds": reynolds,
                    "mach": mach,
                    "turbulence_model": "kOmegaSST",
                    "grading": 15,
                },
                fidelity_level="RANS_STEADY",
                expected_outcome_if_h1="Resolves boundary layer profiles and pressure recovery; confirms attached friction",
                expected_outcome_if_h2="Directly captures recirculation zone or separation bubble on upper surface",
                utility=ExperimentUtilityMetrics(
                    scientific_value=sci_val_cfd,
                    hypothesis_discrimination=disc_cfd,
                    expected_information_gain_bits=info_cfd,
                    computational_cost_index=cost_cfd,
                    execution_risk=risk_cfd,
                    verification_difficulty=0.40,
                    composite_utility=u_cfd,
                    utility_breakdown=f"({disc_cfd} * {sci_val_cfd} * {info_cfd}) / ({cost_cfd} * {1.0+risk_cfd}) = {u_cfd}",
                ),
                is_safe_to_execute_locally=has_local_openfoam,
                requires_human_approval=not has_local_openfoam,  # If local OpenFOAM not installed, staging Colab requires approval
            )
        )

        # Sort strictly descending by composite utility
        candidates.sort(key=lambda x: x.utility.composite_utility, reverse=True)
        logger.info("Planned %d candidate experiments; top candidate: %s (U=%.3f)", len(candidates), candidates[0].title, candidates[0].utility.composite_utility)
        return candidates
