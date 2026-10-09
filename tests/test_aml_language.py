"""
Comprehensive test suite for AASI Aerospace Mission Language (AML).
Validates tokenization, AST generation, semantic validation, and round-trip serialization.
"""

import pytest
from backend.scientific_language import (
    parse_aml,
    validate_aml,
    serialize_aml,
    AMLLexer,
    AMLLexerError,
    AMLParser,
    AMLParseError,
    InvestigateStatement,
    CompareStatement,
    OptimizeStatement,
    ValidateStatement,
    SweepStatement,
    CharacterizeStatement,
    ObjectiveDirection,
    ConstraintOp,
)


def test_aml_lexer_tokens():
    code = 'INVESTIGATE "NACA0012 Test" { alpha: 4.0 deg, Mach: 0.15 }'
    lexer = AMLLexer(code)
    tokens = lexer.tokenize()
    assert len(tokens) > 5
    assert tokens[0].value == "INVESTIGATE"
    assert tokens[1].value == "NACA0012 Test"


def test_aml_parse_investigate_block():
    script = """
    INVESTIGATE "Transonic Characterization" {
        GEOMETRY "NACA0012"
        CONDITIONS {
            alpha: 2.5 deg,
            Mach: 0.72,
            Re: 3000000.0,
            altitude: 0.0 m
        }
        OBJECTIVES [CL, CD, CM]
        FIDELITY MULTI_FIDELITY
        TOLERANCE 0.02
        AUTONOMY L3_BOUNDED
    }
    """
    program = parse_aml(script)
    assert len(program.statements) == 1
    stmt = program.statements[0]
    assert isinstance(stmt, InvestigateStatement)
    assert stmt.name == "Transonic Characterization"
    assert stmt.geometry == "NACA0012"
    assert stmt.conditions.alpha_deg == 2.5
    assert stmt.conditions.mach == 0.72
    assert stmt.conditions.reynolds == 3e6
    assert stmt.fidelity == "MULTI_FIDELITY"
    assert stmt.tolerance == 0.02
    assert stmt.autonomy_level == "L3_BOUNDED"

    # Validation check
    val = validate_aml(program)
    assert val.is_valid
    assert len(val.errors) == 0


def test_aml_parse_investigate_inline():
    cmd = "INVESTIGATE NACA4412 AT alpha=5.0 deg, Mach=0.2, Re=2000000 WITH FIDELITY PANEL"
    program = parse_aml(cmd)
    assert len(program.statements) == 1
    stmt = program.statements[0]
    assert isinstance(stmt, InvestigateStatement)
    assert stmt.geometry == "NACA4412"
    assert stmt.conditions.alpha_deg == 5.0
    assert stmt.conditions.mach == 0.2
    assert stmt.conditions.reynolds == 2e6
    assert stmt.fidelity == "PANEL"


def test_aml_parse_compare():
    script = """
    COMPARE "Supercritical Comparison" {
        BASE "RAE2822"
        CANDIDATES ["NACA64A010", "SC(2)-0714"]
        CONDITIONS {
            Mach: 0.73,
            alpha: 2.0 deg,
            Re: 6.5e6
        }
        METRICS [CL, CD, L_OVER_D]
        FIDELITY LIVE_CFD
    }
    """
    program = parse_aml(script)
    assert len(program.statements) == 1
    stmt = program.statements[0]
    assert isinstance(stmt, CompareStatement)
    assert stmt.base_geometry == "RAE2822"
    assert stmt.candidate_geometries == ["NACA64A010", "SC(2)-0714"]
    assert stmt.conditions.mach == 0.73
    assert "L_OVER_D" in stmt.metrics

    val = validate_aml(program)
    assert val.is_valid


def test_aml_parse_optimize():
    script = """
    OPTIMIZE "High-Lift Flap" {
        GEOMETRY "NACA2412"
        OBJECTIVE MAXIMIZE L_OVER_D
        CONSTRAINTS {
            CD <= 0.03,
            thickness >= 0.12
        }
        CONDITIONS {
            alpha: 8.0 deg,
            Re: 1.5e6
        }
        MAX_ITERATIONS 30
        FIDELITY PANEL
        AUTONOMY L4_GOAL_DRIVEN
    }
    """
    program = parse_aml(script)
    assert len(program.statements) == 1
    stmt = program.statements[0]
    assert isinstance(stmt, OptimizeStatement)
    assert stmt.objective.direction == ObjectiveDirection.MAXIMIZE
    assert stmt.objective.metric == "L_OVER_D"
    assert len(stmt.constraints) == 2
    assert stmt.constraints[0].operator == ConstraintOp.LE
    assert stmt.constraints[0].value == 0.03
    assert stmt.max_iterations == 30
    assert stmt.autonomy_level == "L4_GOAL_DRIVEN"


def test_aml_parse_sweep():
    script = """
    SWEEP "AoA Polar" {
        GEOMETRY "NACA0012"
        VARIABLE alpha FROM -4.0 TO 16.0 STEP 2.0 deg
        CONDITIONS {
            Mach: 0.15,
            Re: 3.0e6
        }
        RECORD [CL, CD, CM]
        FIDELITY PANEL
    }
    """
    program = parse_aml(script)
    assert len(program.statements) == 1
    stmt = program.statements[0]
    assert isinstance(stmt, SweepStatement)
    pts = stmt.sweep_range.points
    assert len(pts) == 11
    assert pts[0] == -4.0
    assert pts[-1] == 16.0


def test_aml_parse_validate():
    script = """
    VALIDATE "Grid Convergence" {
        GEOMETRY "NACA0012"
        DATASET "Abbott_1945"
        TOLERANCE 0.03
        CRITERIA [DRAG_POSITIVITY, BOUNDED_PRESSURE]
    }
    """
    program = parse_aml(script)
    assert len(program.statements) == 1
    stmt = program.statements[0]
    assert isinstance(stmt, ValidateStatement)
    assert stmt.dataset == "Abbott_1945"
    assert stmt.tolerance == 0.03


def test_aml_semantic_validator_catches_physical_errors():
    # Negative Reynolds number should fail validation
    invalid_script = """
    INVESTIGATE "Physical Violation" {
        GEOMETRY "NACA0012"
        CONDITIONS {
            Re: -50000.0,
            Mach: -0.5,
            alpha: 120.0 deg
        }
    }
    """
    program = parse_aml(invalid_script)
    val = validate_aml(program)
    assert not val.is_valid
    err_msgs = [e.message for e in val.errors]
    assert any("Reynolds" in m for m in err_msgs)
    assert any("Mach" in m for m in err_msgs)
    assert any("Angle of attack" in m for m in err_msgs)


def test_aml_serialization_roundtrip():
    script = """
    INVESTIGATE "Roundtrip Test" {
        GEOMETRY "NACA0012"
        CONDITIONS {
            alpha: 4.0 deg,
            Mach: 0.15,
            Re: 3000000.0
        }
        OBJECTIVES [CL, CD, CM]
        FIDELITY PANEL
        TOLERANCE 0.05
        AUTONOMY L3_BOUNDED
    }
    """
    program = parse_aml(script)
    serialized = serialize_aml(program)
    assert "INVESTIGATE" in serialized
    assert 'GEOMETRY "NACA0012"' in serialized

    # Re-parse serialized output
    program2 = parse_aml(serialized)
    assert len(program2.statements) == 1
    assert program2.statements[0].geometry == "NACA0012"
    assert program2.statements[0].conditions.alpha_deg == 4.0
