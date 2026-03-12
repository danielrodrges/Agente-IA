"""
Schemas Pydantic para MCP.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class MCPClientCriar(BaseModel):
    """Schema para criar um novo cliente MCP."""
    agente_id: int
    nome: str = Field(..., min_length=1, max_length=100, description="Nome do servidor MCP")
    descricao: Optional[str] = Field(None, description="Descrição do servidor")
    preset_key: Optional[str] = Field(None, description="Identificador do preset aplicado")
    preset_inputs: Optional[Dict[str, str]] = Field(
        default=None,
        description="Valores fornecidos pelo usuário para inputs do preset"
    )
    transport_type: Literal["stdio", "sse", "streamable-http"] = Field(
        "stdio",
        description="Tipo de transporte MCP"
    )
    
    # Campos para STDIO
    command: Optional[str] = Field(None, description="Comando para executar (python, npx, uv, etc.)")
    args: Optional[List[str]] = Field(None, description="Argumentos do comando")
    env_vars: Optional[Dict[str, str]] = Field(None, description="Variáveis de ambiente")
    
    # Campos para SSE/HTTP
    url: Optional[str] = Field(None, description="URL do servidor MCP (para HTTP/SSE)")
    headers: Optional[Dict[str, str]] = Field(None, description="Headers HTTP para autenticação ou metadados")
    
    ativo: bool = Field(True, description="Se o cliente está ativo")
    
    @field_validator('command')
    @classmethod
    def validar_stdio_command(cls, v, info):
        """Valida que command está presente se transport_type é stdio."""
        if (
            info.data.get('transport_type') == 'stdio'
            and not v
            and not info.data.get('preset_key')
        ):
            raise ValueError("Command é obrigatório para transport_type=stdio")
        return v
    
    @field_validator('url')
    @classmethod
    def validar_http_url(cls, v, info):
        """Valida que URL está presente se transport_type é http."""
        transport = info.data.get('transport_type')
        if (
            transport in ['sse', 'streamable-http']
            and not v
            and not info.data.get('preset_key')
        ):
            raise ValueError(f"URL é obrigatória para transport_type={transport}")
        return v


class MCPClientAtualizar(BaseModel):
    """Schema para atualizar um cliente MCP."""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = None
    ativo: Optional[bool] = None
    # Não permite mudar transport/conexão (deletar e recriar se necessário)


class MCPToolResposta(BaseModel):
    """Schema de resposta para uma tool MCP."""
    id: int
    mcp_client_id: int
    name: str
    display_name: Optional[str]
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]]
    ativa: bool
    criado_em: datetime
    ultima_sincronizacao: datetime
    
    class Config:
        from_attributes = True


class MCPClientResposta(BaseModel):
    """Schema de resposta para um cliente MCP."""
    id: int
    agente_id: int
    nome: str
    descricao: Optional[str]
    transport_type: str
    preset_key: Optional[str]
    preset_inputs: Optional[Dict[str, str]]
    conectado: bool
    ativo: bool
    ultimo_erro: Optional[str]
    
    # Metadados do servidor
    server_name: Optional[str]
    server_version: Optional[str]
    command: Optional[str]
    args: Optional[List[str]]
    env_vars: Optional[Dict[str, str]]
    url: Optional[str]
    headers: Optional[Dict[str, str]]
    
    # Estatísticas
    total_tools: int = Field(0, description="Número de tools ativas")
    
    # Timestamps
    criado_em: datetime
    ultima_conexao: Optional[datetime]
    ultima_sincronizacao: Optional[datetime]
    
    class Config:
        from_attributes = True


class MCPClientComTools(MCPClientResposta):
    """Schema de resposta de cliente MCP com suas tools."""
    tools: List[MCPToolResposta] = []


class MCPPresetResposta(BaseModel):
    """Informações exibidas sobre um preset disponível."""
    key: str
    name: str
    description: str
    transport_type: str
    tags: List[str]
    documentation_url: Optional[str]
    notes: Optional[str]
    command: Optional[str]
    args: Optional[List[str]]
    url: Optional[str]
    env: Dict[str, str]
    headers: Dict[str, str]
    inputs: List[Dict[str, Any]]


class MCPOneClickRequest(BaseModel):
    """Payload para instalar MCP via JSON one-click."""
    agente_id: int
    json_config: str = Field(..., description="JSON de configuração MCP no formato padrão (mcpServers)")
    nome: Optional[str] = Field(None, description="Sobrescreve o nome extraído do JSON")
    descricao: Optional[str] = None


class MCPPresetAplicarRequest(BaseModel):
    """Payload para aplicar um preset a um agente."""
    preset_key: str
    agente_id: int
    nome: Optional[str] = Field(None, description="Sobrescreve o nome padrão sugerido")
    descricao: Optional[str] = None
    inputs: Optional[Dict[str, str]] = None


class MCPConexaoStatus(BaseModel):
    """Status de conexão de um cliente MCP."""
    mcp_client_id: int
    conectado: bool
    server_name: Optional[str]
    server_version: Optional[str]
    total_tools: int
    mensagem: str


class MCPToolExecutarRequest(BaseModel):
    """Request para executar uma tool MCP."""
    tool_name: str
    arguments: Dict[str, Any]


class MCPToolExecutarResposta(BaseModel):
    """Resposta da execução de uma tool MCP."""
    sucesso: bool
    structured_content: Optional[Dict[str, Any]]  # Structured output (se houver)
    erro: Optional[str]
    tempo_ms: int
