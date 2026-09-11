"""Simulation execution runner coordinating case setup, sandbox invocation, and manifest archiving."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional
from .artifacts import SimulationArtifactManager
from .models import SimulationCase, SimulationManifest, SimulationRunMode
from .registry import solver_registry

logger = logging.getLogger(__name__)


class SimulationRunner:
    """Coordinates execution of scientific simulation cases across supported solver adapters."""

    def __init__(self, artifact_manager: Optional[SimulationArtifactManager] = None):
        self.artifact_manager = artifact_manager or SimulationArtifactManager()

    def run_case(self, case: SimulationCase) -> SimulationManifest:
        """Set up and execute simulation case in requested run mode."""
        adapter = solver_registry.get_adapter(case.solver)
        if not adapter:
            raise ValueError(f"Solver '{case.solver}' is not supported. Choose from OpenFOAM, SU2, XFOIL, XFLR5.")

        case_dir = self.artifact_manager.prepare_case_directory(case)
        logger.info(
            "Executing simulation case '%s' using solver '%s' in mode '%s' at %s",
            case.case_id,
            case.solver,
            case.run_mode.value,
            case_dir,
        )

        manifest = adapter.execute_run(case=case, case_dir=case_dir, run_mode=case.run_mode)
        return manifest

    # Backward-compatible alias
    run = run_case


# Default simulation runner singleton
simulation_runner = SimulationRunner()
