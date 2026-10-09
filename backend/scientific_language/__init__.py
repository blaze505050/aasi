"""
AASI Aerospace Mission Language (AML) Package.
A formal, deterministic domain-specific language for aerospace scientific missions,
multi-fidelity investigations, trade studies, and autonomous discovery.
"""

from typing import Union
from backend.scientific_language.tokens import TokenType, Token
from backend.scientific_language.lexer import AMLLexer, AMLLexerError
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
    AMLObjective,
    AMLConstraint,
    AMLSweepRange,
    ObjectiveDirection,
    ConstraintOp,
)
from backend.scientific_language.parser import AMLParser, AMLParseError
from backend.scientific_language.validator import (
    AMLSemanticValidator,
    AMLValidationResult,
    SemanticDiagnostic,
)
from backend.scientific_language.serializer import AMLSerializer


def parse_aml(source: str) -> AMLProgram:
    """Tokenize and parse AML source text into an AST."""
    lexer = AMLLexer(source)
    tokens = lexer.tokenize()
    parser = AMLParser(tokens)
    return parser.parse()


def validate_aml(item: Union[AMLProgram, AMLStatement]) -> AMLValidationResult:
    """Perform semantic and physical sanity checking on AML AST."""
    validator = AMLSemanticValidator()
    if isinstance(item, AMLProgram):
        return validator.validate_program(item)
    return validator.validate_statement(item)


def serialize_aml(item: Union[AMLProgram, AMLStatement]) -> str:
    """Format an AML AST node back to standard textual AML code."""
    if isinstance(item, AMLProgram):
        return AMLSerializer.serialize_program(item)
    return AMLSerializer.serialize_statement(item)


__all__ = [
    # Main API
    "parse_aml",
    "validate_aml",
    "serialize_aml",
    # Components
    "AMLLexer",
    "AMLLexerError",
    "AMLParser",
    "AMLParseError",
    "AMLSemanticValidator",
    "AMLValidationResult",
    "SemanticDiagnostic",
    "AMLSerializer",
    # AST
    "AMLProgram",
    "AMLStatement",
    "InvestigateStatement",
    "CompareStatement",
    "OptimizeStatement",
    "ValidateStatement",
    "SweepStatement",
    "CharacterizeStatement",
    "AMLConditions",
    "AMLObjective",
    "AMLConstraint",
    "AMLSweepRange",
    "ObjectiveDirection",
    "ConstraintOp",
    "TokenType",
    "Token",
]
