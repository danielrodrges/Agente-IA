"""
Rotas da API para mensagens.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from mensagem.mensagem_schema import MensagemResposta, MensagemEnviar, HistoricoMensagens
from mensagem.mensagem_service import MensagemService
from sessao.sessao_service import SessaoService

router = APIRouter(prefix="/api/mensagens", tags=["Mensagens"])


@router.get("/sessao/{sessao_id}", response_model=List[MensagemResposta])
def listar_mensagens_sessao(
    sessao_id: int,
    limite: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Lista mensagens de uma sessão."""
    return MensagemService.listar_por_sessao(db, sessao_id, limite, offset)


@router.get("/sessao/{sessao_id}/cliente/{telefone}", response_model=HistoricoMensagens)
def listar_mensagens_cliente(
    sessao_id: int,
    telefone: str,
    limite: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """Lista mensagens de um cliente específico."""
    mensagens = MensagemService.listar_por_cliente(db, sessao_id, telefone, limite)
    return HistoricoMensagens(
        telefone_cliente=telefone,
        mensagens=mensagens,
        total=len(mensagens)
    )


@router.get("/{mensagem_id}", response_model=MensagemResposta)
def obter_mensagem(mensagem_id: int, db: Session = Depends(get_db)):
    """Obtém uma mensagem específica."""
    mensagem = MensagemService.obter_por_id(db, mensagem_id)
    if not mensagem:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    return mensagem


@router.post("/enviar")
def enviar_mensagem(mensagem: MensagemEnviar, db: Session = Depends(get_db)):
    """Envia uma mensagem através de uma sessão."""
    try:
        sucesso = SessaoService.enviar_mensagem(
            db,
            mensagem.sessao_id,
            mensagem.telefone_destino,
            mensagem.texto
        )
        
        if sucesso:
            return {"mensagem": "Mensagem enviada com sucesso"}
        else:
            raise HTTPException(status_code=500, detail="Erro ao enviar mensagem")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessao/{sessao_id}/estatisticas")
def obter_estatisticas_sessao(sessao_id: int, db: Session = Depends(get_db)):
    """Obtém estatísticas de mensagens de uma sessão."""
    total = MensagemService.contar_mensagens_por_sessao(db, sessao_id)
    ultimos_7_dias = MensagemService.contar_mensagens_por_periodo(db, sessao_id, 7)
    clientes_unicos = len(MensagemService.obter_clientes_unicos(db, sessao_id))
    
    return {
        "total_mensagens": total,
        "mensagens_7_dias": ultimos_7_dias,
        "clientes_unicos": clientes_unicos
    }
