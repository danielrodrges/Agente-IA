"""
Modelo de dados para métricas de uso do RAG.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class RAGMetrica(Base):
    """
    Tabela de métricas de uso do RAG.
    Registra cada busca realizada na base de conhecimento.
    """
    __tablename__ = "rag_metricas"

    id = Column(Integer, primary_key=True, index=True)
    
    # Referências
    rag_id = Column(Integer, ForeignKey("rags.id", ondelete='CASCADE'), nullable=False, index=True)
    agente_id = Column(Integer, ForeignKey("agentes.id", ondelete='SET NULL'), nullable=True, index=True)
    sessao_id = Column(Integer, ForeignKey("sessoes.id", ondelete='SET NULL'), nullable=True, index=True)
    
    # Dados da busca
    query = Column(Text, nullable=False)
    telefone_cliente = Column(String(50), nullable=True, index=True)
    
    # Resultados
    num_resultados_solicitados = Column(Integer, nullable=False)
    num_resultados_retornados = Column(Integer, nullable=False)
    
    # Performance
    tempo_ms = Column(Integer, nullable=False)  # Tempo de resposta em milissegundos
    
    # Qualidade (pode ser preenchido posteriormente)
    feedback_util = Column(Boolean, nullable=True)  # Se o usuário achou útil
    
    # Timestamps
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relacionamentos
    rag = relationship("RAG", foreign_keys=[rag_id])
    agente = relationship("Agente", foreign_keys=[agente_id])
    sessao = relationship("Sessao", foreign_keys=[sessao_id])

    def __repr__(self):
        return f"<RAGMetrica(rag_id={self.rag_id}, query='{self.query[:50]}...', tempo_ms={self.tempo_ms})>"

