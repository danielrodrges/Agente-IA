"""
Schemas Pydantic para validação de provedores LLM.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TipoProvedor(str, Enum):
    """Tipos de provedores LLM suportados."""
    LM_STUDIO = "lm_studio"
    LLAMA_CPP = "llama_cpp"
    OLLAMA = "ollama"


class StatusProvedor(str, Enum):
    """Status do provedor."""
    ATIVO = "ativo"
    INATIVO = "inativo"
    ERRO = "erro"


class ProvedorLLMBase(BaseModel):
    """Schema base para provedor LLM."""
    nome: str = Field(..., description="Nome do provedor")
    base_url: HttpUrl = Field(..., description="URL base da API")
    api_key: Optional[str] = Field(None, description="Chave da API (se necessário)")
    descricao: Optional[str] = Field(None, description="Descrição do provedor")
    ativo: bool = Field(default=True, description="Se o provedor está ativo")
    configuracao: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Configurações específicas")


class ProvedorLLMCriar(ProvedorLLMBase):
    """Schema para criar novo provedor LLM."""
    pass


class ProvedorLLMAtualizar(BaseModel):
    """Schema para atualizar provedor LLM."""
    nome: Optional[str] = None
    base_url: Optional[HttpUrl] = None
    api_key: Optional[str] = None
    porta: Optional[int] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None
    configuracao: Optional[Dict[str, Any]] = None


class ProvedorLLMResposta(ProvedorLLMBase):
    """Schema de resposta com dados completos."""
    id: int
    status: StatusProvedor
    criado_em: datetime
    atualizado_em: Optional[datetime] = None
    ultimo_teste: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModeloLLM(BaseModel):
    """Schema para modelo LLM disponível."""
    id: str
    nome: str
    contexto: Optional[int] = None
    suporta_imagens: bool = False
    suporta_ferramentas: bool = False
    tamanho: Optional[str] = None
    quantizacao: Optional[str] = None


class TesteConexaoResposta(BaseModel):
    """Schema de resposta ao testar conexão."""
    sucesso: bool
    mensagem: str
    modelos: Optional[List[ModeloLLM]] = None
    tempo_resposta_ms: Optional[float] = None


class ConfiguracaoProvedor(BaseModel):
    """Schema para configuração específica do provedor."""
    temperatura: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperatura para geração")
    max_tokens: int = Field(default=2000, ge=1, le=100000, description="Máximo de tokens")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Top P para amostragem")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Penalidade de frequência (evita repetição)")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Penalidade de presença (novos tópicos)")
    top_k: Optional[int] = Field(default=None, ge=1, description="Top K para amostragem")
    repeat_penalty: Optional[float] = Field(default=None, ge=0.0, description="Penalidade de repetição")
    stop: Optional[List[str]] = Field(default=None, description="Sequências de parada")
    stream: bool = Field(default=True, description="Se deve usar streaming")


class RequisicaoLLM(BaseModel):
    """Schema para requisição ao LLM."""
    # content pode ser string ou lista (para suporte a imagens/vision)
    mensagens: List[Dict[str, Any]] = Field(..., description="Lista de mensagens")
    modelo: str = Field(..., description="Nome do modelo")
    configuracao: Optional[ConfiguracaoProvedor] = Field(default=None, description="Configurações específicas")
    tools: Optional[List[Dict[str, Any]]] = Field(default=None, description="Ferramentas disponíveis para o LLM")
    stream: bool = Field(default=True, description="Se deve usar streaming")


class RespostaLLM(BaseModel):
    """Schema para resposta do LLM."""
    conteudo: str = Field(..., description="Conteúdo da resposta")
    modelo: str = Field(..., description="Modelo usado")
    tokens_usados: Optional[int] = Field(None, description="Número de tokens usados")
    tempo_geracao_ms: Optional[float] = Field(None, description="Tempo de geração em ms")
    finalizado: bool = Field(default=True, description="Se a resposta foi finalizada")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Chamadas de ferramentas")
    finish_reason: Optional[str] = Field(None, description="Motivo de finalização")


class EstatisticasProvedor(BaseModel):
    """Schema para estatísticas do provedor."""
    total_requisicoes: int = Field(default=0, description="Total de requisições")
    requisicoes_sucesso: int = Field(default=0, description="Requisições bem-sucedidas")
    requisicoes_erro: int = Field(default=0, description="Requisições com erro")
    tempo_medio_ms: float = Field(default=0.0, description="Tempo médio de resposta")
    ultima_requisicao: Optional[datetime] = Field(None, description="Última requisição")
    modelos_carregados: List[str] = Field(default_factory=list, description="Modelos atualmente carregados")
