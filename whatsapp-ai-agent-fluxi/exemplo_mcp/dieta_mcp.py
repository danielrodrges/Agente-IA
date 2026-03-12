"""
MCP Server de Dieta - Exemplo funcional para Fluxi

Este servidor MCP permite registrar refeições, consultar histórico
e calcular totais de calorias consumidas.

Para rodar via SSE (HTTP):
    python dieta_mcp.py
    
Servidor ficará disponível em: http://localhost:8002/sse
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastmcp import FastMCP

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('dieta-mcp')

# Criar servidor MCP
mcp = FastMCP(
    name="Dieta MCP",
    instructions="""
    Servidor MCP para controle de dieta e refeições.
    
    Use as ferramentas disponíveis para:
    - Registrar refeições (café da manhã, almoço, lanche, jantar, etc)
    - Consultar refeições do dia
    - Ver histórico de dias anteriores
    - Calcular total de calorias
    """
)

# Arquivo JSON para persistência
DATA_FILE = os.path.join(os.path.dirname(__file__), "dieta_data.json")


def carregar_dados() -> dict:
    """Carrega dados do arquivo JSON."""
    logger.debug(f"Carregando dados de {DATA_FILE}")
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            logger.debug(f"Dados carregados: {len(dados.get('refeicoes', []))} refeições")
            return dados
    logger.debug("Arquivo não existe, retornando dados vazios")
    return {"refeicoes": [], "meta_diaria": 2000}


def salvar_dados(dados: dict):
    """Salva dados no arquivo JSON."""
    logger.debug(f"Salvando dados em {DATA_FILE}")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    logger.info(f"Dados salvos: {len(dados.get('refeicoes', []))} refeições")


# ============== TOOLS ==============

@mcp.tool
def registrar_refeicao(
    tipo_refeicao: str,
    alimentos: str,
    calorias: int,
    observacoes: Optional[str] = None
) -> str:
    """
    Registra uma refeição no diário alimentar.
    
    Args:
        tipo_refeicao: Tipo da refeição (cafe_da_manha, almoco, lanche, jantar, ceia)
        alimentos: Descrição dos alimentos consumidos
        calorias: Quantidade estimada de calorias
        observacoes: Observações opcionais sobre a refeição
    
    Returns:
        Confirmação do registro
    """
    logger.info(f"[TOOL] registrar_refeicao chamada: {tipo_refeicao}, {alimentos}, {calorias} kcal")
    dados = carregar_dados()
    
    refeicao = {
        "id": len(dados["refeicoes"]) + 1,
        "data": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M"),
        "tipo": tipo_refeicao.lower().replace(" ", "_"),
        "alimentos": alimentos,
        "calorias": calorias,
        "observacoes": observacoes
    }
    
    dados["refeicoes"].append(refeicao)
    salvar_dados(dados)
    
    resultado = f"Refeição registrada! ID: {refeicao['id']} | {tipo_refeicao}: {alimentos} ({calorias} kcal)"
    logger.info(f"[TOOL] registrar_refeicao resultado: {resultado}")
    return resultado


@mcp.tool
def listar_refeicoes_hoje() -> str:
    """
    Lista todas as refeições registradas hoje.
    
    Returns:
        Lista de refeições do dia com total de calorias
    """
    logger.info("[TOOL] listar_refeicoes_hoje chamada")
    dados = carregar_dados()
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    refeicoes_hoje = [r for r in dados["refeicoes"] if r["data"] == hoje]
    
    if not refeicoes_hoje:
        return "Nenhuma refeição registrada hoje."
    
    resultado = ["REFEIÇÕES DE HOJE", "=" * 40]
    total_calorias = 0
    
    for r in refeicoes_hoje:
        resultado.append(f"\n[{r['hora']}] {r['tipo'].upper()} (ID: {r['id']})")
        resultado.append(f"  {r['alimentos']}")
        resultado.append(f"  {r['calorias']} kcal")
        if r.get("observacoes"):
            resultado.append(f"  Obs: {r['observacoes']}")
        total_calorias += r["calorias"]
    
    resultado.append("\n" + "=" * 40)
    resultado.append(f"TOTAL DO DIA: {total_calorias} kcal")
    
    return "\n".join(resultado)


@mcp.tool
def listar_refeicoes_data(data: str) -> str:
    """
    Lista refeições de uma data específica.
    
    Args:
        data: Data no formato YYYY-MM-DD (ex: 2025-11-27)
    
    Returns:
        Lista de refeições da data especificada
    """
    logger.info(f"[TOOL] listar_refeicoes_data chamada: {data}")
    dados = carregar_dados()
    
    refeicoes_data = [r for r in dados["refeicoes"] if r["data"] == data]
    
    if not refeicoes_data:
        return f"Nenhuma refeição registrada em {data}."
    
    resultado = [f"REFEIÇÕES DE {data}", "=" * 40]
    total_calorias = 0
    
    for r in refeicoes_data:
        resultado.append(f"\n[{r['hora']}] {r['tipo'].upper()} (ID: {r['id']})")
        resultado.append(f"  {r['alimentos']}")
        resultado.append(f"  {r['calorias']} kcal")
        if r.get("observacoes"):
            resultado.append(f"  Obs: {r['observacoes']}")
        total_calorias += r["calorias"]
    
    resultado.append("\n" + "=" * 40)
    resultado.append(f"TOTAL: {total_calorias} kcal")
    
    return "\n".join(resultado)


@mcp.tool
def resumo_semanal() -> str:
    """
    Gera um resumo das calorias consumidas nos últimos 7 dias.
    
    Returns:
        Resumo semanal com média diária
    """
    logger.info("[TOOL] resumo_semanal chamada")
    dados = carregar_dados()
    hoje = datetime.now()
    
    resultado = ["RESUMO SEMANAL", "=" * 40]
    total_semana = 0
    dias_com_registro = 0
    
    for i in range(7):
        data = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
        refeicoes_dia = [r for r in dados["refeicoes"] if r["data"] == data]
        calorias_dia = sum(r["calorias"] for r in refeicoes_dia)
        
        if calorias_dia > 0:
            dias_com_registro += 1
            total_semana += calorias_dia
            resultado.append(f"{data}: {calorias_dia} kcal")
        else:
            resultado.append(f"{data}: -- sem registro --")
    
    resultado.append("\n" + "=" * 40)
    resultado.append(f"TOTAL SEMANA: {total_semana} kcal")
    
    if dias_com_registro > 0:
        media = total_semana // dias_com_registro
        resultado.append(f"MÉDIA DIÁRIA: {media} kcal")
    
    return "\n".join(resultado)


@mcp.tool
def deletar_refeicao(refeicao_id: int) -> str:
    """
    Remove uma refeição pelo ID.
    
    Args:
        refeicao_id: ID da refeição a ser removida
    
    Returns:
        Confirmação da remoção
    """
    logger.info(f"[TOOL] deletar_refeicao chamada: ID {refeicao_id}")
    dados = carregar_dados()
    
    refeicao_encontrada = None
    for i, r in enumerate(dados["refeicoes"]):
        if r["id"] == refeicao_id:
            refeicao_encontrada = dados["refeicoes"].pop(i)
            break
    
    if not refeicao_encontrada:
        return f"Refeição com ID {refeicao_id} não encontrada."
    
    salvar_dados(dados)
    
    return f"Refeição removida: {refeicao_encontrada['tipo']} - {refeicao_encontrada['alimentos']}"


@mcp.tool
def definir_meta_calorica(meta: int) -> str:
    """
    Define a meta diária de calorias.
    
    Args:
        meta: Meta de calorias por dia (ex: 2000)
    
    Returns:
        Confirmação da meta definida
    """
    logger.info(f"[TOOL] definir_meta_calorica chamada: {meta} kcal")
    dados = carregar_dados()
    dados["meta_diaria"] = meta
    salvar_dados(dados)
    
    return f"Meta diária definida: {meta} kcal"


@mcp.tool
def verificar_meta_hoje() -> str:
    """
    Verifica o progresso em relação à meta diária.
    
    Returns:
        Status do consumo vs meta
    """
    logger.info("[TOOL] verificar_meta_hoje chamada")
    dados = carregar_dados()
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    meta = dados.get("meta_diaria", 2000)
    refeicoes_hoje = [r for r in dados["refeicoes"] if r["data"] == hoje]
    consumido = sum(r["calorias"] for r in refeicoes_hoje)
    
    restante = meta - consumido
    percentual = (consumido / meta) * 100 if meta > 0 else 0
    
    resultado = [
        "STATUS DO DIA",
        "=" * 40,
        f"Meta: {meta} kcal",
        f"Consumido: {consumido} kcal ({percentual:.1f}%)",
    ]
    
    if restante > 0:
        resultado.append(f"Restante: {restante} kcal")
    else:
        resultado.append(f"Excedido: {abs(restante)} kcal")
    
    resultado.append("=" * 40)
    
    if percentual < 50:
        resultado.append("Ainda tem bastante margem hoje!")
    elif percentual < 80:
        resultado.append("Indo bem, continue assim!")
    elif percentual < 100:
        resultado.append("Quase na meta, atenção nas próximas refeições.")
    else:
        resultado.append("Meta ultrapassada!")
    
    return "\n".join(resultado)


# ============== MAIN ==============

if __name__ == "__main__":
    # Rodar servidor MCP via SSE (HTTP)
    print("="* 50)
    print("  DIETA MCP SERVER")
    print("="* 50)
    print(f"  URL: http://localhost:8002/sse")
    print(f"  Data: {DATA_FILE}")
    print("="* 50)
    print("")
    print("Ferramentas disponíveis:")
    print("  - registrar_refeicao")
    print("  - listar_refeicoes_hoje")
    print("  - listar_refeicoes_data")
    print("  - resumo_semanal")
    print("  - deletar_refeicao")
    print("  - definir_meta_calorica")
    print("  - verificar_meta_hoje")
    print("")
    print("Aguardando conexões...")
    print("-" * 50)
    
    logger.info("Servidor iniciando na porta 8002")
    mcp.run(transport="sse", port=8002)
