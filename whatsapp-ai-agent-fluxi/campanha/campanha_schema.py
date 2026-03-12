"""
Schemas Pydantic para campanhas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CampanhaCriar(BaseModel):
    """Schema para criar uma campanha."""
    nome: str
    descricao: Optional[str] = None
    tipo: str
    template_name: Optional[str] = None
    template_language: str = "pt_BR"
    template_components: Optional[List[Dict[str, Any]]] = None
    mensagem_texto: Optional[str] = None
    agendamento_tipo: str = "unico"
    agendamento_cron: Optional[str] = None
    antecedencia_horas: int = 24
    sessao_id: Optional[int] = None
    agendado_para: Optional[datetime] = None


class CampanhaAtualizar(BaseModel):
    """Schema para atualizar campanha."""
    nome: Optional[str] = None
    descricao: Optional[str] = None
    template_name: Optional[str] = None
    template_language: Optional[str] = None
    template_components: Optional[List[Dict[str, Any]]] = None
    mensagem_texto: Optional[str] = None
    agendamento_tipo: Optional[str] = None
    agendamento_cron: Optional[str] = None
    antecedencia_horas: Optional[int] = None
    agendado_para: Optional[datetime] = None
    status: Optional[str] = None


class CampanhaResposta(BaseModel):
    """Schema de resposta da campanha."""
    id: int
    nome: str
    descricao: Optional[str] = None
    tipo: str
    template_name: Optional[str] = None
    template_language: str
    mensagem_texto: Optional[str] = None
    agendamento_tipo: str
    antecedencia_horas: int
    sessao_id: Optional[int] = None
    status: str
    total_destinatarios: int
    total_enviados: int
    total_entregues: int
    total_lidos: int
    total_respondidos: int
    total_erros: int
    criado_em: Optional[datetime] = None
    agendado_para: Optional[datetime] = None
    executado_em: Optional[datetime] = None
    concluido_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class EnvioCriar(BaseModel):
    """Schema para adicionar destinatário à campanha."""
    telefone: str
    nome_paciente: Optional[str] = None
    paciente_id: Optional[str] = None
    agendamento_id: Optional[str] = None
    evento_data_hora: Optional[datetime] = None
    evento_descricao: Optional[str] = None
    template_params: Optional[Dict[str, Any]] = None


class EnvioResposta(BaseModel):
    """Schema de resposta do envio."""
    id: int
    campanha_id: int
    telefone: str
    nome_paciente: Optional[str] = None
    agendamento_id: Optional[str] = None
    evento_data_hora: Optional[datetime] = None
    evento_descricao: Optional[str] = None
    status: str
    mensagem_id_whatsapp: Optional[str] = None
    resposta_paciente: Optional[str] = None
    erro: Optional[str] = None
    criado_em: Optional[datetime] = None
    enviado_em: Optional[datetime] = None

    class Config:
        from_attributes = True
