# Módulo Agente 🤖

## 📖 Visão Geral

O módulo `agente` é responsável por gerenciar os agentes inteligentes do Fluxi. Cada agente é uma "personalidade" única com seu próprio system prompt, ferramentas e base de conhecimento (RAG). Os agentes processam mensagens recebidas via WhatsApp e geram respostas contextualizadas usando modelos LLM.

## 🎯 Objetivo

Permitir a criação e gerenciamento de múltiplos agentes especializados dentro de uma mesma sessão WhatsApp, cada um com:
- **System Prompt personalizado** (papel, objetivo, políticas, restrições)
- **Até 20 ferramentas ativas** (funções que o agente pode executar)
- **Base de conhecimento RAG** (opcional)
- **Configurações LLM específicas** (modelo, temperatura, max_tokens, top_p)
- **Integração com clientes MCP** (Model Context Protocol)

## 📂 Estrutura de Arquivos

```
agente/
├── __init__.py                    # Inicialização do módulo
├── agente_model.py                # Modelo SQLAlchemy (entidade Agente)
├── agente_schema.py               # Schemas Pydantic (validação de dados)
├── agente_service.py              # Lógica de negócio e processamento LLM
├── agente_router.py               # Endpoints REST API
├── agente_frontend_router.py      # Rotas de interface web
└── README.md                      # Esta documentação
```

## 🔧 Componentes Principais

### 1. Models (agente_model.py)

Define a estrutura de dados dos agentes no banco de dados:

#### **Tabela: `agentes`**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único do agente |
| `sessao_id` | Integer | FK para sessão WhatsApp |
| `codigo` | String(10) | Código único do agente na sessão (ex: "01", "02") |
| `nome` | String(100) | Nome do agente |
| `descricao` | Text | Descrição opcional |
| `agente_papel` | Text | **System Prompt**: Papel do agente |
| `agente_objetivo` | Text | **System Prompt**: Objetivo do agente |
| `agente_politicas` | Text | **System Prompt**: Políticas do agente |
| `agente_tarefa` | Text | **System Prompt**: Tarefa do agente |
| `agente_objetivo_explicito` | Text | **System Prompt**: Objetivo explícito |
| `agente_publico` | Text | **System Prompt**: Público-alvo |
| `agente_restricoes` | Text | **System Prompt**: Restrições e políticas |
| `modelo_llm` | String(100) | Modelo LLM específico (opcional) |
| `temperatura` | String(10) | Temperatura do modelo (opcional) |
| `max_tokens` | String(10) | Máximo de tokens (opcional) |
| `top_p` | String(10) | Top P (opcional) |
| `rag_id` | Integer | FK para base de conhecimento RAG (opcional) |
| `ativo` | Boolean | Se o agente está ativo |
| `criado_em` | DateTime | Data de criação |
| `atualizado_em` | DateTime | Data de atualização |

#### **Tabela Associativa: `agente_ferramenta`**
Relacionamento many-to-many entre Agentes e Ferramentas.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `agente_id` | Integer | FK para agente |
| `ferramenta_id` | Integer | FK para ferramenta |
| `ativa` | Boolean | Se a ferramenta está ativa para este agente |
| `criado_em` | DateTime | Data de associação |

#### **Relacionamentos:**
- `sessao` → Pertence a uma Sessão
- `ferramentas` → Muitas ferramentas (máximo 20 ativas)
- `rag` → Uma base de conhecimento RAG (opcional)
- `mcp_clients` → Vários clientes MCP

### 2. Schemas (agente_schema.py)

Validação de dados usando Pydantic:

- **`AgenteBase`**: Schema base com campos comuns
- **`AgenteCriar`**: Para criar novo agente (inclui `sessao_id`)
- **`AgenteAtualizar`**: Para atualizar agente (todos os campos opcionais)
- **`AgenteResposta`**: Resposta da API (inclui IDs e timestamps)
- **`AgenteFerramentasAtualizar`**: Para atualizar lista de ferramentas (máximo 20)

### 3. Service (agente_service.py)

Contém toda a lógica de negócio do módulo. Principais funcionalidades:

#### **Gerenciamento de Agentes:**
- `listar_todos()` - Lista todos os agentes
- `listar_por_sessao()` - Lista agentes de uma sessão
- `listar_por_sessao_ativos()` - Lista agentes ativos de uma sessão
- `obter_por_id()` - Obtém agente por ID
- `obter_por_codigo()` - Obtém agente por código dentro de uma sessão
- `criar()` - Cria novo agente (valida código único)
- `atualizar()` - Atualiza agente existente
- `deletar()` - Remove agente
- `criar_agente_padrao()` - Cria agente padrão para nova sessão

#### **Gerenciamento de Ferramentas:**
- `atualizar_ferramentas()` - Atualiza ferramentas do agente (máx. 20)
- `listar_ferramentas()` - Lista ferramentas ativas do agente

#### **Processamento LLM:**
- `construir_system_prompt()` - Constrói system prompt a partir dos campos do agente
- `construir_historico_mensagens()` - Prepara histórico de mensagens
- **`processar_mensagem()`** - **FUNÇÃO PRINCIPAL**: Processa mensagem com LLM e executa ferramentas

### 4. Router API (agente_router.py)

Endpoints REST para gerenciamento de agentes:

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/agentes/` | Lista agentes (filtros: sessao_id, apenas_ativos) |
| GET | `/api/agentes/{id}` | Obtém agente específico |
| POST | `/api/agentes/` | Cria novo agente |
| PUT | `/api/agentes/{id}` | Atualiza agente |
| DELETE | `/api/agentes/{id}` | Deleta agente |
| GET | `/api/agentes/{id}/ferramentas` | Lista ferramentas do agente |
| POST | `/api/agentes/{id}/ferramentas` | Atualiza ferramentas do agente |
| POST | `/api/agentes/{id}/vincular-treinamento` | Vincula/desvincula RAG |

### 5. Frontend Router (agente_frontend_router.py)

Rotas de interface web com templates Jinja2:

| Rota | Descrição | Template |
|------|-----------|----------|
| GET `/agentes/sessao/{sessao_id}` | Lista agentes da sessão | `agente/lista.html` |
| GET `/agentes/sessao/{sessao_id}/novo` | Formulário de novo agente | `agente/form.html` |
| GET `/agentes/{id}/editar` | Formulário de edição | `agente/form.html` |
| POST `/agentes/sessao/{id}/criar` | Cria agente | Redirect |
| POST `/agentes/{id}/atualizar` | Atualiza agente | Redirect |
| GET `/agentes/{id}/ferramentas` | Gerenciar ferramentas | `agente/ferramentas.html` |
| POST `/agentes/{id}/ferramentas/atualizar` | Atualiza ferramentas | Redirect |
| POST `/agentes/{id}/deletar` | Deleta agente | Redirect |
| POST `/agentes/{id}/ativar` | Define agente como ativo na sessão | Redirect |

## 🔄 Fluxo de Funcionamento

### 1️⃣ **Criação de Agente**
```
Usuario → Formulário Web → agente_frontend_router.criar_agente()
    → AgenteService.criar()
    → Valida código único na sessão
    → Salva no banco de dados
    → Redirect para lista de agentes
```

### 2️⃣ **Processamento de Mensagem com LLM** (Loop Agentic)

```python
# Fluxo principal em AgenteService.processar_mensagem()

1. Obter agente ativo da sessão
2. Construir system prompt (papel, objetivo, políticas, etc.)
3. Construir histórico de mensagens (últimas 10)
4. Buscar ferramentas ativas do agente (máx. 20)
5. Buscar clientes MCP ativos
6. Se agente tem RAG, adicionar ferramenta de busca

LOOP (máximo 10 iterações):
    7. Chamar LLM via LLMIntegrationService
    8. Receber resposta do LLM
    9. Verificar finish_reason:
    
    SE finish_reason == "tool_calls":
        Para cada tool_call:
            - Se é ferramenta MCP → MCPService.executar_tool_mcp()
            - Se é busca RAG → RAGService.buscar()
            - Senão → FerramentaService.executar_ferramenta()
            
            Adicionar resultado ao histórico
        
        Voltar ao passo 7 (próxima iteração)
    
    SE finish_reason == "stop":
        Resposta final recebida → SAIR DO LOOP

10. Retornar resposta + tokens + tempo + ferramentas usadas
```

### 3️⃣ **Vinculação de Ferramentas**

```
Usuario → Página de ferramentas → Seleciona até 20 ferramentas
    → agente_frontend_router.atualizar_ferramentas_agente()
    → AgenteService.atualizar_ferramentas()
    → Remove associações antigas
    → Cria novas associações na tabela agente_ferramenta
    → Commit no banco
```

## 🔗 Dependências

### Módulos Internos:
- **`database`** - Conexão e modelos SQLAlchemy
- **`config`** - Configurações padrão (system prompt, LLM)
- **`sessao`** - Sessões WhatsApp
- **`ferramenta`** - Ferramentas executáveis pelo agente
- **`llm_providers`** - Integração com provedores LLM (OpenRouter, OpenAI, etc.)
- **`rag`** - Sistema RAG (Retrieval-Augmented Generation)
- **`mcp_client`** - Clientes MCP (Model Context Protocol)
- **`mensagem`** - Mensagens WhatsApp

### Bibliotecas Externas:
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **Pydantic** - Validação de dados
- **httpx** - Cliente HTTP async
- **Jinja2** - Templates

## 💡 Exemplos de Uso

### Criar Agente via API

```python
POST /api/agentes/
{
    "sessao_id": 1,
    "codigo": "01",
    "nome": "Assistente de Vendas",
    "descricao": "Agente especializado em vendas",
    "agente_papel": "vendedor especializado em produtos tecnológicos",
    "agente_objetivo": "auxiliar clientes na compra de produtos",
    "agente_politicas": "ser sempre educado e consultivo",
    "agente_tarefa": "recomendar produtos adequados ao perfil do cliente",
    "agente_objetivo_explicito": "aumentar conversão de vendas",
    "agente_publico": "clientes interessados em tecnologia",
    "agente_restricoes": "não oferecer descontos sem autorização",
    "modelo_llm": "google/gemini-2.0-flash-001",
    "temperatura": "0.7",
    "max_tokens": "2000",
    "ativo": true
}
```

### Vincular Ferramentas

```python
POST /api/agentes/1/ferramentas
{
    "ferramentas": [1, 2, 5, 7]  # IDs das ferramentas (máx. 20)
}
```

### Vincular Base de Conhecimento RAG

```python
POST /api/agentes/1/vincular-treinamento
{
    "rag_id": 3
}
```

### System Prompt Gerado

O agente constrói automaticamente um system prompt formatado:

```
Você é: vendedor especializado em produtos tecnológicos.
Objetivo: auxiliar clientes na compra de produtos.
Políticas: ser sempre educado e consultivo.
Tarefa: recomendar produtos adequados ao perfil do cliente.
Objetivo explícito: aumentar conversão de vendas.
Público/usuário-alvo: clientes interessados em tecnologia.
Restrições e políticas: não oferecer descontos sem autorização.
```

## 🔌 Integrações

### 1. **LLM Providers** (`llm_providers`)
O agente usa `LLMIntegrationService.processar_mensagem_com_llm()` para enviar mensagens ao LLM escolhido (OpenRouter, OpenAI, Anthropic, etc.). Suporta:
- Múltiplos provedores
- Fallback automático
- Streaming (opcional)
- Contagem de tokens
- Tool calling (function calling)

### 2. **Ferramentas** (`ferramenta`)
Cada agente pode ter até 20 ferramentas ativas. As ferramentas são convertidas para o formato OpenAI Function Calling e enviadas ao LLM. Tipos de ferramentas:
- **PRINCIPAL** - Ferramentas completas com execução
- **SECUNDÁRIA** - Ferramentas auxiliares (não enviadas ao LLM)

### 3. **RAG** (`rag`)
Agentes podem ter uma base de conhecimento RAG vinculada. Quando vinculado, uma ferramenta especial `buscar_base_conhecimento` é adicionada automaticamente ao agente, permitindo que ele busque informações nos documentos treinados.

### 4. **MCP Clients** (`mcp_client`)
Model Context Protocol permite conectar ferramentas externas (GitHub, databases, APIs). As ferramentas MCP são:
- Prefixadas com `mcp_{client_id}_{tool_name}`
- Executadas via `MCPService.executar_tool_mcp()`
- Registradas automaticamente quando o cliente está ativo

### 5. **Sessões** (`sessao`)
Cada agente pertence a uma sessão WhatsApp. A sessão define qual agente está ativo (`agente_ativo_id`). Quando uma mensagem chega:
1. Sistema busca a sessão
2. Identifica o agente ativo
3. Processa a mensagem com esse agente

### 6. **Métricas** (`metrica`)
O módulo registra métricas de uso:
- Tempo de processamento
- Tokens consumidos (input/output)
- Ferramentas executadas
- Modelo LLM utilizado

## 📝 Notas Técnicas

### Limite de Ferramentas
Um agente pode ter **no máximo 20 ferramentas ativas**. Esta limitação existe porque:
1. LLMs têm limite de tokens no prompt
2. Muitas ferramentas confundem o modelo
3. Mantém foco e especialização do agente

### Loop Agentic
O processamento de mensagens usa um **loop agentic** (máximo 10 iterações):
- Permite múltiplas chamadas de ferramentas em sequência
- LLM pode usar resultado de uma ferramenta para decidir chamar outra
- Evita loops infinitos com limite de iterações

### Tool Calling Paralelo
O sistema suporta **tool calling paralelo**:
- LLM pode chamar múltiplas ferramentas de uma vez
- Todas são executadas em paralelo
- Resultados são adicionados ao contexto
- LLM recebe todos os resultados e continua

### Output Types
Ferramentas têm diferentes tipos de output:
- **`llm`** - Resultado enviado apenas ao LLM
- **`user`** - Resultado enviado apenas ao usuário (via WhatsApp)
- **`both`** - Resultado enviado ao LLM E ao usuário

### Histórico de Mensagens
- Sistema mantém **últimas 10 mensagens** no contexto
- Inclui mensagens de texto e imagens (formato multimodal)
- Inclui respostas do assistente (`resposta_texto`)
- Formato: `user` → `assistant` → `user` → `assistant` → ...
- Suporte a conteúdo misto (texto + imagem na mesma mensagem)

### Configurações Padrão
Se o agente não tiver configurações LLM específicas, usa valores padrão do módulo `config`:
- `openrouter_modelo_padrao`
- `openrouter_temperatura`
- `openrouter_max_tokens`
- `openrouter_top_p`

### System Prompt Estruturado
O system prompt é dividido em 7 campos específicos (baseado em boas práticas de prompt engineering):
1. **Papel** - Quem o agente é
2. **Objetivo** - O que o agente deve alcançar
3. **Políticas** - Como o agente deve se comportar
4. **Tarefa** - O que o agente deve fazer
5. **Objetivo explícito** - Meta mensurável
6. **Público** - Quem é o usuário-alvo
7. **Restrições** - O que o agente NÃO deve fazer

Esta estrutura garante prompts consistentes e eficazes.

---

## 🚀 Próximos Passos

Para usar este módulo:
1. Crie uma sessão WhatsApp (`sessao`)
2. Crie um agente para a sessão
3. Configure ferramentas (opcional)
4. Vincule RAG (opcional)
5. Configure clientes MCP (opcional)
6. Defina o agente como ativo na sessão
7. Envie mensagens via WhatsApp!

---

**Módulo criado por:** Fluxi Team  
**Versão:** 1.0.0  
**Última atualização:** 2025

