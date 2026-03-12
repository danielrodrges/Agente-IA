"""
Schemas Pydantic para validação de variáveis de ferramentas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FerramentaVariavelBase(BaseModel):
    """Schema base para variável de ferramenta."""
    chave: str = Field(..., description="Nome da variável (ex: API_TOKEN)")
    valor: str = Field(..., description="Valor da variável")
    tipo: str = Field(default="string", description="Tipo: string, secret, json")
    descricao: Optional[str] = Field(None, description="Descrição da variável")
    is_secret: bool = Field(default=True, description="Se é sensível (não mostrar)")


class FerramentaVariavelCriar(FerramentaVariavelBase):
    """Schema para criar nova variável."""
    ferramenta_id: int = Field(..., description="ID da ferramenta")


class FerramentaVariavelAtualizar(BaseModel):
    """Schema para atualizar variável."""
    valor: Optional[str] = None
    tipo: Optional[str] = None
    descricao: Optional[str] = None
    is_secret: Optional[bool] = None


class FerramentaVariavelResposta(FerramentaVariavelBase):
    """Schema de resposta com dados completos."""
    id: int
    ferramenta_id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None
    
    # Ocultar valor se for secret
    @property
    def valor_display(self):
        return "***" if self.is_secret else self.valor

    class Config:
        from_attributes = True
