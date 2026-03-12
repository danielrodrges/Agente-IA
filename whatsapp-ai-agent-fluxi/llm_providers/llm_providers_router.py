"""
Rotas da API para provedores LLM.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from llm_providers.llm_providers_schema import (
    ProvedorLLMResposta,
    ProvedorLLMCriar,
    ProvedorLLMAtualizar,
    TesteConexaoResposta,
    ModeloLLM,
    RequisicaoLLM,
    RespostaLLM,
    EstatisticasProvedor as EstatisticasProvedorSchema
)
from llm_providers.llm_providers_service import ProvedorLLMService

router = APIRouter(prefix="/api/provedores-llm", tags=["Provedores LLM"])


@router.get("/", response_model=List[ProvedorLLMResposta])
def listar_provedores(db: Session = Depends(get_db)):
    """Lista todos os provedores LLM."""
    return ProvedorLLMService.listar_todos(db)


@router.get("/ativos", response_model=List[ProvedorLLMResposta])
def listar_provedores_ativos(db: Session = Depends(get_db)):
    """Lista apenas provedores ativos."""
    return ProvedorLLMService.listar_ativos(db)


@router.get("/tipo/{tipo}", response_model=List[ProvedorLLMResposta])
def listar_por_tipo(tipo: str, db: Session = Depends(get_db)):
    """Lista provedores por tipo."""
    return ProvedorLLMService.obter_por_tipo(db, tipo)


@router.get("/{provedor_id}", response_model=ProvedorLLMResposta)
def obter_provedor(provedor_id: int, db: Session = Depends(get_db)):
    """Obtém um provedor específico."""
    provedor = ProvedorLLMService.obter_por_id(db, provedor_id)
    if not provedor:
        raise HTTPException(status_code=404, detail="Provedor não encontrado")
    return provedor


@router.post("/", response_model=ProvedorLLMResposta)
def criar_provedor(provedor: ProvedorLLMCriar, db: Session = Depends(get_db)):
    """Cria um novo provedor LLM."""
    return ProvedorLLMService.criar(db, provedor)


@router.put("/{provedor_id}", response_model=ProvedorLLMResposta)
def atualizar_provedor(
    provedor_id: int,
    provedor: ProvedorLLMAtualizar,
    db: Session = Depends(get_db)
):
    """Atualiza um provedor existente."""
    provedor_atualizado = ProvedorLLMService.atualizar(db, provedor_id, provedor)
    if not provedor_atualizado:
        raise HTTPException(status_code=404, detail="Provedor não encontrado")
    return provedor_atualizado


@router.delete("/{provedor_id}")
def deletar_provedor(provedor_id: int, db: Session = Depends(get_db)):
    """Deleta um provedor."""
    sucesso = ProvedorLLMService.deletar(db, provedor_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Provedor não encontrado")
    return {"mensagem": "Provedor deletado com sucesso"}


@router.post("/{provedor_id}/testar", response_model=TesteConexaoResposta)
async def testar_conexao(provedor_id: int, db: Session = Depends(get_db)):
    """Testa a conexão com um provedor e busca modelos disponíveis."""
    return await ProvedorLLMService.testar_conexao(db, provedor_id)


@router.get("/{provedor_id}/modelos", response_model=List[ModeloLLM])
def obter_modelos(provedor_id: int, db: Session = Depends(get_db)):
    """Obtém modelos disponíveis para um provedor."""
    # Verificar se o provedor existe
    provedor = ProvedorLLMService.obter_por_id(db, provedor_id)
    if not provedor:
        raise HTTPException(status_code=404, detail="Provedor não encontrado")
    
    modelos_db = ProvedorLLMService.obter_modelos(db, provedor_id)
    modelos = []
    
    for modelo_db in modelos_db:
        modelo = ModeloLLM(
            id=modelo_db.modelo_id,
            nome=modelo_db.nome,
            contexto=modelo_db.contexto,
            suporta_imagens=modelo_db.suporta_imagens,
            suporta_ferramentas=modelo_db.suporta_ferramentas,
            tamanho=modelo_db.tamanho,
            quantizacao=modelo_db.quantizacao
        )
        modelos.append(modelo)
    
    return modelos


@router.post("/{provedor_id}/requisicao", response_model=RespostaLLM)
async def enviar_requisicao(
    provedor_id: int,
    requisicao: RequisicaoLLM,
    db: Session = Depends(get_db)
):
    """Envia uma requisição para um provedor LLM."""
    try:
        return await ProvedorLLMService.enviar_requisicao(db, provedor_id, requisicao)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/{provedor_id}/estatisticas", response_model=EstatisticasProvedorSchema)
def obter_estatisticas(provedor_id: int, db: Session = Depends(get_db)):
    """Obtém estatísticas de um provedor."""
    # Verificar se o provedor existe
    provedor = ProvedorLLMService.obter_por_id(db, provedor_id)
    if not provedor:
        raise HTTPException(status_code=404, detail="Provedor não encontrado")
    
    estatisticas = ProvedorLLMService.obter_estatisticas(db, provedor_id)
    if not estatisticas:
        raise HTTPException(status_code=404, detail="Estatísticas não encontradas")
    
    return estatisticas
