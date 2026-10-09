"""
AASI Aerospace Mission Language (AML) Serializer.
Converts AST structures back to formatted AML scripts and JSON schemas.
"""

import json
from typing import Any, Dict
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


class AMLSerializer:
    """
    Renders strongly-typed AML AST objects into canonical textual AML syntax.
    """

    @classmethod
    def serialize_program(cls, program: AMLProgram) -> str:
        return "\n\n".join(cls.serialize_statement(s) for s in program.statements)

    @classmethod
    def serialize_statement(cls, stmt: AMLStatement) -> str:
        if isinstance(stmt, InvestigateStatement):
            return cls._serialize_investigate(stmt)
        elif isinstance(stmt, CompareStatement):
            return cls._serialize_compare(stmt)
        elif isinstance(stmt, OptimizeStatement):
            return cls._serialize_optimize(stmt)
        elif isinstance(stmt, ValidateStatement):
            return cls._serialize_validate(stmt)
        elif isinstance(stmt, SweepStatement):
            return cls._serialize_sweep(stmt)
        elif isinstance(stmt, CharacterizeStatement):
            return cls._serialize_characterize(stmt)
        return f"# Unsupported statement: {type(stmt)}"

    @classmethod
    def to_json(cls, program: AMLProgram) -> Dict[str, Any]:
        return program.model_dump()

    @classmethod
    def _format_conditions(cls, cond: AMLConditions) -> str:
        parts = []
        if cond.alpha_deg is not None: parts.append(f"alpha: {cond.alpha_deg} deg")
        if cond.mach is not None: parts.append(f"Mach: {cond.mach}")
        if cond.reynolds is not None: parts.append(f"Re: {cond.reynolds:.2e}")
        if cond.altitude_m is not None: parts.append(f"altitude: {cond.altitude_m} m")
        if cond.temperature_k is not None: parts.append(f"temperature: {cond.temperature_k} K")
        if cond.pressure_pa is not None: parts.append(f"pressure: {cond.pressure_pa} Pa")
        for k, v in cond.extra_params.items():
            parts.append(f"{k}: {v}")
        return ", ".join(parts)

    @classmethod
    def _serialize_investigate(cls, stmt: InvestigateStatement) -> str:
        title = f'"{stmt.name}" ' if stmt.name else ""
        lines = [f"INVESTIGATE {title}{{"]
        lines.append(f'    GEOMETRY "{stmt.geometry}"')
        lines.append(f"    CONDITIONS {{ {cls._format_conditions(stmt.conditions)} }}")
        lines.append(f"    OBJECTIVES [{', '.join(stmt.objectives)}]")
        lines.append(f"    FIDELITY {stmt.fidelity}")
        if stmt.tolerance is not None:
            lines.append(f"    TOLERANCE {stmt.tolerance}")
        lines.append(f"    AUTONOMY {stmt.autonomy_level}")
        lines.append("}")
        return "\n".join(lines)

    @classmethod
    def _serialize_compare(cls, stmt: CompareStatement) -> str:
        title = f'"{stmt.name}" ' if stmt.name else ""
        lines = [f"COMPARE {title}{{"]
        lines.append(f'    BASE "{stmt.base_geometry}"')
        cands = ", ".join(f'"{c}"' for c in stmt.candidate_geometries)
        lines.append(f"    CANDIDATES [{cands}]")
        lines.append(f"    CONDITIONS {{ {cls._format_conditions(stmt.conditions)} }}")
        lines.append(f"    METRICS [{', '.join(stmt.metrics)}]")
        lines.append(f"    FIDELITY {stmt.fidelity}")
        lines.append("}")
        return "\n".join(lines)

    @classmethod
    def _serialize_optimize(cls, stmt: OptimizeStatement) -> str:
        title = f'"{stmt.name}" ' if stmt.name else ""
        lines = [f"OPTIMIZE {title}{{"]
        lines.append(f'    GEOMETRY "{stmt.geometry}"')
        lines.append(f"    OBJECTIVE {stmt.objective.direction.value} {stmt.objective.metric}")
        if stmt.constraints:
            cstr_strs = [f"{c.variable} {c.operator.value} {c.value}" for c in stmt.constraints]
            lines.append(f"    CONSTRAINTS {{ {', '.join(cstr_strs)} }}")
        lines.append(f"    CONDITIONS {{ {cls._format_conditions(stmt.conditions)} }}")
        lines.append(f"    MAX_ITERATIONS {stmt.max_iterations}")
        lines.append(f"    FIDELITY {stmt.fidelity}")
        lines.append(f"    AUTONOMY {stmt.autonomy_level}")
        lines.append("}")
        return "\n".join(lines)

    @classmethod
    def _serialize_validate(cls, stmt: ValidateStatement) -> str:
        title = f'"{stmt.name}" ' if stmt.name else ""
        lines = [f"VALIDATE {title}{{"]
        lines.append(f'    GEOMETRY "{stmt.geometry}"')
        if stmt.dataset:
            lines.append(f'    DATASET "{stmt.dataset}"')
        lines.append(f"    TOLERANCE {stmt.tolerance}")
        lines.append(f"    CRITERIA [{', '.join(stmt.criteria)}]")
        lines.append("}")
        return "\n".join(lines)

    @classmethod
    def _serialize_sweep(cls, stmt: SweepStatement) -> str:
        title = f'"{stmt.name}" ' if stmt.name else ""
        lines = [f"SWEEP {title}{{"]
        lines.append(f'    GEOMETRY "{stmt.geometry}"')
        sw = stmt.sweep_range
        u = f" {sw.unit}" if sw.unit else ""
        lines.append(f"    VARIABLE {sw.variable} FROM {sw.start} TO {sw.end} STEP {sw.step}{u}")
        lines.append(f"    CONDITIONS {{ {cls._format_conditions(stmt.conditions)} }}")
        lines.append(f"    RECORD [{', '.join(stmt.record_metrics)}]")
        lines.append(f"    FIDELITY {stmt.fidelity}")
        lines.append("}")
        return "\n".join(lines)

    @classmethod
    def _serialize_characterize(cls, stmt: CharacterizeStatement) -> str:
        title = f'"{stmt.name}" ' if stmt.name else ""
        lines = [f"CHARACTERIZE {title}\"{stmt.geometry}\""]
        if stmt.reynolds or stmt.mach:
            lines.append(f"AT Re={stmt.reynolds:.2e}, Mach={stmt.mach}")
        lines.append(f"WITH FIDELITY {stmt.fidelity}")
        return " ".join(lines)
