"""
Modelo de comandos personalizáveis por sessão.
Permite configurar atalhos e mensagens de resposta.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class SessaoComando(Base):
    """
    Configuração de comandos personalizáveis por sessão.
    Cada sessão pode ter seus próprios comandos com textos customizados.
    """
    __tablename__ = "sessao_comandos"

    id = Column(Integer, primary_key=True, index=True)
    sessao_id = Column(Integer, ForeignKey("sessoes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Identificador do comando (limpar, ajuda, status, listar, trocar_agente)
    comando_id = Column(String(30), nullable=False)
    
    # Gatilho personalizado (ex: #limpar, @limpar, /limpar)
    gatilho = Column(String(50), nullable=False)
    
    # Se o comando está ativo
    ativo = Column(Boolean, default=True)
    
    # Mensagem de resposta personalizada (suporta variáveis)
    resposta = Column(Text, nullable=True)
    
    # Descrição do comando (para exibir no #ajuda)
    descricao = Column(String(200), nullable=True)
    
    # Relacionamento com sessão
    sessao = relationship("Sessao", back_populates="comandos")

    def __repr__(self):
        return f"<SessaoComando(sessao_id={self.sessao_id}, comando='{self.comando_id}', gatilho='{self.gatilho}')>"


# Comandos padrão do sistema
COMANDOS_PADRAO = {
    "ativar": {
        "gatilho": "#ativar",
        "descricao": "Ativa o auto-responder da IA",
        "resposta": "🤖 *IA Ativada!*\n\nAgora vou responder suas mensagens automaticamente.",
        "ativo": True
    },
    "desativar": {
        "gatilho": "#desativar",
        "descricao": "Desativa o auto-responder da IA",
        "resposta": "😴 *IA Desativada!*\n\nNão vou mais responder automaticamente.\nDigite *#ativar* quando quiser me acordar!",
        "ativo": True
    },
    "limpar": {
        "gatilho": "#limpar",
        "descricao": "Apaga o histórico de conversas",
        "resposta": "🧹 *Histórico limpo!*\n\nSeu histórico de conversas foi apagado.\nVamos começar uma nova conversa! 🆕",
        "ativo": True
    },
    "ajuda": {
        "gatilho": "#ajuda",
        "descricao": "Mostra comandos disponíveis",
        "resposta": None,  # Gerada dinamicamente
        "ativo": True
    },
    "status": {
        "gatilho": "#status",
        "descricao": "Mostra informações da sessão",
        "resposta": None,  # Gerada dinamicamente
        "ativo": True
    },
    "listar": {
        "gatilho": "#listar",
        "descricao": "Lista agentes disponíveis",
        "resposta": None,  # Gerada dinamicamente
        "ativo": True
    },
    "trocar_agente": {
        "gatilho": "#",  # Prefixo + código do agente (ex: #01)
        "descricao": "Ativa um agente específico",
        "resposta": "✅ *Agente Ativado!*\n\n🤖 *{agente_nome}*\n_{agente_descricao}_\n\nAgora estou pronto para ajudar como {agente_papel}!",
        "ativo": True
    }
}
