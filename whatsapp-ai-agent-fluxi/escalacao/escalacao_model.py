"""
Modelo de dados para escalações ao atendente humano.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
from enum import Enum


class TipoEscalacao(str, Enum):
    """Tipos de escalação."""
    DUVIDA_AGENDAMENTO = "duvida_agendamento"
    AUTORIZACAO_CANCELAMENTO = "autorizacao_cancelamento"
    INFORMACAO_ERP = "informacao_erp"
    EXCECAO_POLITICA = "excecao_politica"
    RECLAMACAO = "reclamacao"
    CADASTRO_PACIENTE = "cadastro_paciente"
    INFORMACAO_CLINICA = "informacao_clinica"
    OUTRO = "outro"


class PrioridadeEscalacao(str, Enum):
    """Prioridade da escalação."""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


class StatusEscalacao(str, Enum):
    """Status da escalação."""
    PENDENTE = "pendente"
    EM_ATENDIMENTO = "em_atendimento"
    RESPONDIDA = "respondida"
    EXPIRADA = "expirada"
    ASSUMIDA_HUMANO = "assumida_humano"
    DEVOLVIDA_IA = "devolvida_ia"


class Escalacao(Base):
    """
    Tabela de escalações para atendente humano.
    Cada escalação é uma solicitação do IA ao atendente.
    """
    __tablename__ = "escalacoes"

    id = Column(Integer, primary_key=True, index=True)
    
    # Contexto da conversa
    sessao_id = Column(Integer, nullable=False, index=True)
    telefone_cliente = Column(String(20), nullable=False, index=True)
    nome_cliente = Column(String(100), nullable=True)
    mensagem_id = Column(Integer, nullable=True)  # ID da mensagem que gerou a escalação
    
    # Dados da escalação
    tipo = Column(SQLEnum(TipoEscalacao), nullable=False, default=TipoEscalacao.OUTRO)
    prioridade = Column(SQLEnum(PrioridadeEscalacao), nullable=False, default=PrioridadeEscalacao.MEDIA)
    pergunta_ia = Column(Text, nullable=False)  # O que o IA precisa saber
    contexto_conversa = Column(JSON, nullable=True)  # Últimas mensagens para contexto
    
    # Resposta do atendente
    atendente_id = Column(String(50), nullable=True)  # Identificador do atendente
    atendente_nome = Column(String(100), nullable=True)
    resposta_atendente = Column(Text, nullable=True)
    
    # Status
    status = Column(SQLEnum(StatusEscalacao), nullable=False, default=StatusEscalacao.PENDENTE)
    
    # Métricas
    tempo_espera_ms = Column(Integer, nullable=True)  # Tempo até primeira resposta
    tempo_resolucao_ms = Column(Integer, nullable=True)  # Tempo até resolução completa
    
    # Timestamps
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    atendido_em = Column(DateTime(timezone=True), nullable=True)
    respondido_em = Column(DateTime(timezone=True), nullable=True)
    expirado_em = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Escalacao(id={self.id}, tipo='{self.tipo}', status='{self.status}', telefone='{self.telefone_cliente}')>"


class InteracaoAtendimento(Base):
    """
    Tabela de interações de atendimento.
    Registra cada interação para métricas detalhadas.
    """
    __tablename__ = "interacoes_atendimento"

    id = Column(Integer, primary_key=True, index=True)
    
    # Contexto
    sessao_id = Column(Integer, nullable=False, index=True)
    telefone_cliente = Column(String(20), nullable=False, index=True)
    nome_cliente = Column(String(100), nullable=True)
    
    # Classificação
    tipo_assunto = Column(String(50), nullable=False)  # agendamento, cancelamento, remarcacao, etc.
    sub_assunto = Column(String(100), nullable=True)  # especialidade, exame, etc.
    
    # Resolução
    resolvido_por = Column(String(10), nullable=False, default="ia")  # ia, humano, ambos
    escalacao_id = Column(Integer, nullable=True)  # Se houve escalação
    
    # Métricas
    tempo_primeira_resposta_ms = Column(Integer, nullable=True)
    tempo_resolucao_ms = Column(Integer, nullable=True)
    total_mensagens_cliente = Column(Integer, default=0)
    total_mensagens_ia = Column(Integer, default=0)
    total_ferramentas_usadas = Column(Integer, default=0)
    
    # Satisfação (futuro)
    satisfacao_nota = Column(Integer, nullable=True)  # 1-5
    satisfacao_comentario = Column(Text, nullable=True)
    
    # Resultado específico
    resultado = Column(String(50), nullable=True)  # agendado, cancelado, informado, etc.
    detalhes_resultado = Column(JSON, nullable=True)
    
    # Timestamps
    inicio_em = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    fim_em = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<InteracaoAtendimento(id={self.id}, tipo='{self.tipo_assunto}', resolvido_por='{self.resolvido_por}')>"
