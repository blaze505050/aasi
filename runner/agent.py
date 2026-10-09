"""
AASI Local Runner Agent.
Encapsulates host detection, sandbox enforcement, and solver execution.
Can run as a standalone process or be invoked as an authenticated local service.
"""

from __future__ import annotations

import os
import uuid
import logging
from pathlib import Path
from typing import Optional

from runner.protocol.models import (
    RunnerCapabilities,
    RunnerRegistration,
    ExecutionRequest,
    ExecutionResult,
)
from runner.detector.capabilities import HostCapabilityDetector
from runner.sandbox.security import ExecutionSandbox
from runner.executors.openfoam import OpenFOAMExecutor

logger = logging.getLogger("aasi.runner.agent")


class LocalRunnerAgent:
    """
    Explicitly installed AASI Local Runner instance.
    """

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        runner_id: Optional[str] = None,
        auth_token: Optional[str] = None,
    ):
        self.workspace_root = (workspace_root or Path("./aasi_runner_workspace")).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        self.runner_id = runner_id or f"RUNNER-{uuid.uuid4().hex[:12].upper()}"
        self.auth_token = auth_token or f"tok_{uuid.uuid4().hex}"

        # Initialize detector, sandbox, executor
        self.capabilities: RunnerCapabilities = HostCapabilityDetector.detect(runner_id=self.runner_id)
        self.sandbox = ExecutionSandbox(workspace_root=self.workspace_root)
        self.executor = OpenFOAMExecutor(sandbox=self.sandbox, runner_id=self.runner_id)

        logger.info("AASI Local Runner %s initialized in workspace %s", self.runner_id, self.workspace_root)

    def get_capabilities(self, refresh: bool = False) -> RunnerCapabilities:
        """Returns the current workstation capability matrix."""
        if refresh:
            self.capabilities = HostCapabilityDetector.detect(runner_id=self.runner_id)
        return self.capabilities

    def get_registration_payload(self) -> RunnerRegistration:
        """Creates registration handshake payload for FastAPI control plane."""
        return RunnerRegistration(
            runner_id=self.runner_id,
            auth_token=self.auth_token,
            workspace_path=str(self.workspace_root),
            capabilities=self.get_capabilities(),
        )

    def execute_job(self, request: ExecutionRequest) -> ExecutionResult:
        """
        Executes a job under sandbox validation and returns structured artifacts.
        """
        logger.info("Executing job %s (command: %s)", request.job_id, request.solver_command)
        return self.executor.execute(request)
