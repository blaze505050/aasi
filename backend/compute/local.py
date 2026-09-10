"""
AASI Local Compute Backend.

Wraps local sandboxed simulation execution when local binaries are installed.
"""

from typing import Dict, Any
from backend.compute.models import ComputeRequest, ExecutionStatus
from backend.simulation.runner import SimulationRunner
from backend.simulation.detector import SolverDetector
from backend.simulation.models import SimulationCase, SimulationRunMode


class LocalComputeBackend:
    """Dispatches simulation cases to local sandboxed solvers when available."""

    def __init__(self):
        self.runner = SimulationRunner()
        self.detector = SolverDetector()

    def execute(self, request: ComputeRequest) -> Dict[str, Any]:
        """Runs case on local workstation if installed, else returns diagnostic."""
        solvers = self.detector.detect_all()
        target_solver = solvers.get(request.solver.lower())
        
        is_available = target_solver.available if target_solver else False
        if not is_available:
            return {
                "status": ExecutionStatus.FAILED.value,
                "reason": f"Solver '{request.solver}' is not installed locally on this host.",
                "diagnostic": target_solver.diagnostic if target_solver else "Unknown solver",
                "recommendation": "Use USER_EXECUTED backend to generate standalone aasi_case/ deck for external cluster execution."
            }

        sim_case = SimulationCase(
            case_id=request.case_id,
            geometry=request.geometry,
            solver=request.solver,
            mach=request.mach,
            reynolds=request.reynolds,
            aoa_deg=request.aoa_deg,
            turbulence_model=request.turbulence_model,
            mode=SimulationRunMode.FULL_RUN,
            parameters=request.mesh_parameters
        )

        manifest = self.runner.run(sim_case)
        return {
            "status": ExecutionStatus.COMPLETED.value if manifest.result_status == "SUCCESS" else ExecutionStatus.FAILED.value,
            "manifest": manifest.model_dump()
        }
