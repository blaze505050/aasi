"""
AASI 2.0 Agent Task Harness Package.

Provides:
1. TaskHarness: Complete QUESTION→PLAN→VALIDATE→EXECUTE→VERIFY→RECONCILE→LEARN→DECIDE loop.
2. ToolBus: Strongly-typed dispatch gated by fail-closed Safety Governor.
3. Core Skills: 9 registered aerospace calculation, validation, and export tools.
4. TaskState & TaskResult: Formally auditable state machine models with SHA-256 Merkle chain.
"""

from backend.tools.contracts import EpistemicTier, ToolDomain, UncertaintyModel, ComputationalCostModel
from backend.harness.tool_protocol import ToolSpec, ToolParameter, ToolResult
from backend.harness.tool_bus import ToolBus, global_tool_bus
from backend.harness.skills import register_aasi_core_skills
from backend.harness.task_state import TaskState, TaskStep, TaskResult as HarnessTaskResult
from backend.harness.task_harness import TaskHarness, global_task_harness

__all__ = [
    "TaskHarness",
    "global_task_harness",
    "ToolBus",
    "global_tool_bus",
    "ToolSpec",
    "ToolParameter",
    "ToolResult",
    "HarnessTaskResult",
    "TaskState",
    "TaskStep",
    "EpistemicTier",
    "ToolDomain",
    "UncertaintyModel",
    "ComputationalCostModel",
    "register_aasi_core_skills",
]
