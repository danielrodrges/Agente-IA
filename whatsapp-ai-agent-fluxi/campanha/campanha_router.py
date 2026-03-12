"""
Router API para campanhas de mensagens ativas.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from campanha.campanha_service import CampanhaService
from campanha.campanha_schema import (
    CampanhaCriar,
    CampanhaAtualizar,
    CampanhaResposta,
    EnvioCriar,
    EnvioResposta,
)

router = APIRouter(prefix="/api/campanhas", tags=["Campanhas"])


@router.get("/")
def listar_campanhas(
    tipo: Optional[str] = None,
    status: Optional[str] = None,
    limite: int = 50,
    db: Session = Depends(get_db),
):
    """Lista todas as campanhas."""
    campanhas = CampanhaService.listar_todas(db, tipo, status, limite)
    return [CampanhaResposta.model_validate(c) for c in campanhas]


@router.get("/{campanha_id}")
def obter_campanha(campanha_id: int, db: Session = Depends(get_db)):
    """Obtém uma campanha por ID."""
    campanha = CampanhaService.obter_por_id(db, campanha_id)
    if not campanha:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return CampanhaResposta.model_validate(campanha)


@router.post("/")
def criar_campanha(campanha: CampanhaCriar, db: Session = Depends(get_db)):
    """Cria uma nova campanha."""
    db_campanha = CampanhaService.criar(db, campanha)
    return CampanhaResposta.model_validate(db_campanha)


@router.put("/{campanha_id}")
def atualizar_campanha(
    campanha_id: int, dados: CampanhaAtualizar, db: Session = Depends(get_db)
):
    """Atualiza uma campanha."""
    campanha = CampanhaService.atualizar(db, campanha_id, dados)
    if not campanha:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return CampanhaResposta.model_validate(campanha)


@router.delete("/{campanha_id}")
def deletar_campanha(campanha_id: int, db: Session = Depends(get_db)):
    """Deleta uma campanha."""
    if not CampanhaService.deletar(db, campanha_id):
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return {"mensagem": "Campanha deletada"}


# --- Destinatários ---

@router.post("/{campanha_id}/destinatarios")
def adicionar_destinatario(
    campanha_id: int, envio: EnvioCriar, db: Session = Depends(get_db)
):
    """Adiciona destinatário à campanha."""
    db_envio = CampanhaService.adicionar_destinatario(db, campanha_id, envio)
    if not db_envio:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return EnvioResposta.model_validate(db_envio)


@router.get("/{campanha_id}/envios")
def listar_envios(
    campanha_id: int,
    status: Optional[str] = None,
    limite: int = 100,
    db: Session = Depends(get_db),
):
    """Lista envios de uma campanha."""
    envios = CampanhaService.listar_envios(db, campanha_id, status, limite)
    return [EnvioResposta.model_validate(e) for e in envios]


# --- Execução ---

@router.post("/{campanha_id}/executar")
async def executar_campanha(campanha_id: int, db: Session = Depends(get_db)):
    """Executa uma campanha (envia mensagens)."""
    resultado = await CampanhaService.executar_campanha(db, campanha_id)
    return resultado


@router.post("/confirmar-automatico")
async def gerar_confirmacoes(
    antecedencia_horas: int = 24, db: Session = Depends(get_db)
):
    """Gera confirmações automáticas de consultas."""
    resultado = await CampanhaService.gerar_confirmacoes_automaticas(
        db, antecedencia_horas
    )
    return resultado


# --- Métricas ---

@router.get("/metricas/geral")
def metricas_campanhas(dias: int = 30, db: Session = Depends(get_db)):
    """Obtém métricas das campanhas."""
    return CampanhaService.obter_metricas_campanhas(db, dias)
