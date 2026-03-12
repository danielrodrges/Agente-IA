"""
Rotas da API para sessões WhatsApp.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from sessao.sessao_schema import (
    SessaoResposta,
    SessaoCriar,
    SessaoAtualizar,
    SessaoStatusResposta
)
from sessao.sessao_service import SessaoService

router = APIRouter(prefix="/api/sessoes", tags=["Sessões"])


@router.get("/", response_model=List[SessaoResposta])
def listar_sessoes(apenas_ativas: bool = False, db: Session = Depends(get_db)):
    """Lista todas as sessões."""
    return SessaoService.listar_todas(db, apenas_ativas)


@router.get("/{sessao_id}", response_model=SessaoResposta)
def obter_sessao(sessao_id: int, db: Session = Depends(get_db)):
    """Obtém uma sessão específica."""
    sessao = SessaoService.obter_por_id(db, sessao_id)
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return sessao


@router.post("/", response_model=SessaoResposta)
def criar_sessao(sessao: SessaoCriar, db: Session = Depends(get_db)):
    """Cria uma nova sessão."""
    try:
        return SessaoService.criar(db, sessao)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{sessao_id}", response_model=SessaoResposta)
def atualizar_sessao(
    sessao_id: int,
    sessao: SessaoAtualizar,
    db: Session = Depends(get_db)
):
    """Atualiza uma sessão existente."""
    sessao_atualizada = SessaoService.atualizar(db, sessao_id, sessao)
    if not sessao_atualizada:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return sessao_atualizada


@router.delete("/{sessao_id}")
def deletar_sessao(sessao_id: int, db: Session = Depends(get_db)):
    """Deleta uma sessão."""
    sucesso = SessaoService.deletar(db, sessao_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return {"mensagem": "Sessão deletada com sucesso"}


@router.post("/{sessao_id}/conectar", response_model=SessaoStatusResposta)
def conectar_sessao(sessao_id: int, db: Session = Depends(get_db)):
    """Conecta uma sessão WhatsApp."""
    try:
        return SessaoService.conectar(db, sessao_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{sessao_id}/desconectar", response_model=SessaoStatusResposta)
def desconectar_sessao(sessao_id: int, db: Session = Depends(get_db)):
    """Desconecta uma sessão WhatsApp."""
    try:
        return SessaoService.desconectar(db, sessao_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{sessao_id}/status", response_model=SessaoStatusResposta)
def obter_status_sessao(sessao_id: int, db: Session = Depends(get_db)):
    """Obtém o status atual de uma sessão."""
    try:
        return SessaoService.obter_status(db, sessao_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
