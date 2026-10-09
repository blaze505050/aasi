"""
AASI Aerospace Mission Language (AML) Abstract Syntax Tree (AST) Definitions.
Strongly-typed Pydantic nodes representing scientific missions and experiments.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class ObjectiveDirection(str, Enum):
    MAXIMIZE = "MAXIMIZE"
    MINIMIZE = "MINIMIZE"
    TARGET = "TARGET"


class ConstraintOp(str, Enum):
    LE = "<="
    GE = ">="
    LT = "<"
    GT = ">"
    EQ = "=="


class AMLNode(BaseModel):
    """Base class for all AML AST nodes."""
    line: Optional[int] = None
    column: Optional[int] = None


class PhysicalValue(AMLNode):
    """Physical quantity with optional explicit unit."""
    value: float
    unit: Optional[str] = None


class AMLConditions(AMLNode):
    """Aerodynamic and fluid flow operating conditions."""
    alpha_deg: Optional[float] = None
    mach: Optional[float] = None
    reynolds: Optional[float] = None
    altitude_m: Optional[float] = None
    temperature_k: Optional[float] = None
    pressure_pa: Optional[float] = None
    q_inf_pa: Optional[float] = None
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class AMLObjective(AMLNode):
    """Optimization or investigation objective."""
    direction: ObjectiveDirection
    metric: str
    target_value: Optional[float] = None


class AMLConstraint(AMLNode):
    """Physical or geometric constraint."""
    variable: str
    operator: ConstraintOp
    value: float
    unit: Optional[str] = None


class AMLSweepRange(AMLNode):
    """Parametric variation range."""
    variable: str
    start: float
    end: float
    step: float
    unit: Optional[str] = None

    @property
    def points(self) -> List[float]:
        """Compute discretized sequence of evaluation points."""
        pts = []
        curr = self.start
        step = abs(self.step) if self.end >= self.start else -abs(self.step)
        if step == 0:
            return [self.start]
        while (curr <= self.end + 1e-9 and step > 0) or (curr >= self.end - 1e-9 and step < 0):
            pts.append(round(curr, 6))
            curr += step
        return pts


# Statement Nodes

class AMLStatement(AMLNode):
    """Base for top-level statements."""
    statement_type: str
    name: Optional[str] = None


class InvestigateStatement(AMLStatement):
    """Full scientific investigation of a geometry under specific conditions."""
    statement_type: Literal["INVESTIGATE"] = "INVESTIGATE"
    geometry: str
    conditions: AMLConditions = Field(default_factory=AMLConditions)
    objectives: List[str] = Field(default_factory=lambda: ["CL", "CD", "CM"])
    fidelity: str = "MULTI_FIDELITY"
    tolerance: Optional[float] = 0.05
    autonomy_level: str = "L3_BOUNDED"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CompareStatement(AMLStatement):
    """Multi-geometry or multi-method comparative trade study."""
    statement_type: Literal["COMPARE"] = "COMPARE"
    base_geometry: str
    candidate_geometries: List[str]
    conditions: AMLConditions = Field(default_factory=AMLConditions)
    metrics: List[str] = Field(default_factory=lambda: ["CL", "CD", "L_OVER_D"])
    fidelity: str = "MULTI_FIDELITY"


class OptimizeStatement(AMLStatement):
    """Aerodynamic shape or setting optimization."""
    statement_type: Literal["OPTIMIZE"] = "OPTIMIZE"
    geometry: str
    objective: AMLObjective
    constraints: List[AMLConstraint] = Field(default_factory=list)
    conditions: AMLConditions = Field(default_factory=AMLConditions)
    max_iterations: int = 20
    fidelity: str = "PANEL"
    autonomy_level: str = "L3_BOUNDED"


class ValidateStatement(AMLStatement):
    """V&V 20 grid convergence and experimental benchmark validation."""
    statement_type: Literal["VALIDATE"] = "VALIDATE"
    geometry: str
    dataset: Optional[str] = None
    conditions: Optional[AMLConditions] = None
    tolerance: float = 0.05
    criteria: List[str] = Field(default_factory=lambda: ["DRAG_POSITIVITY", "BOUNDED_PRESSURE"])


class SweepStatement(AMLStatement):
    """Parametric angle-of-attack, Mach, or Reynolds sweep."""
    statement_type: Literal["SWEEP"] = "SWEEP"
    geometry: str
    sweep_range: AMLSweepRange
    conditions: AMLConditions = Field(default_factory=AMLConditions)
    record_metrics: List[str] = Field(default_factory=lambda: ["CL", "CD", "CM"])
    fidelity: str = "PANEL"


class CharacterizeStatement(AMLStatement):
    """Comprehensive aerodynamic polar characterization (stall, drag polar, neutral point)."""
    statement_type: Literal["CHARACTERIZE"] = "CHARACTERIZE"
    geometry: str
    reynolds: Optional[float] = None
    mach: Optional[float] = None
    fidelity: str = "MULTI_FIDELITY"


class AMLProgram(AMLNode):
    """Top-level container for an AML script containing multiple statements."""
    statements: List[Union[
        InvestigateStatement,
        CompareStatement,
        OptimizeStatement,
        ValidateStatement,
        SweepStatement,
        CharacterizeStatement
    ]] = Field(default_factory=list)
