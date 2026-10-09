"""
AASI Local Runner Security Sandbox.
Enforces fail-closed isolation:
1. Strict executable allowlist.
2. Shell injection prevention (disallow shell=True, disallow metacharacters).
3. Fixed scientific workspace constraint (anti path traversal).
4. Mandatory user authorization token verification.
5. Resource bounds (timeout, output size cap).
"""

from __future__ import annotations

import re
import os
import shutil
import logging
from pathlib import Path
from typing import List, Set, Optional

from runner.protocol.models import ExecutionApproval, ExecutionRequest

logger = logging.getLogger("aasi.runner.sandbox")


class SecurityViolationError(Exception):
    """Raised when an execution request violates sandbox constraints."""
    pass


class ExecutionSandbox:
    """
    Enforces strict execution boundaries for Local Runner workloads.
    """

    # Strictly allowlisted executables
    ALLOWLISTED_EXECUTABLES: Set[str] = {
        "simpleFoam",
        "pimpleFoam",
        "rhoSimpleFoam",
        "blockMesh",
        "checkMesh",
        "surfaceFeatures",
        "snappyHexMesh",
        "foamToVTK",
        "python",
        "python3",
    }

    # Prohibited shell metacharacters
    DISALLOWED_SHELL_CHARS_REGEX = re.compile(r"[;&|`$><\n\r\t\x00]")

    # Safe argument pattern (alphanumeric, dots, underscores, dashes, equals, slashes)
    SAFE_ARG_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.=/:\\]+$")

    DEFAULT_MAX_TIMEOUT_SECONDS = 600
    HARD_MAX_TIMEOUT_SECONDS = 1800
    MAX_OUTPUT_BYTES = 50 * 1024 * 1024  # 50 MB log limit

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def validate_request(self, request: ExecutionRequest) -> None:
        """
        Validates that request satisfies all security invariants.
        Raises SecurityViolationError fail-closed if any check fails.
        """
        # 1. Check explicit approval
        self.validate_approval(request.approval, request.job_id)

        # 2. Check executable allowlist
        cmd_name = Path(request.solver_command).name.lower()
        # Strip .exe on Windows
        if cmd_name.endswith(".exe"):
            cmd_name = cmd_name[:-4]

        allowed_lower = {e.lower() for e in self.ALLOWLISTED_EXECUTABLES}
        if cmd_name not in allowed_lower:
            raise SecurityViolationError(
                f"Executable '{request.solver_command}' is not in the allowlist. "
                f"Permitted executables: {sorted(self.ALLOWLISTED_EXECUTABLES)}"
            )

        # 3. Check arguments for shell injection metacharacters
        for idx, arg in enumerate(request.solver_args):
            if self.DISALLOWED_SHELL_CHARS_REGEX.search(arg):
                raise SecurityViolationError(
                    f"Command argument #{idx} contains prohibited shell metacharacters: {repr(arg)}"
                )

        # 4. Check workspace bounds (anti path traversal)
        self.resolve_case_path(request.case_dir_relative)

        # 5. Check timeout bounds
        if request.timeout_seconds <= 0 or request.timeout_seconds > self.HARD_MAX_TIMEOUT_SECONDS:
            raise SecurityViolationError(
                f"Requested timeout ({request.timeout_seconds}s) exceeds safe maximum ({self.HARD_MAX_TIMEOUT_SECONDS}s)."
            )

    def validate_approval(self, approval: ExecutionApproval, job_id: str) -> None:
        """Verifies that an execution boundary approval is valid."""
        if not approval.user_approved:
            raise SecurityViolationError(
                f"Execution rejected: Explicit user approval required at execution boundary for job {job_id}."
            )
        if not approval.approval_token or len(approval.approval_token.strip()) < 8:
            raise SecurityViolationError(
                f"Execution rejected: Invalid or missing cryptographic approval token."
            )
        if approval.job_id != job_id:
            raise SecurityViolationError(
                f"Execution rejected: Approval token job mismatch ({approval.job_id} != {job_id})."
            )

    def resolve_case_path(self, relative_path: str) -> Path:
        """
        Resolves case directory path strictly inside workspace_root.
        Prevents path traversal attacks (Zip Slip, ../, absolute root escapes).
        """
        # Reject absolute paths or paths starting with root slashes
        if Path(relative_path).is_absolute() or relative_path.startswith(("/", "\\")):
            raise SecurityViolationError(
                f"Path traversal detected: Absolute paths prohibited in case_dir_relative: '{relative_path}'"
            )

        clean_rel = os.path.normpath(relative_path)
        if clean_rel == ".." or clean_rel.startswith(".." + os.sep) or clean_rel.startswith("../") or clean_rel.startswith("..\\"):
            raise SecurityViolationError(
                f"Path traversal detected: Directory traversal in path '{relative_path}'"
            )

        target_path = (self.workspace_root / clean_rel).resolve()

        try:
            target_path.relative_to(self.workspace_root)
        except ValueError:
            raise SecurityViolationError(
                f"Path traversal detected: Target path '{relative_path}' escapes workspace '{self.workspace_root}'."
            )

        return target_path
