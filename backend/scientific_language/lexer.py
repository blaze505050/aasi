"""
AASI Aerospace Mission Language (AML) Lexical Analyzer.
Extracts strongly typed tokens with precise line and column location tracking.
"""

from typing import List, Optional
from backend.scientific_language.tokens import Token, TokenType, KEYWORDS


class AMLLexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Lexical error at line {line}, col {column}: {message}")
        self.line = line
        self.column = column


class AMLLexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(source)

    def _peek(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return None

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _skip_whitespace_and_comments(self) -> None:
        while self.pos < self.length:
            ch = self.source[self.pos]
            if ch in ' \t\r\n':
                self._advance()
            elif ch == '#' or (ch == '/' and self._peek(1) == '/'):
                # Line comment
                while self.pos < self.length and self.source[self.pos] != '\n':
                    self._advance()
            else:
                break

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < self.length:
            self._skip_whitespace_and_comments()
            if self.pos >= self.length:
                break

            start_line = self.line
            start_col = self.column
            ch = self.source[self.pos]

            # 1. Delimiters and operators
            if ch == '{':
                self._advance()
                tokens.append(Token(TokenType.LBRACE, '{', start_line, start_col))
            elif ch == '}':
                self._advance()
                tokens.append(Token(TokenType.RBRACE, '}', start_line, start_col))
            elif ch == '[':
                self._advance()
                tokens.append(Token(TokenType.LBRACKET, '[', start_line, start_col))
            elif ch == ']':
                self._advance()
                tokens.append(Token(TokenType.RBRACKET, ']', start_line, start_col))
            elif ch == '(':
                self._advance()
                tokens.append(Token(TokenType.LPAREN, '(', start_line, start_col))
            elif ch == ')':
                self._advance()
                tokens.append(Token(TokenType.RPAREN, ')', start_line, start_col))
            elif ch == ':':
                self._advance()
                tokens.append(Token(TokenType.COLON, ':', start_line, start_col))
            elif ch == ',':
                self._advance()
                tokens.append(Token(TokenType.COMMA, ',', start_line, start_col))
            elif ch == '<':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.LE, '<=', start_line, start_col))
                else:
                    tokens.append(Token(TokenType.LT, '<', start_line, start_col))
            elif ch == '>':
                self._advance()
                if self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.GE, '>=', start_line, start_col))
                else:
                    tokens.append(Token(TokenType.GT, '>', start_line, start_col))
            elif ch == '=':
                self._advance()
                tokens.append(Token(TokenType.EQUALS, '=', start_line, start_col))
            
            # 2. String literals
            elif ch in ('"', "'"):
                quote_type = self._advance()
                val_chars = []
                while self.pos < self.length and self.source[self.pos] != quote_type:
                    if self.source[self.pos] == '\\' and self.pos + 1 < self.length:
                        self._advance()
                        esc = self._advance()
                        if esc == 'n': val_chars.append('\n')
                        elif esc == 't': val_chars.append('\t')
                        else: val_chars.append(esc)
                    else:
                        val_chars.append(self._advance())
                if self.pos >= self.length:
                    raise AMLLexerError("Unterminated string literal", start_line, start_col)
                self._advance()  # closing quote
                tokens.append(Token(TokenType.STRING, "".join(val_chars), start_line, start_col))

            # 3. Numbers (including negative sign when followed by digit)
            elif ch.isdigit() or (ch in ('+', '-') and self._peek(1) and (self._peek(1).isdigit() or self._peek(1) == '.')):
                num_chars = [self._advance()]
                has_dot = (num_chars[0] == '.')
                has_exp = False

                while self.pos < self.length:
                    cur = self.source[self.pos]
                    if cur.isdigit():
                        num_chars.append(self._advance())
                    elif cur == '.' and not has_dot and not has_exp:
                        has_dot = True
                        num_chars.append(self._advance())
                    elif cur in ('e', 'E') and not has_exp:
                        has_exp = True
                        num_chars.append(self._advance())
                        if self._peek() in ('+', '-'):
                            num_chars.append(self._advance())
                    else:
                        break

                num_str = "".join(num_chars)
                try:
                    num_val = float(num_str) if (has_dot or has_exp) else int(num_str)
                    tokens.append(Token(TokenType.NUMBER, num_val, start_line, start_col))
                except ValueError:
                    raise AMLLexerError(f"Invalid number format: '{num_str}'", start_line, start_col)

            # 4. Identifiers and Keywords
            elif ch.isalpha() or ch == '_':
                ident_chars = []
                while self.pos < self.length:
                    cur = self.source[self.pos]
                    # Also permit hyphens and slashes in identifiers like L/D, m/s, SC(2)-0714
                    if cur.isalnum() or cur in ('_', '-', '/'):
                        ident_chars.append(self._advance())
                    else:
                        break
                ident = "".join(ident_chars)
                upper_ident = ident.upper()

                if upper_ident in KEYWORDS:
                    tokens.append(Token(KEYWORDS[upper_ident], ident, start_line, start_col))
                elif ident in KEYWORDS:
                    tokens.append(Token(KEYWORDS[ident], ident, start_line, start_col))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, ident, start_line, start_col))

            else:
                self._advance()
                raise AMLLexerError(f"Unexpected character: {ch!r}", start_line, start_col)

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens
