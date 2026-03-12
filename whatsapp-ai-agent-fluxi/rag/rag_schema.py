"""
Schemas Pydantic para validação de dados RAG.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class RAGCriar(BaseModel):
    """Schema para criação de RAG."""
    nome: str = Field(..., min_length=1, max_length=100)
    descricao: Optional[str] = None
    provider: str = Field(default="openai")
    modelo_embed: str = Field(default="text-embedding-3-small")
    chunk_size: int = Field(default=1000, gt=0)
    chunk_overlap: int = Field(default=200, ge=0)
    top_k: int = Field(default=3, gt=0)
    score_threshold: Optional[float] = None
    api_key_embed: Optional[str] = None
    ativo: bool = True


class RAGAtualizar(BaseModel):
    """Schema para atualização de RAG."""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = None
    provider: Optional[str] = None
    modelo_embed: Optional[str] = None
    chunk_size: Optional[int] = Field(None, gt=0)
    chunk_overlap: Optional[int] = Field(None, ge=0)
    top_k: Optional[int] = Field(None, gt=0)
    score_threshold: Optional[float] = None
    api_key_embed: Optional[str] = None
    ativo: Optional[bool] = None


class RAGResposta(BaseModel):
    """Schema de resposta para RAG."""
    id: int
    nome: str
    descricao: Optional[str]
    provider: str
    modelo_embed: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    score_threshold: Optional[float]
    ativo: bool
    treinado: bool
    total_chunks: int
    storage_path: Optional[str]
    criado_em: datetime
    atualizado_em: Optional[datetime]
    treinado_em: Optional[datetime]

    class Config:
        from_attributes = True


class RAGBuscaRequest(BaseModel):
    """Schema para requisição de busca semântica."""
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(None, gt=0)
    session_id: Optional[str] = None


class RAGBuscaResultado(BaseModel):
    """Schema para resultado de busca."""
    context: str
    metadata: Dict[str, Any]
    score: Optional[float] = None


class RAGTextoRequest(BaseModel):
    """Schema para adicionar texto ao RAG."""
    titulo: str = Field(..., min_length=1, max_length=200)
    texto: str = Field(..., min_length=1)
    chunk_size: Optional[int] = Field(None, gt=0)
    chunk_overlap: Optional[int] = Field(None, ge=0)
    processar_agora: bool = True
