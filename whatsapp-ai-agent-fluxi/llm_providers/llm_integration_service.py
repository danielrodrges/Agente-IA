"""
Serviço de integração LLM que gerencia a escolha do provedor correto.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import httpx
import json
import time
from config.config_service import ConfiguracaoService
from llm_providers.llm_providers_service import ProvedorLLMService
from llm_providers.llm_providers_schema import RequisicaoLLM, ConfiguracaoProvedor

# Tentar importar Anthropic SDK
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class LLMIntegrationService:
    """Serviço para integrar diferentes provedores LLM de forma transparente."""

    @staticmethod
    async def processar_mensagem_com_llm(
        db: Session,
        messages: List[Dict[str, Any]],
        modelo: str,
        agente_id: Optional[int] = None,
        temperatura: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Processa mensagem usando o provedor LLM apropriado.
        
        Args:
            db: Sessão do banco
            messages: Lista de mensagens no formato OpenAI
            modelo: Nome do modelo a usar
            agente_id: ID do agente (para configurações específicas)
            temperatura: Temperatura para geração
            max_tokens: Máximo de tokens
            top_p: Top P para amostragem
            frequency_penalty: Penalidade de frequência (-2.0 a 2.0)
            presence_penalty: Penalidade de presença (-2.0 a 2.0)
            tools: Lista de ferramentas disponíveis
            stream: Se deve usar streaming
            
        Returns:
            Dict com resposta do LLM
        """
        inicio = time.time()
        
        # 1. Determinar qual provedor usar
        provedor_info = await LLMIntegrationService._determinar_provedor(
            db, modelo, agente_id
        )
        
        # 2. Fazer a requisição usando o provedor apropriado
        try:
            if provedor_info["tipo"] == "local":
                # Usar provedor local via llm_providers
                resultado = await LLMIntegrationService._usar_provedor_local(
                    db, provedor_info, messages, modelo, temperatura, 
                    max_tokens, top_p, frequency_penalty, presence_penalty, tools, stream
                )
            elif provedor_info["tipo"] == "openrouter":
                # Usar OpenRouter diretamente
                resultado = await LLMIntegrationService._usar_openrouter(
                    db, messages, modelo, temperatura, max_tokens, top_p, 
                    frequency_penalty, presence_penalty, tools, stream
                )
            elif provedor_info["tipo"] == "anthropic":
                # Usar Anthropic (Claude) diretamente
                resultado = await LLMIntegrationService._usar_anthropic(
                    db, messages, modelo, temperatura, max_tokens, top_p, tools
                )
            else:
                raise ValueError(f"Tipo de provedor não suportado: {provedor_info['tipo']}")
            
            # 3. Adicionar metadados
            resultado["provedor_usado"] = provedor_info["tipo"]
            resultado["provedor_id"] = provedor_info.get("id")
            resultado["tempo_total_ms"] = (time.time() - inicio) * 1000
            
            return resultado
            
        except Exception as e:
            # 4. Fallback para OpenRouter se configurado E disponível
            fallback_habilitado = ConfiguracaoService.obter_valor(
                db, "llm_fallback_openrouter", True
            )
            openrouter_disponivel = LLMIntegrationService._openrouter_disponivel(db)
            
            if (provedor_info["tipo"] != "openrouter" and 
                fallback_habilitado and 
                openrouter_disponivel):
                print(f"⚠️ Erro com provedor {provedor_info['tipo']}, tentando OpenRouter: {e}")
                try:
                    resultado = await LLMIntegrationService._usar_openrouter(
                        db, messages, modelo, temperatura, max_tokens, top_p,
                        frequency_penalty, presence_penalty, tools, stream
                    )
                    resultado["provedor_usado"] = "openrouter_fallback"
                    resultado["erro_original"] = str(e)
                    resultado["tempo_total_ms"] = (time.time() - inicio) * 1000
                    return resultado
                except Exception as fallback_error:
                    raise Exception(f"Erro no provedor principal e no fallback: {e} | {fallback_error}")
            else:
                raise e

    @staticmethod
    async def _determinar_provedor(
        db: Session, 
        modelo: str, 
        agente_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Determina qual provedor usar baseado no modelo e configurações."""
        
        # 1. Verificar configuração global primeiro
        provedor_padrao = ConfiguracaoService.obter_valor(db, "llm_provedor_padrao", "auto")
        
        # 2. Se configurado para local, tentar usar provedor local específico
        if provedor_padrao == "local":
            provedor_local_id = ConfiguracaoService.obter_valor(db, "llm_provedor_local_id")
            if provedor_local_id:
                provedor = ProvedorLLMService.obter_por_id(db, int(provedor_local_id))
                if provedor and provedor.ativo:
                    return {
                        "tipo": "local",
                        "id": provedor.id,
                        "provedor": provedor,
                        "motivo": "configuracao_local"
                    }
        
        # 3. Se configurado para OpenRouter E tem chave, usar
        if provedor_padrao == "openrouter" and LLMIntegrationService._openrouter_disponivel(db):
            return {"tipo": "openrouter", "motivo": "configuracao_openrouter"}
        
        # 4. Tentar encontrar qualquer provedor disponível (modo auto ou fallback)
        # 4.1 Primeiro verificar provedores locais ativos
        provedores_ativos = ProvedorLLMService.listar_ativos(db)
        if provedores_ativos:
            provedor = provedores_ativos[0]  # Usar primeiro provedor ativo
            print(f"🔄 Usando provedor local: {provedor.nome} ({provedor.base_url})")
            return {
                "tipo": "local",
                "id": provedor.id,
                "provedor": provedor,
                "motivo": "auto_local"
            }
        
        # 4.2 Verificar se é modelo Anthropic direto (Claude)
        modelos_anthropic = ["claude-opus", "claude-sonnet", "claude-haiku", "claude-4", "claude-3"]
        if any(modelo.startswith(prefix) or modelo.startswith(f"anthropic/{prefix}") for prefix in modelos_anthropic):
            if LLMIntegrationService._anthropic_disponivel(db):
                return {"tipo": "anthropic", "motivo": "modelo_anthropic_direto"}

        # 4.3 Verificar se modelo é específico do OpenRouter (Gemini, etc.)
        modelos_openrouter = [
            "google/gemini", "openai/gpt", 
            "mistralai/mistral", "cohere/command"
        ]
        
        if any(modelo.startswith(prefix) for prefix in modelos_openrouter):
            if LLMIntegrationService._openrouter_disponivel(db):
                return {"tipo": "openrouter", "motivo": "modelo_especifico_openrouter"}
            else:
                raise ValueError(
                    f"Modelo '{modelo}' requer OpenRouter, mas a API Key não está configurada. "
                    "Configure a chave em Configurações ou use um modelo local."
                )
        
        # 4.3 Fallback para OpenRouter se disponível
        if LLMIntegrationService._openrouter_disponivel(db):
            return {"tipo": "openrouter", "motivo": "fallback_padrao"}
        
        # 4.5 Fallback para Anthropic se disponível
        if LLMIntegrationService._anthropic_disponivel(db):
            return {"tipo": "anthropic", "motivo": "fallback_anthropic"}

        # 5. Nenhum provedor disponível
        raise ValueError(
            "Nenhum provedor LLM disponível. "
            "Configure um provedor local em 'Provedores LLM', adicione sua chave Anthropic, "
            "ou adicione sua chave de API do OpenRouter em 'Configurações'."  
        )

    @staticmethod
    def _openrouter_disponivel(db: Session) -> bool:
        """Verifica se o OpenRouter está disponível (tem chave configurada)."""
        api_key = ConfiguracaoService.obter_valor(db, "openrouter_api_key")
        return api_key is not None and api_key.strip() != ""
    
    @staticmethod
    async def _usar_provedor_local(
        db: Session,
        provedor_info: Dict[str, Any],
        messages: List[Dict[str, Any]],
        modelo: str,
        temperatura: float,
        max_tokens: int,
        top_p: float,
        frequency_penalty: float,
        presence_penalty: float,
        tools: Optional[List[Dict]],
        stream: bool
    ) -> Dict[str, Any]:
        """Usa um provedor local via llm_providers."""
        
        # Log de debug para tools
        if tools:
            print(f"🔧 [LLM_LOCAL] Passando {len(tools)} tools para o provedor local")
        
        # Preparar requisição
        requisicao = RequisicaoLLM(
            mensagens=messages,
            modelo=modelo,
            configuracao=ConfiguracaoProvedor(
                temperatura=temperatura,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty
            ),
            tools=tools,  # Passar tools para o provedor local
            stream=stream
        )
        
        # Enviar requisição
        resposta = await ProvedorLLMService.enviar_requisicao(
            db, provedor_info["id"], requisicao
        )
        
        # Log de debug
        if resposta.tool_calls:
            print(f"🔧 [LLM_LOCAL] Resposta contém {len(resposta.tool_calls)} tool_calls")
        
        # Converter para formato padrão
        return {
            "conteudo": resposta.conteudo,
            "modelo": resposta.modelo,
            "tokens_input": None,  # Provedores locais podem não retornar
            "tokens_output": resposta.tokens_usados,
            "tempo_geracao_ms": resposta.tempo_geracao_ms,
            "tool_calls": resposta.tool_calls,
            "finish_reason": resposta.finish_reason,
            "finalizado": resposta.finalizado
        }

    @staticmethod
    async def _usar_openrouter(
        db: Session,
        messages: List[Dict[str, Any]],
        modelo: str,
        temperatura: float,
        max_tokens: int,
        top_p: float,
        frequency_penalty: float,
        presence_penalty: float,
        tools: Optional[List[Dict]],
        stream: bool
    ) -> Dict[str, Any]:
        """Usa OpenRouter diretamente."""
        
        api_key = ConfiguracaoService.obter_valor(db, "openrouter_api_key")
        if not api_key:
            raise ValueError("Chave API OpenRouter não configurada")

        # Preparar payload
        payload = {
            "model": modelo,
            "messages": messages,
            "temperature": temperatura,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stream": stream
        }
        
        if tools:
            payload["tools"] = tools
            print(f"🔧 [OPENROUTER] Enviando {len(tools)} tools para API")
        
        # Fazer requisição
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise ValueError(f"Erro na API OpenRouter: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Extrair resposta
            choice = data.get("choices", [{}])[0]
            message_response = choice.get("message", {})
            
            # Extrair uso de tokens
            usage = data.get("usage", {})
            
            return {
                "conteudo": message_response.get("content", ""),
                "modelo": modelo,
                "tokens_input": usage.get("prompt_tokens", 0),
                "tokens_output": usage.get("completion_tokens", 0),
                "tool_calls": message_response.get("tool_calls"),
                "finish_reason": choice.get("finish_reason"),
                "finalizado": True
            }

    @staticmethod
    def _anthropic_disponivel(db: Session) -> bool:
        """Verifica se o Anthropic está disponível."""
        if not ANTHROPIC_AVAILABLE:
            return False
        api_key = ConfiguracaoService.obter_valor(db, "anthropic_api_key")
        return api_key is not None and api_key.strip() != ""

    @staticmethod
    async def _usar_anthropic(
        db: Session,
        messages: List[Dict[str, Any]],
        modelo: str,
        temperatura: float,
        max_tokens: int,
        top_p: float,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Usa Anthropic (Claude) diretamente.
        Converte formato OpenAI -> Anthropic e vice-versa.
        """
        if not ANTHROPIC_AVAILABLE:
            raise ValueError("SDK Anthropic não instalado. Execute: pip install anthropic")

        api_key = ConfiguracaoService.obter_valor(db, "anthropic_api_key")
        if not api_key:
            raise ValueError("Chave API Anthropic não configurada")

        # Modelo padrão
        if not modelo or modelo.startswith("anthropic/"):
            modelo = modelo.replace("anthropic/", "") if modelo else ""
        if not modelo:
            modelo = ConfiguracaoService.obter_valor(
                db, "anthropic_modelo_padrao", "claude-opus-4-20250514"
            )

        # Separar system message das demais
        system_content = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg.get("role") == "system":
                system_content = msg.get("content", "")
            elif msg.get("role") == "tool":
                # Converter tool result para formato Anthropic
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": msg.get("content", ""),
                    }],
                })
            elif msg.get("role") == "assistant":
                content = msg.get("content", "")
                tool_calls = msg.get("tool_calls")
                
                if tool_calls:
                    # Mensagem do assistente com tool_use
                    blocks = []
                    if content:
                        blocks.append({"type": "text", "text": content})
                    for tc in tool_calls:
                        blocks.append({
                            "type": "tool_use",
                            "id": tc.get("id", ""),
                            "name": tc.get("function", {}).get("name", ""),
                            "input": json.loads(tc.get("function", {}).get("arguments", "{}")),
                        })
                    anthropic_messages.append({"role": "assistant", "content": blocks})
                else:
                    anthropic_messages.append({"role": "assistant", "content": content or ""})
            else:
                # user message
                content = msg.get("content", "")
                if isinstance(content, list):
                    # Multi-modal (text + image)
                    anthropic_content = []
                    for part in content:
                        if part.get("type") == "text":
                            anthropic_content.append({"type": "text", "text": part["text"]})
                        elif part.get("type") == "image_url":
                            url = part.get("image_url", {}).get("url", "")
                            if url.startswith("data:"):
                                # base64 data URI
                                media_type = url.split(";")[0].split(":")[1]
                                data = url.split(",")[1]
                                anthropic_content.append({
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": data,
                                    },
                                })
                    anthropic_messages.append({"role": "user", "content": anthropic_content})
                else:
                    anthropic_messages.append({"role": "user", "content": content})

        # Converter tools do formato OpenAI para Anthropic
        anthropic_tools = None
        if tools:
            anthropic_tools = []
            for tool in tools:
                func = tool.get("function", {})
                anthropic_tools.append({
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })
            print(f"🔧 [ANTHROPIC] Enviando {len(anthropic_tools)} tools para Claude")

        # Fazer requisição
        client = anthropic.Anthropic(api_key=api_key)

        kwargs = {
            "model": modelo,
            "max_tokens": max_tokens or 4096,
            "messages": anthropic_messages,
            "temperature": temperatura,
            "top_p": top_p,
        }
        if system_content:
            kwargs["system"] = system_content
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        try:
            response = client.messages.create(**kwargs)
        except Exception as e:
            raise ValueError(f"Erro na API Anthropic: {e}")

        # Converter resposta para formato padrão (OpenAI-like)
        text_content = ""
        tool_calls = None
        finish_reason = response.stop_reason  # end_turn, tool_use, max_tokens

        for block in response.content:
            if block.type == "text":
                text_content += block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input),
                    },
                })

        # Mapear finish_reason para formato OpenAI
        if finish_reason == "tool_use":
            finish_reason = "tool_calls"
        elif finish_reason == "end_turn":
            finish_reason = "stop"

        return {
            "conteudo": text_content,
            "modelo": modelo,
            "tokens_input": response.usage.input_tokens,
            "tokens_output": response.usage.output_tokens,
            "tool_calls": tool_calls,
            "finish_reason": finish_reason,
            "finalizado": True,
        }

    @staticmethod
    def obter_modelos_disponiveis(db: Session) -> Dict[str, List[str]]:
        """Obtém lista de modelos disponíveis por provedor."""
        modelos = {
            "anthropic": [],
            "openrouter": [],
            "local": []
        }
        
        # Modelos Anthropic (direto)
        modelos["anthropic"] = [
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
            "claude-3-7-sonnet-20250219",
            "claude-3-5-haiku-20241022",
        ]

        # Modelos OpenRouter (hardcoded para principais)
        modelos["openrouter"] = [
            "google/gemini-2.0-flash-001",
            "google/gemini-1.5-pro",
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "mistralai/mistral-7b-instruct",
            "cohere/command-r-plus"
        ]
        
        # Modelos locais (buscar dos provedores ativos)
        provedores_locais = ProvedorLLMService.listar_ativos(db)
        for provedor in provedores_locais:
            modelos_provedor = ProvedorLLMService.obter_modelos(db, provedor.id)
            for modelo in modelos_provedor:
                modelos["local"].append(f"{provedor.nome}:{modelo.nome}")
        
        return modelos

    @staticmethod
    def configurar_provedor_padrao(db: Session, tipo: str, provedor_id: Optional[int] = None):
        """
        Configura o provedor padrão do sistema.
        
        Args:
            tipo: "auto", "local" ou "openrouter"
            provedor_id: ID do provedor local (obrigatório se tipo == "local")
        """
        if tipo not in ["auto", "local", "openrouter", "anthropic"]:
            raise ValueError(f"Tipo de provedor inválido: {tipo}. Use 'auto', 'local', 'openrouter' ou 'anthropic'.")
        
        ConfiguracaoService.definir_valor(db, "llm_provedor_padrao", tipo)
        
        if tipo == "local" and provedor_id:
            ConfiguracaoService.definir_valor(db, "llm_provedor_local_id", str(provedor_id))
        elif tipo in ["openrouter", "auto", "anthropic"]:
            ConfiguracaoService.definir_valor(db, "llm_provedor_local_id", None)
