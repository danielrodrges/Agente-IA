"""
Modelo de dados para RAG (Retrieval-Augmented Generation).
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class RAG(Base):
    """
    Tabela de configurações RAG.
    Cada RAG representa uma base de conhecimento com embeddings.
    """
    __tablename__ = "rags"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identificação
    nome = Column(String(100), nullable=False, unique=True, index=True)
    descricao = Column(Text, nullable=True)
    
    # Configurações do Provider
    provider = Column(String(50), nullable=False, default="openai")
    modelo_embed = Column(String(100), nullable=False, default="text-embedding-3-small")
    
    # Configurações de chunking
    chunk_size = Column(Integer, default=1000)
    chunk_overlap = Column(Integer, default=200)
    
    # Configurações de retrieval
    top_k = Column(Integer, default=3)
    score_threshold = Column(Float, nullable=True)
    
    # API Key
    api_key_embed = Column(Text, nullable=True)
    
    # Status
    ativo = Column(Boolean, default=True)
    treinado = Column(Boolean, default=False)
    
    # Metadados
    total_chunks = Column(Integer, default=0)
    
    # Diretório de armazenamento
    storage_path = Column(String(500), nullable=True)
    
    # Timestamps
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
    treinado_em = Column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    agentes = relationship("Agente", back_populates="rag")

    def __repr__(self):
        return f"<RAG(nome='{self.nome}', provider={self.provider}, treinado={self.treinado})>"
