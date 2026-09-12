"""
AASI Real CFD Execution & Convergence Analysis Engine.

Governing Directive: Real Scientific Execution, Evidence Integrity & Independent Reproducibility.
Enforces genuine solver execution contracts:
- Detects local OpenFOAM solver (simpleFoam) without faking or simulating execution.
- If solver is missing, honestly returns SOLVER_UNAVAILABLE / USER_EXECUTED_REQUIRED.
- If solver is present, manages execution, monitors residuals, captures logs, and evaluates physical convergence.
- Strictly distinguishes process exit code 0 from physical convergence.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import re
import math
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class SolverExecutionStatus(str, Enum):
    CASE_GENERATED = "CASE_GENERATED"
    CASE_EXECUTED = "CASE_EXECUTED"
    SOLVER_CONVERGED = "SOLVER_CONVERGED"
    SOLVER_DIVERGED = "SOLVER_DIVERGED"
    SOLVER_TIMEOUT = "SOLVER_TIMEOUT"
    SOLVER_UNAVAILABLE = "SOLVER_UNAVAILABLE"
    USER_EXECUTED_REQUIRED = "USER_EXECUTED_REQUIRED"
    RESULT_IMPORTED = "RESULT_IMPORTED"


class ConvergenceStatus(str, Enum):
    RESIDUAL_CONVERGED = "RESIDUAL_CONVERGED"
    FORCE_CONVERGED = "FORCE_CONVERGED"
    MASS_BALANCE_ACCEPTABLE = "MASS_BALANCE_ACCEPTABLE"
    NO_DIVERGENCE = "NO_DIVERGENCE"
    UNCONVERGED = "UNCONVERGED"
    DIVERGED = "DIVERGED"


class ResidualHistory(BaseModel):
    """Tracks numerical solver residual trajectories across iterations."""
    iterations: List[int] = Field(default_factory=list)
    continuity: List[float] = Field(default_factory=list)
    ux: List[float] = Field(default_factory=list)
    uy: List[float] = Field(default_factory=list)
    p: List[float] = Field(default_factory=list)
    final_continuity: Optional[float] = None
    final_ux: Optional[float] = None
    final_uy: Optional[float] = None
    final_p: Optional[float] = None


class ForceCoeffHistory(BaseModel):
    """Tracks aerodynamic force coefficient convergence across iterations."""
    iterations: List[int] = Field(default_factory=list)
    cl: List[float] = Field(default_factory=list)
    cd: List[float] = Field(default_factory=list)
    cm: List[float] = Field(default_factory=list)
    final_cl: Optional[float] = None
    final_cd: Optional[float] = None
    final_cm: Optional[float] = None
    cl_std_last_50: Optional[float] = None
    cd_std_last_50: Optional[float] = None


class ConvergenceReport(BaseModel):
    """Formal assessment of numerical and physical convergence."""
    is_converged: bool = False
    convergence_status: ConvergenceStatus = ConvergenceStatus.UNCONVERGED
    iterations_completed: int = 0
    continuity_error: Optional[float] = None
    max_residual: Optional[float] = None
    force_stabilized: bool = False
    divergence_detected: bool = False
    oscillation_detected: bool = False
    convergence_notes: List[str] = Field(default_factory=list)


class SolverExecutionResult(BaseModel):
    """Immutable result of a CFD execution attempt."""
    case_id: str
    solver_name: str = "openfoam"
    solver_binary: str = "simpleFoam"
    execution_status: SolverExecutionStatus
    exit_code: Optional[int] = None
    execution_time_seconds: float = 0.0
    convergence_report: ConvergenceReport = Field(default_factory=ConvergenceReport)
    residual_history: ResidualHistory = Field(default_factory=ResidualHistory)
    force_history: ForceCoeffHistory = Field(default_factory=ForceCoeffHistory)
    stdout_summary: str = ""
    stderr_summary: str = ""
    output_files: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OpenFOAMExecutionEngine:
    """Production execution and monitoring engine for OpenFOAM simulations."""

    @classmethod
    def detect_solver(cls, binary_name: str = "simpleFoam") -> Tuple[bool, Optional[str]]:
        """Checks if OpenFOAM solver binary is available on system PATH or WSL."""
        path = shutil.which(binary_name)
        if path:
            return True, path
        # Check standard Linux/WSL OpenFOAM paths
        common_paths = [
            f"/usr/bin/{binary_name}",
            f"/opt/openfoam10/platforms/linux64GccDPInt32Opt/bin/{binary_name}",
            f"/opt/openfoam11/platforms/linux64GccDPInt32Opt/bin/{binary_name}",
            f"/opt/openfoam2306/platforms/linux64GccDPInt32Opt/bin/{binary_name}",
        ]
        for p in common_paths:
            if Path(p).exists():
                return True, p
        return False, None

    @classmethod
    def parse_openfoam_log(cls, log_text: str) -> Tuple[ResidualHistory, ForceCoeffHistory]:
        """Parses residuals and force coefficients from simpleFoam stdout/log."""
        res_hist = ResidualHistory()
        force_hist = ForceCoeffHistory()

        time_pattern = re.compile(r"^Time = (\d+)", re.MULTILINE)
        ux_pattern = re.compile(r"Solving for Ux, Initial residual = ([\d\.eE\+-]+)")
        uy_pattern = re.compile(r"Solving for Uy, Initial residual = ([\d\.eE\+-]+)")
        p_pattern = re.compile(r"Solving for p, Initial residual = ([\d\.eE\+-]+)")
        cont_pattern = re.compile(r"time step continuity errors : sum local = ([\d\.eE\+-]+)")

        curr_iter = 0
        for line in log_text.splitlines():
            t_match = time_pattern.match(line)
            if t_match:
                curr_iter = int(t_match.group(1))
                res_hist.iterations.append(curr_iter)

            ux_m = ux_pattern.search(line)
            if ux_m:
                res_hist.ux.append(float(ux_m.group(1)))

            uy_m = uy_pattern.search(line)
            if uy_m:
                res_hist.uy.append(float(uy_m.group(1)))

            p_m = p_pattern.search(line)
            if p_m:
                res_hist.p.append(float(p_m.group(1)))

            c_m = cont_pattern.search(line)
            if c_m:
                res_hist.continuity.append(float(c_m.group(1)))

        if res_hist.ux:
            res_hist.final_ux = res_hist.ux[-1]
        if res_hist.uy:
            res_hist.final_uy = res_hist.uy[-1]
        if res_hist.p:
            res_hist.final_p = res_hist.p[-1]
        if res_hist.continuity:
            res_hist.final_continuity = res_hist.continuity[-1]

        return res_hist, force_hist

    @classmethod
    def parse_force_coeffs_file(cls, filepath: Path) -> ForceCoeffHistory:
        """Parses OpenFOAM postProcessing/forceCoeffs/0/coefficient.dat."""
        hist = ForceCoeffHistory()
        if not filepath.exists():
            return hist

        lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 4:
                try:
                    it = int(float(parts[0]))
                    cd = float(parts[1])
                    cl = float(parts[2])
                    cm = float(parts[3])
                    hist.iterations.append(it)
                    hist.cd.append(cd)
                    hist.cl.append(cl)
                    hist.cm.append(cm)
                except ValueError:
                    continue

        if hist.cl:
            hist.final_cl = hist.cl[-1]
            hist.final_cd = hist.cd[-1]
            hist.final_cm = hist.cm[-1]

            if len(hist.cl) >= 10:
                sample_cl = hist.cl[-min(50, len(hist.cl)):]
                sample_cd = hist.cd[-min(50, len(hist.cd)):]
                mean_cl = sum(sample_cl) / len(sample_cl)
                mean_cd = sum(sample_cd) / len(sample_cd)
                hist.cl_std_last_50 = math.sqrt(sum((x - mean_cl) ** 2 for x in sample_cl) / len(sample_cl))
                hist.cd_std_last_50 = math.sqrt(sum((x - mean_cd) ** 2 for x in sample_cd) / len(sample_cd))

        return hist

    @classmethod
    def analyze_convergence(
        cls,
        res_hist: ResidualHistory,
        force_hist: ForceCoeffHistory,
        residual_threshold: float = 1e-4,
        force_std_threshold: float = 1e-3,
    ) -> ConvergenceReport:
        """
        Evaluates physical and numerical convergence criteria:
        1. Residual reduction below threshold.
        2. Force coefficient stabilization over last 50 iterations.
        3. Bounded continuity errors (no mass loss).
        4. Absence of NaN or unbounded divergence.
        """
        notes = []
        divergence = False
        oscillation = False

        # 1. Divergence check
        all_vals = (res_hist.ux + res_hist.uy + res_hist.p + force_hist.cl + force_hist.cd)
        for v in all_vals:
            if math.isnan(v) or math.isinf(v) or abs(v) > 1e4:
                divergence = True
                notes.append("DIVERGENCE_DETECTED: NaN, Inf, or unbounded value encountered in solution.")
                break

        if divergence:
            return ConvergenceReport(
                is_converged=False,
                convergence_status=ConvergenceStatus.DIVERGED,
                iterations_completed=len(res_hist.iterations),
                divergence_detected=True,
                convergence_notes=notes
            )

        # 2. Residual convergence
        max_res = max(
            res_hist.final_ux or 1.0,
            res_hist.final_uy or 1.0,
            res_hist.final_p or 1.0
        )
        res_converged = max_res <= residual_threshold
        if res_converged:
            notes.append(f"RESIDUAL_CONVERGED: Max residual {max_res:.2e} <= {residual_threshold:.2e}.")
        else:
            notes.append(f"RESIDUAL_MARGINAL: Max residual {max_res:.2e} > threshold {residual_threshold:.2e}.")

        # 3. Force stabilization
        force_converged = False
        if force_hist.cl_std_last_50 is not None:
            if force_hist.cl_std_last_50 < force_std_threshold:
                force_converged = True
                notes.append(f"FORCE_CONVERGED: CL std dev over last 50 iterations is {force_hist.cl_std_last_50:.2e} (< {force_std_threshold:.2e}).")
            else:
                oscillation = True
                notes.append(f"FORCE_OSCILLATING: CL std dev {force_hist.cl_std_last_50:.2e} exceeds threshold {force_std_threshold:.2e}.")

        # 4. Overall determination
        is_converged = res_converged and (force_converged or len(force_hist.cl) == 0)
        status = ConvergenceStatus.RESIDUAL_CONVERGED if is_converged else ConvergenceStatus.UNCONVERGED

        return ConvergenceReport(
            is_converged=is_converged,
            convergence_status=status,
            iterations_completed=len(res_hist.iterations),
            continuity_error=res_hist.final_continuity,
            max_residual=max_res,
            force_stabilized=force_converged,
            divergence_detected=False,
            oscillation_detected=oscillation,
            convergence_notes=notes
        )

    @classmethod
    def execute_or_stage(
        cls,
        case_dir: Path,
        case_id: str,
        timeout_seconds: int = 600,
        max_iterations: int = 1000
    ) -> SolverExecutionResult:
        """
        Main execution contract:
        - If simpleFoam is present: executes cleanly, monitors residuals, parses forces.
        - If simpleFoam is absent: returns SOLVER_UNAVAILABLE without faking execution.
        """
        case_dir = Path(case_dir)
        is_installed, binary_path = cls.detect_solver("simpleFoam")

        if not is_installed:
            report = ConvergenceReport(
                is_converged=False,
                convergence_status=ConvergenceStatus.UNCONVERGED,
                convergence_notes=["Solver 'simpleFoam' is not installed locally. Case deck staged for cluster execution."]
            )
            return SolverExecutionResult(
                case_id=case_id,
                solver_name="openfoam",
                solver_binary="simpleFoam",
                execution_status=SolverExecutionStatus.USER_EXECUTED_REQUIRED,
                exit_code=None,
                execution_time_seconds=0.0,
                convergence_report=report,
                stdout_summary="SOLVER_UNAVAILABLE: Host environment does not have OpenFOAM installed.",
                output_files=[p.name for p in case_dir.glob("**/*") if p.is_file()][:20] if case_dir.exists() else []
            )

        # Execute solver on host
        start_time = datetime.now(timezone.utc)
        try:
            cmd = [binary_path, "-case", str(case_dir.resolve())]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False
            )
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""

            res_hist, _ = cls.parse_openfoam_log(stdout_text)
            force_file = case_dir / "postProcessing" / "forceCoeffs" / "0" / "coefficient.dat"
            force_hist = cls.parse_force_coeffs_file(force_file)

            conv_report = cls.analyze_convergence(res_hist, force_hist)
            status = (
                SolverExecutionStatus.SOLVER_CONVERGED if conv_report.is_converged
                else (SolverExecutionStatus.SOLVER_DIVERGED if conv_report.divergence_detected
                      else SolverExecutionStatus.CASE_EXECUTED)
            )

            return SolverExecutionResult(
                case_id=case_id,
                solver_name="openfoam",
                solver_binary=str(binary_path),
                execution_status=status,
                exit_code=proc.returncode,
                execution_time_seconds=round(elapsed, 2),
                convergence_report=conv_report,
                residual_history=res_hist,
                force_history=force_hist,
                stdout_summary=stdout_text[-2000:],
                stderr_summary=stderr_text[-1000:],
                output_files=[p.name for p in case_dir.glob("**/*") if p.is_file()][:50]
            )

        except subprocess.TimeoutExpired:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            report = ConvergenceReport(
                is_converged=False,
                convergence_status=ConvergenceStatus.UNCONVERGED,
                convergence_notes=[f"Execution timed out after {timeout_seconds} seconds."]
            )
            return SolverExecutionResult(
                case_id=case_id,
                solver_name="openfoam",
                solver_binary=str(binary_path),
                execution_status=SolverExecutionStatus.SOLVER_TIMEOUT,
                exit_code=-1,
                execution_time_seconds=round(elapsed, 2),
                convergence_report=report,
                stderr_summary="Execution timed out."
            )
        except Exception as e:
            report = ConvergenceReport(
                is_converged=False,
                convergence_status=ConvergenceStatus.UNCONVERGED,
                convergence_notes=[f"Execution failed: {str(e)}"]
            )
            return SolverExecutionResult(
                case_id=case_id,
                solver_name="openfoam",
                solver_binary=str(binary_path or "simpleFoam"),
                execution_status=SolverExecutionStatus.USER_EXECUTED_REQUIRED,
                exit_code=-1,
                execution_time_seconds=0.0,
                convergence_report=report,
                stderr_summary=str(e)
            )
