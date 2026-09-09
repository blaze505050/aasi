"""Base abstract adapter for computational solvers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from ..models import SimulationCase, SimulationManifest, SimulationRunMode, SolverInfo


class BaseSolverAdapter(ABC):
    """Abstract base class for solver execution adapters."""

    @abstractmethod
    def detect(self) -> SolverInfo:
        """Detect availability and status of solver on host system."""
        pass

    @abstractmethod
    def generate_case_files(self, case: SimulationCase, target_dir: Path) -> Path:
        """Generate solver configuration dictionaries, boundary files, and grid definitions."""
        pass

    @abstractmethod
    def execute_run(
        self,
        case: SimulationCase,
        case_dir: Path,
        run_mode: SimulationRunMode,
    ) -> SimulationManifest:
        """Execute simulation run under sandbox and return reproducible manifest."""
        pass
