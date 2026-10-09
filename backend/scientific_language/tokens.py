"""
AASI Aerospace Mission Language (AML) Tokenizer Definitions.
"""

from enum import Enum, auto
from typing import Any, NamedTuple, Optional


class TokenType(Enum):
    # End of input / formatting
    EOF = auto()
    NEWLINE = auto()
    
    # Literals & Identifiers
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    
    # Delimiters & Operators
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    COLON = auto()        # :
    COMMA = auto()        # ,
    EQUALS = auto()       # =
    LE = auto()           # <=
    GE = auto()           # >=
    LT = auto()           # <
    GT = auto()           # >
    
    # Top-Level Mission Commands
    INVESTIGATE = auto()
    COMPARE = auto()
    OPTIMIZE = auto()
    VALIDATE = auto()
    SWEEP = auto()
    CHARACTERIZE = auto()
    
    # Clauses & Parameter Keywords
    GEOMETRY = auto()
    CONDITIONS = auto()
    OBJECTIVES = auto()
    OBJECTIVE = auto()
    CONSTRAINTS = auto()
    FIDELITY = auto()
    TOLERANCE = auto()
    AUTONOMY = auto()
    BASE = auto()
    CANDIDATES = auto()
    METRICS = auto()
    VARIABLE = auto()
    FROM = auto()
    TO = auto()
    STEP = auto()
    RECORD = auto()
    DATASET = auto()
    CRITERIA = auto()
    MAX_ITERATIONS = auto()
    AT = auto()
    WITH = auto()
    FOR = auto()
    MAXIMIZE = auto()
    MINIMIZE = auto()
    TARGET = auto()
    
    # Physical Units
    DEG = auto()
    RAD = auto()
    M = auto()
    M_S = auto()
    PA = auto()
    KPA = auto()
    ATM = auto()
    K = auto()
    C = auto()
    PCT = auto()


KEYWORDS = {
    "INVESTIGATE": TokenType.INVESTIGATE,
    "COMPARE": TokenType.COMPARE,
    "OPTIMIZE": TokenType.OPTIMIZE,
    "VALIDATE": TokenType.VALIDATE,
    "SWEEP": TokenType.SWEEP,
    "CHARACTERIZE": TokenType.CHARACTERIZE,
    "GEOMETRY": TokenType.GEOMETRY,
    "CONDITIONS": TokenType.CONDITIONS,
    "OBJECTIVES": TokenType.OBJECTIVES,
    "OBJECTIVE": TokenType.OBJECTIVE,
    "CONSTRAINTS": TokenType.CONSTRAINTS,
    "FIDELITY": TokenType.FIDELITY,
    "TOLERANCE": TokenType.TOLERANCE,
    "AUTONOMY": TokenType.AUTONOMY,
    "BASE": TokenType.BASE,
    "CANDIDATES": TokenType.CANDIDATES,
    "METRICS": TokenType.METRICS,
    "VARIABLE": TokenType.VARIABLE,
    "FROM": TokenType.FROM,
    "TO": TokenType.TO,
    "STEP": TokenType.STEP,
    "RECORD": TokenType.RECORD,
    "DATASET": TokenType.DATASET,
    "CRITERIA": TokenType.CRITERIA,
    "MAX_ITERATIONS": TokenType.MAX_ITERATIONS,
    "AT": TokenType.AT,
    "WITH": TokenType.WITH,
    "FOR": TokenType.FOR,
    "MAXIMIZE": TokenType.MAXIMIZE,
    "MINIMIZE": TokenType.MINIMIZE,
    "TARGET": TokenType.TARGET,
    # Units
    "deg": TokenType.DEG,
    "rad": TokenType.RAD,
    "m": TokenType.M,
    "m/s": TokenType.M_S,
    "Pa": TokenType.PA,
    "kPa": TokenType.KPA,
    "atm": TokenType.ATM,
    "K": TokenType.K,
    "C": TokenType.C,
    "%": TokenType.PCT,
}


class Token(NamedTuple):
    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"
