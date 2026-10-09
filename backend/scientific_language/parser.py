"""
AASI Aerospace Mission Language (AML) Parser.
Parses AML token streams into validated AST structures.
Supports both structured block-based syntax and concise inline mission statements.
"""

from typing import Any, List, Optional, Union
from backend.scientific_language.tokens import Token, TokenType
from backend.scientific_language.lexer import AMLLexer
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


class AMLParseError(Exception):
    def __init__(self, message: str, token: Optional[Token] = None):
        if token:
            super().__init__(f"Parse error at line {token.line}, col {token.column}: {message}")
            self.line = token.line
            self.column = token.column
        else:
            super().__init__(f"Parse error: {message}")
            self.line = 1
            self.column = 1


class AMLParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def _match(self, *expected_types: TokenType) -> bool:
        return self._peek().type in expected_types

    def _consume(self, expected_type: TokenType, err_msg: str) -> Token:
        token = self._peek()
        if token.type != expected_type:
            raise AMLParseError(f"{err_msg}. Expected {expected_type.name}, found {token.type.name} ({token.value!r})", token)
        self.pos += 1
        return token

    def _advance(self) -> Token:
        tok = self._peek()
        self.pos += 1
        return tok

    def parse(self) -> AMLProgram:
        """Parse complete AML script or command list."""
        statements: List[AMLStatement] = []
        while not self._match(TokenType.EOF):
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
        return AMLProgram(statements=statements)

    def _parse_statement(self) -> AMLStatement:
        tok = self._peek()
        if tok.type == TokenType.INVESTIGATE:
            return self._parse_investigate()
        elif tok.type == TokenType.COMPARE:
            return self._parse_compare()
        elif tok.type == TokenType.OPTIMIZE:
            return self._parse_optimize()
        elif tok.type == TokenType.VALIDATE:
            return self._parse_validate()
        elif tok.type == TokenType.SWEEP:
            return self._parse_sweep()
        elif tok.type == TokenType.CHARACTERIZE:
            return self._parse_characterize()
        else:
            raise AMLParseError(f"Unexpected token at start of statement: {tok.value!r}", tok)

    # -------------------------------------------------------------------------
    # INVESTIGATE Statement
    # -------------------------------------------------------------------------
    def _parse_investigate(self) -> InvestigateStatement:
        start_tok = self._consume(TokenType.INVESTIGATE, "Expected INVESTIGATE keyword")
        name = None
        geometry = "NACA0012"
        conditions = AMLConditions()
        objectives = ["CL", "CD", "CM"]
        fidelity = "MULTI_FIDELITY"
        tolerance = 0.05
        autonomy_level = "L3_BOUNDED"

        # Check for title string or direct geometry
        if self._match(TokenType.STRING):
            name = self._advance().value

        # Block syntax: INVESTIGATE ["Title"] { ... }
        if self._match(TokenType.LBRACE):
            self._advance()
            while not self._match(TokenType.RBRACE, TokenType.EOF):
                kwd = self._advance()
                if kwd.type == TokenType.GEOMETRY:
                    geometry = self._parse_identifier_or_string()
                elif kwd.type == TokenType.CONDITIONS:
                    conditions = self._parse_conditions_block()
                elif kwd.type in (TokenType.OBJECTIVES, TokenType.OBJECTIVE):
                    objectives = self._parse_identifier_list()
                elif kwd.type == TokenType.FIDELITY:
                    fidelity = self._parse_identifier_or_string()
                elif kwd.type == TokenType.TOLERANCE:
                    tolerance = float(self._consume(TokenType.NUMBER, "Expected tolerance number").value)
                elif kwd.type == TokenType.AUTONOMY:
                    autonomy_level = self._parse_identifier_or_string()
                else:
                    # Skip unknown or comma
                    if kwd.type == TokenType.COMMA:
                        continue
            self._consume(TokenType.RBRACE, "Expected '}' closing INVESTIGATE block")
        else:
            # Inline syntax: INVESTIGATE <geometry> [AT conditions] [WITH FIDELITY <fid>]
            if not name and self._match(TokenType.IDENTIFIER, TokenType.STRING):
                geometry = self._parse_identifier_or_string()
            elif name and not self._match(TokenType.AT, TokenType.WITH):
                geometry = name

            if self._match(TokenType.AT):
                self._advance()
                conditions = self._parse_inline_conditions()

            if self._match(TokenType.WITH):
                self._advance()
                if self._match(TokenType.FIDELITY):
                    self._advance()
                    fidelity = self._parse_identifier_or_string()

        return InvestigateStatement(
            line=start_tok.line,
            column=start_tok.column,
            name=name,
            geometry=geometry,
            conditions=conditions,
            objectives=objectives,
            fidelity=fidelity,
            tolerance=tolerance,
            autonomy_level=autonomy_level,
        )

    # -------------------------------------------------------------------------
    # COMPARE Statement
    # -------------------------------------------------------------------------
    def _parse_compare(self) -> CompareStatement:
        start_tok = self._consume(TokenType.COMPARE, "Expected COMPARE keyword")
        name = None
        base_geom = ""
        candidates = []
        conditions = AMLConditions()
        metrics = ["CL", "CD", "L_OVER_D"]
        fidelity = "MULTI_FIDELITY"

        if self._match(TokenType.STRING):
            name = self._advance().value

        if self._match(TokenType.LBRACE):
            self._advance()
            while not self._match(TokenType.RBRACE, TokenType.EOF):
                kwd = self._advance()
                if kwd.type == TokenType.BASE:
                    base_geom = self._parse_identifier_or_string()
                elif kwd.type == TokenType.CANDIDATES:
                    candidates = self._parse_string_or_identifier_list()
                elif kwd.type == TokenType.CONDITIONS:
                    conditions = self._parse_conditions_block()
                elif kwd.type == TokenType.METRICS:
                    metrics = self._parse_identifier_list()
                elif kwd.type == TokenType.FIDELITY:
                    fidelity = self._parse_identifier_or_string()
            self._consume(TokenType.RBRACE, "Expected '}' closing COMPARE block")
        else:
            # Inline syntax: COMPARE <base> WITH <cand1> [, <cand2>] [AT conditions]
            base_geom = self._parse_identifier_or_string()
            if self._match(TokenType.WITH):
                self._advance()
                candidates.append(self._parse_identifier_or_string())
                while self._match(TokenType.COMMA):
                    self._advance()
                    candidates.append(self._parse_identifier_or_string())
            if self._match(TokenType.AT):
                self._advance()
                conditions = self._parse_inline_conditions()

        return CompareStatement(
            line=start_tok.line,
            column=start_tok.column,
            name=name,
            base_geometry=base_geom,
            candidate_geometries=candidates,
            conditions=conditions,
            metrics=metrics,
            fidelity=fidelity,
        )

    # -------------------------------------------------------------------------
    # OPTIMIZE Statement
    # -------------------------------------------------------------------------
    def _parse_optimize(self) -> OptimizeStatement:
        start_tok = self._consume(TokenType.OPTIMIZE, "Expected OPTIMIZE keyword")
        name = None
        geometry = "NACA0012"
        obj = AMLObjective(direction=ObjectiveDirection.MAXIMIZE, metric="L_OVER_D")
        constraints = []
        conditions = AMLConditions()
        max_iters = 20
        fidelity = "PANEL"
        autonomy_level = "L3_BOUNDED"

        if self._match(TokenType.STRING):
            name = self._advance().value

        if self._match(TokenType.LBRACE):
            self._advance()
            while not self._match(TokenType.RBRACE, TokenType.EOF):
                kwd = self._advance()
                if kwd.type == TokenType.GEOMETRY:
                    geometry = self._parse_identifier_or_string()
                elif kwd.type == TokenType.OBJECTIVE:
                    obj = self._parse_objective()
                elif kwd.type == TokenType.CONSTRAINTS:
                    constraints = self._parse_constraints_block()
                elif kwd.type == TokenType.CONDITIONS:
                    conditions = self._parse_conditions_block()
                elif kwd.type == TokenType.MAX_ITERATIONS:
                    max_iters = int(self._consume(TokenType.NUMBER, "Expected max iterations integer").value)
                elif kwd.type == TokenType.FIDELITY:
                    fidelity = self._parse_identifier_or_string()
                elif kwd.type == TokenType.AUTONOMY:
                    autonomy_level = self._parse_identifier_or_string()
            self._consume(TokenType.RBRACE, "Expected '}' closing OPTIMIZE block")
        else:
            geometry = self._parse_identifier_or_string()
            if self._match(TokenType.FOR):
                self._advance()
            if self._match(TokenType.MAXIMIZE, TokenType.MINIMIZE, TokenType.TARGET):
                obj = self._parse_objective()
            if self._match(TokenType.AT):
                self._advance()
                conditions = self._parse_inline_conditions()

        return OptimizeStatement(
            line=start_tok.line,
            column=start_tok.column,
            name=name,
            geometry=geometry,
            objective=obj,
            constraints=constraints,
            conditions=conditions,
            max_iterations=max_iters,
            fidelity=fidelity,
            autonomy_level=autonomy_level,
        )

    # -------------------------------------------------------------------------
    # VALIDATE Statement
    # -------------------------------------------------------------------------
    def _parse_validate(self) -> ValidateStatement:
        start_tok = self._consume(TokenType.VALIDATE, "Expected VALIDATE keyword")
        name = None
        geometry = "NACA0012"
        dataset = None
        tolerance = 0.05
        criteria = ["DRAG_POSITIVITY", "BOUNDED_PRESSURE"]

        if self._match(TokenType.STRING):
            name = self._advance().value

        if self._match(TokenType.LBRACE):
            self._advance()
            while not self._match(TokenType.RBRACE, TokenType.EOF):
                kwd = self._advance()
                if kwd.type == TokenType.GEOMETRY:
                    geometry = self._parse_identifier_or_string()
                elif kwd.type == TokenType.DATASET:
                    dataset = self._parse_identifier_or_string()
                elif kwd.type == TokenType.TOLERANCE:
                    tolerance = float(self._consume(TokenType.NUMBER, "Expected tolerance").value)
                elif kwd.type == TokenType.CRITERIA:
                    criteria = self._parse_identifier_list()
            self._consume(TokenType.RBRACE, "Expected '}' closing VALIDATE block")
        else:
            geometry = self._parse_identifier_or_string()
            if self._match(TokenType.IDENTIFIER) and self._peek().value.upper() == "AGAINST":
                self._advance()
                dataset = self._parse_identifier_or_string()

        return ValidateStatement(
            line=start_tok.line,
            column=start_tok.column,
            name=name,
            geometry=geometry,
            dataset=dataset,
            tolerance=tolerance,
            criteria=criteria,
        )

    # -------------------------------------------------------------------------
    # SWEEP Statement
    # -------------------------------------------------------------------------
    def _parse_sweep(self) -> SweepStatement:
        start_tok = self._consume(TokenType.SWEEP, "Expected SWEEP keyword")
        name = None
        geometry = "NACA0012"
        var_name = "alpha"
        start_val = 0.0
        end_val = 10.0
        step_val = 1.0
        unit = "deg"
        conditions = AMLConditions()
        records = ["CL", "CD", "CM"]
        fidelity = "PANEL"

        if self._match(TokenType.STRING):
            name = self._advance().value

        if self._match(TokenType.LBRACE):
            self._advance()
            while not self._match(TokenType.RBRACE, TokenType.EOF):
                kwd = self._advance()
                if kwd.type == TokenType.GEOMETRY:
                    geometry = self._parse_identifier_or_string()
                elif kwd.type == TokenType.VARIABLE:
                    var_name = self._parse_identifier_or_string()
                    self._consume(TokenType.FROM, "Expected FROM")
                    start_val = float(self._consume(TokenType.NUMBER, "Expected start number").value)
                    self._consume(TokenType.TO, "Expected TO")
                    end_val = float(self._consume(TokenType.NUMBER, "Expected end number").value)
                    self._consume(TokenType.STEP, "Expected STEP")
                    step_val = float(self._consume(TokenType.NUMBER, "Expected step number").value)
                    if self._match(TokenType.DEG, TokenType.RAD, TokenType.IDENTIFIER):
                        unit = str(self._advance().value)
                elif kwd.type == TokenType.CONDITIONS:
                    conditions = self._parse_conditions_block()
                elif kwd.type == TokenType.RECORD:
                    records = self._parse_identifier_list()
                elif kwd.type == TokenType.FIDELITY:
                    fidelity = self._parse_identifier_or_string()
            self._consume(TokenType.RBRACE, "Expected '}' closing SWEEP block")
        else:
            # Inline: SWEEP <var> FROM <sval> TO <eval> STEP <step> FOR <geom>
            var_name = self._parse_identifier_or_string()
            self._consume(TokenType.FROM, "Expected FROM")
            start_val = float(self._consume(TokenType.NUMBER, "Expected start number").value)
            self._consume(TokenType.TO, "Expected TO")
            end_val = float(self._consume(TokenType.NUMBER, "Expected end number").value)
            self._consume(TokenType.STEP, "Expected STEP")
            step_val = float(self._consume(TokenType.NUMBER, "Expected step number").value)
            if self._match(TokenType.FOR):
                self._advance()
                geometry = self._parse_identifier_or_string()

        sweep_range = AMLSweepRange(
            variable=var_name,
            start=start_val,
            end=end_val,
            step=step_val,
            unit=unit,
        )

        return SweepStatement(
            line=start_tok.line,
            column=start_tok.column,
            name=name,
            geometry=geometry,
            sweep_range=sweep_range,
            conditions=conditions,
            record_metrics=records,
            fidelity=fidelity,
        )

    # -------------------------------------------------------------------------
    # CHARACTERIZE Statement
    # -------------------------------------------------------------------------
    def _parse_characterize(self) -> CharacterizeStatement:
        start_tok = self._consume(TokenType.CHARACTERIZE, "Expected CHARACTERIZE keyword")
        name = None
        geometry = "NACA0012"
        reynolds = 3e6
        mach = 0.15
        fidelity = "MULTI_FIDELITY"

        if self._match(TokenType.STRING):
            name = self._advance().value

        geometry = self._parse_identifier_or_string()
        if self._match(TokenType.AT):
            self._advance()
            conds = self._parse_inline_conditions()
            reynolds = conds.reynolds or reynolds
            mach = conds.mach or mach

        return CharacterizeStatement(
            line=start_tok.line,
            column=start_tok.column,
            name=name,
            geometry=geometry,
            reynolds=reynolds,
            mach=mach,
            fidelity=fidelity,
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _parse_identifier_or_string(self) -> str:
        tok = self._peek()
        if tok.type in (TokenType.IDENTIFIER, TokenType.STRING):
            self._advance()
            return str(tok.value)
        raise AMLParseError(f"Expected identifier or string, found {tok.value!r}", tok)

    def _parse_identifier_list(self) -> List[str]:
        items = []
        if self._match(TokenType.LBRACKET):
            self._advance()
            while not self._match(TokenType.RBRACKET, TokenType.EOF):
                items.append(self._parse_identifier_or_string())
                if self._match(TokenType.COMMA):
                    self._advance()
            self._consume(TokenType.RBRACKET, "Expected ']'")
        else:
            items.append(self._parse_identifier_or_string())
        return items

    def _parse_string_or_identifier_list(self) -> List[str]:
        return self._parse_identifier_list()

    def _parse_conditions_block(self) -> AMLConditions:
        conds = AMLConditions()
        self._consume(TokenType.LBRACE, "Expected '{' for CONDITIONS")
        while not self._match(TokenType.RBRACE, TokenType.EOF):
            tok = self._advance()
            var_name = str(tok.value).lower()
            if self._match(TokenType.COLON, TokenType.EQUALS):
                self._advance()
            val = float(self._consume(TokenType.NUMBER, "Expected condition value").value)
            # optional unit
            if self._match(TokenType.DEG, TokenType.RAD, TokenType.M, TokenType.M_S, TokenType.PA, TokenType.KPA, TokenType.ATM, TokenType.K, TokenType.C):
                self._advance()

            if "alpha" in var_name:
                conds.alpha_deg = val
            elif "mach" in var_name:
                conds.mach = val
            elif "re" in var_name:
                conds.reynolds = val
            elif "alt" in var_name:
                conds.altitude_m = val
            elif "temp" in var_name:
                conds.temperature_k = val
            elif "press" in var_name:
                conds.pressure_pa = val
            elif "q" in var_name:
                conds.q_inf_pa = val
            else:
                conds.extra_params[var_name] = val

            if self._match(TokenType.COMMA):
                self._advance()
        self._consume(TokenType.RBRACE, "Expected '}' closing CONDITIONS block")
        return conds

    def _parse_inline_conditions(self) -> AMLConditions:
        conds = AMLConditions()
        while not self._match(TokenType.EOF, TokenType.WITH, TokenType.RBRACE):
            tok = self._advance()
            var_name = str(tok.value).lower()
            if self._match(TokenType.EQUALS, TokenType.COLON):
                self._advance()
            val = float(self._consume(TokenType.NUMBER, f"Expected value for condition {var_name}").value)
            if self._match(TokenType.DEG, TokenType.RAD, TokenType.M, TokenType.M_S, TokenType.PA, TokenType.KPA, TokenType.ATM, TokenType.K, TokenType.C):
                self._advance()

            if "alpha" in var_name:
                conds.alpha_deg = val
            elif "mach" in var_name:
                conds.mach = val
            elif "re" in var_name:
                conds.reynolds = val
            elif "alt" in var_name:
                conds.altitude_m = val
            else:
                conds.extra_params[var_name] = val

            if self._match(TokenType.COMMA):
                self._advance()
            else:
                break
        return conds

    def _parse_objective(self) -> AMLObjective:
        direction = ObjectiveDirection.MAXIMIZE
        if self._match(TokenType.MAXIMIZE):
            self._advance()
            direction = ObjectiveDirection.MAXIMIZE
        elif self._match(TokenType.MINIMIZE):
            self._advance()
            direction = ObjectiveDirection.MINIMIZE
        elif self._match(TokenType.TARGET):
            self._advance()
            direction = ObjectiveDirection.TARGET

        metric = self._parse_identifier_or_string()
        target_val = None
        if direction == ObjectiveDirection.TARGET and self._match(TokenType.NUMBER):
            target_val = float(self._advance().value)
        return AMLObjective(direction=direction, metric=metric, target_value=target_val)

    def _parse_constraints_block(self) -> List[AMLConstraint]:
        constraints = []
        self._consume(TokenType.LBRACE, "Expected '{' for CONSTRAINTS")
        while not self._match(TokenType.RBRACE, TokenType.EOF):
            var_name = self._parse_identifier_or_string()
            op_tok = self._advance()
            op = ConstraintOp.LE
            if op_tok.type == TokenType.LE: op = ConstraintOp.LE
            elif op_tok.type == TokenType.GE: op = ConstraintOp.GE
            elif op_tok.type == TokenType.LT: op = ConstraintOp.LT
            elif op_tok.type == TokenType.GT: op = ConstraintOp.GT
            elif op_tok.type == TokenType.EQUALS: op = ConstraintOp.EQ
            
            val = float(self._consume(TokenType.NUMBER, "Expected constraint value").value)
            constraints.append(AMLConstraint(variable=var_name, operator=op, value=val))
            if self._match(TokenType.COMMA):
                self._advance()
        self._consume(TokenType.RBRACE, "Expected '}' closing CONSTRAINTS")
        return constraints
