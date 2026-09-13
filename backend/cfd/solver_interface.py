"""
AASI Phase 21: Real CFD Solver Interface and Abstraction Layer.
Governing Rule: Absolute Anti-Fabrication Rule.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class SolverMode(str, Enum):
    MODE_A_NATIVE_LINUX = "NATIVE_LINUX"
    MODE_B_WSL2 = "WSL2"
    MODE_C_DOCKER = "DOCKER"
    MODE_D_REMOTE = "REMOTE_WORKER"
    MODE_E_NO_SOLVER = "NO_SOLVER"


class ConvergenceState(str, Enum):
    CONVERGED = "CONVERGED"
    UNCONVERGED = "UNCONVERGED"
    CONVERGENCE_NOT_ESTABLISHED = "CONVERGENCE_NOT_ESTABLISHED"
    DIVERGED = "DIVERGED"
    SOLVER_FAILED = "SOLVER_FAILED"
    NOT_RUN = "NOT_RUN"


class PhysicalValidationState(str, Enum):
    PHYSICALLY_VALID = "PHYSICALLY_VALID"
    PHYSICS_GATE_FAILED = "PHYSICS_GATE_FAILED"
    NUMERICAL_ERROR = "NUMERICAL_ERROR"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass
class CFDExecutionResult:
    run_id: str
    case_name: str
    case_dir: str
    solver_mode: SolverMode
    solver_name: str
    solver_version: str
    exit_code: Optional[int]
    status: str  # REAL_EXECUTED, USER_EXECUTED_REQUIRED, SOLVER_UNAVAILABLE
    convergence_state: ConvergenceState
    physical_state: PhysicalValidationState
    execution_time_sec: float
    residuals: Dict[str, List[float]] = field(default_factory=dict)
    forces: Dict[str, Any] = field(default_factory=dict)
    convergence_evidence: Dict[str, Any] = field(default_factory=dict)
    physical_checks: Dict[str, Any] = field(default_factory=dict)
    provenance_hash: str = ""
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "case_name": self.case_name,
            "case_dir": self.case_dir,
            "solver_mode": self.solver_mode.value,
            "solver_name": self.solver_name,
            "solver_version": self.solver_version,
            "exit_code": self.exit_code,
            "status": self.status,
            "convergence_state": self.convergence_state.value,
            "physical_state": self.physical_state.value,
            "execution_time_sec": self.execution_time_sec,
            "residuals": self.residuals,
            "forces": self.forces,
            "convergence_evidence": self.convergence_evidence,
            "physical_checks": self.physical_checks,
            "provenance_hash": self.provenance_hash,
            "error_message": self.error_message,
        }


class CFDSolverAdapter(ABC):
    """
    Abstract interface for physical fluid dynamics solvers.
    Must never fabricate convergence, residuals, or force coefficients.
    """

    @abstractmethod
    def probe_environment(self) -> Dict[str, Any]:
        """Probe host OS, PATH, WSL2, Docker, and remote workers."""
        pass

    @abstractmethod
    def prepare_case(
        self,
        case_name: str,
        airfoil_name: str,
        coordinates: List[List[float]],
        alpha_deg: float,
        reynolds: float,
        mach: float = 0.15,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Synthesize valid simulation case deck."""
        pass

    @abstractmethod
    def validate_case(self, case_dir: Path) -> Dict[str, Any]:
        """Verify dictionaries, boundary conditions, and meshes."""
        pass

    @abstractmethod
    def execute(self, case_dir: Path, timeout_sec: int = 600) -> CFDExecutionResult:
        """Execute simulation or return fail-closed degraded status."""
        pass

    @abstractmethod
    def parse_residuals(self, case_dir: Path) -> Dict[str, List[float]]:
        """Parse raw log files for residual histories."""
        pass

    @abstractmethod
    def parse_forces(self, case_dir: Path) -> Dict[str, Any]:
        """Extract lift, drag, and moment coefficient histories."""
        pass

    @abstractmethod
    def check_convergence(
        self, residuals: Dict[str, List[float]], forces: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate mathematical and physical convergence criteria."""
        pass

    @abstractmethod
    def validate_physics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Independent physical sanity checks on forces and pressures."""
        pass

    @abstractmethod
    def hash_case_provenance(self, case_dir: Path) -> str:
        """Cryptographic SHA-256 tree of input deck, mesh, and outputs."""
        pass
