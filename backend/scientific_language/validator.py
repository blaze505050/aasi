"""
AASI Aerospace Mission Language (AML) Semantic Validator.
Enforces physical laws, valid aerodynamic domains, geometric existence,
and autonomy tier constraints on AST models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from backend.scientific_language.ast import (
    AMLProgram,
    AMLStatement,
    InvestigateStatement,
    CompareStatement,
    OptimizeStatement,
    ValidateStatement,
    SweepStatement,
    CharacterizeStatement,
    AMLConditions,
)
from backend.agent.investigation_lifecycle import AutonomyLevel


VALID_METRICS = {
    "CL", "CD", "CM", "L_OVER_D", "CP", "CP_DISTRIBUTION",
    "PRESSURE", "DRAG", "LIFT", "MOMENT", "CD_WAVE", "CD_INDUCED", "CD_FRICTION"
}

VALID_FIDELITY_TIERS = {
    "ANALYTICAL", "PANEL", "SURROGATE", "DATABASE_REAL", "LIVE_CFD", "MULTI_FIDELITY"
}


class SemanticDiagnostic(BaseModel):
    severity: str  # "ERROR" or "WARNING"
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    field: Optional[str] = None


class AMLValidationResult(BaseModel):
    is_valid: bool
    diagnostics: List[SemanticDiagnostic] = Field(default_factory=list)

    @property
    def errors(self) -> List[SemanticDiagnostic]:
        return [d for d in self.diagnostics if d.severity == "ERROR"]

    @property
    def warnings(self) -> List[SemanticDiagnostic]:
        return [d for d in self.diagnostics if d.severity == "WARNING"]


class AMLSemanticValidator:
    """
    Validates physical conservation, flight envelope constraints,
    and computational feasibility of AML statements.
    """

    def validate_program(self, program: AMLProgram) -> AMLValidationResult:
        diagnostics: List[SemanticDiagnostic] = []
        for stmt in program.statements:
            self._validate_statement(stmt, diagnostics)
        return AMLValidationResult(
            is_valid=not any(d.severity == "ERROR" for d in diagnostics),
            diagnostics=diagnostics,
        )

    def validate_statement(self, stmt: AMLStatement) -> AMLValidationResult:
        diagnostics: List[SemanticDiagnostic] = []
        self._validate_statement(stmt, diagnostics)
        return AMLValidationResult(
            is_valid=not any(d.severity == "ERROR" for d in diagnostics),
            diagnostics=diagnostics,
        )

    def _validate_statement(self, stmt: AMLStatement, diagnostics: List[SemanticDiagnostic]) -> None:
        if isinstance(stmt, InvestigateStatement):
            self._validate_investigate(stmt, diagnostics)
        elif isinstance(stmt, CompareStatement):
            self._validate_compare(stmt, diagnostics)
        elif isinstance(stmt, OptimizeStatement):
            self._validate_optimize(stmt, diagnostics)
        elif isinstance(stmt, ValidateStatement):
            self._validate_validate(stmt, diagnostics)
        elif isinstance(stmt, SweepStatement):
            self._validate_sweep(stmt, diagnostics)
        elif isinstance(stmt, CharacterizeStatement):
            self._validate_characterize(stmt, diagnostics)

    def _validate_conditions(self, conditions: Optional[AMLConditions], line: Optional[int], diagnostics: List[SemanticDiagnostic]) -> None:
        if not conditions:
            return

        # 1. Mach number
        if conditions.mach is not None:
            if conditions.mach < 0.0:
                diagnostics.append(SemanticDiagnostic(
                    severity="ERROR",
                    message=f"Mach number cannot be negative ({conditions.mach})",
                    line=line,
                    field="mach"
                ))
            elif conditions.mach > 15.0:
                diagnostics.append(SemanticDiagnostic(
                    severity="WARNING",
                    message=f"Hypersonic Mach number ({conditions.mach}) requires specialized aerothermodynamic solver",
                    line=line,
                    field="mach"
                ))

        # 2. Reynolds number
        if conditions.reynolds is not None:
            if conditions.reynolds <= 0.0:
                diagnostics.append(SemanticDiagnostic(
                    severity="ERROR",
                    message=f"Reynolds number must be strictly positive ({conditions.reynolds})",
                    line=line,
                    field="reynolds"
                ))
            elif conditions.reynolds < 1e3:
                diagnostics.append(SemanticDiagnostic(
                    severity="WARNING",
                    message=f"Very low Reynolds number ({conditions.reynolds:.1e}) implies Stokes or micro-air-vehicle flow regime",
                    line=line,
                    field="reynolds"
                ))

        # 3. Angle of attack
        if conditions.alpha_deg is not None:
            if abs(conditions.alpha_deg) > 90.0:
                diagnostics.append(SemanticDiagnostic(
                    severity="ERROR",
                    message=f"Angle of attack exceeds physical limit [-90°, 90°]: {conditions.alpha_deg}°",
                    line=line,
                    field="alpha_deg"
                ))
            elif abs(conditions.alpha_deg) > 25.0:
                diagnostics.append(SemanticDiagnostic(
                    severity="WARNING",
                    message=f"Deep post-stall angle of attack ({conditions.alpha_deg}°) requires unsteady detached eddy simulation",
                    line=line,
                    field="alpha_deg"
                ))

        # 4. Thermodynamic constraints
        if conditions.temperature_k is not None and conditions.temperature_k <= 0.0:
            diagnostics.append(SemanticDiagnostic(
                severity="ERROR",
                message=f"Absolute temperature must be positive ({conditions.temperature_k} K)",
                line=line,
                field="temperature_k"
            ))

        if conditions.pressure_pa is not None and conditions.pressure_pa <= 0.0:
            diagnostics.append(SemanticDiagnostic(
                severity="ERROR",
                message=f"Static pressure must be positive ({conditions.pressure_pa} Pa)",
                line=line,
                field="pressure_pa"
            ))

    def _validate_geometry(self, geometry: str, line: Optional[int], diagnostics: List[SemanticDiagnostic]) -> None:
        if not geometry or not geometry.strip():
            diagnostics.append(SemanticDiagnostic(
                severity="ERROR",
                message="Geometry identifier cannot be empty",
                line=line,
                field="geometry"
            ))

    def _validate_investigate(self, stmt: InvestigateStatement, diagnostics: List[SemanticDiagnostic]) -> None:
        self._validate_geometry(stmt.geometry, stmt.line, diagnostics)
        self._validate_conditions(stmt.conditions, stmt.line, diagnostics)

        if stmt.fidelity.upper() not in VALID_FIDELITY_TIERS:
            diagnostics.append(SemanticDiagnostic(
                severity="ERROR",
                message=f"Unrecognized fidelity tier: '{stmt.fidelity}'. Valid tiers: {sorted(list(VALID_FIDELITY_TIERS))}",
                line=stmt.line,
                field="fidelity"
            ))

        # Check autonomy level
        valid_autonomies = {l.value for l in AutonomyLevel}
        if stmt.autonomy_level.upper() not in valid_autonomies:
            diagnostics.append(SemanticDiagnostic(
                severity="WARNING",
                message=f"Unknown autonomy level: '{stmt.autonomy_level}'. Falling back to L3_BOUNDED",
                line=stmt.line,
                field="autonomy_level"
            ))

        for obj in stmt.objectives:
            if obj.upper() not in VALID_METRICS:
                diagnostics.append(SemanticDiagnostic(
                    severity="WARNING",
                    message=f"Non-standard aerodynamic metric requested: '{obj}'",
                    line=stmt.line,
                    field="objectives"
                ))

    def _validate_compare(self, stmt: CompareStatement, diagnostics: List[SemanticDiagnostic]) -> None:
        self._validate_geometry(stmt.base_geometry, stmt.line, diagnostics)
        if not stmt.candidate_geometries:
            diagnostics.append(SemanticDiagnostic(
                severity="ERROR",
                message="COMPARE statement must have at least one candidate geometry",
                line=stmt.line,
                field="candidate_geometries"
            ))
        for cand in stmt.candidate_geometries:
            self._validate_geometry(cand, stmt.line, diagnostics)
        self._validate_conditions(stmt.conditions, stmt.line, diagnostics)

    def _validate_optimize(self, stmt: OptimizeStatement, diagnostics: List[SemanticDiagnostic]) -> None:
        self._validate_geometry(stmt.geometry, stmt.line, diagnostics)
        self._validate_conditions(stmt.conditions, stmt.line, diagnostics)
        if stmt.max_iterations <= 0:
            diagnostics.append(SemanticDiagnostic(
                severity="ERROR",
                message=f"Optimization iterations must be positive ({stmt.max_iterations})",
                line=stmt.line,
                field="max_iterations"
            ))

    def _validate_validate(self, stmt: ValidateStatement, diagnostics: List[SemanticDiagnostic]) -> None:
        self._validate_geometry(stmt.geometry, stmt.line, diagnostics)
        if stmt.tolerance <= 0.0 or stmt.tolerance > 1.0:
            diagnostics.append(SemanticDiagnostic(
                severity="ERROR",
                message=f"Validation tolerance must be within (0.0, 1.0], found {stmt.tolerance}",
                line=stmt.line,
                field="tolerance"
            ))

    def _validate_sweep(self, stmt: SweepStatement, diagnostics: List[SemanticDiagnostic]) -> None:
        self._validate_geometry(stmt.geometry, stmt.line, diagnostics)
        self._validate_conditions(stmt.conditions, stmt.line, diagnostics)
        if stmt.sweep_range.step == 0:
            diagnostics.append(SemanticDiagnostic(
                severity="ERROR",
                message="Sweep step cannot be zero",
                line=stmt.line,
                field="sweep_range"
            ))
        points = stmt.sweep_range.points
        if len(points) > 500:
            diagnostics.append(SemanticDiagnostic(
                severity="WARNING",
                message=f"Sweep generates {len(points)} evaluation points; this may exceed computational envelope",
                line=stmt.line,
                field="sweep_range"
            ))

    def _validate_characterize(self, stmt: CharacterizeStatement, diagnostics: List[SemanticDiagnostic]) -> None:
        self._validate_geometry(stmt.geometry, stmt.line, diagnostics)
        if stmt.reynolds is not None and stmt.reynolds <= 0:
            diagnostics.append(SemanticDiagnostic(
                severity="ERROR",
                message="Reynolds number must be strictly positive",
                line=stmt.line,
                field="reynolds"
            ))
