"""
Rotas da API para métricas.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from metrica.metrica_service import MetricaService

router = APIRouter(prefix="/api/metricas", tags=["Métricas"])


@router.get("/gerais")
def obter_metricas_gerais(db: Session = Depends(get_db)):
    """Obtém métricas gerais do sistema."""
    return MetricaService.obter_metricas_gerais(db)


@router.get("/sessao/{sessao_id}")
def obter_metricas_sessao(sessao_id: int, db: Session = Depends(get_db)):
    """Obtém métricas de uma sessão específica."""
    return MetricaService.obter_metricas_sessao(db, sessao_id)


@router.get("/periodo")
def obter_metricas_periodo(
    sessao_id: Optional[int] = Query(None),
    dias: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Obtém métricas de um período específico."""
    return MetricaService.obter_metricas_periodo(db, sessao_id, dias)


@router.get("/sessao/{sessao_id}/top-clientes")
def obter_top_clientes(
    sessao_id: int,
    limite: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtém os clientes que mais enviaram mensagens."""
    return MetricaService.obter_top_clientes(db, sessao_id, limite)


@router.get("/ferramentas")
def obter_uso_ferramentas(
    sessao_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtém estatísticas de uso de ferramentas."""
    return MetricaService.obter_uso_ferramentas(db, sessao_id)


@router.get("/callcenter")
def obter_metricas_callcenter(
    sessao_id: Optional[int] = Query(None),
    dias: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Obtém métricas completas do call center: atendimento, escalação, agendamentos, custos."""
    return MetricaService.obter_metricas_callcenter(db, sessao_id, dias)
