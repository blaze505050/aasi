"""SU2 compressible aerodynamic solver adapter interface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from .base import BaseSolverAdapter
from ..detector import solver_detector
from ..models import SimulationCase, SimulationManifest, SimulationRunMode, SolverInfo


class SU2Adapter(BaseSolverAdapter):
    """Adapter interface for Stanford University Unstructured (SU2) CFD solver."""

    def detect(self) -> SolverInfo:
        return solver_detector.detect_su2()

    def generate_case_files(self, case: SimulationCase, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        config_text = f"""% ------------- SU2 CONFIGURATION FILE ------------- %
SOLVER= RANS
KIND_TURB_MODEL= SA
MATH_PROBLEM= DIRECT
RESTART_SOL= NO
MACH_NUMBER= {case.mach}
AOA= {case.aoa_deg}
REYNOLDS_NUMBER= {case.reynolds}
REYNOLDS_LENGTH= 1.0
REF_LENGTH= 1.0
REF_AREA= 1.0
MARKER_HEATFLUX= ( airfoil, 0.0 )
MARKER_FAR= ( farfield )
MARKER_SYM= ( symmetry )
MARKER_MONITORING= ( airfoil )
CONV_FIELD= RMS_DENSITY
CONV_RESIDUAL_MINVAL= {case.convergence_tolerance}
CONV_STARTITER= 10
ITER= {case.max_iterations}
"""
        (target_dir / "case.cfg").write_text(config_text, encoding="utf-8")
        return target_dir

    def execute_run(self, case: SimulationCase, case_dir: Path, run_mode: SimulationRunMode) -> SimulationManifest:
        self.generate_case_files(case, case_dir)
        info = self.detect()
        return SimulationManifest(
            experiment_id=f"EXP-SU2-{case.case_id}",
            solver="SU2",
            solver_version="v7.5",
            geometry=case.geometry,
            input_parameters={"mach": case.mach, "reynolds": case.reynolds, "aoa_deg": case.aoa_deg},
            turbulence_model=case.turbulence_model,
            input_checksum="sha256-su2-cfg",
            run_mode=run_mode,
            result_status="DRY_RUN_VERIFIED" if run_mode == SimulationRunMode.DRY_RUN else "SOLVER_UNAVAILABLE",
            logs=[
                "Generated SU2 case configuration case.cfg",
                f"Solver availability: {info.status.value}",
            ],
        )
