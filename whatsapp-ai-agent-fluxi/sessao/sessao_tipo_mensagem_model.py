"""
Modelo de configuração de tipos de mensagem por sessão.
Define como cada sessão trata diferentes tipos de mensagem recebida.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
import enum


class AcaoTipoMensagem(str, enum.Enum):
    """Ações possíveis para cada tipo de mensagem."""
    IGNORAR = "ignorar"
    ENVIAR_IA = "enviar_ia"
    TRANSCRICAO_APENAS = "transcricao_apenas"  # Só para áudio
    RESPOSTA_FIXA = "resposta_fixa"


class TipoMensagemEnum(str, enum.Enum):
    """Tipos de mensagem suportados."""
    AUDIO = "audio"
    IMAGEM = "imagem"
    VIDEO = "video"
    STICKER = "sticker"
    LOCALIZACAO = "localizacao"
    DOCUMENTO = "documento"


class SessaoTipoMensagem(Base):
    """
    Configuração de comportamento por tipo de mensagem para cada sessão.
    Cada sessão pode ter configurações diferentes para cada tipo de mensagem.
    """
    __tablename__ = "sessao_tipo_mensagem"

    id = Column(Integer, primary_key=True, index=True)
    sessao_id = Column(Integer, ForeignKey("sessoes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Tipo de mensagem (audio, imagem, video, sticker, localizacao, documento)
    tipo = Column(String(20), nullable=False)
    
    # Ação a ser tomada (ignorar, enviar_ia, transcricao_apenas, resposta_fixa)
    acao = Column(String(30), nullable=False, default="ignorar")
    
    # Texto para resposta fixa (quando acao = resposta_fixa)
    resposta_fixa = Column(Text, nullable=True)
    
    # Relacionamento com sessão
    sessao = relationship("Sessao", back_populates="tipos_mensagem")

    def __repr__(self):
        return f"<SessaoTipoMensagem(sessao_id={self.sessao_id}, tipo='{self.tipo}', acao='{self.acao}')>"


# Configurações padrão para novos tipos de mensagem
CONFIGURACOES_PADRAO = {
    TipoMensagemEnum.AUDIO: {
        "acao": AcaoTipoMensagem.ENVIAR_IA,
        "resposta_fixa": None,
        "opcoes_disponiveis": [
            AcaoTipoMensagem.IGNORAR,
            AcaoTipoMensagem.ENVIAR_IA,
            AcaoTipoMensagem.TRANSCRICAO_APENAS,
            AcaoTipoMensagem.RESPOSTA_FIXA
        ]
    },
    TipoMensagemEnum.IMAGEM: {
        "acao": AcaoTipoMensagem.ENVIAR_IA,
        "resposta_fixa": None,
        "opcoes_disponiveis": [
            AcaoTipoMensagem.IGNORAR,
            AcaoTipoMensagem.ENVIAR_IA,
            AcaoTipoMensagem.RESPOSTA_FIXA
        ]
    },
    TipoMensagemEnum.VIDEO: {
        "acao": AcaoTipoMensagem.IGNORAR,
        "resposta_fixa": None,
        "opcoes_disponiveis": [
            AcaoTipoMensagem.IGNORAR,
            AcaoTipoMensagem.RESPOSTA_FIXA
        ]
    },
    TipoMensagemEnum.STICKER: {
        "acao": AcaoTipoMensagem.IGNORAR,
        "resposta_fixa": None,
        "opcoes_disponiveis": [
            AcaoTipoMensagem.IGNORAR,
            AcaoTipoMensagem.RESPOSTA_FIXA
        ]
    },
    TipoMensagemEnum.LOCALIZACAO: {
        "acao": AcaoTipoMensagem.IGNORAR,
        "resposta_fixa": None,
        "opcoes_disponiveis": [
            AcaoTipoMensagem.IGNORAR,
            AcaoTipoMensagem.ENVIAR_IA,
            AcaoTipoMensagem.RESPOSTA_FIXA
        ]
    },
    TipoMensagemEnum.DOCUMENTO: {
        "acao": AcaoTipoMensagem.IGNORAR,
        "resposta_fixa": None,
        "opcoes_disponiveis": [
            AcaoTipoMensagem.IGNORAR,
            AcaoTipoMensagem.RESPOSTA_FIXA
        ]
    }
}
