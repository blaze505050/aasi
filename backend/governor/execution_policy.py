"""
AASI 2.0 Execution Policy — Allowlists, Security Bounds & Action Authorization.

Deterministic, fail-closed policy engine verifying every requested agent action
prior to execution.
"""

from __future__ import annotations

import os
import re
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field

logger = logging.getLogger("aasi.governor.policy")


class ActionType(str, Enum):
    TOOL_INVOCATION = "TOOL_INVOCATION"
    SOLVER_EXECUTION = "SOLVER_EXECUTION"
    FILE_READ = "FILE_READ"
    FILE_WRITE = "FILE_WRITE"
    NETWORK_REQUEST = "NETWORK_REQUEST"
    SYSTEM_COMMAND = "SYSTEM_COMMAND"


class ExecutionAction(BaseModel):
    """Structured description of an action requested by an agent or user."""
    action_type: ActionType
    tool_name: Optional[str] = None
    target_path: Optional[str] = None
    command: Optional[List[str]] = None
    network_url: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requester: str = "agent"


class PolicyVerdict(BaseModel):
    """Deterministic verdict from policy evaluation."""
    allowed: bool
    reasons: List[str] = Field(default_factory=list)
    action_type: ActionType
    matched_rules: List[str] = Field(default_factory=list)


# ─── Permitted Tools & Solvers Allowlists ─────────────────────────────────────

PERMITTED_AASI_TOOLS: Set[str] = {
    # Physics & Panel Solvers
    "aero_2d_solve",
    "aero_3d_vlm",
    "polar_sweep",
    "uncertainty_quantify",
    "benchmark_verify",
    # Geometry & Mesh
    "geometry_parse",
    "mesh_generate",
    "naca_generate",
    # Data & Export
    "export_datcom",
    "export_shabp",
    "export_dossier",
    "export_6dof",
    "export_jsbsim",
    "export_px4",
    # Lineage & Scientific Memory
    "merkle_inspect",
    "epistemic_query",
    "dataset_catalog_search",
    # Aerospace Adapters & Digital Twin
    "rocket_trajectory",
    "mdao_evaluate",
    "su2_case_setup",
    "digital_twin_simulate",
    # Permitted Research
    "browser_research",
}

PERMITTED_EXECUTABLES: Set[str] = {
    "simpleFoam",
    "pimpleFoam",
    "rhoSimpleFoam",
    "blockMesh",
    "checkMesh",
    "foamToVTK",
    "wsl",
    "python",
    "git",
}

# ─── Prohibited Patterns ──────────────────────────────────────────────────────

DANGEROUS_CMD_PATTERNS = [
    r"rm\s+(-[rfRF]+\s+)?[\/\\]",       # Root deletion
    r"del\s+([\/][sS]\s+)?[\/\\]",      # Windows root deletion
    r"format\s+[a-zA-Z]:",             # Format drive
    r"mkfs",                           # Format filesystem
    r"dd\s+if=",                       # Raw disk overwrite
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\};:", # Fork bomb
    r"shutdown",                       # System shutdown
    r"reboot",                         # System reboot
    r"curl.*\|\s*(bash|sh)",           # Piping curl to shell
    r"wget.*\|\s*(bash|sh)",           # Piping wget to shell
    r"powershell.*-enc",               # Encoded powershell payload
]

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


class ExecutionPolicyEngine:
    """
    Deterministic rule engine that verifies execution requests.
    Fail-closed: returns allowed=False if any rule fails or if action is unhandled.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = os.path.abspath(workspace_root or ".")

    def evaluate(self, action: ExecutionAction) -> PolicyVerdict:
        """Evaluates action against security and operational policies."""
        reasons: List[str] = []
        matched_rules: List[str] = []

        if action.action_type == ActionType.TOOL_INVOCATION:
            if not action.tool_name:
                reasons.append("Tool invocation missing tool_name")
            elif action.tool_name not in PERMITTED_AASI_TOOLS:
                reasons.append(f"Tool '{action.tool_name}' is not in permitted tool allowlist")
            else:
                matched_rules.append(f"ALLOWED_TOOL:{action.tool_name}")

        elif action.action_type == ActionType.SOLVER_EXECUTION:
            tool = action.tool_name or (action.command[0] if action.command else "")
            if tool not in PERMITTED_EXECUTABLES and tool not in PERMITTED_AASI_TOOLS:
                reasons.append(f"Solver executable '{tool}' is not in permitted solver allowlist")
            else:
                matched_rules.append(f"ALLOWED_SOLVER:{tool}")

        elif action.action_type in (ActionType.FILE_READ, ActionType.FILE_WRITE):
            if not action.target_path:
                reasons.append("File operation requires target_path")
            else:
                norm_target = os.path.normpath(action.target_path)
                # Check prohibited directories
                for prohibited in PROHIBITED_DIRECTORIES:
                    if norm_target.lower().startswith(prohibited.lower()):
                        reasons.append(f"Access to system directory '{prohibited}' is prohibited")

                # Check path traversal
                if ".." in action.target_path.replace("\\", "/").split("/"):
                    # Check if resolved path is outside workspace
                    abs_target = os.path.abspath(action.target_path)
                    if not abs_target.startswith(self.workspace_root):
                        reasons.append(f"Path traversal outside workspace root is prohibited: {action.target_path}")

                if not reasons:
                    matched_rules.append(f"ALLOWED_FILE_OP:{action.action_type.value}")

        elif action.action_type == ActionType.SYSTEM_COMMAND:
            if not action.command:
                reasons.append("System command operation missing command list")
            else:
                full_cmd = " ".join(action.command)
                for pat in DANGEROUS_CMD_PATTERNS:
                    if re.search(pat, full_cmd, re.IGNORECASE):
                        reasons.append(f"Command matches prohibited dangerous pattern: {pat}")
                        break

                exe = action.command[0]
                base_exe = os.path.basename(exe).lower().replace(".exe", "")
                if base_exe not in {e.lower().replace(".exe", "") for e in PERMITTED_EXECUTABLES}:
                    reasons.append(f"Binary '{exe}' is not in permitted system executables allowlist")

                if not reasons:
                    matched_rules.append("ALLOWED_SYSTEM_COMMAND")

        elif action.action_type == ActionType.NETWORK_REQUEST:
            if not action.network_url:
                reasons.append("Network request missing network_url")
            else:
                url = action.network_url.lower()
                # Local loopback or verified API endpoints allowed
                if "127.0.0.1" in url or "localhost" in url:
                    matched_rules.append("ALLOWED_LOOPBACK_NETWORK")
                else:
                    reasons.append(f"Outbound external network request to '{url}' prohibited by policy")

        else:
            reasons.append(f"Unhandled action type: {action.action_type}")

        allowed = len(reasons) == 0
        return PolicyVerdict(
            allowed=allowed,
            reasons=reasons,
            action_type=action.action_type,
            matched_rules=matched_rules,
        )


# Global singleton
default_policy_engine = ExecutionPolicyEngine()
