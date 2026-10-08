"""
Lexer and Tokenizer for the Juridico DSL (.jur / .juridico)
Designed for Brazilian Legal Language & Finite State Machine Contracts.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Any

class TokenType(Enum):
    # Keywords / Structure
    CONTRATO = "CONTRATO"
    OBRIGACAO = "OBRIGACAO"
    ESTADO = "ESTADO"
    TRANSICAO = "TRANSICAO"
    REQUER = "REQUER"
    SE = "SE"
    ENTAO = "ENTAO"
    E = "E"
    OU = "OU"
    SENAO = "SENAO"
    APLICAR = "APLICAR"
    NOTIFICAR = "NOTIFICAR"
    AUDITORIA = "AUDITORIA"
    DOCUMENTO = "DOCUMENTO"
    CONSULTAR_PDF = "CONSULTAR_PDF"

    # Field labels
    DEVEDOR = "DEVEDOR"
    CREDOR = "CREDOR"
    VALOR = "VALOR"
    VENCIMENTO = "VENCIMENTO"
    AUTOR = "AUTOR"
    REU = "REU"
    PARTES = "PARTES"
    MULTA = "MULTA"
    JUROS = "JUROS"
    ASSINATURA = "ASSINATURA"
    
    # Operators & Symbols
    ASSIGN = "="
    COLON = ":"
    DOT = "."
    COMMA = ","
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    NEQ = "!="
    PERCENT = "%"
    
    # Literals
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    CURRENCY = "CURRENCY"
    DATE = "DATE"
    
    # Special
    EOF = "EOF"
    NEWLINE = "NEWLINE"


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line}:C{self.column})"


KEYWORDS = {
    "CONTRATO": TokenType.CONTRATO,
    "OBRIGAÇÃO": TokenType.OBRIGACAO,
    "OBRIGACAO": TokenType.OBRIGACAO,
    "ESTADO": TokenType.ESTADO,
    "TRANSIÇÃO": TokenType.TRANSICAO,
    "TRANSICAO": TokenType.TRANSICAO,
    "REQUER": TokenType.REQUER,
    "SE": TokenType.SE,
    "ENTÃO": TokenType.ENTAO,
    "ENTAO": TokenType.ENTAO,
    "E": TokenType.E,
    "OU": TokenType.OU,
    "SENÃO": TokenType.SENAO,
    "SENAO": TokenType.SENAO,
    "APLICAR": TokenType.APLICAR,
    "NOTIFICAR": TokenType.NOTIFICAR,
    "AUDITORIA": TokenType.AUDITORIA,
    "DOCUMENTO": TokenType.DOCUMENTO,
    "CONSULTAR_PDF": TokenType.CONSULTAR_PDF,
    "CONSULTAR": TokenType.CONSULTAR_PDF,
    
    "DEVEDOR": TokenType.DEVEDOR,
    "CREDOR": TokenType.CREDOR,
    "VALOR": TokenType.VALOR,
    "VENCIMENTO": TokenType.VENCIMENTO,
    "AUTOR": TokenType.AUTOR,
    "RÉU": TokenType.REU,
    "REU": TokenType.REU,
    "PARTES": TokenType.PARTES,
    "MULTA": TokenType.MULTA,
    "JUROS": TokenType.JUROS,
    "ASSINATURA": TokenType.ASSINATURA,
}


class Lexer:
    def __init__(self, source_code: str):
        self.source = source_code
        self.length = len(source_code)
        self.pos = 0
        self.line = 1
        self.col = 1

    def error(self, msg: str):
        raise ValueError(f"Lexer Error at line {self.line}, col {self.col}: {msg}")

    def peek(self, offset: int = 0) -> Optional[str]:
        target = self.pos + offset
        if target < self.length:
            return self.source[target]
        return None

    def advance(self) -> Optional[str]:
        if self.pos < self.length:
            ch = self.source[self.pos]
            self.pos += 1
            if ch == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            return ch
        return None

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        
        while self.pos < self.length:
            ch = self.peek()

            # Skip spaces & tabs
            if ch in (' ', '\t', '\r'):
                self.advance()
                continue

            # Comments with '#' or '//'
            if ch == '#' or (ch == '/' and self.peek(1) == '/'):
                while self.peek() and self.peek() != '\n':
                    self.advance()
                continue

            # Multi-line comment /* ... */
            if ch == '/' and self.peek(1) == '*':
                self.advance()
                self.advance()
                while self.peek() and not (self.peek() == '*' and self.peek(1) == '/'):
                    self.advance()
                if self.peek() == '*' and self.peek(1) == '/':
                    self.advance()
                    self.advance()
                continue

            start_col = self.col
            start_line = self.line

            # Newline
            if ch == '\n':
                self.advance()
                # Deduplicate consecutive newlines if desired
                if not tokens or tokens[-1].type != TokenType.NEWLINE:
                    tokens.append(Token(TokenType.NEWLINE, '\n', start_line, start_col))
                continue

            # Strings
            if ch in ('"', "'"):
                quote_char = self.advance()
                val = []
                while self.peek() and self.peek() != quote_char:
                    if self.peek() == '\\':
                        self.advance()
                        escaped = self.advance()
                        val.append(escaped or '')
                    else:
                        val.append(self.advance() or '')
                if self.peek() == quote_char:
                    self.advance()
                tokens.append(Token(TokenType.STRING, "".join(val), start_line, start_col))
                continue

            # Currency check (e.g. R$ 500.000 or R$500.000,00 or $500)
            if (ch == 'R' and self.peek(1) == '$') or ch == '$':
                curr_symbol = "R$" if ch == 'R' else "$"
                if ch == 'R':
                    self.advance()
                    self.advance()
                else:
                    self.advance()
                while self.peek() in (' ', '\t'):
                    self.advance()
                num_chars = []
                while self.peek() and (self.peek().isdigit() or self.peek() in ('.', ',')):
                    num_chars.append(self.advance())
                curr_val = "".join(num_chars)
                tokens.append(Token(TokenType.CURRENCY, f"{curr_symbol} {curr_val}".strip(), start_line, start_col))
                continue

            # Two-character symbols
            two_char = self.source[self.pos:self.pos+2]
            if two_char == ">=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.GTE, ">=", start_line, start_col))
                continue
            elif two_char == "<=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.LTE, "<=", start_line, start_col))
                continue
            elif two_char == "==":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.EQ, "==", start_line, start_col))
                continue
            elif two_char == "!=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.NEQ, "!=", start_line, start_col))
                continue

            # Single char symbols
            if ch == '=':
                self.advance()
                tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_col))
                continue
            elif ch == ':':
                self.advance()
                tokens.append(Token(TokenType.COLON, ":", start_line, start_col))
                continue
            elif ch == '.':
                self.advance()
                tokens.append(Token(TokenType.DOT, ".", start_line, start_col))
                continue
            elif ch == ',':
                self.advance()
                tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))
                continue
            elif ch == '>':
                self.advance()
                tokens.append(Token(TokenType.GT, ">", start_line, start_col))
                continue
            elif ch == '<':
                self.advance()
                tokens.append(Token(TokenType.LT, "<", start_line, start_col))
                continue
            elif ch == '%':
                self.advance()
                tokens.append(Token(TokenType.PERCENT, "%", start_line, start_col))
                continue

            # Date check (e.g. 10/12/2026 or 2026-12-10)
            if ch.isdigit():
                # Peek forward to check if it's a date
                chunk = self.source[self.pos:self.pos+12]
                import re
                date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2})', chunk)
                if date_match:
                    d_str = date_match.group(1)
                    for _ in range(len(d_str)):
                        self.advance()
                    tokens.append(Token(TokenType.DATE, d_str, start_line, start_col))
                    continue

                # Normal number (e.g. 500, 2%, 500.000)
                num_buf = []
                while self.peek() and (self.peek().isdigit() or self.peek() in ('.', ',')):
                    # ensure dot or comma is numeric separator
                    num_buf.append(self.advance())
                num_str = "".join(num_buf)
                tokens.append(Token(TokenType.NUMBER, num_str, start_line, start_col))
                continue

            # Identifiers or Keywords (supports latin characters á, é, í, ó, ú, ç, ã, õ, etc.)
            if ch.isalpha() or ch == '_' or ord(ch) > 127:
                ident_buf = []
                while self.peek() and (self.peek().isalnum() or self.peek() in ('_', '-') or ord(self.peek()) > 127):
                    ident_buf.append(self.advance())
                ident_str = "".join(ident_buf)
                upper_key = ident_str.upper()

                if upper_key in KEYWORDS:
                    tokens.append(Token(KEYWORDS[upper_key], ident_str, start_line, start_col))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, ident_str, start_line, start_col))
                continue

            # If unrecognized character
            self.advance()
            # fallback as identifier or ignore

        tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return tokens
