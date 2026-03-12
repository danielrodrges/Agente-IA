"""
Schemas Pydantic para validação de mensagens.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MensagemBase(BaseModel):
    """Schema base para mensagem."""
    sessao_id: int
    telefone_cliente: str
    nome_cliente: Optional[str] = None
    tipo: str = Field(default="texto", description="texto, imagem, documento, audio, video")
    direcao: str = Field(..., description="recebida ou enviada")
    conteudo_texto: Optional[str] = None


class MensagemCriar(MensagemBase):
    """Schema para criar nova mensagem."""
    pass


class MensagemResposta(MensagemBase):
    """Schema de resposta com dados completos."""
    id: int
    mensagem_id_whatsapp: Optional[str] = None
    conteudo_imagem_path: Optional[str] = None
    conteudo_imagem_url: Optional[str] = None
    conteudo_mime_type: Optional[str] = None
    resposta_texto: Optional[str] = None
    resposta_tokens_input: Optional[int] = None
    resposta_tokens_output: Optional[int] = None
    resposta_tempo_ms: Optional[int] = None
    resposta_modelo: Optional[str] = None
    resposta_erro: Optional[str] = None
    ferramentas_usadas: Optional[List[Dict[str, Any]]] = None
    processada: bool
    respondida: bool
    criado_em: datetime
    processado_em: Optional[datetime] = None
    respondido_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class MensagemEnviar(BaseModel):
    """Schema para enviar mensagem."""
    sessao_id: int
    telefone_destino: str
    texto: str


class HistoricoMensagens(BaseModel):
    """Schema para histórico de mensagens de um cliente."""
    telefone_cliente: str
    mensagens: List[MensagemResposta]
    total: int
