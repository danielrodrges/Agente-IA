"""
Serviço para gerenciar métricas de uso do RAG.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from rag.rag_metrica_model import RAGMetrica

logger = logging.getLogger(__name__)


class RAGMetricaService:
    """Serviço para registrar e consultar métricas de uso do RAG."""

    @staticmethod
    def registrar_busca(
        db: Session,
        rag_id: int,
        query: str,
        resultados: List[Dict[str, Any]],
        num_solicitados: int,
        tempo_ms: int,
        agente_id: Optional[int] = None,
        sessao_id: Optional[int] = None,
        telefone_cliente: Optional[str] = None
    ) -> RAGMetrica:
        """
        Registra uma busca realizada no RAG.
        
        Args:
            db: Sessão do banco de dados
            rag_id: ID do RAG utilizado
            query: Texto da consulta
            resultados: Lista de resultados retornados
            num_solicitados: Quantidade de resultados solicitados
            tempo_ms: Tempo de processamento em milissegundos
            agente_id: ID do agente que realizou a busca
            sessao_id: ID da sessão
            telefone_cliente: Telefone do cliente que fez a pergunta
            
        Returns:
            RAGMetrica criada
        """
        try:
            metrica = RAGMetrica(
                rag_id=rag_id,
                agente_id=agente_id,
                sessao_id=sessao_id,
                query=query,
                telefone_cliente=telefone_cliente,
                num_resultados_solicitados=num_solicitados,
                num_resultados_retornados=len(resultados),
                tempo_ms=tempo_ms
            )
            
            db.add(metrica)
            db.commit()
            db.refresh(metrica)
            
            logger.info(f"Métrica registrada: RAG {rag_id}, query='{query[:50]}...', {len(resultados)} resultados, {tempo_ms}ms")
            return metrica
            
        except Exception as e:
            logger.error(f"Erro ao registrar métrica: {str(e)}", exc_info=True)
            db.rollback()
            # Não falhar se não conseguir registrar métrica
            return None

    @staticmethod
    def listar_por_rag(
        db: Session,
        rag_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[RAGMetrica]:
        """Lista métricas de um RAG específico."""
        return db.query(RAGMetrica).filter(
            RAGMetrica.rag_id == rag_id
        ).order_by(RAGMetrica.criado_em.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def listar_por_agente(
        db: Session,
        agente_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[RAGMetrica]:
        """Lista métricas de um agente específico."""
        return db.query(RAGMetrica).filter(
            RAGMetrica.agente_id == agente_id
        ).order_by(RAGMetrica.criado_em.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def listar_por_sessao(
        db: Session,
        sessao_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[RAGMetrica]:
        """Lista métricas de uma sessão específica."""
        return db.query(RAGMetrica).filter(
            RAGMetrica.sessao_id == sessao_id
        ).order_by(RAGMetrica.criado_em.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def obter_estatisticas_rag(db: Session, rag_id: int, dias: int = 30) -> Dict[str, Any]:
        """
        Obtém estatísticas de uso de um RAG.
        
        Args:
            db: Sessão do banco
            rag_id: ID do RAG
            dias: Quantidade de dias para análise
            
        Returns:
            Dicionário com estatísticas
        """
        data_inicio = datetime.now() - timedelta(days=dias)
        
        metricas = db.query(RAGMetrica).filter(
            RAGMetrica.rag_id == rag_id,
            RAGMetrica.criado_em >= data_inicio
        ).all()
        
        if not metricas:
            return {
                "total_buscas": 0,
                "tempo_medio_ms": 0,
                "tempo_minimo_ms": 0,
                "tempo_maximo_ms": 0,
                "media_resultados": 0,
                "queries_unicas": 0,
                "agentes_distintos": 0,
                "sessoes_distintas": 0,
                "periodo_dias": dias
            }
        
        tempos = [m.tempo_ms for m in metricas]
        resultados = [m.num_resultados_retornados for m in metricas]
        queries_unicas = len(set(m.query for m in metricas))
        agentes_distintos = len(set(m.agente_id for m in metricas if m.agente_id))
        sessoes_distintas = len(set(m.sessao_id for m in metricas if m.sessao_id))
        
        return {
            "total_buscas": len(metricas),
            "tempo_medio_ms": int(sum(tempos) / len(tempos)),
            "tempo_minimo_ms": min(tempos),
            "tempo_maximo_ms": max(tempos),
            "media_resultados": round(sum(resultados) / len(resultados), 2),
            "queries_unicas": queries_unicas,
            "agentes_distintos": agentes_distintos,
            "sessoes_distintas": sessoes_distintas,
            "periodo_dias": dias
        }

    @staticmethod
    def obter_queries_mais_frequentes(
        db: Session,
        rag_id: int,
        limit: int = 10,
        dias: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Obtém as queries mais frequentes em um período.
        
        Args:
            db: Sessão do banco
            rag_id: ID do RAG
            limit: Limite de resultados
            dias: Período em dias
            
        Returns:
            Lista com queries e suas frequências
        """
        data_inicio = datetime.now() - timedelta(days=dias)
        
        from sqlalchemy import func
        
        resultados = db.query(
            RAGMetrica.query,
            func.count(RAGMetrica.id).label('frequencia'),
            func.avg(RAGMetrica.tempo_ms).label('tempo_medio_ms'),
            func.avg(RAGMetrica.num_resultados_retornados).label('media_resultados')
        ).filter(
            RAGMetrica.rag_id == rag_id,
            RAGMetrica.criado_em >= data_inicio
        ).group_by(
            RAGMetrica.query
        ).order_by(
            func.count(RAGMetrica.id).desc()
        ).limit(limit).all()
        
        return [
            {
                "query": r.query,
                "frequencia": r.frequencia,
                "tempo_medio_ms": int(r.tempo_medio_ms),
                "media_resultados": round(r.media_resultados, 2)
            }
            for r in resultados
        ]

    @staticmethod
    def deletar_metricas_antigas(db: Session, dias: int = 90) -> int:
        """
        Deleta métricas mais antigas que X dias.
        
        Args:
            db: Sessão do banco
            dias: Idade máxima das métricas em dias
            
        Returns:
            Número de métricas deletadas
        """
        data_limite = datetime.now() - timedelta(days=dias)
        
        count = db.query(RAGMetrica).filter(
            RAGMetrica.criado_em < data_limite
        ).delete()
        
        db.commit()
        logger.info(f"Deletadas {count} métricas com mais de {dias} dias")
        return count

