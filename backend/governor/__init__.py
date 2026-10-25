"""
AASI 2.0 Governor Package — Resource Awareness, Safety Enforcement & Execution Control.

Provides:
1. ResourceMonitor: Live CPU/RAM/disk/GPU polling with structured snapshots.
2. ResourceBudget: Per-task resource allocation and headroom evaluation.
3. ExecutionPolicyEngine: Permitted tools allowlist, dangerous pattern blocks, path traversal protection.
4. KillSwitch: Global emergency halt with cooperative cancellation.
5. SafetyGovernor: Central fail-closed authorization gate with tamper-evident audit log.
"""

from backend.governor.constants import (
    DEFAULT_TASK_TIMEOUT_SECONDS,
    HARD_MAX_TIMEOUT_SECONDS,
    DEFAULT_MAX_CPU_PERCENT,
    CRITICAL_CPU_PERCENT,
    DEFAULT_MAX_RAM_GB,
    CRITICAL_RAM_AVAILABLE_GB,
    MIN_FREE_RAM_FRACTION,
    DEFAULT_MAX_DISK_GB,
    CRITICAL_DISK_FREE_GB,
    DEFAULT_MAX_GPU_VRAM_GB,
    CRITICAL_GPU_VRAM_FREE_FRACTION,
)

from backend.governor.resource_monitor import (
    ResourceMonitor,
    ResourceSnapshot,
    GpuSnapshot,
    ProcessSnapshot,
    default_monitor,
)

from backend.governor.resource_budget import (
    ResourceBudget,
    BudgetEnforcement,
    BudgetVerdict,
)

from backend.governor.kill_switch import (
    KillSwitch,
    KillSwitchState,
    KillSwitchActiveError,
    global_kill_switch,
)

from backend.governor.execution_policy import (
    ActionType,
    ExecutionAction,
    PolicyVerdict,
    ExecutionPolicyEngine,
    default_policy_engine,
    PERMITTED_AASI_TOOLS,
    PERMITTED_EXECUTABLES,
)

from backend.governor.safety_governor import (
    SafetyGovernor,
    DecisionVerdict,
    global_governor,
)

__all__ = [
    # Monitor
    "ResourceMonitor",
    "ResourceSnapshot",
    "GpuSnapshot",
    "ProcessSnapshot",
    "default_monitor",
    # Budget
    "ResourceBudget",
    "BudgetEnforcement",
    "BudgetVerdict",
    # Kill switch
    "KillSwitch",
    "KillSwitchState",
    "KillSwitchActiveError",
    "global_kill_switch",
    # Policy
    "ActionType",
    "ExecutionAction",
    "PolicyVerdict",
    "ExecutionPolicyEngine",
    "default_policy_engine",
    "PERMITTED_AASI_TOOLS",
    "PERMITTED_EXECUTABLES",
    # Governor
    "SafetyGovernor",
    "DecisionVerdict",
    "global_governor",
    # Constants
    "DEFAULT_TASK_TIMEOUT_SECONDS",
    "HARD_MAX_TIMEOUT_SECONDS",
    "DEFAULT_MAX_CPU_PERCENT",
    "CRITICAL_CPU_PERCENT",
    "DEFAULT_MAX_RAM_GB",
    "CRITICAL_RAM_AVAILABLE_GB",
    "MIN_FREE_RAM_FRACTION",
    "DEFAULT_MAX_DISK_GB",
    "CRITICAL_DISK_FREE_GB",
    "DEFAULT_MAX_GPU_VRAM_GB",
    "CRITICAL_GPU_VRAM_FREE_FRACTION",
]
