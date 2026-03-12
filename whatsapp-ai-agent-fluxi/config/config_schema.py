"""
Schemas Pydantic para validação de configurações.
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ConfiguracaoBase(BaseModel):
    """Schema base para configuração."""
    chave: str = Field(..., description="Chave única da configuração")
    valor: Optional[str] = Field(None, description="Valor da configuração")
    tipo: str = Field(default="string", description="Tipo do valor: string, int, float, bool, json")
    descricao: Optional[str] = Field(None, description="Descrição da configuração")
    categoria: str = Field(default="geral", description="Categoria: geral, openrouter, whatsapp, agente")
    editavel: bool = Field(default=True, description="Se a configuração pode ser editada")


class ConfiguracaoCriar(ConfiguracaoBase):
    """Schema para criar nova configuração."""
    pass


class ConfiguracaoAtualizar(BaseModel):
    """Schema para atualizar configuração."""
    valor: Optional[str] = None
    descricao: Optional[str] = None


class ConfiguracaoResposta(ConfiguracaoBase):
    """Schema de resposta com dados completos."""
    id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModeloLLM(BaseModel):
    """Schema para modelo LLM disponível."""
    id: str
    nome: str
    contexto: Optional[int] = None
    preco_input: Optional[float] = None
    preco_output: Optional[float] = None
    suporta_imagens: bool = False
    suporta_ferramentas: bool = False


class TestarConexaoResposta(BaseModel):
    """Schema de resposta ao testar conexão com OpenRouter."""
    sucesso: bool
    mensagem: str
    modelos: Optional[list[ModeloLLM]] = None
