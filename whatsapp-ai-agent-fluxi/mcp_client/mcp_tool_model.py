"""
Modelo de dados para tools MCP.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class MCPTool(Base):
    """
    Tabela de tools expostas por servidores MCP.
    Sincronizadas automaticamente do servidor MCP.
    """
    __tablename__ = "mcp_tools"

    id = Column(Integer, primary_key=True, index=True)
    mcp_client_id = Column(Integer, ForeignKey("mcp_clients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Informações da Tool (do servidor MCP)
    name = Column(String(200), nullable=False)  # Nome original da tool no MCP
    display_name = Column(String(200), nullable=True)  # title ou name
    description = Column(Text, nullable=False)
    input_schema = Column(JSON, nullable=False)  # Schema de parâmetros (JSON Schema)
    output_schema = Column(JSON, nullable=True)  # Schema de resposta (se houver)
    
    # Metadados
    ativa = Column(Boolean, default=True)  # Se está disponível para uso
    
    # Timestamps
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
    ultima_sincronizacao = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamento
    mcp_client = relationship("MCPClient", back_populates="tools")

    def __repr__(self):
        return f"<MCPTool(name='{self.name}', mcp_client_id={self.mcp_client_id})>"
