"""
Rotas do frontend para provedores LLM.
"""
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from shared import templates
from llm_providers.llm_providers_service import ProvedorLLMService
from llm_providers.llm_providers_schema import ProvedorLLMCriar, ProvedorLLMAtualizar

router = APIRouter(prefix="/provedores-llm", tags=["Frontend - Provedores LLM"])


@router.get("/", response_class=HTMLResponse)
def pagina_provedores(request: Request, db: Session = Depends(get_db), erro: str = None):
    """Página principal de provedores LLM."""
    provedores = ProvedorLLMService.listar_todos(db)
    
    return templates.TemplateResponse("llm_providers/lista.html", {
        "request": request,
        "provedores": provedores,
        "titulo": "Provedores LLM",
        "erro": erro
    })


@router.get("/novo", response_class=HTMLResponse)
def pagina_novo_provedor(request: Request):
    """Página para criar novo provedor."""
    return templates.TemplateResponse("llm_providers/form.html", {
        "request": request,
        "titulo": "Novo Provedor LLM",
        "provedor": None,
        "acao": "criar"
    })


@router.get("/{provedor_id}/editar", response_class=HTMLResponse)
def pagina_editar_provedor(provedor_id: int, request: Request, db: Session = Depends(get_db)):
    """Redireciona para a página de detalhes com aba de edição."""
    return RedirectResponse(url=f"/provedores-llm/{provedor_id}/detalhes", status_code=302)


@router.get("/{provedor_id}/detalhes", response_class=HTMLResponse)
def pagina_detalhes_provedor(
    provedor_id: int, 
    request: Request, 
    db: Session = Depends(get_db),
    erro: str = None,
    sucesso: str = None
):
    """Página de detalhes do provedor."""
    provedor = ProvedorLLMService.obter_por_id(db, provedor_id)
    if not provedor:
        raise HTTPException(status_code=404, detail="Provedor não encontrado")
    
    modelos = ProvedorLLMService.obter_modelos(db, provedor_id)
    estatisticas = ProvedorLLMService.obter_estatisticas(db, provedor_id)
    
    return templates.TemplateResponse("llm_providers/detalhes.html", {
        "request": request,
        "provedor": provedor,
        "modelos": modelos,
        "estatisticas": estatisticas,
        "titulo": f"{provedor.nome}",
        "erro": erro,
        "sucesso": sucesso
    })


@router.post("/salvar")
async def salvar_provedor(
    request: Request,
    acao: str = Form(...),
    provedor_id: Optional[int] = Form(None),
    nome: str = Form(...),
    base_url: str = Form(...),
    api_key: Optional[str] = Form(None),
    descricao: Optional[str] = Form(None),
    ativo: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Salva um provedor (criar ou editar)."""
    try:
        if acao == "criar":
            # Criar novo provedor
            provedor_data = ProvedorLLMCriar(
                nome=nome,
                base_url=base_url,
                api_key=api_key,
                descricao=descricao,
                ativo=ativo
            )
            provedor = ProvedorLLMService.criar(db, provedor_data)
            return RedirectResponse(
                url=f"/provedores-llm/{provedor.id}/detalhes?sucesso=Provedor criado com sucesso!", 
                status_code=303
            )
            
        elif acao == "editar" and provedor_id:
            # Editar provedor existente
            provedor_data = ProvedorLLMAtualizar(
                nome=nome,
                base_url=base_url,
                api_key=api_key,
                descricao=descricao,
                ativo=ativo
            )
            provedor = ProvedorLLMService.atualizar(db, provedor_id, provedor_data)
            if not provedor:
                raise HTTPException(status_code=404, detail="Provedor não encontrado")
            return RedirectResponse(
                url=f"/provedores-llm/{provedor_id}/detalhes?sucesso=Provedor atualizado com sucesso!", 
                status_code=303
            )
        else:
            raise HTTPException(status_code=400, detail="Ação inválida")
            
    except Exception as e:
        # Em caso de erro, redirecionar com mensagem de erro
        if provedor_id:
            return RedirectResponse(
                url=f"/provedores-llm/{provedor_id}/detalhes?erro={str(e)}", 
                status_code=303
            )
        return RedirectResponse(url=f"/provedores-llm?erro={str(e)}", status_code=303)


@router.post("/{provedor_id}/testar")
async def testar_provedor(provedor_id: int, db: Session = Depends(get_db)):
    """Testa a conexão com um provedor."""
    resultado = await ProvedorLLMService.testar_conexao(db, provedor_id)
    
    if resultado.sucesso:
        return RedirectResponse(
            url=f"/provedores-llm/{provedor_id}/detalhes?sucesso={resultado.mensagem}", 
            status_code=303
        )
    else:
        return RedirectResponse(
            url=f"/provedores-llm/{provedor_id}/detalhes?erro={resultado.mensagem}", 
            status_code=303
        )


@router.post("/{provedor_id}/deletar")
def deletar_provedor(provedor_id: int, db: Session = Depends(get_db)):
    """Deleta um provedor."""
    try:
        sucesso = ProvedorLLMService.deletar(db, provedor_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Provedor não encontrado")
        return RedirectResponse(url="/provedores-llm", status_code=303)
    except ValueError as e:
        # Redirecionar com mensagem de erro
        return RedirectResponse(url=f"/provedores-llm?erro={str(e)}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/provedores-llm?erro=Erro interno: {str(e)}", status_code=303)


@router.get("/{provedor_id}/modelos", response_class=HTMLResponse)
def pagina_modelos(provedor_id: int, request: Request, db: Session = Depends(get_db)):
    """Redireciona para a página de detalhes."""
    return RedirectResponse(url=f"/provedores-llm/{provedor_id}/detalhes", status_code=302)


@router.get("/{provedor_id}/estatisticas", response_class=HTMLResponse)
def pagina_estatisticas(provedor_id: int, request: Request, db: Session = Depends(get_db)):
    """Redireciona para a página de detalhes."""
    return RedirectResponse(url=f"/provedores-llm/{provedor_id}/detalhes", status_code=302)


@router.get("/{provedor_id}/testar", response_class=HTMLResponse)
def pagina_teste(provedor_id: int, request: Request, db: Session = Depends(get_db)):
    """Redireciona para a página de detalhes."""
    return RedirectResponse(url=f"/provedores-llm/{provedor_id}/detalhes", status_code=302)


@router.post("/{provedor_id}/enviar-teste")
async def enviar_teste(
    provedor_id: int,
    request: Request,
    modelo: str = Form(...),
    mensagem: str = Form(...),
    temperatura: float = Form(0.7),
    max_tokens: int = Form(2000),
    ajax: str = None,
    db: Session = Depends(get_db)
):
    """Envia um teste para um provedor."""
    try:
        from llm_providers.llm_providers_schema import RequisicaoLLM, ConfiguracaoProvedor
        from fastapi.responses import JSONResponse
        
        # Preparar requisição
        requisicao = RequisicaoLLM(
            mensagens=[{"role": "user", "content": mensagem}],
            modelo=modelo,
            configuracao=ConfiguracaoProvedor(
                temperatura=temperatura,
                max_tokens=max_tokens
            ),
            stream=False
        )
        
        # Enviar requisição
        resposta = await ProvedorLLMService.enviar_requisicao(db, provedor_id, requisicao)
        
        # Se for AJAX, retornar JSON
        if ajax:
            return JSONResponse({
                "sucesso": True,
                "conteudo": resposta.conteudo,
                "modelo": resposta.modelo,
                "tokens": resposta.tokens_usados,
                "tempo_ms": int(resposta.tempo_geracao_ms) if resposta.tempo_geracao_ms else 0
            })
        
        # Senão, redirecionar (fallback)
        msg_sucesso = f"Teste realizado com sucesso! Tempo: {resposta.tempo_geracao_ms:.0f}ms"
        if resposta.tokens_usados:
            msg_sucesso += f" | Tokens: {resposta.tokens_usados}"
        
        return RedirectResponse(
            url=f"/provedores-llm/{provedor_id}/detalhes?sucesso={msg_sucesso}", 
            status_code=303
        )
        
    except Exception as e:
        # Se for AJAX, retornar JSON com erro
        if ajax:
            from fastapi.responses import JSONResponse
            return JSONResponse({
                "sucesso": False,
                "erro": str(e)
            }, status_code=200)
        
        # Senão, redirecionar com erro
        return RedirectResponse(
            url=f"/provedores-llm/{provedor_id}/detalhes?erro=Erro no teste: {str(e)}", 
            status_code=303
        )
