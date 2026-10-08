"""
Parser for the Juridico DSL.
Parses Portuguese legal structures into an AST.
"""

from typing import List, Optional, Dict, Any
from .lexer import Lexer, Token, TokenType
from .ast import DocumentProgram, ContractNode, ObligationNode, TransitionNode, AuditInfoNode

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.length = len(tokens)

    def current_token(self) -> Token:
        if self.pos < self.length:
            return self.tokens[self.pos]
        return self.tokens[-1]

    def peek(self, offset: int = 1) -> Token:
        target = self.pos + offset
        if target < self.length:
            return self.tokens[target]
        return self.tokens[-1]

    def advance(self) -> Token:
        tok = self.current_token()
        if self.pos < self.length:
            self.pos += 1
        return tok

    def match(self, *types: TokenType) -> bool:
        if self.current_token().type in types:
            self.advance()
            return True
        return False

    def expect(self, tok_type: TokenType, err_msg: str = "") -> Token:
        tok = self.current_token()
        if tok.type == tok_type:
            return self.advance()
        raise ValueError(
            f"Parser error at line {tok.line}, col {tok.column}: "
            f"Expected {tok_type.name}, got {tok.type.name} ('{tok.value}'). {err_msg}"
        )

    def skip_newlines(self):
        while self.current_token().type == TokenType.NEWLINE:
            self.advance()

    def parse(self) -> DocumentProgram:
        program = DocumentProgram()

        while self.current_token().type != TokenType.EOF:
            self.skip_newlines()
            if self.current_token().type == TokenType.EOF:
                break

            tok = self.current_token()
            if tok.type == TokenType.CONTRATO:
                contract = self.parse_contract()
                program.contracts.append(contract)
            elif tok.type == TokenType.OBRIGACAO:
                obligation = self.parse_obligation()
                program.obligations.append(obligation)
            elif tok.type == TokenType.AUDITORIA:
                audit = self.parse_audit()
                program.audit = audit
            else:
                # Could be raw key: value or fallback
                # Consume token to avoid infinite loop
                self.advance()

        return program

    def parse_contract(self) -> ContractNode:
        self.expect(TokenType.CONTRATO)
        name_tok = self.current_token()
        name = "ContratoSemNome"
        if name_tok.type in (TokenType.IDENTIFIER, TokenType.STRING):
            name = str(name_tok.value)
            self.advance()
        
        contract = ContractNode(name=name)

        # Parse contract body until next top-level CONTRATO or EOF
        while self.current_token().type != TokenType.EOF:
            self.skip_newlines()
            tok = self.current_token()

            if tok.type == TokenType.CONTRATO:
                break

            if tok.type == TokenType.ESTADO:
                self.advance()
                if self.current_token().type in (TokenType.ASSIGN, TokenType.COLON):
                    self.advance()
                val_tok = self.advance()
                contract.initial_state = str(val_tok.value).strip().upper()
                contract.current_state = contract.initial_state
            
            elif tok.type == TokenType.PARTES:
                self.advance()
                if self.current_token().type in (TokenType.ASSIGN, TokenType.COLON):
                    self.advance()
                # Read line of parties
                partes_str = self.consume_until_newline()
                parts = [p.strip() for p in partes_str.replace(';', ',').split(',') if p.strip()]
                contract.partes.extend(parts)

            elif tok.type == TokenType.OBRIGACAO:
                ob = self.parse_obligation()
                contract.obligations.append(ob)
                if ob.devedor and ob.devedor not in contract.partes:
                    contract.partes.append(ob.devedor)
                if ob.credor and ob.credor not in contract.partes:
                    contract.partes.append(ob.credor)

            elif tok.type == TokenType.TRANSICAO:
                tr = self.parse_transition()
                contract.transitions.append(tr)

            elif tok.type == TokenType.AUDITORIA:
                contract.audit = self.parse_audit()

            elif tok.type == TokenType.CONSULTAR_PDF:
                self.advance()
                query = self.consume_until_newline()
                contract.pdf_verifications.append({"query": query.strip()})

            else:
                # Check for key: value inside contract
                if self.peek().type in (TokenType.COLON, TokenType.ASSIGN):
                    k = self.advance().value
                    self.advance() # consume : or =
                    v = self.consume_until_newline()
                    contract.raw_variables[str(k).upper()] = v
                else:
                    self.advance()

        return contract

    def parse_obligation(self) -> ObligationNode:
        self.expect(TokenType.OBRIGACAO)
        name_tok = self.current_token()
        title = "Obrigação"
        if name_tok.type not in (TokenType.NEWLINE, TokenType.EOF):
            title = str(name_tok.value)
            self.advance()

        ob = ObligationNode(title=title)

        # Parse fields of obligation
        while self.current_token().type != TokenType.EOF:
            self.skip_newlines()
            tok = self.current_token()

            # End of obligation block if encountering another major block
            if tok.type in (TokenType.CONTRATO, TokenType.TRANSICAO, TokenType.AUDITORIA):
                break
            if tok.type == TokenType.OBRIGACAO and self.pos > 0:
                # Next obligation
                break

            if tok.type == TokenType.DEVEDOR:
                self.advance()
                if self.current_token().type in (TokenType.COLON, TokenType.ASSIGN):
                    self.advance()
                ob.devedor = self.consume_until_newline().strip()

            elif tok.type == TokenType.CREDOR:
                self.advance()
                if self.current_token().type in (TokenType.COLON, TokenType.ASSIGN):
                    self.advance()
                ob.credor = self.consume_until_newline().strip()

            elif tok.type == TokenType.VALOR:
                self.advance()
                if self.current_token().type in (TokenType.COLON, TokenType.ASSIGN):
                    self.advance()
                ob.valor = self.consume_until_newline().strip()

            elif tok.type == TokenType.VENCIMENTO:
                self.advance()
                if self.current_token().type in (TokenType.COLON, TokenType.ASSIGN):
                    self.advance()
                ob.vencimento = self.consume_until_newline().strip()

            elif tok.type == TokenType.SE:
                cond = self.parse_conditional_block()
                ob.condicoes.append(cond)

            else:
                # Maybe generic key value
                if self.peek().type in (TokenType.COLON, TokenType.ASSIGN):
                    k = self.advance().value
                    self.advance()
                    v = self.consume_until_newline()
                else:
                    break

        return ob

    def parse_conditional_block(self) -> Dict[str, Any]:
        self.expect(TokenType.SE)
        condition_text = self.consume_until_newline()
        
        then_actions = []
        else_actions = []

        self.skip_newlines()
        if self.current_token().type == TokenType.ENTAO:
            self.advance()
            # Actions under ENTAO
            while self.current_token().type != TokenType.EOF:
                self.skip_newlines()
                tok = self.current_token()
                if tok.type in (TokenType.SENAO, TokenType.SE, TokenType.CONTRATO, TokenType.TRANSICAO, TokenType.OBRIGACAO, TokenType.EOF):
                    break
                
                # Check for E / APLICAR / NOTIFICAR / assignment
                if tok.type == TokenType.E:
                    self.advance()
                action_text = self.consume_until_newline()
                if action_text.strip():
                    then_actions.append(action_text.strip())

        self.skip_newlines()
        if self.current_token().type == TokenType.SENAO:
            self.advance()
            while self.current_token().type != TokenType.EOF:
                self.skip_newlines()
                tok = self.current_token()
                if tok.type in (TokenType.SE, TokenType.CONTRATO, TokenType.TRANSICAO, TokenType.OBRIGACAO, TokenType.EOF):
                    break
                if tok.type == TokenType.E:
                    self.advance()
                action_text = self.consume_until_newline()
                if action_text.strip():
                    else_actions.append(action_text.strip())

        return {
            "se": condition_text.strip(),
            "entao": then_actions,
            "senao": else_actions
        }

    def parse_transition(self) -> TransitionNode:
        self.expect(TokenType.TRANSICAO)
        name_tok = self.current_token()
        name = "TRANSICAO"
        if name_tok.type not in (TokenType.NEWLINE, TokenType.COLON, TokenType.EOF):
            name = str(name_tok.value)
            self.advance()
        if self.current_token().type == TokenType.COLON:
            self.advance()

        tr = TransitionNode(name=name)

        while self.current_token().type != TokenType.EOF:
            self.skip_newlines()
            tok = self.current_token()

            if tok.type in (TokenType.CONTRATO, TokenType.TRANSICAO, TokenType.OBRIGACAO, TokenType.AUDITORIA):
                break

            if tok.type == TokenType.REQUER:
                self.advance()
                req_text = self.consume_until_newline()
                tr.requires.append(req_text.strip())

            elif tok.type == TokenType.SE:
                cond = self.parse_conditional_block()
                tr.conditions.append(cond)

            elif tok.type == TokenType.ENTAO:
                self.advance()
                while self.current_token().type != TokenType.EOF:
                    self.skip_newlines()
                    sub_tok = self.current_token()
                    if sub_tok.type in (TokenType.REQUER, TokenType.SE, TokenType.TRANSICAO, TokenType.CONTRATO, TokenType.OBRIGACAO, TokenType.AUDITORIA, TokenType.EOF):
                        break
                    
                    if sub_tok.type == TokenType.APLICAR:
                        self.advance()
                        target = self.consume_until_newline()
                        tr.actions.append({"type": "APLICAR", "target": target.strip()})
                    elif sub_tok.type == TokenType.NOTIFICAR:
                        self.advance()
                        target = self.consume_until_newline()
                        tr.actions.append({"type": "NOTIFICAR", "target": target.strip()})
                    else:
                        line_text = self.consume_until_newline()
                        if line_text.strip():
                            tr.actions.append({"type": "EXEC", "command": line_text.strip()})

            elif tok.type == TokenType.APLICAR:
                self.advance()
                target = self.consume_until_newline()
                tr.actions.append({"type": "APLICAR", "target": target.strip()})

            elif tok.type == TokenType.NOTIFICAR:
                self.advance()
                target = self.consume_until_newline()
                tr.actions.append({"type": "NOTIFICAR", "target": target.strip()})

            else:
                self.advance()

        return tr

    def parse_audit(self) -> AuditInfoNode:
        self.expect(TokenType.AUDITORIA)
        if self.current_token().type == TokenType.DOCUMENTO:
            self.advance()
        if self.current_token().type == TokenType.COLON:
            self.advance()

        audit = AuditInfoNode()
        while self.current_token().type != TokenType.EOF:
            self.skip_newlines()
            tok = self.current_token()

            if tok.type in (TokenType.CONTRATO, TokenType.OBRIGACAO, TokenType.TRANSICAO):
                break

            line = self.consume_until_newline().strip()
            if not line:
                continue

            lower = line.lower()
            if "criado em:" in lower or "criado em" in lower:
                audit.criado_em = line.split(":", 1)[-1].strip()
            elif "criador:" in lower or "criador" in lower:
                audit.criador = line.split(":", 1)[-1].strip()
            elif "editado pela última vez:" in lower or "editado em:" in lower or "editado" in lower:
                audit.editado_em = line.split(":", 1)[-1].strip()
            elif "último editor:" in lower or "ultimo editor:" in lower:
                audit.ultimo_editor = line.split(":", 1)[-1].strip()
            elif "uuid:" in lower:
                audit.uuid = line.split(":", 1)[-1].strip()
            elif "adicionadas" in lower or "adições" in lower or "adicoes" in lower:
                import re
                m = re.search(r'(\d+)\s+adiç', line) or re.search(r'(\d+)\s+adic', line)
                if m: audit.adicoes = int(m.group(1))
                m2 = re.search(r'(\d+)\s+deleç', line) or re.search(r'(\d+)\s+delec', line)
                if m2: audit.delecoes = int(m2.group(1))
            elif "pgp" in lower or "assinatura" in lower:
                audit.pgp_signature = line

        return audit

    def consume_until_newline(self) -> str:
        parts = []
        while self.current_token().type not in (TokenType.NEWLINE, TokenType.EOF):
            tok = self.advance()
            parts.append(str(tok.value))
        return " ".join(parts)
