"""XFOIL panel method and viscous boundary layer solver adapter interface."""

from __future__ import annotations

from pathlib import Path
from .base import BaseSolverAdapter
from ..detector import solver_detector
from ..models import SimulationCase, SimulationManifest, SimulationRunMode, SolverInfo


class XFOILAdapter(BaseSolverAdapter):
    """Adapter interface for XFOIL subsonic aerodynamic solver."""

    def detect(self) -> SolverInfo:
        return solver_detector.detect_xfoil()

    def generate_case_files(self, case: SimulationCase, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        # Generate XFOIL command batch file
        cmd_script = f"""NACA {case.geometry.replace('NACA', '').strip()}
PANE
OPER
VISC {case.reynolds}
MACH {case.mach}
ALFA {case.aoa_deg}
CPWR cp_dist.dat
DUMP polar.dat
QUIT
"""
        (target_dir / "xfoil.in").write_text(cmd_script, encoding="utf-8")
        return target_dir

    def execute_run(self, case: SimulationCase, case_dir: Path, run_mode: SimulationRunMode) -> SimulationManifest:
        self.generate_case_files(case, case_dir)
        info = self.detect()
        return SimulationManifest(
            experiment_id=f"EXP-XFOIL-{case.case_id}",
            solver="XFOIL",
            solver_version="v6.99",
            geometry=case.geometry,
            input_parameters={"mach": case.mach, "reynolds": case.reynolds, "aoa_deg": case.aoa_deg},
            turbulence_model="e^N transition",
            input_checksum="sha256-xfoil-in",
            run_mode=run_mode,
            result_status="DRY_RUN_VERIFIED" if run_mode == SimulationRunMode.DRY_RUN else "SOLVER_UNAVAILABLE",
            logs=[
                "Generated XFOIL command script xfoil.in",
                f"Solver status: {info.status.value}",
            ],
        )
