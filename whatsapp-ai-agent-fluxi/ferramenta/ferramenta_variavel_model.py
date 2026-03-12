"""
Modelo de dados para variáveis de ferramentas.
Armazena tokens, API keys e outras configurações por ferramenta.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class FerramentaVariavel(Base):
    """
    Tabela de variáveis de ferramentas.
    Armazena tokens de API, chaves secretas e outras configurações.
    """
    __tablename__ = "ferramenta_variaveis"

    id = Column(Integer, primary_key=True, index=True)
    ferramenta_id = Column(Integer, ForeignKey("ferramentas.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Identificação da variável
    chave = Column(String(100), nullable=False)  # Ex: "API_TOKEN", "SECRET_KEY"
    valor = Column(Text, nullable=False)  # Valor da variável (pode ser criptografado)
    
    # Tipo e descrição
    tipo = Column(String(20), default="string")  # string, secret, json
    descricao = Column(Text, nullable=True)
    
    # Segurança
    is_secret = Column(Boolean, default=True)  # Se é sensível (não mostrar no frontend)
    
    # Timestamps
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamento
    ferramenta = relationship("Ferramenta", back_populates="variaveis")

    def __repr__(self):
        valor_display = "***" if self.is_secret else self.valor[:20]
        return f"<FerramentaVariavel(ferramenta_id={self.ferramenta_id}, chave='{self.chave}', valor='{valor_display}')>"
