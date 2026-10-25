"""
AASI 2.0 Agent Harness — Strongly-Typed Tool Protocol.

Defines schemas, epistemic metadata, cost models, and verifiable output contracts
for all tools invoked by the AASI Agent Harness.
"""

from __future__ import annotations

import time
import json
import hashlib
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.tools.contracts import EpistemicTier, ToolDomain, UncertaintyModel, ComputationalCostModel


class ToolParameter(BaseModel):
    """Specification of an input parameter to a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None
    bounds: Optional[List[float]] = None  # [min, max] if continuous

    def __init__(self, **data):
        if "required" not in data and "default" in data and data["default"] is not None:
            data["required"] = False
        super().__init__(**data)


class ToolSpec(BaseModel):
    """Declarative specification of an agent-executable scientific tool."""
    name: str
    description: str
    domain: ToolDomain = ToolDomain.AERODYNAMICS
    epistemic_tier: EpistemicTier = EpistemicTier.ANALYTICAL
    parameters: List[ToolParameter] = Field(default_factory=list)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    cost: ComputationalCostModel = Field(default_factory=ComputationalCostModel)
    uncertainty: UncertaintyModel = Field(default_factory=UncertaintyModel)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "domain": self.domain.value,
            "epistemic_tier": self.epistemic_tier.value,
            "parameters": [p.model_dump() for p in self.parameters],
            "cost": self.cost.model_dump(),
            "uncertainty": self.uncertainty.model_dump(),
        }


class ToolResult(BaseModel):
    """Structured, verifiable result of tool dispatch with cryptographic provenance."""
    tool_name: str
    inputs: Dict[str, Any]
    output: Any
    success: bool
    error: Optional[str] = None
    latency_ms: float = 0.0
    epistemic_tier: EpistemicTier = EpistemicTier.ANALYTICAL
    provenance_hash: str = ""
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def compute_hash(cls, tool_name: str, inputs: Dict[str, Any], output: Any, success: bool) -> str:
        payload = f"{tool_name}:{json.dumps(inputs, sort_keys=True, default=str)}:{json.dumps(output, sort_keys=True, default=str)}:{success}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
