"""
AASI Phase 1C: Strongly-Typed Tool Bus Contracts.
Defines formal epistemic, uncertainty, computational cost, and input/output contracts
for all scientific calculators and execution tools in AASI.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import hashlib
import json
import time
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class EpistemicTier(str, Enum):
    """Epistemic classification tiers for calculations and results."""
    DATABASE_REAL = "DATABASE_REAL"
    LIVE_CFD = "LIVE_CFD"
    SURROGATE = "SURROGATE"
    ANALYTICAL = "ANALYTICAL"
    USER_PROVIDED = "USER_PROVIDED"
    DERIVED = "DERIVED"
    SYNTHETIC = "SYNTHETIC"
    ESTIMATED = "ESTIMATED"
    UNVERIFIED = "UNVERIFIED"
    NOT_EXECUTED = "NOT_EXECUTED"
    STAGED_ONLY = "STAGED_ONLY"


class ToolDomain(str, Enum):
    AERODYNAMICS = "AERODYNAMICS"
    PROPULSION = "PROPULSION"
    ORBITAL = "ORBITAL"
    NUMERICAL_MATH = "NUMERICAL_MATH"
    UNITS = "UNITS"
    VALIDATION = "VALIDATION"
    CFD = "CFD"


class UncertaintyModel(BaseModel):
    """Declared epistemic uncertainty and applicability bounds for a computational tool."""
    typical_relative_error: float = Field(default=0.01, ge=0.0)
    confidence_level: float = Field(default=0.95, ge=0.0, le=1.0)
    validity_envelope: Dict[str, Any] = Field(default_factory=dict)
    known_limitations: List[str] = Field(default_factory=list)


class ComputationalCostModel(BaseModel):
    """Hardware and latency requirements for resource scheduling."""
    typical_latency_ms: float = 10.0
    memory_mb: float = 64.0
    device_requirement: str = "CPU"  # "CPU", "GPU", "CLUSTER"


class ToolExecutionResult(BaseModel):
    """Verifiable execution result with cryptographic input/output provenance."""
    tool_id: str
    operation: str
    domain: ToolDomain
    epistemic_tier: EpistemicTier
    inputs: Dict[str, Any]
    output: Any
    latency_ms: float
    uncertainty: UncertaintyModel
    provenance_hash: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    success: bool = True
    error_message: Optional[str] = None


class ToolContract:
    """
    Formal contract wrapping an engineering computation tool.
    Guarantees validation, provenance tracking, and error taxonomy adherence.
    """

    def __init__(
        self,
        tool_id: str,
        operation: str,
        domain: ToolDomain,
        epistemic_tier: EpistemicTier,
        description: str,
        handler: Callable,
        input_parameters: Dict[str, Any],
        output_description: str,
        uncertainty: Optional[UncertaintyModel] = None,
        cost: Optional[ComputationalCostModel] = None,
    ):
        self.tool_id = tool_id
        self.operation = operation
        self.domain = domain
        self.epistemic_tier = epistemic_tier
        self.description = description
        self.handler = handler
        self.input_parameters = input_parameters
        self.output_description = output_description
        self.uncertainty = uncertainty or UncertaintyModel()
        self.cost = cost or ComputationalCostModel()

    def validate_inputs(self, **kwargs) -> List[str]:
        """Check provided inputs against the contract's envelope."""
        issues = []
        for param, spec in self.input_parameters.items():
            if spec.get("required", False) and param not in kwargs:
                issues.append(f"Missing required parameter '{param}'")

        # Check validity envelope
        for var, bounds in self.uncertainty.validity_envelope.items():
            if var in kwargs and isinstance(bounds, (list, tuple)) and len(bounds) == 2:
                val = kwargs[var]
                if isinstance(val, (int, float)):
                    if val < bounds[0] or val > bounds[1]:
                        issues.append(
                            f"Input '{var}'={val} is outside certified validity envelope [{bounds[0]}, {bounds[1]}]"
                        )
        return issues

    def execute(self, **kwargs) -> ToolExecutionResult:
        """
        Executes the underlying tool and packages result with cryptographic provenance.
        """
        t0 = time.perf_counter()
        issues = self.validate_inputs(**kwargs)
        if issues:
            # If critical missing params, fail
            missing = [i for i in issues if "Missing required" in i]
            if missing:
                return ToolExecutionResult(
                    tool_id=self.tool_id,
                    operation=self.operation,
                    domain=self.domain,
                    epistemic_tier=self.epistemic_tier,
                    inputs=kwargs,
                    output=None,
                    latency_ms=0.0,
                    uncertainty=self.uncertainty,
                    provenance_hash="",
                    success=False,
                    error_message="; ".join(issues),
                )

        try:
            raw_out = self.handler(**kwargs)
            latency = (time.perf_counter() - t0) * 1000.0

            # Compute SHA-256 provenance hash of inputs + outputs
            payload = f"{self.tool_id}:{self.operation}:{json.dumps(kwargs, default=str)}:{json.dumps(raw_out, default=str)}"
            digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()

            return ToolExecutionResult(
                tool_id=self.tool_id,
                operation=self.operation,
                domain=self.domain,
                epistemic_tier=self.epistemic_tier,
                inputs=kwargs,
                output=raw_out,
                latency_ms=round(latency, 2),
                uncertainty=self.uncertainty,
                provenance_hash=digest,
                success=True,
                error_message="; ".join(issues) if issues else None,
            )
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000.0
            return ToolExecutionResult(
                tool_id=self.tool_id,
                operation=self.operation,
                domain=self.domain,
                epistemic_tier=self.epistemic_tier,
                inputs=kwargs,
                output=None,
                latency_ms=round(latency, 2),
                uncertainty=self.uncertainty,
                provenance_hash="",
                success=False,
                error_message=str(e),
            )
