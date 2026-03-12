"""
Router Frontend para escalações e painel do atendente.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import get_db
from escalacao.escalacao_service import EscalacaoService
from mensagem.mensagem_service import MensagemService
from shared import templates

router = APIRouter(prefix="/atendente", tags=["Atendente Frontend"])


@router.get("/painel", response_class=HTMLResponse)
def painel_atendente(request: Request, db: Session = Depends(get_db)):
    """Painel principal do atendente com fila de escalações."""
    pendentes = EscalacaoService.listar_pendentes(db)
    metricas_escalacao = EscalacaoService.obter_metricas_escalacao(db, dias=1)
    contagem = EscalacaoService.contar_pendentes(db)
    
    return templates.TemplateResponse("atendente/painel.html", {
        "request": request,
        "pendentes": pendentes,
        "metricas": metricas_escalacao,
        "contagem_pendentes": contagem,
        "titulo": "Painel do Atendente",
    })


@router.get("/escalacao/{escalacao_id}", response_class=HTMLResponse)
def detalhes_escalacao(
    escalacao_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Detalhes de uma escalação com conversa completa."""
    escalacao = EscalacaoService.obter_por_id(db, escalacao_id)
    if not escalacao:
        return templates.TemplateResponse("atendente/painel.html", {
            "request": request,
            "erro": "Escalação não encontrada",
            "titulo": "Erro",
        })
    
    # Obter conversa completa do paciente
    conversa = MensagemService.listar_conversa_completa(
        db, escalacao.sessao_id, escalacao.telefone_cliente, limite=50
    )
    
    return templates.TemplateResponse("atendente/conversa.html", {
        "request": request,
        "escalacao": escalacao,
        "conversa": conversa,
        "titulo": f"Escalação #{escalacao.id}",
    })


@router.get("/metricas", response_class=HTMLResponse)
def metricas_atendente(request: Request, db: Session = Depends(get_db)):
    """Dashboard de métricas de atendimento."""
    metricas_escalacao = EscalacaoService.obter_metricas_escalacao(db, dias=30)
    metricas_atendimento = EscalacaoService.obter_metricas_atendimento(db, dias=30)
    metricas_por_atendente = EscalacaoService.obter_metricas_por_atendente(db, dias=30)
    volume_horario = EscalacaoService.obter_volume_por_hora(db, dias=7)
    
    return templates.TemplateResponse("atendente/metricas.html", {
        "request": request,
        "metricas_escalacao": metricas_escalacao,
        "metricas_atendimento": metricas_atendimento,
        "metricas_por_atendente": metricas_por_atendente,
        "volume_horario": volume_horario,
        "titulo": "Métricas de Atendimento",
    })


@router.get("/historico", response_class=HTMLResponse)
def historico_escalacoes(
    request: Request,
    status: str = None,
    tipo: str = None,
    db: Session = Depends(get_db),
):
    """Histórico de escalações com filtros."""
    escalacoes = EscalacaoService.listar_todas(
        db, status=status, tipo=tipo, limite=100
    )
    
    return templates.TemplateResponse("atendente/historico.html", {
        "request": request,
        "escalacoes": escalacoes,
        "filtro_status": status,
        "filtro_tipo": tipo,
        "titulo": "Histórico de Escalações",
    })
