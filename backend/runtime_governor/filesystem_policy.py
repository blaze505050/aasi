"""
AASI 2.0 Runtime Governor — Filesystem Access Policy.
"""

from __future__ import annotations

import os
from typing import Tuple, List

PROHIBITED_DIRECTORIES = [
    "/etc",
    "/root",
    "/boot",
    "/sys",
    "/dev",
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\ProgramData",
]


class FilesystemPolicy:
    """Enforces workspace boundary sandboxing and path traversal rejection."""

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)

    def validate_path(self, target_path: str, for_write: bool = False) -> Tuple[bool, str]:
        if not target_path:
            return False, "Target path cannot be empty"

        norm = os.path.normpath(target_path)
        for prohibited in PROHIBITED_DIRECTORIES:
            if norm.lower().startswith(prohibited.lower()):
                return False, f"Access to system directory '{prohibited}' is prohibited"

        abs_target = os.path.abspath(target_path)
        if not abs_target.startswith(self.workspace_root):
            return False, f"Path '{target_path}' escapes workspace boundary '{self.workspace_root}'"

        return True, ""
