"""
AASI Autonomous Scientific Research Loop Subsystem.

Coordinates active learning, campaign planning, retraining, benchmark verification,
model promotion, and scientific report compilation.
"""

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
from backend.research.benchmarks import FixedBenchmarkSuite, BenchmarkEvaluationResult
from backend.research.comparison import ModelComparisonEngine, ModelComparisonReport
from backend.research.promotion import ModelPromotionPipeline, ModelPromotionAudit, PromotionTier
from backend.research.retraining import RetrainingOrchestrator, RetrainingSummary
from backend.research.report_generator import ScientificReportGenerator
from backend.research.service import ResearchLoopService, research_loop_service

__all__ = [
    "ResearchObjective",
    "ObjectiveStatus",
    "ResearchExperiment",
    "ExperimentStatus",
    "ResearchNotebook",
    "NotebookCell",
    "NotebookCellType",
    "SimulationPlanner",
    "CampaignPlan",
    "FixedBenchmarkSuite",
    "BenchmarkEvaluationResult",
    "ModelComparisonEngine",
    "ModelComparisonReport",
    "ModelPromotionPipeline",
    "ModelPromotionAudit",
    "PromotionTier",
    "RetrainingOrchestrator",
    "RetrainingSummary",
    "ScientificReportGenerator",
    "ResearchLoopService",
    "research_loop_service",
]
