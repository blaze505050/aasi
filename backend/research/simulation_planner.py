"""
AASI Simulation Planner & Campaign Generator.

Translates high-level scientific objectives into cost-optimized,
information-maximizing CFD simulation campaigns.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import hashlib

from backend.research.models import ResearchObjective, ObjectiveStatus
from backend.physics_ai.active_learning import (
    ActiveLearning2Engine,
    AcquisitionStrategy,
    ActiveLearningCandidateRecord,
    CandidateStatus,
    active_learning_registry,
)
from backend.simulation.job_spec import (
    CFDJobSpec,
    SolverType,
    ExecutionBackend,
    MeshSpecification,
    PhysicsSpecification,
    ValidationRequirements,
    EstimatedComputeCost,
)


class CampaignPlan(BaseModel):
    campaign_id: str
    objective_id: str
    title: str
    candidate_jobs: List[CFDJobSpec] = Field(default_factory=list)
    total_estimated_cpu_hours: float = 0.0
    expected_uncertainty_reduction_pct: float = 0.0
    human_approval_required: bool = True
    status: str = "PROPOSED"  # PROPOSED, APPROVED, IN_EXECUTION, COMPLETED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SimulationPlanner:
    """
    Formulates scientific CFD campaigns balancing epistemic information gain
    against computational budget and user execution limits.
    """

    @classmethod
    def plan_campaign_for_objective(
        cls,
        objective: ResearchObjective,
        existing_dataset_points: List[Dict[str, float]],
        max_cases: int = 5,
        max_cpu_budget_hours: float = 5.0,
        preferred_solver: SolverType = SolverType.OPENFOAM
    ) -> CampaignPlan:
        """
        Formulates an optimal campaign plan for a given research objective.
        """
        campaign_id = f"CAMP-{hashlib.sha256(objective.objective_id.encode()).hexdigest()[:8]}"
        
        # Determine sampling regime grids based on objective target regime
        if objective.target_regime == "HIGH_AOA_STALL":
            mach_grid = [0.15, 0.25, 0.35]
            aoa_grid = [10.0, 12.0, 14.0, 16.0, 18.0]
        elif objective.target_regime == "TRANSONIC":
            mach_grid = [0.55, 0.65, 0.72, 0.75]
            aoa_grid = [0.0, 2.0, 4.0, 6.0]
        else:  # General / Subsonic / Default
            mach_grid = [0.15, 0.30, 0.45, 0.60]
            aoa_grid = [-2.0, 0.0, 4.0, 8.0, 12.0, 16.0]

        target_geom = objective.target_geometries[0] if objective.target_geometries else "NACA 0012"

        # Generate candidates using ActiveLearning2Engine with cost awareness
        candidates = ActiveLearning2Engine.generate_candidates(
            geometry=target_geom,
            existing_points=existing_dataset_points,
            strategy=AcquisitionStrategy.COST_AWARE,
            mach_grid=mach_grid,
            aoa_grid=aoa_grid,
            max_candidates=max_cases * 2,
            cost_weight=0.25
        )

        planned_jobs: List[CFDJobSpec] = []
        cumulative_hours = 0.0
        est_unc_reduction = 0.0

        for cand in candidates:
            # Register in active learning candidate pool
            active_learning_registry.register_candidate(cand)

            if len(planned_jobs) >= max_cases:
                break
            if (cumulative_hours + cand.estimated_cost_hours) > max_cpu_budget_hours:
                continue

            # Construct CFDJobSpec
            job = ActiveLearning2Engine.convert_to_job_spec(
                candidate=cand,
                solver=preferred_solver,
                backend=ExecutionBackend.USER_EXECUTED
            )
            job.objective_id = objective.objective_id
            job.estimated_cost = EstimatedComputeCost(
                cpu_hours=cand.estimated_cost_hours,
                ram_mb=1024 if cand.flow_conditions.mach < 0.4 else 2048,
                complexity_class="MODERATE_2D" if cand.flow_conditions.mach < 0.4 else "COMPRESSIBLE_2D"
            )

            # Link candidate to job
            cand.associated_job_id = job.job_id
            planned_jobs.append(job)
            cumulative_hours += cand.estimated_cost_hours
            est_unc_reduction += (cand.estimated_uncertainty * 15.0)

        est_unc_reduction = min(60.0, round(est_unc_reduction, 1))

        return CampaignPlan(
            campaign_id=campaign_id,
            objective_id=objective.objective_id,
            title=f"Campaign for: {objective.title}",
            candidate_jobs=planned_jobs,
            total_estimated_cpu_hours=round(cumulative_hours, 2),
            expected_uncertainty_reduction_pct=est_unc_reduction,
            human_approval_required=True,
            status="PROPOSED"
        )
