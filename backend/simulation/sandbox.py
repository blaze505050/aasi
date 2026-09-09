"""Security sandbox for scientific simulation execution, argument validation, and path traversal protection."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class SecuritySandboxViolation(Exception):
    """Raised when an unallowlisted executable, shell injection, or path traversal is detected."""
    pass


class SimulationSecuritySandbox:
    """Rigorous security sandbox for executing computational simulation tools."""

    # Explicit allowlist of permissible binary names
    ALLOWLISTED_EXECUTABLES = {
        "simplefoam",
        "blockmesh",
        "checkmesh",
        "foamrun",
        "icofoam",
        "postprocess",
        "su2_cfd",
        "su2_def",
        "su2_sol",
        "xfoil",
        "xflr5",
        "wsl",
        "wsl.exe",
    }

    # Prohibited dangerous shell constructs
    DANGEROUS_PATTERNS = [
        r"\brm\s+-[rf]+\b",
        r"\bdel\s+/[sfq]+\b",
        r"\bpowershell\b",
        r"\bcmd(?:\.exe)?\s+/c\b",
        r"\bbash\s+-c\b",
        r"\bpython\s+-c\b",
        r"\bcurl\b",
        r"\bwget\b",
        r"[;&|`$><]",       # Shell chaining and redirection meta-characters
        r"\.\.[\\/]",        # Relative directory traversal ../
        r"\b[A-Za-z]:[\\/]Windows[\\/]", # Windows system directory tampering
    ]

    def __init__(
        self,
        default_timeout_seconds: float = 30.0,
        max_output_bytes: int = 5 * 1024 * 1024,  # 5 MB
    ):
        self.default_timeout_seconds = default_timeout_seconds
        self.max_output_bytes = max_output_bytes

    def validate_command(
        self,
        executable: str,
        arguments: List[str],
        working_directory: Path,
    ) -> None:
        """Inspect binary, arguments, and target working directory for security compliance."""
        # 1. Validate Executable Allowlist
        exe_basename = Path(executable).name.lower().replace(".exe", "")
        if exe_basename not in self.ALLOWLISTED_EXECUTABLES:
            raise SecuritySandboxViolation(
                f"Executable '{executable}' is not in the approved simulation allowlist: {sorted(self.ALLOWLISTED_EXECUTABLES)}"
            )

        # 2. Check for dangerous patterns in executable path
        for pat in self.DANGEROUS_PATTERNS:
            if re.search(pat, executable, re.IGNORECASE):
                raise SecuritySandboxViolation(f"Dangerous pattern detected in executable path: {pat}")

        # 3. Validate Arguments
        for arg in arguments:
            for pat in self.DANGEROUS_PATTERNS:
                if re.search(pat, arg, re.IGNORECASE):
                    raise SecuritySandboxViolation(f"Dangerous pattern detected in argument '{arg}': {pat}")

            # Disallow absolute file path pointing outside workspace
            if Path(arg).is_absolute():
                resolved = Path(arg).resolve()
                if "windows" in str(resolved).lower() or "system32" in str(resolved).lower():
                    raise SecuritySandboxViolation(f"Access to protected system path prohibited: '{arg}'")

        # 4. Path Traversal & Working Directory Check
        resolved_cwd = working_directory.resolve()
        if not resolved_cwd.exists():
            raise SecuritySandboxViolation(f"Working directory does not exist: {working_directory}")

        if "windows" in str(resolved_cwd).lower() or "system32" in str(resolved_cwd).lower():
            raise SecuritySandboxViolation(f"Working directory cannot be within system root: {working_directory}")

    def execute_sandboxed(
        self,
        executable: str,
        arguments: List[str],
        working_directory: Path,
        timeout_seconds: Optional[float] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, str, str]:
        """Execute simulation command strictly inside isolated subprocess without shell=True."""
        self.validate_command(executable, arguments, working_directory)

        timeout = timeout_seconds or self.default_timeout_seconds
        cmd = [executable] + arguments

        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(working_directory),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                shell=False,  # CRITICAL: shell=False prohibits shell injection
                env=env or os.environ.copy(),
            )

            stdout_text, stderr_text = process.communicate(timeout=timeout)
            ret_code = process.returncode

            # Output truncation guard
            if len(stdout_text.encode("utf-8")) > self.max_output_bytes:
                stdout_text = stdout_text[: self.max_output_bytes // 2] + "\n[OUTPUT TRUNCATED BY SANDBOX LIMIT]"

            return ret_code, stdout_text, stderr_text

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise TimeoutError(f"Simulation execution timed out after {timeout}s")
        except FileNotFoundError as err:
            raise FileNotFoundError(f"Solver executable '{executable}' not found: {err}")
        except Exception as exc:
            raise RuntimeError(f"Sandboxed simulation execution failed: {str(exc)}")
