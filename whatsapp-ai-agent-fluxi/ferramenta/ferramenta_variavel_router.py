"""
Rotas da API para variáveis de ferramentas.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from ferramenta.ferramenta_variavel_schema import (
    FerramentaVariavelResposta,
    FerramentaVariavelCriar,
    FerramentaVariavelAtualizar
)
from ferramenta.ferramenta_variavel_service import FerramentaVariavelService

router = APIRouter(prefix="/api/ferramentas", tags=["Variáveis de Ferramentas"])


@router.get("/{ferramenta_id}/variaveis", response_model=List[FerramentaVariavelResposta])
def listar_variaveis(ferramenta_id: int, db: Session = Depends(get_db)):
    """Lista todas as variáveis de uma ferramenta."""
    return FerramentaVariavelService.listar_por_ferramenta(db, ferramenta_id)


@router.post("/{ferramenta_id}/variaveis", response_model=FerramentaVariavelResposta)
def criar_variavel(
    ferramenta_id: int,
    variavel: FerramentaVariavelCriar,
    db: Session = Depends(get_db)
):
    """Cria uma nova variável para a ferramenta."""
    # Garantir que o ferramenta_id do path seja usado
    variavel.ferramenta_id = ferramenta_id
    
    try:
        return FerramentaVariavelService.criar(db, variavel)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/variaveis/{variavel_id}", response_model=FerramentaVariavelResposta)
def atualizar_variavel(
    variavel_id: int,
    variavel: FerramentaVariavelAtualizar,
    db: Session = Depends(get_db)
):
    """Atualiza uma variável existente."""
    variavel_atualizada = FerramentaVariavelService.atualizar(db, variavel_id, variavel)
    if not variavel_atualizada:
        raise HTTPException(status_code=404, detail="Variável não encontrada")
    return variavel_atualizada


@router.delete("/variaveis/{variavel_id}")
def deletar_variavel(variavel_id: int, db: Session = Depends(get_db)):
    """Deleta uma variável."""
    sucesso = FerramentaVariavelService.deletar(db, variavel_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Variável não encontrada")
    return {"mensagem": "Variável deletada com sucesso"}
