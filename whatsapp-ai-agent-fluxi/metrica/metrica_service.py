"""
Serviço de métricas e estatísticas.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from mensagem.mensagem_model import Mensagem
from sessao.sessao_model import Sessao


class MetricaService:
    """Serviço para calcular métricas e estatísticas."""

    @staticmethod
    def obter_metricas_gerais(db: Session) -> Dict[str, Any]:
        """Obtém métricas gerais do sistema."""
        # Total de sessões
        total_sessoes = db.query(Sessao).count()
        sessoes_ativas = db.query(Sessao).filter(Sessao.ativa == True).count()
        sessoes_conectadas = db.query(Sessao).filter(Sessao.status == "conectado").count()
        
        # Total de mensagens
        total_mensagens = db.query(Mensagem).count()
        mensagens_recebidas = db.query(Mensagem).filter(Mensagem.direcao == "recebida").count()
        mensagens_enviadas = db.query(Mensagem).filter(Mensagem.direcao == "enviada").count()
        
        # Mensagens processadas
        mensagens_processadas = db.query(Mensagem).filter(Mensagem.processada == True).count()
        mensagens_respondidas = db.query(Mensagem).filter(Mensagem.respondida == True).count()
        
        # Taxa de sucesso
        taxa_sucesso = (mensagens_respondidas / mensagens_recebidas * 100) if mensagens_recebidas > 0 else 0
        
        # Clientes únicos
        clientes_unicos = db.query(Mensagem.telefone_cliente).distinct().count()
        
        return {
            "sessoes": {
                "total": total_sessoes,
                "ativas": sessoes_ativas,
                "conectadas": sessoes_conectadas
            },
            "mensagens": {
                "total": total_mensagens,
                "recebidas": mensagens_recebidas,
                "enviadas": mensagens_enviadas,
                "processadas": mensagens_processadas,
                "respondidas": mensagens_respondidas
            },
            "performance": {
                "taxa_sucesso": round(taxa_sucesso, 2),
                "clientes_unicos": clientes_unicos
            }
        }

    @staticmethod
    def obter_metricas_sessao(db: Session, sessao_id: int) -> Dict[str, Any]:
        """Obtém métricas de uma sessão específica."""
        # Mensagens da sessão
        total_mensagens = db.query(Mensagem)\
            .filter(Mensagem.sessao_id == sessao_id)\
            .count()
        
        mensagens_recebidas = db.query(Mensagem)\
            .filter(
                Mensagem.sessao_id == sessao_id,
                Mensagem.direcao == "recebida"
            )\
            .count()
        
        mensagens_respondidas = db.query(Mensagem)\
            .filter(
                Mensagem.sessao_id == sessao_id,
                Mensagem.respondida == True
            )\
            .count()
        
        # Taxa de resposta
        taxa_resposta = (mensagens_respondidas / mensagens_recebidas * 100) if mensagens_recebidas > 0 else 0
        
        # Tempo médio de resposta
        tempo_medio = db.query(func.avg(Mensagem.resposta_tempo_ms))\
            .filter(
                Mensagem.sessao_id == sessao_id,
                Mensagem.resposta_tempo_ms.isnot(None)
            )\
            .scalar() or 0
        
        # Tokens utilizados
        tokens_input_total = db.query(func.sum(Mensagem.resposta_tokens_input))\
            .filter(Mensagem.sessao_id == sessao_id)\
            .scalar() or 0
        
        tokens_output_total = db.query(func.sum(Mensagem.resposta_tokens_output))\
            .filter(Mensagem.sessao_id == sessao_id)\
            .scalar() or 0
        
        # Clientes únicos
        clientes_unicos = db.query(Mensagem.telefone_cliente)\
            .filter(Mensagem.sessao_id == sessao_id)\
            .distinct()\
            .count()
        
        # Mensagens com imagem
        mensagens_com_imagem = db.query(Mensagem)\
            .filter(
                Mensagem.sessao_id == sessao_id,
                Mensagem.tipo == "imagem"
            )\
            .count()
        
        # Mensagens com ferramentas
        mensagens_com_ferramentas = db.query(Mensagem)\
            .filter(
                Mensagem.sessao_id == sessao_id,
                Mensagem.ferramentas_usadas.isnot(None)
            )\
            .count()
        
        return {
            "mensagens": {
                "total": total_mensagens,
                "recebidas": mensagens_recebidas,
                "respondidas": mensagens_respondidas,
                "com_imagem": mensagens_com_imagem,
                "com_ferramentas": mensagens_com_ferramentas
            },
            "performance": {
                "taxa_resposta": round(taxa_resposta, 2),
                "tempo_medio_ms": round(tempo_medio, 2),
                "clientes_unicos": clientes_unicos
            },
            "tokens": {
                "input_total": int(tokens_input_total),
                "output_total": int(tokens_output_total),
                "total": int(tokens_input_total + tokens_output_total)
            }
        }

    @staticmethod
    def obter_metricas_periodo(
        db: Session,
        sessao_id: Optional[int] = None,
        dias: int = 7
    ) -> Dict[str, Any]:
        """Obtém métricas de um período específico."""
        data_inicio = datetime.now() - timedelta(days=dias)
        
        query = db.query(Mensagem).filter(Mensagem.criado_em >= data_inicio)
        if sessao_id:
            query = query.filter(Mensagem.sessao_id == sessao_id)
        
        mensagens = query.all()
        
        # Agrupar por dia
        mensagens_por_dia = {}
        for msg in mensagens:
            dia = msg.criado_em.strftime("%Y-%m-%d")
            if dia not in mensagens_por_dia:
                mensagens_por_dia[dia] = {
                    "total": 0,
                    "recebidas": 0,
                    "respondidas": 0
                }
            
            mensagens_por_dia[dia]["total"] += 1
            if msg.direcao == "recebida":
                mensagens_por_dia[dia]["recebidas"] += 1
            if msg.respondida:
                mensagens_por_dia[dia]["respondidas"] += 1
        
        return {
            "periodo_dias": dias,
            "data_inicio": data_inicio.strftime("%Y-%m-%d"),
            "data_fim": datetime.now().strftime("%Y-%m-%d"),
            "mensagens_por_dia": mensagens_por_dia,
            "total_periodo": len(mensagens)
        }

    @staticmethod
    def obter_top_clientes(
        db: Session,
        sessao_id: int,
        limite: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtém os clientes que mais enviaram mensagens."""
        result = db.query(
            Mensagem.telefone_cliente,
            func.count(Mensagem.id).label("total_mensagens")
        )\
        .filter(
            Mensagem.sessao_id == sessao_id,
            Mensagem.direcao == "recebida"
        )\
        .group_by(Mensagem.telefone_cliente)\
        .order_by(func.count(Mensagem.id).desc())\
        .limit(limite)\
        .all()
        
        return [
            {
                "telefone": r[0],
                "total_mensagens": r[1]
            }
            for r in result
        ]

    @staticmethod
    def obter_uso_ferramentas(db: Session, sessao_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obtém estatísticas de uso de ferramentas."""
        query = db.query(Mensagem)\
            .filter(Mensagem.ferramentas_usadas.isnot(None))
        
        if sessao_id:
            query = query.filter(Mensagem.sessao_id == sessao_id)
        
        mensagens = query.all()
        
        # Contar uso de cada ferramenta
        uso_ferramentas = {}
        for msg in mensagens:
            if msg.ferramentas_usadas:
                for ferramenta in msg.ferramentas_usadas:
                    nome = ferramenta.get("nome", "desconhecida")
                    if nome not in uso_ferramentas:
                        uso_ferramentas[nome] = 0
                    uso_ferramentas[nome] += 1
        
        # Converter para lista ordenada
        resultado = [
            {"nome": nome, "total_usos": total}
            for nome, total in sorted(uso_ferramentas.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return resultado

    # ================================================================
    # MÉTRICAS DO CALL CENTER
    # ================================================================

    @staticmethod
    def obter_metricas_callcenter(db: Session, sessao_id: Optional[int] = None, dias: int = 30) -> Dict[str, Any]:
        """
        Obtém métricas completas do call center:
        - Volume de atendimentos
        - Taxa de resolução pela IA vs humano
        - Tempo médio de resposta
        - Escalações
        - Agendamentos realizados
        - Satisfação (se disponível)
        """
        data_inicio = datetime.now() - timedelta(days=dias)
        
        # --- Métricas de mensagens ---
        query_msgs = db.query(Mensagem).filter(Mensagem.criado_em >= data_inicio)
        if sessao_id:
            query_msgs = query_msgs.filter(Mensagem.sessao_id == sessao_id)
        
        total_mensagens = query_msgs.count()
        mensagens_recebidas = query_msgs.filter(Mensagem.direcao == "recebida").count()
        mensagens_respondidas = query_msgs.filter(Mensagem.respondida == True).count()
        
        # Tempo médio de resposta
        tempo_medio_query = db.query(func.avg(Mensagem.resposta_tempo_ms)).filter(
            Mensagem.criado_em >= data_inicio,
            Mensagem.resposta_tempo_ms.isnot(None)
        )
        if sessao_id:
            tempo_medio_query = tempo_medio_query.filter(Mensagem.sessao_id == sessao_id)
        tempo_medio_ms = tempo_medio_query.scalar() or 0
        
        # Clientes únicos atendidos
        clientes_query = db.query(Mensagem.telefone_cliente).filter(
            Mensagem.criado_em >= data_inicio,
            Mensagem.direcao == "recebida"
        )
        if sessao_id:
            clientes_query = clientes_query.filter(Mensagem.sessao_id == sessao_id)
        clientes_unicos = clientes_query.distinct().count()
        
        # --- Métricas de escalação ---
        escalacao_metricas = {}
        try:
            from escalacao.escalacao_model import Escalacao, StatusEscalacao
            
            query_esc = db.query(Escalacao).filter(Escalacao.criado_em >= data_inicio)
            if sessao_id:
                query_esc = query_esc.filter(Escalacao.sessao_id == sessao_id)
            
            total_escalacoes = query_esc.count()
            escalacoes_respondidas = query_esc.filter(
                Escalacao.status == StatusEscalacao.RESPONDIDA
            ).count()
            escalacoes_pendentes = query_esc.filter(
                Escalacao.status == StatusEscalacao.PENDENTE
            ).count()
            escalacoes_assumidas = query_esc.filter(
                Escalacao.status == StatusEscalacao.ASSUMIDA_HUMANO
            ).count()
            escalacoes_expiradas = query_esc.filter(
                Escalacao.status == StatusEscalacao.EXPIRADA
            ).count()
            
            # Tempo médio de espera e resolução
            tempo_espera_medio = db.query(func.avg(Escalacao.tempo_espera_ms)).filter(
                Escalacao.criado_em >= data_inicio,
                Escalacao.tempo_espera_ms.isnot(None)
            ).scalar() or 0
            
            tempo_resolucao_medio = db.query(func.avg(Escalacao.tempo_resolucao_ms)).filter(
                Escalacao.criado_em >= data_inicio,
                Escalacao.tempo_resolucao_ms.isnot(None)
            ).scalar() or 0
            
            # Taxa de resolução pela IA (mensagens respondidas sem escalação)
            taxa_ia = ((mensagens_respondidas - total_escalacoes) / mensagens_recebidas * 100) if mensagens_recebidas > 0 else 100
            
            escalacao_metricas = {
                "total_escalacoes": total_escalacoes,
                "respondidas": escalacoes_respondidas,
                "pendentes": escalacoes_pendentes,
                "assumidas_humano": escalacoes_assumidas,
                "expiradas": escalacoes_expiradas,
                "tempo_espera_medio_ms": round(tempo_espera_medio, 0),
                "tempo_resolucao_medio_ms": round(tempo_resolucao_medio, 0),
                "taxa_resolucao_ia_pct": round(max(0, taxa_ia), 2),
            }
        except ImportError:
            escalacao_metricas = {"erro": "Módulo de escalação não disponível"}
        
        # --- Métricas de agendamento (via ferramentas usadas) ---
        agendamento_metricas = MetricaService._calcular_metricas_agendamento(db, data_inicio, sessao_id)
        
        # --- Volume por hora do dia ---
        volume_por_hora = MetricaService._calcular_volume_por_hora(db, data_inicio, sessao_id)
        
        # --- Tokens e custos ---
        tokens_input = db.query(func.sum(Mensagem.resposta_tokens_input)).filter(
            Mensagem.criado_em >= data_inicio
        )
        tokens_output = db.query(func.sum(Mensagem.resposta_tokens_output)).filter(
            Mensagem.criado_em >= data_inicio
        )
        if sessao_id:
            tokens_input = tokens_input.filter(Mensagem.sessao_id == sessao_id)
            tokens_output = tokens_output.filter(Mensagem.sessao_id == sessao_id)
        
        total_tokens_input = tokens_input.scalar() or 0
        total_tokens_output = tokens_output.scalar() or 0
        
        return {
            "periodo_dias": dias,
            "atendimento": {
                "total_mensagens": total_mensagens,
                "mensagens_recebidas": mensagens_recebidas,
                "mensagens_respondidas": mensagens_respondidas,
                "taxa_resposta_pct": round(
                    (mensagens_respondidas / mensagens_recebidas * 100) if mensagens_recebidas > 0 else 0, 2
                ),
                "tempo_medio_resposta_ms": round(tempo_medio_ms, 0),
                "clientes_unicos": clientes_unicos,
            },
            "escalacao": escalacao_metricas,
            "agendamentos": agendamento_metricas,
            "volume_por_hora": volume_por_hora,
            "custos": {
                "tokens_input": int(total_tokens_input),
                "tokens_output": int(total_tokens_output),
                "tokens_total": int(total_tokens_input + total_tokens_output),
            }
        }

    @staticmethod
    def _calcular_metricas_agendamento(
        db: Session, data_inicio: datetime, sessao_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Calcula métricas de agendamento baseadas no uso de ferramentas."""
        query = db.query(Mensagem).filter(
            Mensagem.criado_em >= data_inicio,
            Mensagem.ferramentas_usadas.isnot(None)
        )
        if sessao_id:
            query = query.filter(Mensagem.sessao_id == sessao_id)
        
        mensagens = query.all()
        
        contadores = {
            "consultas_agendadas": 0,
            "consultas_remarcadas": 0,
            "consultas_canceladas": 0,
            "consultas_confirmadas": 0,
            "exames_agendados": 0,
            "pacientes_cadastrados": 0,
            "orcamentos_solicitados": 0,
        }
        
        mapa_ferramentas = {
            "agendar_consulta": "consultas_agendadas",
            "remarcar_consulta": "consultas_remarcadas",
            "cancelar_consulta": "consultas_canceladas",
            "confirmar_consulta": "consultas_confirmadas",
            "agendar_exame": "exames_agendados",
            "cadastrar_paciente": "pacientes_cadastrados",
            "buscar_orcamento": "orcamentos_solicitados",
        }
        
        for msg in mensagens:
            if msg.ferramentas_usadas:
                for ferramenta in msg.ferramentas_usadas:
                    nome = ferramenta.get("nome", "")
                    if nome in mapa_ferramentas:
                        # Verificar se não teve erro
                        resultado = ferramenta.get("resultado", {})
                        if not resultado.get("erro"):
                            contadores[mapa_ferramentas[nome]] += 1
        
        contadores["total_procedimentos"] = (
            contadores["consultas_agendadas"] + 
            contadores["exames_agendados"]
        )
        
        return contadores

    @staticmethod
    def _calcular_volume_por_hora(
        db: Session, data_inicio: datetime, sessao_id: Optional[int] = None
    ) -> Dict[str, int]:
        """Calcula volume de mensagens por hora do dia."""
        query = db.query(Mensagem).filter(
            Mensagem.criado_em >= data_inicio,
            Mensagem.direcao == "recebida"
        )
        if sessao_id:
            query = query.filter(Mensagem.sessao_id == sessao_id)
        
        mensagens = query.all()
        
        volume = {str(h).zfill(2): 0 for h in range(24)}
        for msg in mensagens:
            hora = msg.criado_em.strftime("%H")
            volume[hora] += 1
        
        return volume
