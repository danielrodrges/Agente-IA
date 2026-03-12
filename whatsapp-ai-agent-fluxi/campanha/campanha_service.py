"""
Serviço de campanhas para mensagens ativas/proativas.
Gerencia confirmações automáticas, lembretes e follow-ups.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from campanha.campanha_model import (
    Campanha,
    CampanhaEnvio,
    TipoCampanha,
    StatusCampanha,
    StatusEnvio,
)
from campanha.campanha_schema import CampanhaCriar, CampanhaAtualizar, EnvioCriar

logger = logging.getLogger(__name__)


class CampanhaService:
    """Serviço para gerenciar campanhas de mensagens ativas."""

    # --- CRUD Campanha ---

    @staticmethod
    def criar(db: Session, campanha: CampanhaCriar) -> Campanha:
        """Cria uma nova campanha."""
        db_campanha = Campanha(
            nome=campanha.nome,
            descricao=campanha.descricao,
            tipo=campanha.tipo,
            template_name=campanha.template_name,
            template_language=campanha.template_language,
            template_components=campanha.template_components,
            mensagem_texto=campanha.mensagem_texto,
            agendamento_tipo=campanha.agendamento_tipo,
            agendamento_cron=campanha.agendamento_cron,
            antecedencia_horas=campanha.antecedencia_horas,
            sessao_id=campanha.sessao_id,
            agendado_para=campanha.agendado_para,
        )
        db.add(db_campanha)
        db.commit()
        db.refresh(db_campanha)
        logger.info(f"Campanha criada: {db_campanha.id} - {campanha.nome}")
        return db_campanha

    @staticmethod
    def obter_por_id(db: Session, campanha_id: int) -> Optional[Campanha]:
        return db.query(Campanha).filter(Campanha.id == campanha_id).first()

    @staticmethod
    def listar_todas(
        db: Session,
        tipo: Optional[str] = None,
        status: Optional[str] = None,
        limite: int = 50,
    ) -> List[Campanha]:
        query = db.query(Campanha)
        if tipo:
            query = query.filter(Campanha.tipo == tipo)
        if status:
            query = query.filter(Campanha.status == status)
        return query.order_by(desc(Campanha.criado_em)).limit(limite).all()

    @staticmethod
    def atualizar(
        db: Session, campanha_id: int, dados: CampanhaAtualizar
    ) -> Optional[Campanha]:
        campanha = db.query(Campanha).filter(Campanha.id == campanha_id).first()
        if not campanha:
            return None
        
        update_data = dados.model_dump(exclude_unset=True)
        for campo, valor in update_data.items():
            setattr(campanha, campo, valor)
        
        db.commit()
        db.refresh(campanha)
        return campanha

    @staticmethod
    def deletar(db: Session, campanha_id: int) -> bool:
        campanha = db.query(Campanha).filter(Campanha.id == campanha_id).first()
        if not campanha:
            return False
        
        # Deletar envios associados
        db.query(CampanhaEnvio).filter(CampanhaEnvio.campanha_id == campanha_id).delete()
        db.delete(campanha)
        db.commit()
        return True

    # --- Destinatários ---

    @staticmethod
    def adicionar_destinatario(
        db: Session, campanha_id: int, envio: EnvioCriar
    ) -> Optional[CampanhaEnvio]:
        campanha = db.query(Campanha).filter(Campanha.id == campanha_id).first()
        if not campanha:
            return None

        db_envio = CampanhaEnvio(
            campanha_id=campanha_id,
            telefone=envio.telefone,
            nome_paciente=envio.nome_paciente,
            paciente_id=envio.paciente_id,
            agendamento_id=envio.agendamento_id,
            evento_data_hora=envio.evento_data_hora,
            evento_descricao=envio.evento_descricao,
            template_params=envio.template_params,
        )
        db.add(db_envio)
        
        campanha.total_destinatarios += 1
        db.commit()
        db.refresh(db_envio)
        return db_envio

    @staticmethod
    def listar_envios(
        db: Session,
        campanha_id: int,
        status: Optional[str] = None,
        limite: int = 100,
    ) -> List[CampanhaEnvio]:
        query = db.query(CampanhaEnvio).filter(CampanhaEnvio.campanha_id == campanha_id)
        if status:
            query = query.filter(CampanhaEnvio.status == status)
        return query.order_by(CampanhaEnvio.criado_em).limit(limite).all()

    # --- Execução ---

    @staticmethod
    async def executar_campanha(db: Session, campanha_id: int) -> Dict[str, Any]:
        """Executa uma campanha enviando mensagens para todos os destinatários."""
        from whatsapp_meta.whatsapp_meta_service import WhatsAppMetaService

        campanha = db.query(Campanha).filter(Campanha.id == campanha_id).first()
        if not campanha:
            return {"sucesso": False, "erro": "Campanha não encontrada"}

        if campanha.status not in (StatusCampanha.AGENDADA, StatusCampanha.RASCUNHO):
            return {"sucesso": False, "erro": f"Campanha não pode ser executada no status {campanha.status}"}

        campanha.status = StatusCampanha.EM_EXECUCAO
        campanha.executado_em = datetime.utcnow()
        db.commit()

        envios = (
            db.query(CampanhaEnvio)
            .filter(
                CampanhaEnvio.campanha_id == campanha_id,
                CampanhaEnvio.status == StatusEnvio.PENDENTE,
            )
            .all()
        )

        enviados = 0
        erros = 0

        for envio in envios:
            try:
                if campanha.template_name:
                    # Enviar via template Meta
                    resultado = await WhatsAppMetaService.enviar_mensagem_template(
                        db,
                        envio.telefone,
                        campanha.template_name,
                        campanha.template_language,
                        envio.template_params or campanha.template_components,
                    )
                else:
                    # Enviar mensagem de texto
                    texto = campanha.mensagem_texto or ""
                    # Substituir variáveis
                    texto = texto.replace("{nome}", envio.nome_paciente or "")
                    texto = texto.replace("{evento}", envio.evento_descricao or "")
                    if envio.evento_data_hora:
                        texto = texto.replace("{data}", envio.evento_data_hora.strftime("%d/%m/%Y às %H:%M"))
                    
                    resultado = await WhatsAppMetaService.enviar_mensagem_texto(
                        db, envio.telefone, texto
                    )

                if resultado.get("sucesso"):
                    envio.status = StatusEnvio.ENVIADO
                    envio.enviado_em = datetime.utcnow()
                    envio.mensagem_id_whatsapp = resultado.get("message_id")
                    enviados += 1
                else:
                    envio.status = StatusEnvio.ERRO
                    envio.erro = resultado.get("erro", "Erro desconhecido")
                    erros += 1

            except Exception as e:
                envio.status = StatusEnvio.ERRO
                envio.erro = str(e)
                erros += 1
                logger.error(f"Erro ao enviar campanha para {envio.telefone}: {e}")

        # Atualizar métricas da campanha
        campanha.total_enviados = enviados
        campanha.total_erros = erros
        campanha.status = StatusCampanha.CONCLUIDA
        campanha.concluido_em = datetime.utcnow()
        db.commit()

        logger.info(f"Campanha {campanha_id} concluída: {enviados} enviados, {erros} erros")
        return {
            "sucesso": True,
            "enviados": enviados,
            "erros": erros,
            "total": len(envios),
        }

    # --- Geração Automática ---

    @staticmethod
    async def gerar_confirmacoes_automaticas(
        db: Session, antecedencia_horas: int = 24
    ) -> Dict[str, Any]:
        """
        Gera campanha automática de confirmação de consultas.
        Busca no ERP consultas nas próximas X horas e cria envios.
        """
        from erp.erp_mock import erp_mock  # TODO: Trocar por ERP real quando configurado

        # Buscar consultas para o período
        # Na implementação real, buscar do ERP
        logger.info(f"Gerando confirmações automáticas (antecedência: {antecedencia_horas}h)")
        
        return {
            "sucesso": True,
            "mensagem": "Geração de confirmações automáticas configurada",
            "antecedencia_horas": antecedencia_horas,
        }

    # --- Métricas ---

    @staticmethod
    def obter_metricas_campanhas(db: Session, dias: int = 30) -> Dict[str, Any]:
        """Obtém métricas das campanhas."""
        data_inicio = datetime.utcnow() - timedelta(days=dias)
        
        total = db.query(Campanha).filter(Campanha.criado_em >= data_inicio).count()
        concluidas = db.query(Campanha).filter(
            Campanha.criado_em >= data_inicio,
            Campanha.status == StatusCampanha.CONCLUIDA,
        ).count()

        # Totais de envios
        total_enviados = (
            db.query(func.sum(Campanha.total_enviados))
            .filter(Campanha.criado_em >= data_inicio)
            .scalar() or 0
        )
        total_entregues = (
            db.query(func.sum(Campanha.total_entregues))
            .filter(Campanha.criado_em >= data_inicio)
            .scalar() or 0
        )
        total_lidos = (
            db.query(func.sum(Campanha.total_lidos))
            .filter(Campanha.criado_em >= data_inicio)
            .scalar() or 0
        )
        total_respondidos = (
            db.query(func.sum(Campanha.total_respondidos))
            .filter(Campanha.criado_em >= data_inicio)
            .scalar() or 0
        )

        # Por tipo
        por_tipo = (
            db.query(Campanha.tipo, func.count(Campanha.id))
            .filter(Campanha.criado_em >= data_inicio)
            .group_by(Campanha.tipo)
            .all()
        )

        taxa_entrega = (total_entregues / total_enviados * 100) if total_enviados > 0 else 0
        taxa_leitura = (total_lidos / total_entregues * 100) if total_entregues > 0 else 0
        taxa_resposta = (total_respondidos / total_enviados * 100) if total_enviados > 0 else 0

        return {
            "periodo_dias": dias,
            "total_campanhas": total,
            "concluidas": concluidas,
            "total_enviados": int(total_enviados),
            "total_entregues": int(total_entregues),
            "total_lidos": int(total_lidos),
            "total_respondidos": int(total_respondidos),
            "taxa_entrega": round(taxa_entrega, 2),
            "taxa_leitura": round(taxa_leitura, 2),
            "taxa_resposta": round(taxa_resposta, 2),
            "por_tipo": {t[0]: t[1] for t in por_tipo},
        }
