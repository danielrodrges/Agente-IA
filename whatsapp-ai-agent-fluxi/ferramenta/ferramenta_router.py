"""
Rotas da API para ferramentas.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from ferramenta.ferramenta_schema import (
    FerramentaResposta,
    FerramentaCriar,
    FerramentaAtualizar
)
from ferramenta.ferramenta_service import FerramentaService

router = APIRouter(prefix="/api/ferramentas", tags=["Ferramentas"])


@router.get("/", response_model=List[FerramentaResposta])
def listar_ferramentas(
    apenas_ativas: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Lista todas as ferramentas."""
    if apenas_ativas:
        return FerramentaService.listar_ferramentas_ativas(db)
    return FerramentaService.listar_todas(db)


@router.get("/{ferramenta_id}", response_model=FerramentaResposta)
def obter_ferramenta(ferramenta_id: int, db: Session = Depends(get_db)):
    """Obtém uma ferramenta específica."""
    ferramenta = FerramentaService.obter_por_id(db, ferramenta_id)
    if not ferramenta:
        raise HTTPException(status_code=404, detail="Ferramenta não encontrada")
    return ferramenta


@router.post("/", response_model=FerramentaResposta)
def criar_ferramenta(ferramenta: FerramentaCriar, db: Session = Depends(get_db)):
    """Cria uma nova ferramenta."""
    try:
        return FerramentaService.criar(db, ferramenta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{ferramenta_id}", response_model=FerramentaResposta)
def atualizar_ferramenta(
    ferramenta_id: int,
    ferramenta: FerramentaAtualizar,
    db: Session = Depends(get_db)
):
    """Atualiza uma ferramenta existente."""
    try:
        ferramenta_atualizada = FerramentaService.atualizar(db, ferramenta_id, ferramenta)
        if not ferramenta_atualizada:
            raise HTTPException(status_code=404, detail="Ferramenta não encontrada")
        return ferramenta_atualizada
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{ferramenta_id}")
def deletar_ferramenta(ferramenta_id: int, db: Session = Depends(get_db)):
    """Deleta uma ferramenta."""
    sucesso = FerramentaService.deletar(db, ferramenta_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Ferramenta não encontrada")
    return {"mensagem": "Ferramenta deletada com sucesso"}
