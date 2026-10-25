"""
AASI 2.0 Strongly-Typed Tool Bus.

Dispatches agent tool invocations with:
1. Fail-closed Safety Governor authorization barrier
2. Strict parameter validation against ToolSpec schemas
3. Provenance tracking with SHA-256 signatures
4. Epistemic tier enforcement and latency instrumentation
"""

from __future__ import annotations

import time
import logging
from typing import Dict, List, Optional, Callable, Any

from backend.governor import (
    SafetyGovernor,
    global_governor,
    ExecutionAction,
    ActionType,
    ResourceBudget,
)
from backend.harness.tool_protocol import ToolSpec, ToolResult, EpistemicTier

logger = logging.getLogger("aasi.harness.tool_bus")


class ToolBus:
    """
    Central, strongly-typed dispatcher for agent tool invocations.
    Guarantees that every execution passes through the Safety Governor.
    """

    def __init__(self, governor: Optional[SafetyGovernor] = None):
        self.governor = governor or global_governor
        self._specs: Dict[str, ToolSpec] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(self, spec: ToolSpec, handler: Callable) -> None:
        """Registers a tool specification and its executable handler."""
        self._specs[spec.name] = spec
        self._handlers[spec.name] = handler
        logger.info("Registered tool '%s' (%s)", spec.name, spec.domain.value)

    def get_spec(self, tool_name: str) -> Optional[ToolSpec]:
        return self._specs.get(tool_name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns public catalog of available tools."""
        return [spec.to_dict() for spec in self._specs.values()]

    def dispatch(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        budget: Optional[ResourceBudget] = None,
    ) -> ToolResult:
        """
        Executes a registered tool under Safety Governor control.
        Fail-closed: if the governor denies authorization, the tool will NOT execute.
        """
        if tool_name not in self._specs or tool_name not in self._handlers:
            return ToolResult(
                tool_name=tool_name,
                inputs=parameters,
                output=None,
                success=False,
                error=f"Tool '{tool_name}' is not registered in ToolBus",
            )

        spec = self._specs[tool_name]
        handler = self._handlers[tool_name]

        # 0. Populate defaults for missing optional parameters
        effective_params = dict(parameters)
        for param in spec.parameters:
            if param.name not in effective_params and param.default is not None:
                effective_params[param.name] = param.default

        # 1. Parameter Validation
        validation_errors: List[str] = []
        for param in spec.parameters:
            if param.required and param.name not in effective_params:
                validation_errors.append(f"Missing required parameter '{param.name}'")
            elif param.name in effective_params and param.bounds:
                val = effective_params[param.name]
                if isinstance(val, (int, float)):
                    if val < param.bounds[0] or val > param.bounds[1]:
                        validation_errors.append(
                            f"Parameter '{param.name}'={val} out of valid bounds [{param.bounds[0]}, {param.bounds[1]}]"
                        )

        if validation_errors:
            return ToolResult(
                tool_name=tool_name,
                inputs=effective_params,
                output=None,
                success=False,
                error="; ".join(validation_errors),
                epistemic_tier=spec.epistemic_tier,
            )

        # 2. Safety Governor Authorization Gate (Fail-Closed)
        action = ExecutionAction(
            action_type=ActionType.TOOL_INVOCATION,
            tool_name=tool_name,
            parameters=effective_params,
        )
        decision = self.governor.authorize(action, budget=budget)
        if not decision.approved:
            denial_msg = f"Denied by Governor: {'; '.join(decision.denial_reasons)}"
            logger.warning("Tool dispatch blocked for '%s': %s", tool_name, denial_msg)
            return ToolResult(
                tool_name=tool_name,
                inputs=effective_params,
                output=None,
                success=False,
                error=denial_msg,
                epistemic_tier=spec.epistemic_tier,
                provenance_hash=decision.provenance_hash,
            )

        # 3. Deterministic Execution
        t0 = time.perf_counter()
        try:
            raw_output = handler(**effective_params)
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            prov_hash = ToolResult.compute_hash(tool_name, effective_params, raw_output, True)

            return ToolResult(
                tool_name=tool_name,
                inputs=effective_params,
                output=raw_output,
                success=True,
                latency_ms=elapsed_ms,
                epistemic_tier=spec.epistemic_tier,
                provenance_hash=prov_hash,
            )
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            logger.error("Execution failed for tool '%s': %s", tool_name, exc, exc_info=True)
            return ToolResult(
                tool_name=tool_name,
                inputs=effective_params,
                output=None,
                success=False,
                error=str(exc),
                latency_ms=elapsed_ms,
                epistemic_tier=spec.epistemic_tier,
                provenance_hash=ToolResult.compute_hash(tool_name, effective_params, str(exc), False),
            )


# Global default ToolBus
global_tool_bus = ToolBus()
