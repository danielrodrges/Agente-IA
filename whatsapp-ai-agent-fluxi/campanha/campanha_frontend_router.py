"""
Router Frontend para campanhas.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import get_db
from campanha.campanha_service import CampanhaService
from shared import templates

router = APIRouter(prefix="/campanhas", tags=["Campanhas Frontend"])


@router.get("/", response_class=HTMLResponse)
def listar_campanhas(request: Request, db: Session = Depends(get_db)):
    """Lista de campanhas."""
    campanhas = CampanhaService.listar_todas(db)
    metricas = CampanhaService.obter_metricas_campanhas(db)
    
    return templates.TemplateResponse("campanha/lista.html", {
        "request": request,
        "campanhas": campanhas,
        "metricas": metricas,
        "titulo": "Campanhas",
    })


@router.get("/nova", response_class=HTMLResponse)
def nova_campanha(request: Request, db: Session = Depends(get_db)):
    """Formulário para nova campanha."""
    return templates.TemplateResponse("campanha/form.html", {
        "request": request,
        "campanha": None,
        "titulo": "Nova Campanha",
    })


@router.get("/{campanha_id}", response_class=HTMLResponse)
def detalhes_campanha(
    campanha_id: int, request: Request, db: Session = Depends(get_db)
):
    """Detalhes de uma campanha."""
    campanha = CampanhaService.obter_por_id(db, campanha_id)
    if not campanha:
        return templates.TemplateResponse("campanha/lista.html", {
            "request": request,
            "erro": "Campanha não encontrada",
            "titulo": "Erro",
        })
    
    envios = CampanhaService.listar_envios(db, campanha_id)
    
    return templates.TemplateResponse("campanha/detalhes.html", {
        "request": request,
        "campanha": campanha,
        "envios": envios,
        "titulo": f"Campanha: {campanha.nome}",
    })
