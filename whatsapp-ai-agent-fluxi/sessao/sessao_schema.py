"""
Schemas Pydantic para validação de sessões.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SessaoBase(BaseModel):
    """Schema base para sessão."""
    nome: str = Field(..., description="Nome identificador da sessão")
    auto_responder: bool = Field(default=True, description="Auto responder mensagens")
    salvar_historico: bool = Field(default=True, description="Salvar histórico de mensagens")


class SessaoCriar(SessaoBase):
    """Schema para criar nova sessão."""
    pass


class SessaoAtualizar(BaseModel):
    """Schema para atualizar sessão."""
    nome: Optional[str] = None
    auto_responder: Optional[bool] = None
    salvar_historico: Optional[bool] = None
    ativa: Optional[bool] = None
    agente_ativo_id: Optional[int] = None


class SessaoResposta(SessaoBase):
    """Schema de resposta com dados completos."""
    id: int
    telefone: Optional[str] = None
    status: str
    qr_code: Optional[str] = None
    ativa: bool
    agente_ativo_id: Optional[int] = None
    criado_em: datetime
    atualizado_em: Optional[datetime] = None
    ultima_conexao: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessaoConectar(BaseModel):
    """Schema para conectar sessão."""
    sessao_id: int


class SessaoDesconectar(BaseModel):
    """Schema para desconectar sessão."""
    sessao_id: int


class SessaoStatusResposta(BaseModel):
    """Schema de resposta de status da sessão."""
    id: int
    nome: str
    status: str
    telefone: Optional[str] = None
    qr_code: Optional[str] = None
    mensagem: str
