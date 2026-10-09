"""
AASI Milestone 5: Experiment Planner & Transparent Heuristic Engine.
Governing Doctrine: Absolute Anti-Fabrication Rule.
Generates candidate experiments with:
- question
- changed parameters
- method
- expected information
- cost estimate
- dependencies
- rationale (reason)

DOES NOT CLAIM MATHEMATICALLY OPTIMAL EXPERIMENT SELECTION.
Uses a fully inspectable, transparent multi-criteria heuristic.
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
from pydantic import BaseModel, Field

from backend.compute.router import DeterministicComputeRouter
from backend.science.hypotheses import ScientificHypothesis

logger = logging.getLogger("aasi.science.planner")


class CandidateStatus(str, Enum):
    CANDIDATE = "CANDIDATE"      # Formulated and proposed by planner
    STAGED = "STAGED"            # OpenFOAM deck / Colab notebook packaged
    EXECUTED = "EXECUTED"        # Solver finished externally
    VERIFIED = "VERIFIED"        # Output ingested and passed scientific verification
    REJECTED = "REJECTED"        # Dismissed by human operator


class CostTier(str, Enum):
    FREE_LOCAL = "FREE_LOCAL"
    FREE_COLAB = "FREE_COLAB"
    REMOTE_HPC = "REMOTE_HPC"


class ExperimentCostEstimate(BaseModel):
    """Transparent order-of-magnitude computational cost footprint."""
    regime: str = Field(..., description="Rapid (< 5 min), Moderate (5-15 min), Extended (15-45 min), Heavy Cluster (> 1 hr)")
    estimated_cells: int = Field(..., ge=1, description="Estimated spatial grid cell count")
    estimated_memory_gb: float = Field(..., ge=0.0, description="Estimated RAM footprint in GB")
    wall_clock_bracket: str = Field(..., description="Order-of-magnitude time estimate bracket")
    cost_tier: CostTier = Field(default=CostTier.FREE_LOCAL, description="Target infrastructure tier")


class CandidateExperiment(BaseModel):
    """
    Structured candidate experiment proposal.
    Complies strictly with Milestone 5 / Prompt 6:
    Contains question, changed_parameters, method, expected_information,
    cost_estimate, dependencies, and rationale (reason).
    Explicitly refuses to claim mathematical optimality.
    """
    experiment_id: str = Field(default_factory=lambda: f"EXP-{uuid.uuid4().hex[:8].upper()}")
    question: str = Field(..., description="The scientific question being investigated by this experiment")
    changed_parameters: Dict[str, Any] = Field(..., description="Concrete parameters altered relative to current baseline")
    method: str = Field(..., description="Numerical solver or database method (e.g. OpenFOAM simpleFoam kOmegaSST)")
    expected_information: str = Field(..., description="Quantifiable knowledge gained if this experiment is executed")
    cost_estimate: ExperimentCostEstimate = Field(..., description="Order-of-magnitude computational requirements")
    dependencies: List[str] = Field(default_factory=list, description="Prerequisites that must be verified first")
    rationale: str = Field(..., description="Physical or epistemic justification explaining why this experiment is proposed")
    status: CandidateStatus = Field(default=CandidateStatus.CANDIDATE, description="Current lifecycle state")

    # Transparent Heuristic Ranking
    heuristic_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Transparent multi-criteria heuristic score [0.0, 1.0]")
    score_breakdown: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed breakdown of heuristic components (discrepancy, regime, uncertainty, cost penalty)",
    )

    # Anti-Optimality Disclaimer (IMMUTABLE)
    optimality_claim: str = Field(
        default=(
            "HEURISTIC_SELECTION (Ranked via transparent multi-criteria heuristic; "
            "does NOT claim global mathematical optimality)."
        ),
        description="Mandatory disclaimer stating that selection is heuristic and not mathematically optimal.",
    )

    # Linkages & Provenance
    associated_hypothesis_id: Optional[str] = Field(default=None, description="Linked scientific hypothesis if applicable")
    geometry_id: Optional[str] = Field(default=None, description="Target airfoil geometry")
    provenance_hash: str = Field(default="", description="Cryptographic SHA-256 digest of experiment specification")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def compute_provenance_hash(self) -> str:
        """Computes deterministic SHA-256 hash sealing question, parameters, method, and rationale."""
        payload = {
            "experiment_id": self.experiment_id,
            "question": self.question.strip(),
            "changed_parameters": self.changed_parameters,
            "method": self.method.strip(),
            "expected_information": self.expected_information.strip(),
            "dependencies": sorted(self.dependencies),
            "rationale": self.rationale.strip(),
        }
        raw = json.dumps(payload, sort_keys=True)
        self.provenance_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self.provenance_hash

    def to_presentation_dict(self) -> Dict[str, Any]:
        """Returns structured dictionary ready for API responses or UI display."""
        return {
            "experiment_id": self.experiment_id,
            "question": self.question,
            "changed_parameters": self.changed_parameters,
            "method": self.method,
            "expected_information": self.expected_information,
            "cost_estimate": self.cost_estimate.model_dump(),
            "dependencies": self.dependencies,
            "rationale": self.rationale,
            "reason": self.rationale,  # alias for prompt 6 compatibility
            "status": self.status.value,
            "heuristic_score": round(self.heuristic_score, 4),
            "score_breakdown": self.score_breakdown,
            "optimality_claim": self.optimality_claim,
            "associated_hypothesis_id": self.associated_hypothesis_id,
            "geometry_id": self.geometry_id,
            "provenance_hash": self.provenance_hash,
            "created_at": self.created_at,
        }


class HeuristicExperimentScorer:
    """
    Transparent, auditable multi-criteria scoring heuristic for candidate experiments.
    Does NOT claim global mathematical optimality.
    Scores candidates based on:
    - Discrepancy resolution value (D)
    - Physical regime boundary proximity (R)
    - Epistemic uncertainty / data sparsity (U)
    - Computational cost penalty (C)
    """

    # Transparently declared heuristic weights
    W_DISCREPANCY = 0.35
    W_REGIME = 0.30
    W_UNCERTAINTY = 0.25
    W_COST_PENALTY = 0.15

    @classmethod
    def score(
        cls,
        discrepancy_factor: float = 0.5,    # [0.0, 1.0] Magnitude of empirical disagreement
        regime_factor: float = 0.5,         # [0.0, 1.0] Proximity to stall, transition, or transonic boundaries
        uncertainty_factor: float = 0.5,    # [0.0, 1.0] Lack of empirical data / surrogate variance
        cost_penalty_factor: float = 0.2,   # [0.0, 1.0] Normalized compute resource burden
    ) -> tuple[float, Dict[str, Any]]:
        """
        Computes transparent score: S = clamp(w_d*D + w_r*R + w_u*U - w_c*C, 0.0, 1.0).
        Returns final score and full component breakdown.
        """
        d = max(0.0, min(1.0, float(discrepancy_factor)))
        r = max(0.0, min(1.0, float(regime_factor)))
        u = max(0.0, min(1.0, float(uncertainty_factor)))
        c = max(0.0, min(1.0, float(cost_penalty_factor)))

        raw_score = (
            cls.W_DISCREPANCY * d
            + cls.W_REGIME * r
            + cls.W_UNCERTAINTY * u
            - cls.W_COST_PENALTY * c
        )
        final_score = max(0.0, min(1.0, round(raw_score, 4)))

        breakdown = {
            "discrepancy_factor": d,
            "regime_factor": r,
            "uncertainty_factor": u,
            "cost_penalty_factor": c,
            "weights": {
                "w_discrepancy": cls.W_DISCREPANCY,
                "w_regime": cls.W_REGIME,
                "w_uncertainty": cls.W_UNCERTAINTY,
                "w_cost_penalty": cls.W_COST_PENALTY,
            },
            "raw_score": round(raw_score, 4),
            "final_score": final_score,
            "formula": "S = clamp(0.35*D + 0.30*R + 0.25*U - 0.15*C, 0.0, 1.0)",
            "optimality_notice": "Score is derived from a transparent linear heuristic and does NOT represent mathematically optimal experiment design.",
        }
        return final_score, breakdown


class ExperimentPlanner:
    """
    Formulates and ranks candidate experiments based on active investigation context,
    hypotheses, and discrepancies.
    """

    def __init__(self):
        self._candidates_cache: Dict[str, CandidateExperiment] = {}

    def generate_candidates(
        self,
        geometry: str = "NACA 0012",
        alpha_deg: float = 4.0,
        reynolds: float = 3.0e6,
        mach: float = 0.15,
        hypotheses: Optional[List[ScientificHypothesis]] = None,
        discrepancies: Optional[List[Dict[str, Any]]] = None,
        has_verified_cfd: bool = False,
    ) -> List[CandidateExperiment]:
        """
        Synthesizes a prioritized suite of candidate experiments covering:
        1. Stall onset and detachment angle-of-attack sweep
        2. Near-wall viscous sublayer mesh refinement (y+ < 1)
        3. Transition-sensitive modeling (gamma-ReTheta SST)
        4. Surface pressure tap distribution (Cp vs x/c)
        5. Reynolds number sensitivity probe
        """
        candidates: List[CandidateExperiment] = []

        # 1. High-Alpha Stall Sweep
        # Question: Where does stall occur and does separation cause sharp drag divergence?
        stall_score, stall_breakdown = HeuristicExperimentScorer.score(
            discrepancy_factor=0.7 if alpha_deg >= 8.0 else 0.4,
            regime_factor=0.9 if alpha_deg >= 6.0 else 0.5,
            uncertainty_factor=0.8,
            cost_penalty_factor=0.3,
        )
        mem_stall = DeterministicComputeRouter.estimate_memory_gb(100_000, "2D")
        regime_stall = DeterministicComputeRouter.classify_regime(100_000, 3000, "2D")

        cand_stall = CandidateExperiment(
            question=f"Does boundary-layer separation induce stall onset on {geometry} between alpha={round(alpha_deg+2, 1)}° and {round(alpha_deg+6, 1)}°?",
            changed_parameters={
                "geometry": geometry,
                "alpha_sweep": [round(alpha_deg + 2.0, 1), round(alpha_deg + 4.0, 1), round(alpha_deg + 6.0, 1)],
                "reynolds": reynolds,
                "mach": mach,
            },
            method="OpenFOAM simpleFoam RANS (kOmegaSST)",
            expected_information="Precise stall angle alpha_stall, maximum lift coefficient CL_max, and post-stall pressure drag divergence.",
            cost_estimate=ExperimentCostEstimate(
                regime=regime_stall,
                estimated_cells=100_000,
                estimated_memory_gb=mem_stall,
                wall_clock_bracket="approx 5-15 minutes (3 AoA cases)",
                cost_tier=CostTier.FREE_COLAB,
            ),
            dependencies=["baseline_mesh_verification", "baseline_polar_verified"],
            rationale=(
                f"Operating at alpha={alpha_deg}° approaches the non-linear lift region. "
                f"Exploring angles [{round(alpha_deg+2, 1)}°, {round(alpha_deg+4, 1)}°, {round(alpha_deg+6, 1)}°] maps "
                f"the adverse pressure gradient separation boundary."
            ),
            heuristic_score=stall_score,
            score_breakdown=stall_breakdown,
            geometry_id=geometry,
        )
        cand_stall.compute_provenance_hash()
        candidates.append(cand_stall)

        # 2. Wall-Resolved Viscous Sublayer Mesh Refinement
        # Question: Does resolving the viscous sublayer (y+ < 1) eliminate empirical wall function errors?
        mesh_score, mesh_breakdown = HeuristicExperimentScorer.score(
            discrepancy_factor=0.6,
            regime_factor=0.4,
            uncertainty_factor=0.6,
            cost_penalty_factor=0.25,
        )
        cand_mesh = CandidateExperiment(
            question=f"Does resolving the laminar sublayer with y+ < 1.0 eliminate skin-friction drag discrepancies on {geometry}?",
            changed_parameters={
                "geometry": geometry,
                "alpha_deg": alpha_deg,
                "reynolds": reynolds,
                "first_cell_height_m": 1.2e-5,
                "target_yplus": 0.8,
                "estimated_cells": 160_000,
            },
            method="OpenFOAM blockMesh + simpleFoam (Wall-Resolved kOmegaSST)",
            expected_information="Direct wall-resolved shear stress profile tau_w(x) without wall function approximations.",
            cost_estimate=ExperimentCostEstimate(
                regime="MODERATE_REGIME (approx 5-15 minutes)",
                estimated_cells=160_000,
                estimated_memory_gb=0.96,
                wall_clock_bracket="< 10 minutes",
                cost_tier=CostTier.FREE_LOCAL if reynolds <= 3e6 else CostTier.FREE_COLAB,
            ),
            dependencies=["baseline_geometry_coordinates_valid"],
            rationale=(
                "Standard wall functions assume logarithmic velocity law which breaks down in adverse pressure gradients. "
                "Refining the near-wall mesh to y+ < 1.0 resolves viscous damping directly."
            ),
            heuristic_score=mesh_score,
            score_breakdown=mesh_breakdown,
            geometry_id=geometry,
        )
        cand_mesh.compute_provenance_hash()
        candidates.append(cand_mesh)

        # 3. Transition-Sensitive Modeling
        # Question: Does accounting for laminar-to-turbulent transition shift the drag polar toward experimental wind tunnel benchmarks?
        trans_score, trans_breakdown = HeuristicExperimentScorer.score(
            discrepancy_factor=0.8 if discrepancies else 0.5,
            regime_factor=0.7 if 1e6 <= reynolds <= 6e6 else 0.3,
            uncertainty_factor=0.7,
            cost_penalty_factor=0.35,
        )
        cand_trans = CandidateExperiment(
            question=f"Does modeling laminar-to-turbulent transition on {geometry} close the drag gap with wind tunnel benchmarks?",
            changed_parameters={
                "geometry": geometry,
                "alpha_deg": alpha_deg,
                "reynolds": reynolds,
                "turbulence_model": "gammaReThetaSST",
                "additional_equations": ["gamma", "ReThetat"],
            },
            method="OpenFOAM simpleFoam with gammaReThetaSST Transition Model",
            expected_information="Intermittency gamma distribution, natural transition onset location x_tr/c, and laminar drag reduction.",
            cost_estimate=ExperimentCostEstimate(
                regime="MODERATE_REGIME (approx 8-15 minutes)",
                estimated_cells=140_000,
                estimated_memory_gb=1.1,
                wall_clock_bracket="8-15 minutes",
                cost_tier=CostTier.FREE_COLAB,
            ),
            dependencies=["wall_resolved_mesh_yplus_sub_1"],
            rationale=(
                f"At Re={reynolds:.1e}, the boundary layer is naturally laminar over the forward 15-30% of the chord. "
                f"Fully turbulent RANS over-predicts leading-edge skin friction drag."
            ),
            heuristic_score=trans_score,
            score_breakdown=trans_breakdown,
            geometry_id=geometry,
        )
        cand_trans.compute_provenance_hash()
        candidates.append(cand_trans)

        # 4. Surface Pressure Distribution Tap Array (Cp profile)
        # Question: What is the chordwise pressure distribution Cp(x) and does a suction peak collapse occur?
        cp_score, cp_breakdown = HeuristicExperimentScorer.score(
            discrepancy_factor=0.5,
            regime_factor=0.5,
            uncertainty_factor=0.5,
            cost_penalty_factor=0.15,
        )
        cand_cp = CandidateExperiment(
            question=f"What is the quantitative chordwise surface pressure distribution Cp(x/c) across {geometry} at alpha={alpha_deg}°?",
            changed_parameters={
                "geometry": geometry,
                "alpha_deg": alpha_deg,
                "reynolds": reynolds,
                "post_processing_functions": ["surfacePressureRaw", "pressureCoeffs"],
            },
            method="OpenFOAM simpleFoam with postProcessing sampling tap array",
            expected_information="Detailed 64-point Cp vs x/c profile, leading-edge suction peak Cp_min, and trailing edge pressure recovery.",
            cost_estimate=ExperimentCostEstimate(
                regime="RAPID_REGIME (< 5 minutes)",
                estimated_cells=100_000,
                estimated_memory_gb=0.75,
                wall_clock_bracket="< 5 minutes",
                cost_tier=CostTier.FREE_LOCAL,
            ),
            dependencies=["baseline_solver_execution_clean"],
            rationale=(
                "Integrated force coefficients (CL, CD) hide localized aerodynamic features. "
                "Extracting surface pressure profiles reveals suction peak height and adverse pressure gradient onset."
            ),
            heuristic_score=cp_score,
            score_breakdown=cp_breakdown,
            geometry_id=geometry,
        )
        cand_cp.compute_provenance_hash()
        candidates.append(cand_cp)

        # 5. Reynolds Number Scaling Probe
        # Question: How does scale effect alter the viscous drag fraction and lift slope?
        re_target = round(reynolds * 2.0, 1)
        re_score, re_breakdown = HeuristicExperimentScorer.score(
            discrepancy_factor=0.4,
            regime_factor=0.4,
            uncertainty_factor=0.6,
            cost_penalty_factor=0.20,
        )
        cand_re = CandidateExperiment(
            question=f"How does Reynolds number scaling from Re={reynolds:.1e} to Re={re_target:.1e} affect boundary-layer thickness on {geometry}?",
            changed_parameters={
                "geometry": geometry,
                "alpha_deg": alpha_deg,
                "reynolds": re_target,
                "nu": round(mach * 340.29 / re_target, 9),
            },
            method="OpenFOAM simpleFoam RANS (kOmegaSST)",
            expected_information="Reynolds scaling exponent for drag delta_CD ~ Re^(-1/5) and boundary-layer thinning rate.",
            cost_estimate=ExperimentCostEstimate(
                regime="RAPID_REGIME (< 5 minutes)",
                estimated_cells=100_000,
                estimated_memory_gb=0.75,
                wall_clock_bracket="< 5 minutes",
                cost_tier=CostTier.FREE_LOCAL,
            ),
            dependencies=["baseline_reynolds_polar_verified"],
            rationale=(
                f"Evaluating aerodynamic forces across an order of magnitude in Reynolds number establishes "
                f"viscous scale independence and validates the classical flat-plate turbulent friction power law."
            ),
            heuristic_score=re_score,
            score_breakdown=re_breakdown,
            geometry_id=geometry,
        )
        cand_re.compute_provenance_hash()
        candidates.append(cand_re)

        # Sort candidates descending by transparent heuristic score
        ranked_candidates = sorted(candidates, key=lambda c: c.heuristic_score, reverse=True)

        for c in ranked_candidates:
            self._candidates_cache[c.experiment_id] = c

        return ranked_candidates

    def get_candidate(self, experiment_id: str) -> Optional[CandidateExperiment]:
        """Retrieves candidate experiment by ID."""
        return self._candidates_cache.get(experiment_id)

    def list_candidates(self) -> List[CandidateExperiment]:
        """Returns all cached candidate experiments ordered by heuristic score."""
        return sorted(list(self._candidates_cache.values()), key=lambda c: c.heuristic_score, reverse=True)


# Global singleton instance
experiment_planner = ExperimentPlanner()
