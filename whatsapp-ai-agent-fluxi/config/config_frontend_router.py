"""
Rotas do frontend para configurações.
"""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from config.config_service import ConfiguracaoService
from llm_providers.llm_providers_service import ProvedorLLMService
from shared import templates

router = APIRouter(prefix="/configuracoes", tags=["Frontend - Configurações"])


@router.get("/", response_class=HTMLResponse)
def pagina_configuracoes(request: Request, db: Session = Depends(get_db)):
    """Página de configurações do sistema."""
    # Buscar configurações por categoria
    config_openrouter = ConfiguracaoService.listar_por_categoria(db, "openrouter")
    config_agente = ConfiguracaoService.listar_por_categoria(db, "agente")
    config_geral = ConfiguracaoService.listar_por_categoria(db, "geral")
    config_llm = ConfiguracaoService.listar_por_categoria(db, "llm")
    config_sessao = ConfiguracaoService.listar_por_categoria(db, "sessao")
    config_ferramenta = ConfiguracaoService.listar_por_categoria(db, "ferramenta")
    config_mcp = ConfiguracaoService.listar_por_categoria(db, "mcp")
    config_audio = ConfiguracaoService.listar_por_categoria(db, "audio")
    
    # Buscar provedores locais para o dropdown
    provedores_locais = ProvedorLLMService.listar_todos(db)
    
    return templates.TemplateResponse("config/settings.html", {
        "request": request,
        "config_openrouter": config_openrouter,
        "config_agente": config_agente,
        "config_geral": config_geral,
        "config_llm": config_llm,
        "config_sessao": config_sessao,
        "config_ferramenta": config_ferramenta,
        "config_mcp": config_mcp,
        "config_audio": config_audio,
        "provedores_locais": provedores_locais,
        "titulo": "Configurações do Sistema"
    })


@router.post("/salvar-openrouter")
async def salvar_openrouter(
    request: Request,
    api_key: str = Form(...),
    modelo_padrao: str = Form(...),
    acao: str = Form(...),
    db: Session = Depends(get_db)
):
    """Salva configurações do OpenRouter."""
    if acao == "testar":
        # Testar conexão
        resultado = await ConfiguracaoService.testar_conexao_openrouter(db, api_key)
        # Redirecionar com mensagem
        return RedirectResponse(url="/configuracoes", status_code=303)
    else:
        # Salvar configurações
        ConfiguracaoService.definir_valor(db, "openrouter_api_key", api_key)
        ConfiguracaoService.definir_valor(db, "openrouter_modelo_padrao", modelo_padrao)
        return RedirectResponse(url="/configuracoes", status_code=303)


@router.post("/salvar-parametros-llm")
def salvar_parametros_llm(
    temperatura: float = Form(...),
    max_tokens: int = Form(...),
    top_p: float = Form(...),
    frequency_penalty: float = Form(...),
    presence_penalty: float = Form(...),
    db: Session = Depends(get_db)
):
    """Salva parâmetros LLM."""
    ConfiguracaoService.definir_valor(db, "openrouter_temperatura", str(temperatura))
    ConfiguracaoService.definir_valor(db, "openrouter_max_tokens", str(max_tokens))
    ConfiguracaoService.definir_valor(db, "openrouter_top_p", str(top_p))
    ConfiguracaoService.definir_valor(db, "openrouter_frequency_penalty", str(frequency_penalty))
    ConfiguracaoService.definir_valor(db, "openrouter_presence_penalty", str(presence_penalty))
    return RedirectResponse(url="/configuracoes", status_code=303)


@router.post("/salvar-agente")
def salvar_agente(
    papel: str = Form(...),
    objetivo: str = Form(...),
    politicas: str = Form(...),
    tarefa: str = Form(...),
    objetivo_explicito: str = Form(...),
    publico: str = Form(...),
    restricoes: str = Form(...),
    db: Session = Depends(get_db)
):
    """Salva configurações do agente."""
    ConfiguracaoService.definir_valor(db, "agente_papel_padrao", papel)
    ConfiguracaoService.definir_valor(db, "agente_objetivo_padrao", objetivo)
    ConfiguracaoService.definir_valor(db, "agente_politicas_padrao", politicas)
    ConfiguracaoService.definir_valor(db, "agente_tarefa_padrao", tarefa)
    ConfiguracaoService.definir_valor(db, "agente_objetivo_explicito_padrao", objetivo_explicito)
    ConfiguracaoService.definir_valor(db, "agente_publico_padrao", publico)
    ConfiguracaoService.definir_valor(db, "agente_restricoes_padrao", restricoes)
    return RedirectResponse(url="/configuracoes", status_code=303)


@router.post("/salvar-geral")
def salvar_geral(
    diretorio_uploads: str = Form(...),
    max_tamanho_imagem_mb: int = Form(...),
    qualidade_jpeg: int = Form(...),
    db: Session = Depends(get_db)
):
    """Salva configurações gerais."""
    ConfiguracaoService.definir_valor(db, "sistema_diretorio_uploads", diretorio_uploads)
    ConfiguracaoService.definir_valor(db, "sistema_max_tamanho_imagem_mb", str(max_tamanho_imagem_mb))
    ConfiguracaoService.definir_valor(db, "sistema_qualidade_jpeg", str(qualidade_jpeg))
    return RedirectResponse(url="/configuracoes", status_code=303)


@router.post("/salvar-provedores-llm")
def salvar_provedores_llm(
    provedor_padrao: str = Form(...),
    provedor_local_id: Optional[str] = Form(None),
    fallback_openrouter: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Salva configurações de provedores LLM."""
    ConfiguracaoService.definir_valor(db, "llm_provedor_padrao", provedor_padrao)
    ConfiguracaoService.definir_valor(db, "llm_fallback_openrouter", str(fallback_openrouter).lower())
    
    # Salvar ID do provedor local se selecionado
    if provedor_padrao == "local" and provedor_local_id:
        ConfiguracaoService.definir_valor(db, "llm_provedor_local_id", provedor_local_id)
    elif provedor_padrao != "local":
        # Limpar ID do provedor local se não for modo local
        ConfiguracaoService.definir_valor(db, "llm_provedor_local_id", "")
    
    return RedirectResponse(url="/configuracoes", status_code=303)


@router.post("/salvar-sessao")
def salvar_sessao(
    sessao_diretorio: str = Form(...),
    history_sync_delay: int = Form(...),
    db: Session = Depends(get_db)
):
    """Salva configurações de sessão WhatsApp."""
    ConfiguracaoService.definir_valor(db, "sessao_diretorio", sessao_diretorio)
    ConfiguracaoService.definir_valor(db, "sessao_history_sync_delay", str(history_sync_delay))
    return RedirectResponse(url="/configuracoes", status_code=303)


@router.post("/salvar-agente-avancado")
def salvar_agente_avancado(
    max_ferramentas: int = Form(...),
    max_iteracoes: int = Form(...),
    historico_mensagens: int = Form(...),
    rag_resultados: int = Form(...),
    db: Session = Depends(get_db)
):
    """Salva configurações avançadas do agente."""
    ConfiguracaoService.definir_valor(db, "agente_max_ferramentas", str(max_ferramentas))
    ConfiguracaoService.definir_valor(db, "agente_max_iteracoes_loop", str(max_iteracoes))
    ConfiguracaoService.definir_valor(db, "agente_historico_mensagens", str(historico_mensagens))
    ConfiguracaoService.definir_valor(db, "agente_rag_resultados_padrao", str(rag_resultados))
    return RedirectResponse(url="/configuracoes", status_code=303)


@router.post("/salvar-ferramenta")
def salvar_ferramenta(
    timeout_http: int = Form(...),
    timeout_download: int = Form(...),
    timeout_teste: int = Form(...),
    db: Session = Depends(get_db)
):
    """Salva configurações de ferramentas."""
    ConfiguracaoService.definir_valor(db, "ferramenta_timeout_http", str(timeout_http))
    ConfiguracaoService.definir_valor(db, "ferramenta_timeout_download", str(timeout_download))
    ConfiguracaoService.definir_valor(db, "ferramenta_timeout_teste", str(timeout_teste))
    return RedirectResponse(url="/configuracoes", status_code=303)


@router.post("/salvar-mcp")
def salvar_mcp(
    max_clients: int = Form(...),
    timeout_execucao: int = Form(...),
    db: Session = Depends(get_db)
):
    """Salva configurações de MCP."""
    ConfiguracaoService.definir_valor(db, "mcp_max_clients_por_agente", str(max_clients))
    ConfiguracaoService.definir_valor(db, "mcp_timeout_execucao", str(timeout_execucao))
    return RedirectResponse(url="/configuracoes", status_code=303)


@router.post("/salvar-audio")
def salvar_audio(
    transcricao_habilitado: str = Form("false"),
    provedor: str = Form(...),
    modelo: str = Form(...),
    idioma: str = Form(...),
    temperatura: float = Form(...),
    prompt: str = Form(""),
    timeout: int = Form(...),
    responder_habilitado: str = Form("false"),
    groq_api_key: str = Form(""),
    openai_api_key: str = Form(""),
    db: Session = Depends(get_db)
):
    """Salva configurações de áudio/transcrição."""
    ConfiguracaoService.definir_valor(db, "audio_transcricao_habilitado", transcricao_habilitado)
    ConfiguracaoService.definir_valor(db, "audio_transcricao_provedor", provedor)
    ConfiguracaoService.definir_valor(db, "audio_transcricao_modelo", modelo)
    ConfiguracaoService.definir_valor(db, "audio_transcricao_idioma", idioma)
    ConfiguracaoService.definir_valor(db, "audio_transcricao_temperatura", str(temperatura))
    ConfiguracaoService.definir_valor(db, "audio_transcricao_prompt", prompt)
    ConfiguracaoService.definir_valor(db, "audio_transcricao_timeout", str(timeout))
    ConfiguracaoService.definir_valor(db, "audio_responder_habilitado", responder_habilitado)
    if groq_api_key:
        ConfiguracaoService.definir_valor(db, "groq_api_key", groq_api_key)
    if openai_api_key:
        ConfiguracaoService.definir_valor(db, "openai_api_key", openai_api_key)
    return RedirectResponse(url="/configuracoes", status_code=303)
