"""
AASI Local Runner OpenFOAM Executor.
Executes allowlisted solvers inside the sandbox, captures logs, measures duration,
and builds structured artifact receipts with SHA-256 hashes.
"""

from __future__ import annotations

import os
import time
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from runner.protocol.models import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ExecutionArtifact,
)
from runner.sandbox.security import ExecutionSandbox, SecurityViolationError

logger = logging.getLogger("aasi.runner.executors.openfoam")


def hash_file_sha256(filepath: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class OpenFOAMExecutor:
    """
    Executes CFD solvers in an isolated workspace under strict security guarantees.
    """

    def __init__(self, sandbox: ExecutionSandbox, runner_id: str):
        self.sandbox = sandbox
        self.runner_id = runner_id

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """
        Validates request and executes solver binary.
        Returns artifact-only ExecutionResult.
        """
        start_time = time.time()

        # 1. Security validation
        try:
            self.sandbox.validate_request(request)
        except SecurityViolationError as sec_err:
            logger.error("Security violation for job %s: %s", request.job_id, sec_err)
            return ExecutionResult(
                job_id=request.job_id,
                runner_id=self.runner_id,
                status=ExecutionStatus.REJECTED_SECURITY,
                exit_code=-1,
                duration_seconds=0.0,
                error_message=str(sec_err),
            )

        case_dir = self.sandbox.resolve_case_path(request.case_dir_relative)
        case_dir.mkdir(parents=True, exist_ok=True)

        # 2. Build sanitized command args
        cmd = [request.solver_command] + request.solver_args

        # 3. Execution under sandbox
        env = os.environ.copy()
        if request.environment_vars:
            # Only allow standard alphanumeric environment variables
            for k, v in request.environment_vars.items():
                if k.isidentifier():
                    env[k] = str(v)

        log_file = case_dir / f"log.{Path(request.solver_command).name}"
        stdout_tail = ""
        stderr_tail = ""
        exit_code = 0
        status = ExecutionStatus.RUNNING

        try:
            with open(log_file, "w", encoding="utf-8", errors="ignore") as log_f:
                proc = subprocess.Popen(
                    cmd,
                    cwd=case_dir,
                    shell=False,  # STRICT: shell=False prevents command chaining/injection
                    stdout=log_f,
                    stderr=subprocess.PIPE,
                    env=env,
                )

                try:
                    _, stderr_bytes = proc.communicate(timeout=request.timeout_seconds)
                    exit_code = proc.returncode
                    stderr_tail = (stderr_bytes or b"").decode("utf-8", errors="ignore")[-2048:]
                    status = ExecutionStatus.COMPLETED if exit_code == 0 else ExecutionStatus.FAILED
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                    exit_code = -9
                    status = ExecutionStatus.TIMED_OUT
                    stderr_tail = f"Process killed after exceeding timeout of {request.timeout_seconds} seconds."

            # Read log tail
            if log_file.exists():
                text = log_file.read_text(encoding="utf-8", errors="ignore")
                stdout_tail = text[-4096:] if len(text) > 4096 else text

        except Exception as exc:
            logger.exception("Execution crashed for job %s: %s", request.job_id, exc)
            return ExecutionResult(
                job_id=request.job_id,
                runner_id=self.runner_id,
                status=ExecutionStatus.FAILED,
                exit_code=-1,
                duration_seconds=round(time.time() - start_time, 3),
                error_message=str(exc),
            )

        duration = round(time.time() - start_time, 3)

        # 4. Collect produced artifacts
        artifacts = self.collect_artifacts(case_dir)

        return ExecutionResult(
            job_id=request.job_id,
            runner_id=self.runner_id,
            status=status,
            exit_code=exit_code,
            duration_seconds=duration,
            stdout_tail=stdout_tail,
            stderr_tail=stderr_tail,
            artifacts=artifacts,
            error_message=None if status == ExecutionStatus.COMPLETED else (stderr_tail or f"Exit code {exit_code}"),
        )

    def collect_artifacts(self, case_dir: Path) -> List[ExecutionArtifact]:
        """Scans case directory and produces cryptographic artifact receipts."""
        artifacts: List[ExecutionArtifact] = []

        for p in case_dir.rglob("*"):
            if p.is_file():
                try:
                    size = p.stat().st_size
                    rel = p.relative_to(case_dir).as_posix()
                    # Skip massive binary files (>100MB) from in-memory hash if needed
                    h = hash_file_sha256(p)
                    artifacts.append(
                        ExecutionArtifact(
                            relative_path=rel,
                            file_size_bytes=size,
                            sha256_hash=h,
                        )
                    )
                except Exception as exc:
                    logger.debug("Failed to hash artifact %s: %s", p, exc)

        return artifacts
