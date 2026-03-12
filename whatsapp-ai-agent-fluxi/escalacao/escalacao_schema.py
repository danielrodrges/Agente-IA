"""
Schemas Pydantic para escalações.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class EscalacaoCriar(BaseModel):
    """Schema para criar uma escalação."""
    sessao_id: int
    telefone_cliente: str
    nome_cliente: Optional[str] = None
    mensagem_id: Optional[int] = None
    tipo: str = "outro"
    prioridade: str = "media"
    pergunta_ia: str = Field(..., description="A pergunta que o IA faz ao atendente")
    contexto_conversa: Optional[List[Dict[str, Any]]] = None


class EscalacaoResponder(BaseModel):
    """Schema para responder uma escalação."""
    resposta_atendente: str = Field(..., description="Resposta do atendente para o IA")
    atendente_id: Optional[str] = None
    atendente_nome: Optional[str] = None


class EscalacaoAssumir(BaseModel):
    """Schema para assumir uma conversa."""
    atendente_id: Optional[str] = None
    atendente_nome: Optional[str] = None


class EscalacaoResposta(BaseModel):
    """Schema de resposta da escalação."""
    id: int
    sessao_id: int
    telefone_cliente: str
    nome_cliente: Optional[str] = None
    mensagem_id: Optional[int] = None
    tipo: str
    prioridade: str
    pergunta_ia: str
    contexto_conversa: Optional[List[Dict[str, Any]]] = None
    atendente_id: Optional[str] = None
    atendente_nome: Optional[str] = None
    resposta_atendente: Optional[str] = None
    status: str
    tempo_espera_ms: Optional[int] = None
    tempo_resolucao_ms: Optional[int] = None
    criado_em: Optional[datetime] = None
    atendido_em: Optional[datetime] = None
    respondido_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class InteracaoCriar(BaseModel):
    """Schema para criar uma interação de atendimento."""
    sessao_id: int
    telefone_cliente: str
    nome_cliente: Optional[str] = None
    tipo_assunto: str
    sub_assunto: Optional[str] = None
    resolvido_por: str = "ia"
    escalacao_id: Optional[int] = None
    tempo_primeira_resposta_ms: Optional[int] = None
    tempo_resolucao_ms: Optional[int] = None
    total_mensagens_cliente: int = 0
    total_mensagens_ia: int = 0
    total_ferramentas_usadas: int = 0
    resultado: Optional[str] = None
    detalhes_resultado: Optional[Dict[str, Any]] = None


class InteracaoResposta(BaseModel):
    """Schema de resposta da interação."""
    id: int
    sessao_id: int
    telefone_cliente: str
    nome_cliente: Optional[str] = None
    tipo_assunto: str
    sub_assunto: Optional[str] = None
    resolvido_por: str
    escalacao_id: Optional[int] = None
    tempo_primeira_resposta_ms: Optional[int] = None
    tempo_resolucao_ms: Optional[int] = None
    total_mensagens_cliente: int
    total_mensagens_ia: int
    total_ferramentas_usadas: int
    satisfacao_nota: Optional[int] = None
    resultado: Optional[str] = None
    detalhes_resultado: Optional[Dict[str, Any]] = None
    inicio_em: Optional[datetime] = None
    fim_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class EscalacaoFiltro(BaseModel):
    """Filtros para listar escalações."""
    status: Optional[str] = None
    tipo: Optional[str] = None
    prioridade: Optional[str] = None
    sessao_id: Optional[int] = None
    atendente_id: Optional[str] = None
    limite: int = 50
    offset: int = 0
