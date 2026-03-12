"""
Modelo de dados para provedores LLM.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum
from sqlalchemy.sql import func
from database import Base
import enum


class TipoProvedorEnum(enum.Enum):
    """Enum para tipos de provedor."""
    LM_STUDIO = "lm_studio"
    LLAMA_CPP = "llama_cpp"
    OLLAMA = "ollama"


class StatusProvedorEnum(enum.Enum):
    """Enum para status do provedor."""
    ATIVO = "ativo"
    INATIVO = "inativo"
    ERRO = "erro"


class ProvedorLLM(Base):
    """
    Tabela de provedores LLM.
    Armazena configurações de provedores como LM Studio, llama.cpp, Ollama, OpenRouter, etc.
    """
    __tablename__ = "provedores_llm"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, index=True)
    base_url = Column(String(500), nullable=False)
    api_key = Column(String(500), nullable=True)
    descricao = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)
    status = Column(Enum(StatusProvedorEnum), default=StatusProvedorEnum.INATIVO)
    configuracao = Column(JSON, default=dict)
    ultimo_teste = Column(DateTime(timezone=True), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ProvedorLLM(nome='{self.nome}', base_url='{self.base_url}')>"


class EstatisticasProvedor(Base):
    """
    Tabela de estatísticas dos provedores.
    Armazena métricas de uso e performance.
    """
    __tablename__ = "estatisticas_provedores"

    id = Column(Integer, primary_key=True, index=True)
    provedor_id = Column(Integer, nullable=False, index=True)
    total_requisicoes = Column(Integer, default=0)
    requisicoes_sucesso = Column(Integer, default=0)
    requisicoes_erro = Column(Integer, default=0)
    tempo_medio_ms = Column(Integer, default=0)  # em milissegundos
    ultima_requisicao = Column(DateTime(timezone=True), nullable=True)
    modelos_carregados = Column(JSON, default=list)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<EstatisticasProvedor(provedor_id={self.provedor_id}, total={self.total_requisicoes})>"


class ModeloProvedor(Base):
    """
    Tabela de modelos disponíveis por provedor.
    Cache dos modelos disponíveis em cada provedor.
    """
    __tablename__ = "modelos_provedores"

    id = Column(Integer, primary_key=True, index=True)
    provedor_id = Column(Integer, nullable=False, index=True)
    modelo_id = Column(String(200), nullable=False)
    nome = Column(String(200), nullable=False)
    contexto = Column(Integer, nullable=True)
    suporta_imagens = Column(Boolean, default=False)
    suporta_ferramentas = Column(Boolean, default=False)
    tamanho = Column(String(50), nullable=True)
    quantizacao = Column(String(50), nullable=True)
    ativo = Column(Boolean, default=True)
    ultima_verificacao = Column(DateTime(timezone=True), server_default=func.now())
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ModeloProvedor(provedor_id={self.provedor_id}, modelo='{self.nome}')>"
