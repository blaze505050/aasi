"""
AASI Autonomous Research Loop Models.

Defines ResearchObjective, Experiment, ResearchNotebook, and Campaign structures.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import hashlib

from backend.simulation.job_spec import CFDJobSpec


class ObjectiveStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SATISFIED = "SATISFIED"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class ExperimentStatus(str, Enum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    AWAITING_INGESTION = "AWAITING_INGESTION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ResearchObjective(BaseModel):
    """Scientific objective guiding autonomous simulation dispatch."""
    objective_id: str
    title: str
    description: str
    target_geometries: List[str] = Field(default_factory=list)
    target_regime: str = "TRANSONIC_STALL"  # SUBSONIC, TRANSONIC, HIGH_AOA_STALL, COMPRESSIBLE
    target_uncertainty_threshold: float = 0.05
    status: ObjectiveStatus = ObjectiveStatus.ACTIVE
    priority: float = Field(default=1.0, ge=0.0, le=10.0)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NotebookCellType(str, Enum):
    MARKDOWN = "MARKDOWN"
    CODE = "CODE"
    OBSERVATION = "OBSERVATION"
    CONCLUSION = "CONCLUSION"


class NotebookCell(BaseModel):
    cell_id: str
    cell_type: NotebookCellType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ResearchNotebook(BaseModel):
    """Reproducible computational notebook recording hypotheses, runs, and findings."""
    notebook_id: str
    title: str
    objective_id: Optional[str] = None
    cells: List[NotebookCell] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ResearchExperiment(BaseModel):
    """An experiment executing a campaign of simulations for an objective."""
    experiment_id: str
    objective_id: str
    title: str
    description: str
    job_specs: List[CFDJobSpec] = Field(default_factory=list)
    status: ExperimentStatus = ExperimentStatus.PLANNED
    completed_jobs: int = 0
    total_jobs: int = 0
    findings_summary: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
