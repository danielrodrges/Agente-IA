"""
Serviço para gerenciar configurações de tipos de mensagem por sessão.
"""
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from sessao.sessao_tipo_mensagem_model import (
    SessaoTipoMensagem,
    TipoMensagemEnum,
    AcaoTipoMensagem,
    CONFIGURACOES_PADRAO
)


class SessaoTipoMensagemService:
    """Serviço para gerenciar tipos de mensagem por sessão."""
    
    @staticmethod
    def criar_configuracoes_padrao(db: Session, sessao_id: int) -> List[SessaoTipoMensagem]:
        """
        Cria configurações padrão para todos os tipos de mensagem de uma sessão.
        Chamado automaticamente ao criar uma nova sessão.
        """
        configs_criadas = []
        
        for tipo in TipoMensagemEnum:
            config_padrao = CONFIGURACOES_PADRAO.get(tipo, {})
            
            config = SessaoTipoMensagem(
                sessao_id=sessao_id,
                tipo=tipo.value,
                acao=config_padrao.get("acao", AcaoTipoMensagem.IGNORAR).value,
                resposta_fixa=config_padrao.get("resposta_fixa")
            )
            db.add(config)
            configs_criadas.append(config)
        
        db.commit()
        return configs_criadas
    
    @staticmethod
    def listar_por_sessao(db: Session, sessao_id: int) -> List[SessaoTipoMensagem]:
        """Lista todas as configurações de tipos de mensagem de uma sessão."""
        return db.query(SessaoTipoMensagem).filter(
            SessaoTipoMensagem.sessao_id == sessao_id
        ).all()
    
    @staticmethod
    def obter_por_tipo(db: Session, sessao_id: int, tipo: str) -> Optional[SessaoTipoMensagem]:
        """Obtém a configuração de um tipo específico de mensagem."""
        return db.query(SessaoTipoMensagem).filter(
            SessaoTipoMensagem.sessao_id == sessao_id,
            SessaoTipoMensagem.tipo == tipo
        ).first()
    
    @staticmethod
    def atualizar(
        db: Session,
        sessao_id: int,
        tipo: str,
        acao: str,
        resposta_fixa: Optional[str] = None
    ) -> Optional[SessaoTipoMensagem]:
        """Atualiza a configuração de um tipo de mensagem."""
        config = SessaoTipoMensagemService.obter_por_tipo(db, sessao_id, tipo)
        
        if not config:
            # Criar se não existir
            config = SessaoTipoMensagem(
                sessao_id=sessao_id,
                tipo=tipo,
                acao=acao,
                resposta_fixa=resposta_fixa
            )
            db.add(config)
        else:
            config.acao = acao
            config.resposta_fixa = resposta_fixa
        
        db.commit()
        db.refresh(config)
        return config
    
    @staticmethod
    def atualizar_todos(
        db: Session,
        sessao_id: int,
        configuracoes: Dict[str, Dict]
    ) -> List[SessaoTipoMensagem]:
        """
        Atualiza todas as configurações de tipos de mensagem de uma sessão.
        
        Args:
            configuracoes: Dict no formato {tipo: {acao: str, resposta_fixa: str}}
        """
        configs_atualizadas = []
        
        for tipo, dados in configuracoes.items():
            config = SessaoTipoMensagemService.atualizar(
                db,
                sessao_id,
                tipo,
                dados.get("acao", "ignorar"),
                dados.get("resposta_fixa")
            )
            configs_atualizadas.append(config)
        
        return configs_atualizadas
    
    @staticmethod
    def obter_acao(db: Session, sessao_id: int, tipo: str) -> Dict:
        """
        Obtém a ação configurada para um tipo de mensagem.
        Retorna um dict com a ação e resposta fixa (se houver).
        
        Usado pelo processamento de mensagens.
        """
        config = SessaoTipoMensagemService.obter_por_tipo(db, sessao_id, tipo)
        
        if not config:
            # Usar padrão se não houver configuração
            try:
                tipo_enum = TipoMensagemEnum(tipo)
                padrao = CONFIGURACOES_PADRAO.get(tipo_enum, {})
                return {
                    "acao": padrao.get("acao", AcaoTipoMensagem.IGNORAR).value,
                    "resposta_fixa": None
                }
            except ValueError:
                return {
                    "acao": AcaoTipoMensagem.IGNORAR.value,
                    "resposta_fixa": None
                }
        
        return {
            "acao": config.acao,
            "resposta_fixa": config.resposta_fixa
        }
    
    @staticmethod
    def obter_opcoes_disponiveis(tipo: str) -> List[str]:
        """Retorna as opções de ação disponíveis para um tipo de mensagem."""
        try:
            tipo_enum = TipoMensagemEnum(tipo)
            config = CONFIGURACOES_PADRAO.get(tipo_enum, {})
            opcoes = config.get("opcoes_disponiveis", [AcaoTipoMensagem.IGNORAR])
            return [o.value for o in opcoes]
        except ValueError:
            return [AcaoTipoMensagem.IGNORAR.value]
    
    @staticmethod
    def deletar_por_sessao(db: Session, sessao_id: int) -> int:
        """Remove todas as configurações de uma sessão. Retorna quantidade removida."""
        count = db.query(SessaoTipoMensagem).filter(
            SessaoTipoMensagem.sessao_id == sessao_id
        ).delete()
        db.commit()
        return count
