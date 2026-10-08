"""
AST Nodes for the Juridico Language.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

@dataclass
class ASTNode:
    pass

@dataclass
class ObligationNode(ASTNode):
    title: str
    devedor: Optional[str] = None
    credor: Optional[str] = None
    valor: Optional[str] = None
    vencimento: Optional[str] = None
    condicoes: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class TransitionNode(ASTNode):
    name: str
    requires: List[str] = field(default_factory=list)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class AuditInfoNode(ASTNode):
    criado_em: Optional[str] = None
    criador: Optional[str] = None
    editado_em: Optional[str] = None
    ultimo_editor: Optional[str] = None
    adicoes: int = 0
    delecoes: int = 0
    uuid: Optional[str] = None
    pgp_signature: Optional[str] = None

@dataclass
class ContractNode(ASTNode):
    name: str
    initial_state: str = "RASCUNHO"
    current_state: str = "RASCUNHO"
    partes: List[str] = field(default_factory=list)
    obligations: List[ObligationNode] = field(default_factory=list)
    transitions: List[TransitionNode] = field(default_factory=list)
    audit: Optional[AuditInfoNode] = None
    raw_variables: Dict[str, Any] = field(default_factory=dict)
    pdf_verifications: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class DocumentProgram(ASTNode):
    contracts: List[ContractNode] = field(default_factory=list)
    obligations: List[ObligationNode] = field(default_factory=list)
    audit: Optional[AuditInfoNode] = None
