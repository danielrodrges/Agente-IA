"""
Modelo de dados para campanhas de mensagens ativas.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
from enum import Enum


class TipoCampanha(str, Enum):
    """Tipos de campanha."""
    CONFIRMACAO_CONSULTA = "confirmacao_consulta"
    LEMBRETE_CONSULTA = "lembrete_consulta"
    FOLLOWUP_POS_CONSULTA = "followup_pos_consulta"
    REENGAJAMENTO = "reengajamento"
    RESULTADO_EXAME = "resultado_exame"
    PESQUISA_SATISFACAO = "pesquisa_satisfacao"
    PERSONALIZADO = "personalizado"


class StatusCampanha(str, Enum):
    """Status da campanha."""
    RASCUNHO = "rascunho"
    AGENDADA = "agendada"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDA = "concluida"
    PAUSADA = "pausada"
    CANCELADA = "cancelada"


class StatusEnvio(str, Enum):
    """Status de envio individual."""
    PENDENTE = "pendente"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    LIDO = "lido"
    RESPONDIDO = "respondido"
    ERRO = "erro"


class Campanha(Base):
    """
    Tabela de campanhas de mensagens ativas.
    """
    __tablename__ = "campanhas"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identificação
    nome = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=True)
    tipo = Column(SQLEnum(TipoCampanha), nullable=False)
    
    # Template Meta
    template_name = Column(String(100), nullable=True)
    template_language = Column(String(10), default="pt_BR")
    template_components = Column(JSON, nullable=True)
    
    # Mensagem personalizada (para quando não usa template)
    mensagem_texto = Column(Text, nullable=True)
    
    # Configurações de agendamento
    agendamento_tipo = Column(String(20), default="unico")  # unico, recorrente
    agendamento_cron = Column(String(50), nullable=True)  # Cron expression para recorrente
    antecedencia_horas = Column(Integer, default=24)  # Horas antes do evento
    
    # Sessão Meta vinculada
    sessao_id = Column(Integer, nullable=True)
    
    # Status
    status = Column(SQLEnum(StatusCampanha), nullable=False, default=StatusCampanha.RASCUNHO)
    
    # Métricas
    total_destinatarios = Column(Integer, default=0)
    total_enviados = Column(Integer, default=0)
    total_entregues = Column(Integer, default=0)
    total_lidos = Column(Integer, default=0)
    total_respondidos = Column(Integer, default=0)
    total_erros = Column(Integer, default=0)
    
    # Timestamps
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
    agendado_para = Column(DateTime(timezone=True), nullable=True)
    executado_em = Column(DateTime(timezone=True), nullable=True)
    concluido_em = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Campanha(id={self.id}, nome='{self.nome}', tipo='{self.tipo}', status='{self.status}')>"


class CampanhaEnvio(Base):
    """
    Tabela de envios individuais de uma campanha.
    """
    __tablename__ = "campanha_envios"

    id = Column(Integer, primary_key=True, index=True)
    
    campanha_id = Column(Integer, nullable=False, index=True)
    
    # Destinatário
    telefone = Column(String(20), nullable=False)
    nome_paciente = Column(String(100), nullable=True)
    paciente_id = Column(String(50), nullable=True)
    
    # Dados do evento (consulta/exame)
    agendamento_id = Column(String(50), nullable=True)
    evento_data_hora = Column(DateTime(timezone=True), nullable=True)
    evento_descricao = Column(String(200), nullable=True)
    
    # Parâmetros do template
    template_params = Column(JSON, nullable=True)
    
    # Status
    status = Column(SQLEnum(StatusEnvio), nullable=False, default=StatusEnvio.PENDENTE)
    mensagem_id_whatsapp = Column(String(100), nullable=True)
    resposta_paciente = Column(Text, nullable=True)
    erro = Column(Text, nullable=True)
    
    # Timestamps
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    enviado_em = Column(DateTime(timezone=True), nullable=True)
    entregue_em = Column(DateTime(timezone=True), nullable=True)
    lido_em = Column(DateTime(timezone=True), nullable=True)
    respondido_em = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<CampanhaEnvio(id={self.id}, campanha_id={self.campanha_id}, telefone='{self.telefone}', status='{self.status}')>"
