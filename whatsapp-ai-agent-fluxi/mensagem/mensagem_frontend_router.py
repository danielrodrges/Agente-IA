"""
Rotas do frontend para mensagens.
"""
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import get_db
from shared import templates
from mensagem.mensagem_service import MensagemService
from sessao.sessao_service import SessaoService

router = APIRouter(prefix="/mensagens", tags=["Frontend - Mensagens"])


@router.get("/sessao/{sessao_id}", response_class=HTMLResponse)
def pagina_historico_sessao(
    sessao_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Página de histórico de conversas de uma sessão."""
    sessao = SessaoService.obter_por_id(db, sessao_id)
    if not sessao:
        return templates.TemplateResponse("shared/erro.html", {
            "request": request,
            "mensagem": "Sessão não encontrada",
            "titulo": "Erro"
        })
    
    # Obter resumo de todas as conversas
    conversas = MensagemService.obter_conversas_resumo(db, sessao_id)
    total_mensagens = MensagemService.contar_mensagens_por_sessao(db, sessao_id)
    
    return templates.TemplateResponse("mensagem/historico.html", {
        "request": request,
        "sessao": sessao,
        "conversas": conversas,
        "total_mensagens": total_mensagens,
        "total_conversas": len(conversas),
        "titulo": f"Histórico - {sessao.nome}"
    })


@router.get("/sessao/{sessao_id}/conversa/{telefone}", response_class=HTMLResponse)
def pagina_conversa_cliente(
    sessao_id: int,
    telefone: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Página de conversa com um cliente específico (estilo chat)."""
    sessao = SessaoService.obter_por_id(db, sessao_id)
    if not sessao:
        return templates.TemplateResponse("shared/erro.html", {
            "request": request,
            "mensagem": "Sessão não encontrada",
            "titulo": "Erro"
        })
    
    # Listar mensagens em ordem cronológica (mais antigas primeiro)
    mensagens = MensagemService.listar_conversa_completa(db, sessao_id, telefone, limite=200)
    
    # Obter nome do cliente (se disponível)
    nome_cliente = None
    if mensagens:
        for msg in mensagens:
            if msg.nome_cliente:
                nome_cliente = msg.nome_cliente
                break
    
    return templates.TemplateResponse("mensagem/conversa.html", {
        "request": request,
        "sessao": sessao,
        "telefone": telefone,
        "nome_cliente": nome_cliente,
        "mensagens": mensagens,
        "titulo": f"Conversa - {nome_cliente or telefone}"
    })
