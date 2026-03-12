"""
Rotas do frontend para métricas.
"""
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from shared import templates
from metrica.metrica_service import MetricaService
from sessao.sessao_service import SessaoService

router = APIRouter(prefix="/metricas", tags=["Frontend - Métricas"])


@router.get("/", response_class=HTMLResponse)
def pagina_metricas_gerais(request: Request, db: Session = Depends(get_db)):
    """Página de métricas gerais do sistema."""
    metricas = MetricaService.obter_metricas_gerais(db)
    sessoes = SessaoService.listar_todas(db)
    
    return templates.TemplateResponse("metrica/geral.html", {
        "request": request,
        "metricas": metricas,
        "sessoes": sessoes,
        "titulo": "Métricas e Estatísticas"
    })


@router.get("/sessao/{sessao_id}", response_class=HTMLResponse)
def pagina_metricas_sessao(
    sessao_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Página de métricas de uma sessão específica."""
    sessao = SessaoService.obter_por_id(db, sessao_id)
    if not sessao:
        return templates.TemplateResponse("shared/erro.html", {
            "request": request,
            "mensagem": "Sessão não encontrada",
            "titulo": "Erro"
        })
    
    metricas = MetricaService.obter_metricas_sessao(db, sessao_id)
    top_clientes = MetricaService.obter_top_clientes(db, sessao_id, 10)
    uso_ferramentas = MetricaService.obter_uso_ferramentas(db, sessao_id)
    
    return templates.TemplateResponse("metrica/sessao.html", {
        "request": request,
        "sessao": sessao,
        "metricas": metricas,
        "top_clientes": top_clientes,
        "uso_ferramentas": uso_ferramentas,
        "titulo": f"Métricas - {sessao.nome}"
    })
