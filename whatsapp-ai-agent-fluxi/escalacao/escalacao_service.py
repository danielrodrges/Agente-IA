"""
Serviço de escalação para atendente humano (Human-in-the-Loop).
Gerencia o fluxo invertido onde o IA sempre comunica com o cliente
e solicita ajuda do atendente quando necessário.
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from escalacao.escalacao_model import (
    Escalacao,
    InteracaoAtendimento,
    StatusEscalacao,
    TipoEscalacao,
    PrioridadeEscalacao,
)
from escalacao.escalacao_schema import (
    EscalacaoCriar,
    EscalacaoResponder,
    InteracaoCriar,
)

logger = logging.getLogger(__name__)

# Store para callbacks de escalação (em memória)
# Mapeia escalacao_id -> callback info para retomar processamento
_escalacao_callbacks: Dict[int, Dict[str, Any]] = {}

# Store para notificações WebSocket
_websocket_connections: List[Any] = []


class EscalacaoService:
    """Serviço para gerenciar escalações ao atendente humano."""

    # --- CRUD ---

    @staticmethod
    def criar_escalacao(db: Session, escalacao: EscalacaoCriar) -> Escalacao:
        """
        Cria uma nova escalação.
        Chamada pelo agente IA quando precisa de ajuda do atendente.
        """
        db_escalacao = Escalacao(
            sessao_id=escalacao.sessao_id,
            telefone_cliente=escalacao.telefone_cliente,
            nome_cliente=escalacao.nome_cliente,
            mensagem_id=escalacao.mensagem_id,
            tipo=escalacao.tipo,
            prioridade=escalacao.prioridade,
            pergunta_ia=escalacao.pergunta_ia,
            contexto_conversa=escalacao.contexto_conversa,
            status=StatusEscalacao.PENDENTE,
        )
        db.add(db_escalacao)
        db.commit()
        db.refresh(db_escalacao)

        logger.info(
            f"Escalação criada: id={db_escalacao.id}, tipo={escalacao.tipo}, "
            f"prioridade={escalacao.prioridade}, telefone={escalacao.telefone_cliente}"
        )

        # Notificar painel do atendente via WebSocket
        EscalacaoService._notificar_nova_escalacao(db_escalacao)

        return db_escalacao

    @staticmethod
    def obter_por_id(db: Session, escalacao_id: int) -> Optional[Escalacao]:
        """Obtém uma escalação por ID."""
        return db.query(Escalacao).filter(Escalacao.id == escalacao_id).first()

    @staticmethod
    def listar_pendentes(db: Session, limite: int = 50) -> List[Escalacao]:
        """Lista escalações pendentes ordenadas por prioridade e tempo."""
        prioridade_ordem = {
            PrioridadeEscalacao.URGENTE: 0,
            PrioridadeEscalacao.ALTA: 1,
            PrioridadeEscalacao.MEDIA: 2,
            PrioridadeEscalacao.BAIXA: 3,
        }
        
        return (
            db.query(Escalacao)
            .filter(
                Escalacao.status.in_([
                    StatusEscalacao.PENDENTE,
                    StatusEscalacao.EM_ATENDIMENTO,
                ])
            )
            .order_by(Escalacao.criado_em.asc())
            .limit(limite)
            .all()
        )

    @staticmethod
    def listar_todas(
        db: Session,
        status: Optional[str] = None,
        tipo: Optional[str] = None,
        prioridade: Optional[str] = None,
        sessao_id: Optional[int] = None,
        atendente_id: Optional[str] = None,
        limite: int = 50,
        offset: int = 0,
    ) -> List[Escalacao]:
        """Lista escalações com filtros."""
        query = db.query(Escalacao)

        if status:
            query = query.filter(Escalacao.status == status)
        if tipo:
            query = query.filter(Escalacao.tipo == tipo)
        if prioridade:
            query = query.filter(Escalacao.prioridade == prioridade)
        if sessao_id:
            query = query.filter(Escalacao.sessao_id == sessao_id)
        if atendente_id:
            query = query.filter(Escalacao.atendente_id == atendente_id)

        return (
            query
            .order_by(desc(Escalacao.criado_em))
            .offset(offset)
            .limit(limite)
            .all()
        )

    @staticmethod
    def contar_pendentes(db: Session) -> int:
        """Conta escalações pendentes."""
        return (
            db.query(Escalacao)
            .filter(
                Escalacao.status.in_([
                    StatusEscalacao.PENDENTE,
                    StatusEscalacao.EM_ATENDIMENTO,
                ])
            )
            .count()
        )

    # --- Ações do Atendente ---

    @staticmethod
    async def responder_escalacao(
        db: Session,
        escalacao_id: int,
        resposta: EscalacaoResponder,
    ) -> Optional[Escalacao]:
        """
        Atendente responde à escalação.
        O IA retoma a conversa com o cliente usando a informação fornecida.
        """
        escalacao = db.query(Escalacao).filter(Escalacao.id == escalacao_id).first()
        if not escalacao:
            return None

        agora = datetime.utcnow()
        
        # Calcular tempos
        tempo_espera = int((agora - escalacao.criado_em).total_seconds() * 1000)

        escalacao.resposta_atendente = resposta.resposta_atendente
        escalacao.atendente_id = resposta.atendente_id
        escalacao.atendente_nome = resposta.atendente_nome
        escalacao.status = StatusEscalacao.RESPONDIDA
        escalacao.respondido_em = agora
        escalacao.tempo_espera_ms = tempo_espera
        escalacao.tempo_resolucao_ms = tempo_espera

        if not escalacao.atendido_em:
            escalacao.atendido_em = agora

        db.commit()
        db.refresh(escalacao)

        logger.info(
            f"Escalação {escalacao_id} respondida por {resposta.atendente_nome or 'atendente'} "
            f"em {tempo_espera}ms"
        )

        # Retomar processamento do IA com a resposta do atendente
        await EscalacaoService._retomar_processamento_ia(db, escalacao)

        return escalacao

    @staticmethod
    def assumir_conversa(
        db: Session,
        escalacao_id: int,
        atendente_id: Optional[str] = None,
        atendente_nome: Optional[str] = None,
    ) -> Optional[Escalacao]:
        """
        Atendente assume a conversa diretamente.
        Último recurso — não é o fluxo ideal.
        """
        escalacao = db.query(Escalacao).filter(Escalacao.id == escalacao_id).first()
        if not escalacao:
            return None

        agora = datetime.utcnow()
        tempo_espera = int((agora - escalacao.criado_em).total_seconds() * 1000)

        escalacao.status = StatusEscalacao.ASSUMIDA_HUMANO
        escalacao.atendente_id = atendente_id
        escalacao.atendente_nome = atendente_nome
        escalacao.atendido_em = agora
        escalacao.tempo_espera_ms = tempo_espera

        db.commit()
        db.refresh(escalacao)

        logger.info(f"Conversa assumida pelo atendente: escalacao={escalacao_id}")
        return escalacao

    @staticmethod
    def devolver_para_ia(
        db: Session,
        escalacao_id: int,
    ) -> Optional[Escalacao]:
        """Atendente devolve a conversa para o IA."""
        escalacao = db.query(Escalacao).filter(Escalacao.id == escalacao_id).first()
        if not escalacao:
            return None

        agora = datetime.utcnow()
        tempo_resolucao = int((agora - escalacao.criado_em).total_seconds() * 1000)

        escalacao.status = StatusEscalacao.DEVOLVIDA_IA
        escalacao.tempo_resolucao_ms = tempo_resolucao

        db.commit()
        db.refresh(escalacao)

        logger.info(f"Conversa devolvida para IA: escalacao={escalacao_id}")
        return escalacao

    @staticmethod
    def marcar_em_atendimento(
        db: Session,
        escalacao_id: int,
        atendente_id: Optional[str] = None,
        atendente_nome: Optional[str] = None,
    ) -> Optional[Escalacao]:
        """Marca escalação como em atendimento."""
        escalacao = db.query(Escalacao).filter(Escalacao.id == escalacao_id).first()
        if not escalacao:
            return None

        escalacao.status = StatusEscalacao.EM_ATENDIMENTO
        escalacao.atendido_em = datetime.utcnow()
        escalacao.atendente_id = atendente_id
        escalacao.atendente_nome = atendente_nome

        db.commit()
        db.refresh(escalacao)
        return escalacao

    # --- Expiração ---

    @staticmethod
    def expirar_antigas(db: Session, timeout_minutos: int = 30) -> int:
        """Expira escalações antigas sem resposta."""
        limite = datetime.utcnow() - timedelta(minutes=timeout_minutos)
        
        expiradas = (
            db.query(Escalacao)
            .filter(
                Escalacao.status == StatusEscalacao.PENDENTE,
                Escalacao.criado_em < limite,
            )
            .all()
        )

        for esc in expiradas:
            esc.status = StatusEscalacao.EXPIRADA
            esc.expirado_em = datetime.utcnow()

        db.commit()
        
        if expiradas:
            logger.info(f"{len(expiradas)} escalações expiradas")
        
        return len(expiradas)

    # --- Interações de Atendimento ---

    @staticmethod
    def registrar_interacao(db: Session, interacao: InteracaoCriar) -> InteracaoAtendimento:
        """Registra uma interação de atendimento para métricas."""
        db_interacao = InteracaoAtendimento(
            sessao_id=interacao.sessao_id,
            telefone_cliente=interacao.telefone_cliente,
            nome_cliente=interacao.nome_cliente,
            tipo_assunto=interacao.tipo_assunto,
            sub_assunto=interacao.sub_assunto,
            resolvido_por=interacao.resolvido_por,
            escalacao_id=interacao.escalacao_id,
            tempo_primeira_resposta_ms=interacao.tempo_primeira_resposta_ms,
            tempo_resolucao_ms=interacao.tempo_resolucao_ms,
            total_mensagens_cliente=interacao.total_mensagens_cliente,
            total_mensagens_ia=interacao.total_mensagens_ia,
            total_ferramentas_usadas=interacao.total_ferramentas_usadas,
            resultado=interacao.resultado,
            detalhes_resultado=interacao.detalhes_resultado,
        )
        db.add(db_interacao)
        db.commit()
        db.refresh(db_interacao)
        return db_interacao

    # --- Métricas de Escalação ---

    @staticmethod
    def obter_metricas_escalacao(db: Session, dias: int = 30) -> Dict[str, Any]:
        """Obtém métricas completas de escalação."""
        data_inicio = datetime.utcnow() - timedelta(days=dias)
        
        base_query = db.query(Escalacao).filter(Escalacao.criado_em >= data_inicio)
        
        total = base_query.count()
        pendentes = base_query.filter(Escalacao.status == StatusEscalacao.PENDENTE).count()
        respondidas = base_query.filter(Escalacao.status == StatusEscalacao.RESPONDIDA).count()
        expiradas = base_query.filter(Escalacao.status == StatusEscalacao.EXPIRADA).count()
        assumidas = base_query.filter(Escalacao.status == StatusEscalacao.ASSUMIDA_HUMANO).count()
        
        # Tempo médio de espera
        tempo_medio_espera = (
            db.query(func.avg(Escalacao.tempo_espera_ms))
            .filter(
                Escalacao.criado_em >= data_inicio,
                Escalacao.tempo_espera_ms.isnot(None),
            )
            .scalar() or 0
        )

        # Tempo médio de resolução
        tempo_medio_resolucao = (
            db.query(func.avg(Escalacao.tempo_resolucao_ms))
            .filter(
                Escalacao.criado_em >= data_inicio,
                Escalacao.tempo_resolucao_ms.isnot(None),
            )
            .scalar() or 0
        )
        
        # Por tipo
        por_tipo = {}
        for tipo in TipoEscalacao:
            count = base_query.filter(Escalacao.tipo == tipo.value).count()
            if count > 0:
                por_tipo[tipo.value] = count

        # Por prioridade
        por_prioridade = {}
        for prio in PrioridadeEscalacao:
            count = base_query.filter(Escalacao.prioridade == prio.value).count()
            if count > 0:
                por_prioridade[prio.value] = count

        # Taxa de resolução
        taxa_resolucao = (respondidas / total * 100) if total > 0 else 0
        taxa_expiracao = (expiradas / total * 100) if total > 0 else 0
        taxa_assuncao = (assumidas / total * 100) if total > 0 else 0

        return {
            "periodo_dias": dias,
            "total": total,
            "pendentes": pendentes,
            "respondidas": respondidas,
            "expiradas": expiradas,
            "assumidas": assumidas,
            "tempo_medio_espera_ms": round(tempo_medio_espera, 0),
            "tempo_medio_resolucao_ms": round(tempo_medio_resolucao, 0),
            "taxa_resolucao": round(taxa_resolucao, 2),
            "taxa_expiracao": round(taxa_expiracao, 2),
            "taxa_assuncao_humano": round(taxa_assuncao, 2),
            "por_tipo": por_tipo,
            "por_prioridade": por_prioridade,
        }

    @staticmethod
    def obter_metricas_atendimento(db: Session, dias: int = 30) -> Dict[str, Any]:
        """Obtém métricas completas de atendimento (interações)."""
        data_inicio = datetime.utcnow() - timedelta(days=dias)
        
        base_query = db.query(InteracaoAtendimento).filter(
            InteracaoAtendimento.inicio_em >= data_inicio
        )

        total = base_query.count()
        
        # Por tipo de assunto
        assuntos = (
            db.query(
                InteracaoAtendimento.tipo_assunto,
                func.count(InteracaoAtendimento.id).label("total"),
            )
            .filter(InteracaoAtendimento.inicio_em >= data_inicio)
            .group_by(InteracaoAtendimento.tipo_assunto)
            .order_by(desc("total"))
            .all()
        )
        
        # Resolução por agente (IA vs humano)
        por_resolucao = (
            db.query(
                InteracaoAtendimento.resolvido_por,
                func.count(InteracaoAtendimento.id).label("total"),
            )
            .filter(InteracaoAtendimento.inicio_em >= data_inicio)
            .group_by(InteracaoAtendimento.resolvido_por)
            .all()
        )

        # Tempo médio de primeira resposta
        tempo_medio_primeira_resposta = (
            db.query(func.avg(InteracaoAtendimento.tempo_primeira_resposta_ms))
            .filter(
                InteracaoAtendimento.inicio_em >= data_inicio,
                InteracaoAtendimento.tempo_primeira_resposta_ms.isnot(None),
            )
            .scalar() or 0
        )

        # Tempo médio de resolução
        tempo_medio_resolucao = (
            db.query(func.avg(InteracaoAtendimento.tempo_resolucao_ms))
            .filter(
                InteracaoAtendimento.inicio_em >= data_inicio,
                InteracaoAtendimento.tempo_resolucao_ms.isnot(None),
            )
            .scalar() or 0
        )

        # Satisfação média
        satisfacao_media = (
            db.query(func.avg(InteracaoAtendimento.satisfacao_nota))
            .filter(
                InteracaoAtendimento.inicio_em >= data_inicio,
                InteracaoAtendimento.satisfacao_nota.isnot(None),
            )
            .scalar()
        )

        # Por resultado
        resultados = (
            db.query(
                InteracaoAtendimento.resultado,
                func.count(InteracaoAtendimento.id).label("total"),
            )
            .filter(
                InteracaoAtendimento.inicio_em >= data_inicio,
                InteracaoAtendimento.resultado.isnot(None),
            )
            .group_by(InteracaoAtendimento.resultado)
            .order_by(desc("total"))
            .all()
        )

        # Calcular taxa de resolução IA
        total_ia = sum(1 for r in por_resolucao if r[0] == "ia")
        taxa_ia = (total_ia / total * 100) if total > 0 else 0

        return {
            "periodo_dias": dias,
            "total_interacoes": total,
            "assuntos_mais_abordados": [
                {"assunto": a[0], "total": a[1]} for a in assuntos
            ],
            "resolucao": {r[0]: r[1] for r in por_resolucao},
            "taxa_resolucao_ia": round(taxa_ia, 2),
            "tempo_medio_primeira_resposta_ms": round(tempo_medio_primeira_resposta, 0),
            "tempo_medio_resolucao_ms": round(tempo_medio_resolucao, 0),
            "satisfacao_media": round(satisfacao_media, 2) if satisfacao_media else None,
            "resultados": [
                {"resultado": r[0], "total": r[1]} for r in resultados
            ],
        }

    @staticmethod
    def obter_metricas_por_atendente(db: Session, dias: int = 30) -> List[Dict[str, Any]]:
        """Obtém métricas individuais por atendente."""
        data_inicio = datetime.utcnow() - timedelta(days=dias)
        
        atendentes = (
            db.query(Escalacao.atendente_id, Escalacao.atendente_nome)
            .filter(
                Escalacao.criado_em >= data_inicio,
                Escalacao.atendente_id.isnot(None),
            )
            .distinct()
            .all()
        )

        metricas = []
        for atendente_id, atendente_nome in atendentes:
            query = db.query(Escalacao).filter(
                Escalacao.criado_em >= data_inicio,
                Escalacao.atendente_id == atendente_id,
            )
            
            total_atendidos = query.count()
            respondidos = query.filter(Escalacao.status == StatusEscalacao.RESPONDIDA).count()
            assumidos = query.filter(Escalacao.status == StatusEscalacao.ASSUMIDA_HUMANO).count()
            
            tempo_medio = (
                db.query(func.avg(Escalacao.tempo_espera_ms))
                .filter(
                    Escalacao.criado_em >= data_inicio,
                    Escalacao.atendente_id == atendente_id,
                    Escalacao.tempo_espera_ms.isnot(None),
                )
                .scalar() or 0
            )

            metricas.append({
                "atendente_id": atendente_id,
                "atendente_nome": atendente_nome or atendente_id,
                "total_atendidos": total_atendidos,
                "respondidos": respondidos,
                "assumidos": assumidos,
                "tempo_medio_resposta_ms": round(tempo_medio, 0),
            })

        return sorted(metricas, key=lambda x: x["total_atendidos"], reverse=True)

    # --- Processamento IA ---

    @staticmethod
    async def _retomar_processamento_ia(db: Session, escalacao: Escalacao):
        """
        Retoma o processamento do IA após resposta do atendente.
        O IA formula uma resposta ao paciente usando a informação do atendente.
        """
        from agente.agente_service import AgenteService
        from sessao.sessao_model import Sessao
        from mensagem.mensagem_model import Mensagem
        from mensagem.mensagem_service import MensagemService
        
        try:
            sessao = db.query(Sessao).filter(Sessao.id == escalacao.sessao_id).first()
            if not sessao or not sessao.agente_ativo_id:
                logger.warning(f"Sessão não encontrada para retomar escalação {escalacao.id}")
                return

            # Criar uma mensagem sintética com a resposta do atendente
            # para que o IA possa formular a resposta ao paciente
            mensagem_contexto = Mensagem(
                sessao_id=escalacao.sessao_id,
                telefone_cliente=escalacao.telefone_cliente,
                tipo="texto",
                direcao="recebida",
                conteudo_texto=(
                    f"[INFORMAÇÃO INTERNA - Resposta do atendente à sua pergunta: "
                    f"'{escalacao.pergunta_ia}']: {escalacao.resposta_atendente}\n\n"
                    f"Use esta informação para responder ao paciente de forma natural, "
                    f"sem mencionar que consultou alguém."
                ),
            )
            db.add(mensagem_contexto)
            db.commit()
            db.refresh(mensagem_contexto)

            # Obter histórico
            historico = MensagemService.listar_por_cliente(
                db, escalacao.sessao_id, escalacao.telefone_cliente, limite=10
            )

            # Processar com o agente
            resultado = await AgenteService.processar_mensagem(
                db=db,
                sessao=sessao,
                mensagem=mensagem_contexto,
                historico_mensagens=historico,
            )

            resposta_texto = resultado.get("texto", "")

            if resposta_texto:
                # Enviar via canal correto (Neonize ou Meta)
                await EscalacaoService._enviar_resposta_paciente(
                    db, escalacao, resposta_texto
                )

                # Atualizar mensagem
                mensagem_contexto.resposta_texto = resposta_texto
                mensagem_contexto.resposta_tokens_input = resultado.get("tokens_input", 0)
                mensagem_contexto.resposta_tokens_output = resultado.get("tokens_output", 0)
                mensagem_contexto.resposta_tempo_ms = resultado.get("tempo_ms", 0)
                mensagem_contexto.resposta_modelo = resultado.get("modelo", "")
                mensagem_contexto.processada = True
                mensagem_contexto.respondida = True
                mensagem_contexto.processado_em = datetime.utcnow()
                mensagem_contexto.respondido_em = datetime.utcnow()
                db.commit()

                logger.info(
                    f"Processamento IA retomado para escalação {escalacao.id}, "
                    f"resposta enviada ao paciente {escalacao.telefone_cliente}"
                )

        except Exception as e:
            logger.error(f"Erro ao retomar processamento IA para escalação {escalacao.id}: {e}")

    @staticmethod
    async def _enviar_resposta_paciente(
        db: Session, escalacao: Escalacao, texto: str
    ):
        """Envia resposta ao paciente via canal apropriado."""
        # Tentar via Meta API primeiro
        from whatsapp_meta.whatsapp_meta_service import WhatsAppMetaService
        
        config_meta = WhatsAppMetaService.obter_config_ativa(db)
        if config_meta and config_meta.sessao_id == escalacao.sessao_id:
            await WhatsAppMetaService.enviar_mensagem_texto(
                db, escalacao.telefone_cliente, texto, config_meta
            )
            return

        # Fallback para Neonize
        try:
            from sessao.sessao_service import SessaoService
            SessaoService.enviar_mensagem(
                db, escalacao.sessao_id, escalacao.telefone_cliente, texto
            )
        except Exception as e:
            logger.error(f"Erro ao enviar resposta ao paciente: {e}")

    # --- WebSocket Notifications ---

    @staticmethod
    def _notificar_nova_escalacao(escalacao: Escalacao):
        """Notifica o painel do atendente sobre nova escalação."""
        # As notificações são gerenciadas pelo WebSocket manager
        from escalacao.websocket_manager import manager
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(manager.broadcast({
                    "tipo": "nova_escalacao",
                    "escalacao": {
                        "id": escalacao.id,
                        "tipo": escalacao.tipo if isinstance(escalacao.tipo, str) else escalacao.tipo.value,
                        "prioridade": escalacao.prioridade if isinstance(escalacao.prioridade, str) else escalacao.prioridade.value,
                        "pergunta_ia": escalacao.pergunta_ia,
                        "telefone_cliente": escalacao.telefone_cliente,
                        "nome_cliente": escalacao.nome_cliente,
                        "criado_em": escalacao.criado_em.isoformat() if escalacao.criado_em else None,
                    },
                }))
            else:
                loop.run_until_complete(manager.broadcast({
                    "tipo": "nova_escalacao",
                    "escalacao": {
                        "id": escalacao.id,
                        "tipo": escalacao.tipo if isinstance(escalacao.tipo, str) else escalacao.tipo.value,
                        "prioridade": escalacao.prioridade if isinstance(escalacao.prioridade, str) else escalacao.prioridade.value,
                        "pergunta_ia": escalacao.pergunta_ia,
                        "telefone_cliente": escalacao.telefone_cliente,
                        "nome_cliente": escalacao.nome_cliente,
                    },
                }))
        except Exception as e:
            logger.debug(f"WebSocket notification skipped: {e}")

    # --- Contagem por horário (para métricas de pico) ---

    @staticmethod
    def obter_volume_por_hora(db: Session, dias: int = 7) -> Dict[str, Any]:
        """Obtém volume de escalações por hora do dia."""
        data_inicio = datetime.utcnow() - timedelta(days=dias)
        
        escalacoes = (
            db.query(Escalacao)
            .filter(Escalacao.criado_em >= data_inicio)
            .all()
        )

        por_hora = {str(h).zfill(2): 0 for h in range(24)}
        por_dia_semana = {str(d): 0 for d in range(7)}  # 0=segunda, 6=domingo
        
        for esc in escalacoes:
            if esc.criado_em:
                hora = str(esc.criado_em.hour).zfill(2)
                dia = str(esc.criado_em.weekday())
                por_hora[hora] += 1
                por_dia_semana[dia] += 1

        return {
            "periodo_dias": dias,
            "por_hora": por_hora,
            "por_dia_semana": por_dia_semana,
            "horario_pico": max(por_hora, key=por_hora.get) if por_hora else "00",
            "dia_pico": max(por_dia_semana, key=por_dia_semana.get) if por_dia_semana else "0",
        }
