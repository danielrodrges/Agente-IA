"""
Router API para escalações ao atendente humano.
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db, SessionLocal
from escalacao.escalacao_service import EscalacaoService
from escalacao.escalacao_schema import (
    EscalacaoCriar,
    EscalacaoResponder,
    EscalacaoAssumir,
    EscalacaoResposta,
    InteracaoCriar,
    InteracaoResposta,
)
from escalacao.websocket_manager import manager

router = APIRouter(prefix="/api/escalacoes", tags=["Escalações"])


# --- WebSocket ---

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket para notificações em tempo real do painel do atendente.
    Envia notificações quando:
    - Nova escalação é criada
    - Escalação é respondida
    - Conversa é assumida/devolvida
    """
    await manager.connect(websocket)
    try:
        while True:
            # Mantém a conexão aberta e escuta mensagens do cliente
            data = await websocket.receive_text()
            # Podemos processar mensagens do painel se necessário
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# --- CRUD ---

@router.get("/")
def listar_escalacoes(
    status: Optional[str] = None,
    tipo: Optional[str] = None,
    prioridade: Optional[str] = None,
    sessao_id: Optional[int] = None,
    atendente_id: Optional[str] = None,
    limite: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Lista escalações com filtros."""
    escalacoes = EscalacaoService.listar_todas(
        db, status, tipo, prioridade, sessao_id, atendente_id, limite, offset
    )
    return [EscalacaoResposta.model_validate(e) for e in escalacoes]


@router.get("/pendentes")
def listar_pendentes(limite: int = 50, db: Session = Depends(get_db)):
    """Lista escalações pendentes (fila do atendente)."""
    escalacoes = EscalacaoService.listar_pendentes(db, limite)
    return [EscalacaoResposta.model_validate(e) for e in escalacoes]


@router.get("/contagem-pendentes")
def contar_pendentes(db: Session = Depends(get_db)):
    """Retorna contagem de escalações pendentes (para badge no sidebar)."""
    return {"pendentes": EscalacaoService.contar_pendentes(db)}


@router.get("/{escalacao_id}")
def obter_escalacao(escalacao_id: int, db: Session = Depends(get_db)):
    """Obtém uma escalação por ID."""
    escalacao = EscalacaoService.obter_por_id(db, escalacao_id)
    if not escalacao:
        raise HTTPException(status_code=404, detail="Escalação não encontrada")
    return EscalacaoResposta.model_validate(escalacao)


@router.post("/")
def criar_escalacao(escalacao: EscalacaoCriar, db: Session = Depends(get_db)):
    """Cria uma nova escalação (chamada pelo IA)."""
    db_escalacao = EscalacaoService.criar_escalacao(db, escalacao)
    return EscalacaoResposta.model_validate(db_escalacao)


# --- Ações do Atendente ---

@router.post("/{escalacao_id}/responder")
async def responder_escalacao(
    escalacao_id: int,
    resposta: EscalacaoResponder,
    db: Session = Depends(get_db),
):
    """
    Atendente responde à escalação.
    O IA retoma a conversa com o paciente usando a informação fornecida.
    """
    escalacao = await EscalacaoService.responder_escalacao(db, escalacao_id, resposta)
    if not escalacao:
        raise HTTPException(status_code=404, detail="Escalação não encontrada")
    
    # Notificar via WebSocket
    await manager.broadcast({
        "tipo": "escalacao_respondida",
        "escalacao_id": escalacao_id,
    })
    
    return EscalacaoResposta.model_validate(escalacao)


@router.post("/{escalacao_id}/assumir")
def assumir_conversa(
    escalacao_id: int,
    dados: EscalacaoAssumir,
    db: Session = Depends(get_db),
):
    """Atendente assume a conversa diretamente (último recurso)."""
    escalacao = EscalacaoService.assumir_conversa(
        db, escalacao_id, dados.atendente_id, dados.atendente_nome
    )
    if not escalacao:
        raise HTTPException(status_code=404, detail="Escalação não encontrada")
    return EscalacaoResposta.model_validate(escalacao)


@router.post("/{escalacao_id}/devolver")
def devolver_para_ia(escalacao_id: int, db: Session = Depends(get_db)):
    """Atendente devolve a conversa para o IA."""
    escalacao = EscalacaoService.devolver_para_ia(db, escalacao_id)
    if not escalacao:
        raise HTTPException(status_code=404, detail="Escalação não encontrada")
    return EscalacaoResposta.model_validate(escalacao)


@router.post("/{escalacao_id}/em-atendimento")
def marcar_em_atendimento(
    escalacao_id: int,
    dados: EscalacaoAssumir,
    db: Session = Depends(get_db),
):
    """Marca escalação como em atendimento."""
    escalacao = EscalacaoService.marcar_em_atendimento(
        db, escalacao_id, dados.atendente_id, dados.atendente_nome
    )
    if not escalacao:
        raise HTTPException(status_code=404, detail="Escalação não encontrada")
    return EscalacaoResposta.model_validate(escalacao)


# --- Métricas ---

@router.get("/metricas/escalacao")
def metricas_escalacao(dias: int = 30, db: Session = Depends(get_db)):
    """Obtém métricas de escalação."""
    return EscalacaoService.obter_metricas_escalacao(db, dias)


@router.get("/metricas/atendimento")
def metricas_atendimento(dias: int = 30, db: Session = Depends(get_db)):
    """Obtém métricas de atendimento (interações)."""
    return EscalacaoService.obter_metricas_atendimento(db, dias)


@router.get("/metricas/por-atendente")
def metricas_por_atendente(dias: int = 30, db: Session = Depends(get_db)):
    """Obtém métricas individuais por atendente."""
    return EscalacaoService.obter_metricas_por_atendente(db, dias)


@router.get("/metricas/volume-horario")
def volume_por_hora(dias: int = 7, db: Session = Depends(get_db)):
    """Obtém volume de escalações por hora/dia."""
    return EscalacaoService.obter_volume_por_hora(db, dias)


# --- Interações ---

@router.post("/interacoes")
def registrar_interacao(interacao: InteracaoCriar, db: Session = Depends(get_db)):
    """Registra uma interação de atendimento."""
    db_interacao = EscalacaoService.registrar_interacao(db, interacao)
    return InteracaoResposta.model_validate(db_interacao)


# --- Manutenção ---

@router.post("/expirar")
def expirar_escalacoes(timeout_minutos: int = 30, db: Session = Depends(get_db)):
    """Expira escalações antigas sem resposta."""
    total = EscalacaoService.expirar_antigas(db, timeout_minutos)
    return {"expiradas": total}
