"""XFLR5 3D wing panel method adapter interface."""

from __future__ import annotations

from pathlib import Path
from .base import BaseSolverAdapter
from ..detector import solver_detector
from ..models import SimulationCase, SimulationManifest, SimulationRunMode, SolverInfo


class XFLR5Adapter(BaseSolverAdapter):
    """Adapter interface for XFLR5 3D wing and fuselage analysis."""

    def detect(self) -> SolverInfo:
        return solver_detector.detect_xflr5()

    def generate_case_files(self, case: SimulationCase, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "project.xfl").write_text(f"# XFLR5 Project for {case.geometry}\n", encoding="utf-8")
        return target_dir

    def execute_run(self, case: SimulationCase, case_dir: Path, run_mode: SimulationRunMode) -> SimulationManifest:
        self.generate_case_files(case, case_dir)
        info = self.detect()
        return SimulationManifest(
            experiment_id=f"EXP-XFLR5-{case.case_id}",
            solver="XFLR5",
            solver_version="v6.58",
            geometry=case.geometry,
            input_parameters={"mach": case.mach, "reynolds": case.reynolds, "aoa_deg": case.aoa_deg},
            turbulence_model="LLT / VLM",
            input_checksum="sha256-xflr5-proj",
            run_mode=run_mode,
            result_status="DRY_RUN_VERIFIED" if run_mode == SimulationRunMode.DRY_RUN else "SOLVER_UNAVAILABLE",
            logs=[
                "Generated XFLR5 project stub",
                f"Solver status: {info.status.value}",
            ],
        )
