# Módulo MCP Client 🔌

## 📖 Visão Geral

O módulo `mcp_client` implementa suporte completo ao **Model Context Protocol (MCP)**, permitindo que agentes conectem-se a servidores MCP externos e utilizem suas ferramentas. MCP é um protocolo padronizado para integrar contexto externo em LLMs, desenvolvido por Anthropic.

Com este módulo, você pode conectar ferramentas de:
- **GitHub** (criar issues, PRs, buscar código)
- **Filesystem** (ler/escrever arquivos locais)
- **Databases** (consultas SQL, PostgreSQL, MySQL)
- **APIs** (clima, notícias, busca web)
- **E muito mais...**

## 🎯 Objetivo

Estender as capacidades dos agentes com ferramentas externas através do protocolo MCP:
- **Presets plug-and-play** para servidores populares (GitHub, Jina AI, Time Server, etc.)
- **Instalação one-click** via JSON
- **Múltiplos transportes** (STDIO, SSE, HTTP)
- **Sincronização automática** de ferramentas do servidor
- **Integração transparente** com agentes (as tools aparecem automaticamente)

## 📂 Estrutura de Arquivos

```
mcp_client/
├── __init__.py                 # Inicialização do módulo
├── mcp_client_model.py         # Modelo SQLAlchemy (MCPClient)
├── mcp_tool_model.py           # Modelo SQLAlchemy (MCPTool)
├── mcp_schema.py               # Schemas Pydantic
├── mcp_service.py              # Lógica de negócio e execução
├── mcp_router.py               # Endpoints REST API
├── mcp_frontend_router.py      # Rotas de interface web
├── mcp_presets.py              # Presets prontos (GitHub, Jina, etc.)
└── README.md                   # Esta documentação
```

## 🔧 Componentes Principais

### 1. Models

#### **Tabela: `mcp_clients`**
Clientes MCP vinculados a agentes.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `agente_id` | Integer | FK para agente |
| `nome` | String(100) | Nome do servidor MCP |
| `descricao` | Text | Descrição |
| `transport_type` | Enum | STDIO, SSE ou STREAMABLE_HTTP |
| `preset_key` | String(100) | Identificador do preset (se aplicado) |
| `preset_inputs` | JSON | Inputs fornecidos pelo usuário |
| `command` | String(500) | Comando (para STDIO) |
| `args` | JSON | Argumentos do comando |
| `env_vars` | JSON | Variáveis de ambiente |
| `url` | String(500) | URL do servidor (para SSE/HTTP) |
| `headers` | JSON | Headers HTTP |
| `ativo` | Boolean | Se está ativo |
| `conectado` | Boolean | Se está conectado |
| `ultimo_erro` | Text | Último erro de conexão |
| `server_name` | String(100) | Nome do servidor MCP |
| `server_version` | String(50) | Versão do servidor |
| `capabilities` | JSON | Capabilities do servidor |
| `criado_em` | DateTime | Data de criação |
| `ultima_conexao` | DateTime | Última conexão bem-sucedida |
| `ultima_sincronizacao` | DateTime | Última sinc. de tools |

#### **Tabela: `mcp_tools`**
Ferramentas expostas pelos servidores MCP (sincronizadas automaticamente).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `mcp_client_id` | Integer | FK para cliente MCP |
| `name` | String(200) | Nome original da tool |
| `display_name` | String(200) | Nome para exibição |
| `description` | Text | Descrição da tool |
| `input_schema` | JSON | JSON Schema de parâmetros |
| `output_schema` | JSON | Schema de resposta (opcional) |
| `ativa` | Boolean | Se está disponível |
| `ultima_sincronizacao` | DateTime | Última atualização |

#### **Enums:**

```python
TransportType:
    STDIO = "stdio"                    # Processo local (npx, uvx, python)
    SSE = "sse"                        # Server-Sent Events
    STREAMABLE_HTTP = "streamable-http"  # HTTP com streaming
```

### 2. Presets (mcp_presets.py)

**Biblioteca de presets prontos** para servidores MCP populares:

#### **Presets Disponíveis:**

| Preset | Transporte | Descrição | Inputs Necessários |
|--------|------------|-----------|-------------------|
| `github-copilot-oauth` | HTTP | GitHub Copilot oficial | - (OAuth automático) |
| `github-copilot-pat` | HTTP | GitHub com token | `github_mcp_pat` |
| `deepwiki-sse` | SSE | Busca em wikis | - |
| `deepwiki-http` | HTTP | Busca em wikis | - |
| `jina-ai-tools` | STDIO | Busca web e leitura | `jina_api_key` |
| `brave-search` | STDIO | Busca no Brave | `brave_api_key` |
| `everything-search` | STDIO | Busca em arquivos locais | - |
| `filesystem` | STDIO | Ler/escrever arquivos | `allowed_directory` |
| `postgres` | STDIO | Consultas PostgreSQL | `postgres_url` |
| `sequential-thinking` | STDIO | Raciocínio sequencial | - |
| `git` | STDIO | Operações Git | `allowed_directory` |
| `google-maps` | STDIO | Google Maps API | `google_maps_api_key` |
| `time-server` | STDIO | Servidor de tempo | - |
| `minimax` | STDIO | MiniMax AI | `minimax_api_key`, `minimax_base_path` |

#### **Estrutura de Preset:**

```python
@dataclass
class MCPPreset:
    key: str                            # Identificador único
    name: str                           # Nome amigável
    description: str                    # Descrição
    transport_type: TransportType       # STDIO, SSE ou HTTP
    command: Optional[str]              # Comando (npx, uvx, python)
    args: Optional[List[str]]           # Argumentos
    url: Optional[str]                  # URL (para SSE/HTTP)
    env: Dict[str, str]                 # Variáveis de ambiente
    headers: Dict[str, str]             # Headers HTTP
    inputs: List[MCPPresetInput]        # Inputs do usuário
    tags: List[str]                     # Tags para filtro
    documentation_url: Optional[str]    # Link da documentação
    notes: Optional[str]                # Notas adicionais
```

### 3. Service (mcp_service.py)

Gerenciamento completo de clientes MCP e execução de tools.

#### **Funções Principais:**

**CRUD:**
- `listar_todos()` - Lista todos os clientes
- `listar_ativos()` - Lista clientes ativos
- `listar_por_agente()` - Lista clientes de um agente
- `obter_por_id()` - Busca cliente por ID
- `criar()` - Cria novo cliente
- `atualizar()` - Atualiza cliente
- `deletar()` - Remove cliente

**Presets:**
- `listar_presets_disponiveis()` - Lista presets disponíveis
- `aplicar_preset()` - Cria cliente a partir de preset
- `aplicar_one_click()` - Cria cliente a partir de JSON

**Conexão:**
- `conectar_cliente()` - **MAIN**: Conecta ao servidor MCP
- `desconectar_cliente()` - Desconecta cliente
- `reconectar_cliente()` - Reconecta cliente
- `sincronizar_tools()` - Sincroniza ferramentas do servidor

**Execução:**
- `executar_tool_mcp()` - **CORE**: Executa tool MCP
- `converter_mcp_tool_para_openai()` - Converte para formato OpenAI

**Tools:**
- `listar_tools_ativas()` - Lista tools ativas de um cliente
- `ativar_tool()` / `desativar_tool()` - Gerencia disponibilidade

### 4. Transportes Suportados

#### **1. STDIO (Standard I/O)**
Executa processo local e comunica via stdin/stdout.

```python
# Exemplo: Filesystem
command: "npx"
args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
env_vars: {}
```

#### **2. SSE (Server-Sent Events)**
Conecta via HTTP com streaming unidirecional.

```python
# Exemplo: DeepWiki
url: "https://mcp.deepwiki.com/sse"
headers: {}
```

#### **3. Streamable HTTP**
Conecta via HTTP com streaming bidirecional.

```python
# Exemplo: GitHub Copilot
url: "https://api.githubcopilot.com/mcp/"
headers: {"Authorization": "Bearer ghp_..."}
```

## 🔄 Fluxo de Funcionamento

### 1️⃣ **Aplicar Preset (Método Recomendado)**

```
Usuario → /mcp/presets (seleciona GitHub Copilot)
  ↓
Preenche inputs (github_mcp_pat)
  ↓
POST /api/mcp/presets/aplicar
  {
    "preset_key": "github-copilot-pat",
    "agente_id": 1,
    "inputs": {"github_mcp_pat": "ghp_abc123..."}
  }
  ↓
MCPService.aplicar_preset()
  - Valida preset existe
  - Valida inputs obrigatórios
  - Substitui ${input:*} em env/headers
  - Cria MCPClient no banco
  ↓
MCPService.conectar_cliente()
  - Inicia processo/conexão HTTP
  - Handshake MCP
  - Recebe server info
  - Sincroniza tools
  ↓
Cliente conectado ✅
```

### 2️⃣ **One-Click Install (JSON)**

```json
// Formato padrão MCP (usado por Claude Desktop, Zed, etc.)
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
      }
    }
  }
}
```

```
Usuario → Cola JSON no formulário
  ↓
POST /api/mcp/one-click/install
  ↓
MCPService.aplicar_one_click()
  - Parse JSON
  - Extrai primeira chave (nome do servidor)
  - Cria MCPClient
  - Conecta
  ↓
Cliente pronto!
```

### 3️⃣ **Execução de Tool MCP pelo Agente**

```python
# 1. LLM decide chamar tool MCP
tool_call: "mcp_5_list_repos"
arguments: {"owner": "openai"}

# 2. Agente detecta prefixo mcp_
#    Formato: mcp_{client_id}_{tool_name}
#    Extrai: client_id=5, tool_name="list_repos"

# 3. Sistema executa
await MCPService.executar_tool_mcp(
    db,
    mcp_client_id=5,
    tool_name="list_repos",
    arguments={"owner": "openai"}
)

# 4. Fluxo interno
- Adquire lock (evita chamadas concorrentes na mesma sessão)
- Valida cliente está conectado
- Envia requisição ao servidor MCP
- Aguarda resposta (com timeout)
- Processa resultado
- Libera lock

# 5. Retorna para LLM
{
    "resultado": {
        "repositories": [
            {"name": "gpt-3", "stars": 12000},
            {"name": "whisper", "stars": 45000}
        ]
    },
    "output": "llm",
    "enviado_usuario": False
}
```

### 4️⃣ **Sincronização Automática de Tools**

```python
# Ao conectar ou reconectar
await MCPService.conectar_cliente(db, mcp_client_id)

# Sistema automaticamente:
1. Chama `tools/list` no servidor MCP
2. Recebe lista de tools disponíveis
3. Para cada tool:
   - Cria/atualiza registro em mcp_tools
   - Armazena name, description, input_schema
4. Remove tools que não existem mais
5. Atualiza timestamp de sincronização
```

## 🔗 Dependências

### Módulos Internos:
- **`agente`** - Vincula clientes MCP aos agentes
- **`database`** - Base SQLAlchemy

### Bibliotecas Externas:
- **mcp** - Biblioteca oficial do Model Context Protocol
- **FastAPI** - Framework web
- **httpx** - Cliente HTTP async
- **asyncio** - Execução assíncrona

## 💡 Exemplos de Uso

### Exemplo 1: Aplicar Preset GitHub Copilot

**Via API:**
```python
POST /api/mcp/presets/aplicar
{
    "preset_key": "github-copilot-pat",
    "agente_id": 1,
    "inputs": {
        "github_mcp_pat": "ghp_abc123xyz..."
    }
}
```

**Via Interface:**
```
1. Acessar /mcp/presets?agente_id=1
2. Selecionar "GitHub Copilot (PAT)"
3. Preencher token
4. Clicar "Aplicar Preset"
```

### Exemplo 2: One-Click Install (Filesystem)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    }
  }
}
```

```
POST /api/mcp/one-click/install
{
    "agente_id": 1,
    "json_config": "{...}",
    "nome": "Meus Documentos",
    "descricao": "Acesso aos meus documentos pessoais"
}
```

### Exemplo 3: Criar Cliente Customizado (STDIO)

```python
from mcp_client.mcp_schema import MCPClientCriar
from mcp_client.mcp_service import MCPService

cliente = MCPClientCriar(
    agente_id=1,
    nome="PostgreSQL Local",
    descricao="Banco de dados local",
    transport_type="stdio",
    command="uvx",
    args=["mcp-server-postgres"],
    env_vars={
        "POSTGRES_CONNECTION_STRING": "postgresql://user:pass@localhost:5432/mydb"
    }
)

db_client = MCPService.criar(db, cliente)

# Conectar
await MCPService.conectar_cliente(db, db_client.id)
```

### Exemplo 4: Uso pelo Agente (Automático)

```
Usuario: "Liste os repositórios da organização openai"

LLM analisa:
  - Tem ferramenta GitHub disponível (via MCP)
  - Tool: mcp_5_list_repos

LLM chama:
  tool_call("mcp_5_list_repos", {"owner": "openai"})

Sistema executa:
  - Identifica MCP client_id=5
  - Executa tool "list_repos"
  - Retorna resultado ao LLM

LLM responde:
  "Aqui estão os repositórios da OpenAI:
   1. gpt-3 (12k ⭐)
   2. whisper (45k ⭐)
   ..."
```

## 🔌 Integrações

### 1. **Agente** (agente/)

Clientes MCP são vinculados a agentes. Quando o agente processa uma mensagem, suas tools MCP são automaticamente disponibilizadas ao LLM:

```python
# agente_service.py
mcp_clients = MCPService.listar_ativos_por_agente(db, agente.id)

for mcp_client in mcp_clients:
    if not mcp_client.conectado:
        continue
    
    mcp_tools = MCPService.listar_tools_ativas(db, mcp_client.id)
    for mcp_tool in mcp_tools:
        tool_openai = MCPService.converter_mcp_tool_para_openai(mcp_client, mcp_tool)
        tools.append(tool_openai)

# LLM recebe todas as tools (ferramentas normais + MCP)
response = await llm.chat(messages, tools=tools)
```

### 2. **Prefixo de Nome**

Para evitar conflitos, tools MCP usam prefixo:

```python
# Tool original: list_repos
# Cliente MCP id: 5
# Nome final: mcp_5_list_repos

function_name = f"mcp_{mcp_client.id}_{mcp_tool.name}"
```

Quando o LLM chama `mcp_5_list_repos`, o sistema:
1. Detecta prefixo `mcp_`
2. Extrai `client_id=5` e `tool_name=list_repos`
3. Executa via `MCPService.executar_tool_mcp()`

## 📝 Notas Técnicas

### Segurança e Isolamento

⚠️ **IMPORTANTE**:
- **STDIO**: Processos são executados localmente (risco de segurança)
- **Variáveis de ambiente** podem conter credenciais
- **Recomendado**: Use Docker ou containers em produção
- **Firewall**: Limite acesso de rede dos processos STDIO

### Concorrência e Locks

Sistema usa locks por cliente para evitar chamadas concorrentes:

```python
# Um lock por mcp_client_id
_session_locks: Dict[int, asyncio.Lock] = {}

async with _session_locks[mcp_client_id]:
    # Apenas uma chamada por vez para este cliente
    resultado = await session.call_tool(tool_name, arguments)
```

### Reconexão Automática

Clientes que estavam conectados são automaticamente reconectados no startup:

```python
# main.py - startup
mcp_clients_ativos = MCPService.listar_ativos(db)
for client in mcp_clients_ativos:
    if client.conectado:
        await MCPService.reconectar_cliente(db, client.id)
```

### Sincronização de Tools

Tools são sincronizadas:
- **Ao conectar**: Primeira vez
- **Ao reconectar**: Após desconexão
- **Manualmente**: Via endpoint `/sincronizar`

### Inputs em Presets

Presets usam placeholders `${input:ID}`:

```python
# Preset
env: {"GITHUB_TOKEN": "${input:github_pat}"}

# Usuario fornece
inputs: {"github_pat": "ghp_abc123..."}

# Sistema substitui
env: {"GITHUB_TOKEN": "ghp_abc123..."}
```

### Compatibilidade com Claude Desktop

JSON one-click é 100% compatível com o formato do Claude Desktop:

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
      }
    }
  }
}
```

Basta copiar e colar no Fluxi!

## 🚀 Quick Start

### 1. Instalar Servidor MCP (Exemplo: GitHub)

```bash
# Instalar globalmente (opcional)
npm install -g @modelcontextprotocol/server-github
```

### 2. Aplicar Preset no Fluxi

```
1. Acesse /mcp/presets?agente_id=1
2. Clique em "GitHub Copilot (PAT)"
3. Cole seu GitHub token
4. Clique "Aplicar Preset"
```

### 3. Usar no Chat

```
Usuario: "Crie uma issue no repositório fluxi-opencode com título 'Adicionar documentação'"

(Agente automaticamente usa a tool GitHub MCP)
```

---

## 📚 Recursos

### Documentação Oficial MCP
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Anthropic MCP](https://www.anthropic.com/news/model-context-protocol)

### Servidores MCP Disponíveis
- [@modelcontextprotocol/server-github](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- [@modelcontextprotocol/server-filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
- [@modelcontextprotocol/server-postgres](https://github.com/modelcontextprotocol/servers/tree/main/src/postgres)
- [Jina MCP Tools](https://github.com/jina-ai/jina-mcp-tools)
- [Brave Search MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search)

---

**Módulo criado por:** Fluxi Team  
**Versão:** 1.0.0  
**Última atualização:** 2025  
**Protocolo:** Model Context Protocol (MCP)

