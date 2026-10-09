"""
AASI Phase 29: Next-Experiment Proposal Engine.
Recognizes when additional scientific investigation is useful.
Proposes concrete, physically grounded follow-up experiments without automatically executing them.
Each proposal contains:
- objective
- variable to change
- expected information gained
- reason
- dependency
- execution requirements
"""

from typing import List, Dict, Any, Optional
import hashlib
from backend.agent.canonical_investigation import (
    NextExperimentProposal,
    OperatingConditions,
    DiscrepancyRecord,
)


class NextExperimentEngine:
    """
    Evaluates evidence gaps, flow regimes, and discrepancies to formulate
    justified subsequent experiment proposals.
    """

    @classmethod
    def propose_next_experiments(
        cls,
        geometry: str,
        conditions: OperatingConditions,
        discrepancies: List[DiscrepancyRecord],
        has_live_cfd: bool = False,
        surrogate_uncertainty: float = 0.08,
    ) -> List[NextExperimentProposal]:
        """
        Synthesizes prioritized follow-up experiment proposals.
        """
        proposals: List[NextExperimentProposal] = []
        alpha = conditions.alpha_deg
        reynolds = conditions.reynolds

        # 1. Proposal: Near-wall mesh refinement for viscous drag & y+ resolution
        # Trigger: Live CFD is pending or drag discrepancy between CFD/Surrogate/Database > 5%
        mesh_pid = hashlib.sha256(f"{geometry}:{alpha}:mesh_refine".encode()).hexdigest()[:8].upper()
        proposals.append(
            NextExperimentProposal(
                proposal_id=f"PROP-MESH-{mesh_pid}",
                objective=f"Evaluate near-wall shear stress and skin friction on {geometry} with refined viscous sublayer mesh.",
                variable_to_change="boundary_layer_first_cell_height_and_expansion_ratio",
                expected_information_gained="Accurate wall-resolved shear stress (y+ < 1.0) eliminating wall function approximations in adverse pressure gradients.",
                reason="High-accuracy drag resolution requires capturing laminar sublayer damping without empirical log-law wall functions.",
                dependency="baseline_mesh_generation",
                execution_requirements={
                    "mesh_cells": 120_000,
                    "target_yplus": 0.8,
                    "solver": "simpleFoam",
                    "turbulence_model": "kOmegaSST",
                    "estimated_colab_runtime_sec": 480,
                },
            )
        )

        # 2. Proposal: Transition-sensitive turbulence modeling (gamma-ReTheta SST)
        # Trigger: Probing moderate Re (1e6 - 5e6) where laminar separation bubble or transition occurs
        if 500_000 <= reynolds <= 6_000_000:
            trans_pid = hashlib.sha256(f"{geometry}:{alpha}:transition".encode()).hexdigest()[:8].upper()
            proposals.append(
                NextExperimentProposal(
                    proposal_id=f"PROP-TRANS-{trans_pid}",
                    objective=f"Investigate laminar-to-turbulent transition displacement on {geometry} upper suction surface.",
                    variable_to_change="turbulence_closure_model (kOmegaSST -> gammaReThetaSST)",
                    expected_information_gained="Location of boundary layer transition (x/c) and laminar separation bubble drag penalty.",
                    reason=(
                        f"At Re={reynolds:.1e}, assumption of fully turbulent flow from leading edge "
                        f"may overestimate skin friction drag and mispredict onset of trailing-edge separation."
                    ),
                    dependency="mesh_yplus_under_1",
                    execution_requirements={
                        "solver": "simpleFoam",
                        "turbulence_model": "kOmegaSSTLM",
                        "additional_transport_equations": ["gamma", "ReThetat"],
                        "estimated_colab_runtime_sec": 600,
                    },
                )
            )

        # 3. Proposal: High-Alpha Adverse Pressure Gradient & Separation Sweep
        # Trigger: Alpha probes upper linear regime (alpha >= 6°)
        if alpha >= 6.0:
            stall_pid = hashlib.sha256(f"{geometry}:{alpha}:stall_onset".encode()).hexdigest()[:8].upper()
            proposals.append(
                NextExperimentProposal(
                    proposal_id=f"PROP-STALL-{stall_pid}",
                    objective=f"Quantify stall onset and trailing edge separation bubble on {geometry} beyond alpha={alpha}°.",
                    variable_to_change="angle_of_attack_sweep_increment (alpha = 10°, 12°, 14°)",
                    expected_information_gained="Critical angle of stall (alpha_stall) and maximum lift coefficient (CL_max).",
                    reason=(
                        "Nonlinear stall mechanics induce massive pressure drag divergence. "
                        "Exploring past alpha=10° establishes the upper operational boundary of the polar."
                    ),
                    dependency="baseline_polar_verification",
                    execution_requirements={
                        "alpha_points": [round(alpha + 2.0, 1), round(alpha + 4.0, 1), round(alpha + 6.0, 1)],
                        "solver": "simpleFoam",
                        "divergence_monitoring": "residual_slope_and_force_oscillation",
                        "estimated_colab_runtime_sec": 900,
                    },
                )
            )

        # 4. Proposal: Pressure Tap Array Validation (Cp distribution)
        # Trigger: Experimental benchmark or detailed surrogate comparison
        cp_pid = hashlib.sha256(f"{geometry}:{alpha}:cp_distribution".encode()).hexdigest()[:8].upper()
        proposals.append(
            NextExperimentProposal(
                proposal_id=f"PROP-CP-{cp_pid}",
                objective=f"Extract chordwise surface pressure distribution (Cp vs x/c) for {geometry} at alpha={alpha}°.",
                variable_to_change="postprocessing_surface_sample_probes (chordwise 100 points)",
                expected_information_gained="Suction peak magnitude (-Cp_min) and adverse pressure gradient recovery profile.",
                reason=(
                    "Force coefficients (CL, CD) collapse spatial physics into scalars. "
                    "Cp profile comparison directly exposes localized separation bubbles and shock / suction anomalies."
                ),
                dependency="converged_flow_field",
                execution_requirements={
                    "probes_count": 100,
                    "fields": ["p", "U"],
                    "output_format": "raw_ascii_csv",
                    "estimated_colab_runtime_sec": 60,
                },
            )
        )

        return proposals
