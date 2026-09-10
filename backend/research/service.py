"""
AASI Autonomous Research Loop Service.

Orchestrates objectives, simulation campaigns, notebooks, and model lifecycle.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json
import os

from backend.research.models import (
    ResearchObjective,
    ObjectiveStatus,
    ResearchExperiment,
    ExperimentStatus,
    ResearchNotebook,
    NotebookCell,
    NotebookCellType,
)
from backend.research.simulation_planner import SimulationPlanner, CampaignPlan
from backend.research.retraining import RetrainingOrchestrator, RetrainingSummary
from backend.research.report_generator import ScientificReportGenerator
from backend.datasets.versioning import dataset_version_manager
from backend.multifidelity.service import multi_fidelity_service


class ResearchLoopService:
    """Singleton service managing research loops and computational campaigns."""

    def __init__(self, storage_dir: str = "data/research"):
        self.storage_dir = storage_dir
        self.objectives: Dict[str, ResearchObjective] = {}
        self.experiments: Dict[str, ResearchExperiment] = {}
        self.notebooks: Dict[str, ResearchNotebook] = {}
        self.campaigns: Dict[str, CampaignPlan] = {}
        os.makedirs(self.storage_dir, exist_ok=True)
        self._init_defaults()

    def _init_defaults(self) -> None:
        """Seed foundational aerospace research objectives."""
        obj1 = ResearchObjective(
            objective_id="OBJ-AERO-001",
            title="High-Angle-of-Attack Post-Stall Lift Uncertainty Reduction",
            description="Characterize epistemic variance in nonlinear stall regime (AoA 12° to 18°) for NACA 0012.",
            target_geometries=["NACA 0012"],
            target_regime="HIGH_AOA_STALL",
            target_uncertainty_threshold=0.035,
            status=ObjectiveStatus.ACTIVE,
            priority=8.5
        )
        obj2 = ResearchObjective(
            objective_id="OBJ-AERO-002",
            title="Transonic Drag Divergence Boundary Mapping",
            description="Acquire targeted compressible CFD data near Mach 0.65-0.75 to map wave drag rise.",
            target_geometries=["NACA 0012", "NACA 2412"],
            target_regime="TRANSONIC",
            target_uncertainty_threshold=0.025,
            status=ObjectiveStatus.ACTIVE,
            priority=9.0
        )
        self.objectives[obj1.objective_id] = obj1
        self.objectives[obj2.objective_id] = obj2

        # Create a default research notebook
        nb = ResearchNotebook(
            notebook_id="NB-RESEARCH-001",
            title="Autonomous Stall Exploration & Multi-Fidelity Synthesis",
            objective_id=obj1.objective_id,
            cells=[
                NotebookCell(
                    cell_id="cell-1",
                    cell_type=NotebookCellType.MARKDOWN,
                    content="# Autonomous Research Notebook: Stall Investigation\nExamining active learning recommendations."
                ),
                NotebookCell(
                    cell_id="cell-2",
                    cell_type=NotebookCellType.OBSERVATION,
                    content="Epistemic uncertainty surges from 0.015 at AoA 4° to 0.082 at AoA 16° due to separation onset."
                )
            ]
        )
        self.notebooks[nb.notebook_id] = nb

    def list_objectives(self) -> List[ResearchObjective]:
        return list(self.objectives.values())

    def create_objective(self, objective: ResearchObjective) -> ResearchObjective:
        self.objectives[objective.objective_id] = objective
        return objective

    def plan_campaign(self, objective_id: str, max_cases: int = 5) -> Optional[CampaignPlan]:
        obj = self.objectives.get(objective_id)
        if not obj:
            return None

        # Fetch training points from multi-fidelity registry
        raw_recs = multi_fidelity_service.query()
        pts = [{"mach": r.conditions.mach, "aoa": r.conditions.aoa_deg, "reynolds": r.conditions.reynolds} for r in raw_recs[:100]]

        campaign = SimulationPlanner.plan_campaign_for_objective(
            objective=obj,
            existing_dataset_points=pts,
            max_cases=max_cases
        )
        self.campaigns[campaign.campaign_id] = campaign

        # Create associated experiment
        exp = ResearchExperiment(
            experiment_id=f"EXP-{campaign.campaign_id}",
            objective_id=obj.objective_id,
            title=f"Execution for {campaign.title}",
            description=f"Automated simulation campaign containing {len(campaign.candidate_jobs)} jobs.",
            job_specs=campaign.candidate_jobs,
            status=ExperimentStatus.PLANNED,
            total_jobs=len(campaign.candidate_jobs),
            completed_jobs=0
        )
        self.experiments[exp.experiment_id] = exp
        return campaign

    def list_campaigns(self) -> List[CampaignPlan]:
        return list(self.campaigns.values())

    def list_experiments(self) -> List[ResearchExperiment]:
        return list(self.experiments.values())

    def get_notebook(self, notebook_id: str) -> Optional[ResearchNotebook]:
        return self.notebooks.get(notebook_id)

    def trigger_retraining(self, dataset_version: str = "AERO-AIRFOIL-V2.0", epochs: int = 5) -> RetrainingSummary:
        """Executes retraining and returns evaluation & promotion summary."""
        return RetrainingOrchestrator.execute_retraining_loop(
            dataset_version_id=dataset_version,
            epochs=epochs
        )

    def export_report(self, objective_id: str, format_type: str = "markdown") -> str:
        obj = self.objectives.get(objective_id)
        if not obj:
            return "# Objective Not Found"

        # Find matching experiment if any
        matching_exp = next((e for e in self.experiments.values() if e.objective_id == objective_id), None)
        if format_type.lower() == "latex":
            return ScientificReportGenerator.generate_latex_report(obj)
        return ScientificReportGenerator.generate_markdown_report(obj, experiment=matching_exp)


# Global singleton service
research_loop_service = ResearchLoopService()
