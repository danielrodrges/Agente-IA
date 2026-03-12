"""
Router frontend para ferramentas.
Rotas para páginas HTML de gerenciamento de ferramentas.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from shared import templates
from ferramenta.ferramenta_service import FerramentaService

router = APIRouter(tags=["Ferramentas Frontend"])


@router.get("/ferramentas", response_class=HTMLResponse)
def listar_ferramentas_page(request: Request, db: Session = Depends(get_db)):
    """Página de listagem de ferramentas."""
    ferramentas = FerramentaService.listar_todas(db)
    
    return templates.TemplateResponse("ferramenta/lista.html", {
        "request": request,
        "ferramentas": ferramentas
    })


@router.get("/ferramentas/{ferramenta_id}/editar", response_class=HTMLResponse)
def editar_ferramenta_page(request: Request, ferramenta_id: int, db: Session = Depends(get_db)):
    """Página de edição de ferramenta."""
    ferramenta = FerramentaService.obter_por_id(db, ferramenta_id)
    
    if not ferramenta:
        return RedirectResponse(url="/ferramentas?erro=Ferramenta não encontrada", status_code=303)
    
    return templates.TemplateResponse("ferramenta/form.html", {
        "request": request,
        "ferramenta": ferramenta,
        "acao": "editar"
    })
