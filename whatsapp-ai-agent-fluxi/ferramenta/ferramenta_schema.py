"""
Schemas Pydantic para validação de ferramentas.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from ferramenta.ferramenta_model import ToolType, ToolScope, OutputDestination, ChannelType
import json


class FerramentaBase(BaseModel):
    """Schema base para ferramenta."""
    nome: str = Field(..., description="Nome da ferramenta")
    descricao: str = Field(..., description="Descrição da ferramenta")
    tool_type: ToolType = Field(default=ToolType.CODE, description="Tipo da ferramenta (web ou code)")
    tool_scope: ToolScope = Field(default=ToolScope.PRINCIPAL, description="Escopo da ferramenta")
    
    # Parâmetros (JSON string ou dict)
    params: Optional[str] = Field(None, description="Parâmetros da ferramenta em JSON")
    
    # Campos para ferramentas WEB
    curl_command: Optional[str] = Field(None, description="Comando CURL completo")
    
    # Campos para ferramentas CODE
    codigo_python: Optional[str] = Field(None, description="Código Python para executar")
    
    # Substituição e mapeamento
    substituir: bool = Field(default=True, description="Permite substituição de variáveis")
    response_map: Optional[str] = Field(None, description="Mapeamento de resposta em JSON")
    
    # Destino e canal
    output: OutputDestination = Field(default=OutputDestination.LLM, description="Destino da saída")
    channel: Optional[ChannelType] = Field(default=ChannelType.TEXT, description="Canal de comunicação")
    
    # Instruções e encadeamento
    post_instruction: Optional[str] = Field(None, description="Instrução pós-execução")
    next_tool: Optional[str] = Field(None, description="Próxima ferramenta a executar")
    print_output_var: Optional[str] = Field(None, description="Variável de saída do código Python")
    
    # Status
    ativa: bool = Field(default=True, description="Se a ferramenta está ativa")

    @field_validator('params', 'response_map')
    @classmethod
    def validate_json_fields(cls, v):
        """Valida que campos JSON são válidos."""
        if v is not None and v.strip():
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Deve ser um JSON válido")
        return v


class FerramentaCriar(FerramentaBase):
    """Schema para criar nova ferramenta."""
    pass


class FerramentaAtualizar(BaseModel):
    """Schema para atualizar ferramenta."""
    nome: Optional[str] = None
    descricao: Optional[str] = None
    tool_type: Optional[ToolType] = None
    tool_scope: Optional[ToolScope] = None
    params: Optional[str] = None
    curl_command: Optional[str] = None
    codigo_python: Optional[str] = None
    substituir: Optional[bool] = None
    response_map: Optional[str] = None
    output: Optional[OutputDestination] = None
    channel: Optional[ChannelType] = None
    post_instruction: Optional[str] = None
    next_tool: Optional[str] = None
    ativa: Optional[bool] = None

    @field_validator('params', 'response_map')
    @classmethod
    def validate_json_fields(cls, v):
        """Valida que campos JSON são válidos."""
        if v is not None and v.strip():
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Deve ser um JSON válido")
        return v


class FerramentaResposta(FerramentaBase):
    """Schema de resposta com dados completos."""
    id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True
