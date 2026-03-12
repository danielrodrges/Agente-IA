"""
Router frontend para RAG.
"""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from shared import templates
from rag.rag_service import RAGService
from rag.rag_schema import RAGCriar, RAGAtualizar
from config.rag_config import RAGConfig

router = APIRouter(prefix="/rags", tags=["RAG Frontend"])


@router.get("/", response_class=HTMLResponse)
def listar_rags_page(request: Request, db: Session = Depends(get_db)):
    """Página de listagem de RAGs."""
    rags = RAGService.listar_todos(db)
    return templates.TemplateResponse("rag/lista.html", {
        "request": request,
        "rags": rags,
        "titulo": "RAG - Base de Conhecimento"
    })


@router.get("/novo", response_class=HTMLResponse)
def novo_rag_page(request: Request, db: Session = Depends(get_db)):
    """Página de criação de RAG."""
    # Obter configurações padrão
    default_config = RAGConfig.get_config(db)
    providers = RAGConfig.get_available_providers()
    
    return templates.TemplateResponse("rag/form.html", {
        "request": request,
        "acao": "criar",
        "rag": None,
        "titulo": "Novo RAG",
        "default_config": default_config,
        "providers": providers
    })


@router.post("/novo", response_class=HTMLResponse)
def criar_rag_post(
    request: Request,
    nome: str = Form(...),
    descricao: str = Form(""),
    provider: str = Form("openai"),
    modelo_embed: str = Form("text-embedding-3-small"),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    top_k: int = Form(3),
    score_threshold: str = Form(""),
    api_key_embed: str = Form(""),
    ativo: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Processa criação de RAG."""
    try:
        # Criar objeto RAG
        rag_data = RAGCriar(
            nome=nome,
            descricao=descricao if descricao else None,
            provider=provider,
            modelo_embed=modelo_embed,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            score_threshold=float(score_threshold) if score_threshold else None,
            api_key_embed=api_key_embed if api_key_embed else None,
            ativo=ativo
        )
        
        # Salvar no banco
        rag = RAGService.criar(db, rag_data)
        
        # Redirecionar para a página de texto
        return RedirectResponse(url=f"/rags/{rag.id}/texto", status_code=303)
        
    except ValueError as e:
        # Em caso de erro, retornar o formulário com erro
        default_config = RAGConfig.get_config(db)
        providers = RAGConfig.get_available_providers()
        
        return templates.TemplateResponse("rag/form.html", {
            "request": request,
            "acao": "criar",
            "rag": None,
            "titulo": "Novo RAG",
            "erro": str(e),
            "default_config": default_config,
            "providers": providers
        })


@router.get("/{rag_id}/editar", response_class=HTMLResponse)
def editar_rag_page(request: Request, rag_id: int, db: Session = Depends(get_db)):
    """Página de edição de RAG."""
    rag = RAGService.obter_por_id(db, rag_id)
    if not rag:
        return RedirectResponse(url="/rags", status_code=303)
    
    providers = RAGConfig.get_available_providers()
    
    return templates.TemplateResponse("rag/form.html", {
        "request": request,
        "acao": "editar",
        "rag": rag,
        "titulo": f"Editar RAG: {rag.nome}",
        "providers": providers
    })


@router.post("/{rag_id}/editar", response_class=HTMLResponse)
def editar_rag_post(
    request: Request,
    rag_id: int,
    nome: str = Form(...),
    descricao: str = Form(""),
    provider: str = Form("openai"),
    modelo_embed: str = Form("text-embedding-3-small"),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    top_k: int = Form(3),
    score_threshold: str = Form(""),
    api_key_embed: str = Form(""),
    ativo: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Processa edição de RAG."""
    try:
        # Verificar se RAG existe
        rag = RAGService.obter_por_id(db, rag_id)
        if not rag:
            return RedirectResponse(url="/rags", status_code=303)
        
        # Criar objeto de atualização
        rag_data = RAGAtualizar(
            nome=nome,
            descricao=descricao if descricao else None,
            provider=provider,
            modelo_embed=modelo_embed,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            score_threshold=float(score_threshold) if score_threshold else None,
            api_key_embed=api_key_embed if api_key_embed else None,
            ativo=ativo
        )
        
        # Atualizar no banco
        rag_atualizado = RAGService.atualizar(db, rag_id, rag_data)
        
        if not rag_atualizado:
            return RedirectResponse(url="/rags", status_code=303)
        
        # Redirecionar para a página de texto
        return RedirectResponse(url=f"/rags/{rag_id}/texto", status_code=303)
        
    except ValueError as e:
        # Em caso de erro, retornar o formulário com erro
        rag = RAGService.obter_por_id(db, rag_id)
        providers = RAGConfig.get_available_providers()
        
        return templates.TemplateResponse("rag/form.html", {
            "request": request,
            "acao": "editar",
            "rag": rag,
            "titulo": f"Editar RAG: {rag.nome if rag else 'RAG'}" if rag else "Editar RAG",
            "erro": str(e),
            "providers": providers
        })


@router.get("/{rag_id}/texto", response_class=HTMLResponse)
def texto_page(request: Request, rag_id: int, db: Session = Depends(get_db)):
    """Página de gerenciamento de texto do RAG."""
    rag = RAGService.obter_por_id(db, rag_id)
    if not rag:
        return RedirectResponse(url="/rags", status_code=303)
    
    return templates.TemplateResponse("rag/texto.html", {
        "request": request,
        "rag": rag,
        "titulo": f"Texto: {rag.nome}"
    })


@router.get("/{rag_id}/testar", response_class=HTMLResponse)
def testar_page(request: Request, rag_id: int, db: Session = Depends(get_db)):
    """Página de teste de busca semântica."""
    rag = RAGService.obter_por_id(db, rag_id)
    if not rag:
        return RedirectResponse(url="/rags", status_code=303)
    
    return templates.TemplateResponse("rag/testar.html", {
        "request": request,
        "rag": rag,
        "titulo": f"Testar RAG: {rag.nome}"
    })


@router.get("/{rag_id}/chunks", response_class=HTMLResponse)
def chunks_page(request: Request, rag_id: int, db: Session = Depends(get_db)):
    """Página para visualizar chunks do RAG."""
    rag = RAGService.obter_por_id(db, rag_id)
    if not rag:
        return RedirectResponse(url="/rags", status_code=303)
    
    # Obter chunks via API
    try:
        chunks = RAGService.obter_chunks(db, rag_id, limit=100)
    except Exception as e:
        chunks = []
    
    return templates.TemplateResponse("rag/chunks.html", {
        "request": request,
        "rag": rag,
        "chunks": chunks,
        "titulo": f"Chunks: {rag.nome}"
    })


@router.get("/{rag_id}/estatisticas", response_class=HTMLResponse)
def estatisticas_page(request: Request, rag_id: int, db: Session = Depends(get_db)):
    """Página de estatísticas do RAG."""
    rag = RAGService.obter_por_id(db, rag_id)
    if not rag:
        return RedirectResponse(url="/rags", status_code=303)
    
    # Obter estatísticas
    try:
        stats = RAGService.obter_estatisticas(db, rag_id)
    except Exception as e:
        stats = {}
    
    return templates.TemplateResponse("rag/estatisticas.html", {
        "request": request,
        "rag": rag,
        "stats": stats,
        "titulo": f"Estatísticas: {rag.nome}"
    })