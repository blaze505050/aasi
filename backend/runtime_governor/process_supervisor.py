"""
AASI 2.0 Runtime Governor — Process Supervisor.
"""

from __future__ import annotations

import time
import subprocess
from typing import List, Optional
from backend.governor.kill_switch import global_kill_switch, KillSwitchActiveError


class ProcessSupervisor:
    """Supervises running subprocesses, enforcing timeouts and cooperative kill-switch cancellation."""

    @classmethod
    def run_bounded(
        cls,
        cmd: List[str],
        timeout_seconds: float = 60.0,
        cwd: str = ".",
    ) -> subprocess.CompletedProcess:
        global_kill_switch.check_or_raise()
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=cwd,
        )
        global_kill_switch.check_or_raise()
        return proc
