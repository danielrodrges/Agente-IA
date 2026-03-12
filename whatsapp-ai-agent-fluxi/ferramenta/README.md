# Módulo Ferramenta 🔧

## 📖 Visão Geral

O módulo `ferramenta` é o **sistema de function calling** do Fluxi. Permite criar, gerenciar e executar ferramentas customizadas que os agentes podem usar para interagir com APIs externas, executar código Python, enviar mensagens formatadas no WhatsApp, e muito mais. Inclui um **wizard visual de 7 etapas** para facilitar a criação de ferramentas sem código.

## 🎯 Objetivo

Fornecer um sistema flexível e extensível para:
- **Integrar APIs externas** via requisições HTTP (GET, POST, PUT, DELETE)
- **Executar código Python** customizado
- **Variáveis dinâmicas** (sessão, cliente, timestamps, etc.)
- **Autenticação** (Bearer, API Key, Basic Auth)
- **Output flexível** (enviar para LLM, usuário ou ambos)
- **Encadeamento de ferramentas** (executar ferramentas em sequência)
- **Wizard visual** para criação sem código

## 📂 Estrutura de Arquivos

```
ferramenta/
├── __init__.py                          # Inicialização do módulo
├── ferramenta_model.py                  # Modelos SQLAlchemy (Ferramenta)
├── ferramenta_variavel_model.py         # Modelo de variáveis por ferramenta
├── ferramenta_schema.py                 # Schemas Pydantic
├── ferramenta_service.py                # Lógica de negócio e execução
├── ferramenta_router.py                 # Endpoints REST API
├── ferramenta_frontend_router.py        # Rotas de interface web
├── ferramenta_wizard_router.py          # Wizard de criação (7 steps)
├── ferramenta_variavel_service.py       # Serviço de variáveis
├── ferramenta_variavel_router.py        # API de variáveis
├── ferramenta_variavel_schema.py        # Schemas de variáveis
├── curl_parser.py                       # Parser de comandos CURL
└── README.md                            # Esta documentação
```

## 🔧 Componentes Principais

### 1. Models (ferramenta_model.py)

Define a estrutura das ferramentas:

#### **Tabela: `ferramentas`**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `nome` | String(100) | Nome único da ferramenta |
| `descricao` | Text | Descrição da ferramenta |
| `tool_type` | Enum | Tipo: `web` (HTTP) ou `code` (Python) |
| `tool_scope` | Enum | Escopo: `principal` ou `auxiliar` |
| `params` | Text (JSON) | Definição dos parâmetros |
| `curl_command` | Text | Comando CURL completo (para type=web) |
| `codigo_python` | Text | Código Python (para type=code) |
| `substituir` | Boolean | Permite substituição de `{variavel}` |
| `response_map` | Text (JSON) | Mapeamento de campos da resposta |
| `output` | Enum | Destino: `llm`, `user`, `both` |
| `channel` | Enum | Canal: `text`, `image`, `audio`, `video`, `document` |
| `post_instruction` | Text | Instrução para LLM sobre o uso da resposta |
| `next_tool` | String(100) | Nome da próxima ferramenta (encadeamento) |
| `print_output_var` | String(100) | Variável de saída (Python) |
| `ativa` | Boolean | Se a ferramenta está disponível |
| `criado_em` | DateTime | Data de criação |
| `atualizado_em` | DateTime | Data de atualização |

#### **Enums Importantes:**

```python
# Tipo da ferramenta
ToolType:
    WEB = "web"        # Requisições HTTP
    CODE = "code"      # Código Python

# Escopo (usado no LLM)
ToolScope:
    PRINCIPAL = "principal"  # Enviada ao LLM (function calling)
    AUXILIAR = "auxiliar"    # Não enviada, apenas execução interna

# Destino do output
OutputDestination:
    LLM = "llm"       # Apenas para o LLM
    USER = "user"     # Apenas para o usuário (WhatsApp)
    BOTH = "both"     # Para ambos

# Canal de envio (quando output=user ou both)
ChannelType:
    TEXT = "text"           # Texto simples
    IMAGE = "image"         # Imagem
    AUDIO = "audio"         # Áudio
    VIDEO = "video"         # Vídeo
    DOCUMENT = "document"   # Documento
```

#### **Tabela: `ferramenta_variaveis`**
Armazena variáveis específicas de cada ferramenta (tokens, API keys, etc.):

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `ferramenta_id` | Integer | FK para ferramenta |
| `chave` | String(100) | Nome da variável (ex: "API_TOKEN") |
| `valor` | Text | Valor da variável |
| `tipo` | String(20) | Tipo: string, secret, json |
| `descricao` | Text | Descrição |
| `is_secret` | Boolean | Se é sensível (não mostrar no frontend) |

### 2. Service (ferramenta_service.py)

Contém toda a lógica de execução de ferramentas. **744 linhas** com funcionalidades complexas:

#### **Principais Funções:**

**CRUD:**
- `listar_todas()` - Lista ferramentas
- `listar_ferramentas_ativas()` - Lista apenas ativas
- `obter_por_id()` - Busca por ID
- `obter_por_nome()` - Busca por nome
- `criar()` - Cria ferramenta
- `atualizar()` - Atualiza ferramenta
- `deletar()` - Remove ferramenta

**Substituição de Variáveis:**
- `substituir_variaveis()` - **CORE**: Substitui `{variavel}` em textos

Suporta 4 tipos de variáveis:
1. `{var.CHAVE}` - Variáveis da ferramenta (do banco)
2. `{variavel}` - Variáveis passadas como argumento
3. `{resultado.campo}` - Variáveis aninhadas
4. `{env.VARIAVEL}` - Variáveis de ambiente

**Execução:**
- `executar_ferramenta_web()` - Executa requisições HTTP
- `executar_ferramenta_code()` - Executa código Python
- `executar_ferramenta()` - **MAIN**: Orquestra execução + encadeamento
- `processar_output_ferramenta()` - Processa destino (LLM/User/Both)
- `enviar_para_usuario()` - Envia resultado via WhatsApp

**Conversão:**
- `converter_para_openai_format()` - Converte para formato OpenAI Function Calling
- `criar_ferramentas_padrao()` - Cria ferramentas built-in

### 3. CURL Parser (curl_parser.py)

Biblioteca especializada para parse de comandos CURL:

**Funcionalidades:**
- `parse_curl(curl_command)` - Converte CURL → Dict
- `dict_to_curl(data)` - Converte Dict → CURL
- `extract_variables(text)` - Extrai `{variavel}` do texto
- `validate_curl(curl_command)` - Valida CURL

**Suporta:**
- ✅ Métodos: GET, POST, PUT, PATCH, DELETE
- ✅ Headers múltiplos (`-H`)
- ✅ Query params na URL
- ✅ Body: JSON, form-data, urlencoded, raw
- ✅ Autenticação: Bearer, Basic Auth, API Key
- ✅ Variáveis: `{var.TOKEN}`, `{nome}`, `{env.KEY}`

**Exemplo:**
```python
curl = """
curl -X POST https://api.example.com/users \
  -H "Authorization: Bearer {var.API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name": "{nome}", "email": "{email}"}'
"""

parsed = CurlParser.parse_curl(curl)
# {
#     "method": "POST",
#     "url": "https://api.example.com/users",
#     "headers": {
#         "Authorization": "Bearer {var.API_TOKEN}",
#         "Content-Type": "application/json"
#     },
#     "body": '{"name": "{nome}", "email": "{email}"}',
#     "body_type": "json"
# }
```

### 4. Wizard (ferramenta_wizard_router.py)

**Wizard visual de 7 etapas** para criação de ferramentas sem código:

#### **📝 Step 1: Definição Básica**
- Nome da ferramenta
- Descrição
- Tipo (WEB ou CODE)
- Escopo (PRINCIPAL ou AUXILIAR)

#### **⚙️ Step 2: Parâmetros**
- Adicionar parâmetros dinâmicos
- Tipos: string, int, float, bool, array, enum, object
- Marcar como obrigatório
- Descrição e validações

#### **🔧 Step 3: Configuração (WEB)**
Para ferramentas WEB:
- Cole comando CURL (completo)
- Sistema faz parse automático
- Edita método, URL, headers, body
- Substitui variáveis com `{variavel}`

#### **💻 Step 3: Configuração (CODE)**
Para ferramentas CODE:
- Escreve código Python
- Acessa `argumentos` dict
- Define `resultado` para retorno
- Ou usa `print_output_var`

#### **🗺️ Step 4: Mapeamento de Resposta**
- JsonPath para extrair campos
- Mapear campo_api → campo_resultado
- Preview com exemplo de resposta

#### **📤 Step 5: Output e Canal**
- Output: LLM, User ou Both
- Canal: Text, Image, Audio, Video, Document
- Post-instruction (orientação para LLM)

#### **🔗 Step 6: Encadeamento**
- Próxima ferramenta a executar
- Resultado da primeira vira input da segunda
- Permite workflows complexos

#### **🔐 Step 7: Variáveis**
- Adicionar variáveis da ferramenta
- API Tokens, secrets, configurações
- Marcar como "secret" (oculta no frontend)
- Usar com `{var.NOME_VARIAVEL}`

**Finaliza:**
- Cria ferramenta no banco
- Cria todas as variáveis
- Redireciona para lista de ferramentas

### 5. Ferramentas Padrão

O sistema cria **ferramentas built-in** na inicialização:

#### **1. obter_data_hora_atual**
```python
Type: CODE
Scope: PRINCIPAL
Output: LLM
```
Retorna data e hora atual formatada.

#### **2. calcular**
```python
Type: CODE
Scope: PRINCIPAL
Output: LLM
Params: {"expressao": "string"}
```
Avalia expressões matemáticas.

## 🔄 Fluxo de Funcionamento

### 1️⃣ **Criação de Ferramenta via Wizard**

```
Usuario → /ferramentas/wizard/step1
  ↓
Step 1: Define nome, tipo, escopo
  ↓
Step 2: Adiciona parâmetros
  ↓
Step 3: Configura (CURL ou código Python)
  ↓
Step 4: Mapeia resposta (opcional)
  ↓
Step 5: Define output (LLM/User/Both) e canal
  ↓
Step 6: Encadeamento (opcional)
  ↓
Step 7: Variáveis (API keys, tokens)
  ↓
Salva no banco → Ferramenta pronta!
```

### 2️⃣ **Execução de Ferramenta (Chamada pelo LLM)**

```python
# 1. Agente chama ferramenta
LLM → tool_call("buscar_usuario", {"id": 123})

# 2. Sistema executa
await FerramentaService.executar_ferramenta(
    db,
    "buscar_usuario",
    {"id": 123},
    sessao_id=1,
    telefone_cliente="+5511999999999"
)

# 3. Fluxo de execução
if ferramenta.tool_type == WEB:
    ↓
    - Carrega variáveis do banco {var.*}
    - Substitui variáveis no CURL
    - Parse CURL → HTTP request
    - Executa requisição
    - Aplica response_map (se houver)
    ↓
elif ferramenta.tool_type == CODE:
    ↓
    - Carrega variáveis do banco
    - Substitui variáveis no código
    - Executa código Python
    - Captura resultado
    ↓

# 4. Encadeamento (se next_tool definido)
if ferramenta.next_tool:
    ↓
    executa_ferramenta(next_tool, {**args, "resultado": resultado})

# 5. Processa output
if output == LLM:
    → Retorna para LLM
elif output == USER:
    → Envia via WhatsApp para usuário
elif output == BOTH:
    → Envia para ambos

# 6. Retorna resultado
return {
    "resultado": {...},
    "output": "llm",
    "enviado_usuario": False,
    "post_instruction": "Use estas informações para..."
}
```

### 3️⃣ **Substituição de Variáveis (Exemplo Real)**

```python
# CURL com variáveis
curl = """
curl -X POST https://api.github.com/repos/{var.OWNER}/{var.REPO}/issues \
  -H "Authorization: Bearer {var.GITHUB_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"title": "{titulo}", "body": "{descricao}"}'
"""

# Argumentos passados pelo LLM
argumentos = {
    "titulo": "Bug na página inicial",
    "descricao": "Erro ao carregar imagens"
}

# Variáveis da ferramenta (do banco)
variaveis_ferramenta = {
    "GITHUB_TOKEN": "ghp_abc123...",
    "OWNER": "fluxiai",
    "REPO": "fluxi-opencode"
}

# Após substituição
curl_final = """
curl -X POST https://api.github.com/repos/fluxiai/fluxi-opencode/issues \
  -H "Authorization: Bearer ghp_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"title": "Bug na página inicial", "body": "Erro ao carregar imagens"}'
"""
```

## 🔗 Dependências

### Módulos Internos:
- **`database`** - Base SQLAlchemy
- **`sessao`** - Envio de mensagens via WhatsApp
- **`agente`** - Usa ferramentas vinculadas

### Bibliotecas Externas:
- **httpx** - Cliente HTTP async
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **Pydantic** - Validação

## 💡 Exemplos de Uso

### Exemplo 1: Ferramenta WEB - Buscar CEP

**Via Wizard:**
```
Step 1:
  Nome: buscar_cep
  Descrição: Busca informações de um CEP brasileiro
  Tipo: WEB
  Escopo: PRINCIPAL

Step 2:
  Parâmetro: cep
    - Tipo: string
    - Obrigatório: sim
    - Descrição: CEP sem formatação (ex: 01310100)

Step 3 (CURL):
  curl -X GET "https://viacep.com.br/ws/{cep}/json/"

Step 4: (skip - sem mapeamento)

Step 5:
  Output: LLM
  Channel: TEXT
  Post-instruction: Use o endereço retornado para responder ao usuário

Step 6: (skip - sem encadeamento)

Step 7: (skip - sem variáveis)
```

**Uso pelo LLM:**
```python
# LLM chama:
tool_call("buscar_cep", {"cep": "01310100"})

# Sistema executa:
GET https://viacep.com.br/ws/01310100/json/

# Retorna:
{
    "cep": "01310-100",
    "logradouro": "Avenida Paulista",
    "bairro": "Bela Vista",
    "localidade": "São Paulo",
    "uf": "SP"
}
```

### Exemplo 2: Ferramenta CODE - Gerar QR Code

```python
# Step 1
Nome: gerar_qrcode
Tipo: CODE
Escopo: PRINCIPAL

# Step 2
Parâmetro: texto (string, obrigatório)

# Step 3 (Código Python)
import qrcode
from io import BytesIO
import base64

# Gerar QR code
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data(argumentos['texto'])
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")

# Converter para base64
buffer = BytesIO()
img.save(buffer, format='PNG')
img_base64 = base64.b64encode(buffer.getvalue()).decode()

resultado = {
    "qrcode_base64": img_base64,
    "formato": "PNG"
}

# Step 5
Output: USER
Channel: IMAGE
```

### Exemplo 3: Ferramenta com Autenticação e Mapeamento

**CURL original:**
```bash
curl -X POST "https://api.example.com/v1/users" \
  -H "Authorization: Bearer {var.API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{nome}",
    "email": "{email}",
    "role": "customer"
  }'
```

**Response mapping:**
```json
{
    "data.user.id": "usuario_id",
    "data.user.name": "nome_completo",
    "data.user.created_at": "data_criacao"
}
```

**Resultado final:**
```json
{
    "usuario_id": 12345,
    "nome_completo": "João Silva",
    "data_criacao": "2025-01-15T10:30:00Z"
}
```

### Exemplo 4: Encadeamento de Ferramentas

**Ferramenta 1: consultar_estoque**
```python
Nome: consultar_estoque
Params: {"produto_id": "int"}
Output: LLM
Next Tool: calcular_desconto  # ← Encadeamento!
```

**Ferramenta 2: calcular_desconto**
```python
Nome: calcular_desconto
Params: {"preco": "float", "quantidade": "int"}
Output: LLM
```

**Fluxo:**
```python
# LLM chama:
tool_call("consultar_estoque", {"produto_id": 123})

# Sistema executa ferramenta 1
resultado_1 = {"preco": 100.0, "estoque": 50}

# Sistema automaticamente chama ferramenta 2 (next_tool)
resultado_2 = calcular_desconto({
    "preco": 100.0,
    "quantidade": 5,
    "resultado": resultado_1  # ← Resultado da primeira
})

# Retorna resultado final
return resultado_2
```

## 🔌 Integrações

### 1. **Agente** (agente/)
Agentes vinculam ferramentas (máx. 20) e as disponibilizam para o LLM:

```python
# agente_service.py
ferramentas = AgenteService.listar_ferramentas(db, agente_id)

for ferramenta in ferramentas:
    tool_openai = FerramentaService.converter_para_openai_format(ferramenta)
    tools.append(tool_openai)

# LLM recebe tools no formato OpenAI Function Calling
response = await llm.chat(messages, tools=tools)
```

### 2. **Sessão** (sessao/)
Ferramentas podem enviar mensagens via WhatsApp:

```python
if output in [USER, BOTH]:
    await SessaoService.enviar_mensagem(
        sessao_id,
        telefone_cliente,
        texto=resultado["mensagem"],
        tipo=ChannelType.TEXT
    )
```

### 3. **Config** (config/)
Variáveis podem usar configurações globais:

```python
# Ferramenta pode acessar
{var.GITHUB_TOKEN}  # Do banco (ferramenta_variaveis)
{env.OPENAI_API_KEY}  # De variável de ambiente
```

## 📝 Notas Técnicas

### Segurança de Execução de Código

⚠️ **IMPORTANTE**: Ferramentas CODE executam Python com `exec()`:
- **Namespace isolado** (não acessa globals)
- **Timeout** implementado (30s padrão)
- **Variáveis limitadas**: argumentos, resultado, datetime, json, httpx
- ⚠️ **Não use em produção com código não confiável**
- ✅ **Para produção**: Considere sandboxing (Docker, Pyodide, etc.)

### Variáveis Especiais

Sistema de prioridade de variáveis:
1. `{var.CHAVE}` - Variáveis da ferramenta (mais alta prioridade)
2. `{campo}` - Argumentos passados
3. `{resultado.campo}` - Aninhamento
4. `{env.VAR}` - Ambiente (mais baixa prioridade)

### Conversão para OpenAI Format

Apenas ferramentas `PRINCIPAL` são convertidas:

```python
def converter_para_openai_format(ferramenta):
    if ferramenta.tool_scope != ToolScope.PRINCIPAL:
        return None  # Auxiliares não vão para o LLM
    
    return {
        "type": "function",
        "function": {
            "name": ferramenta.nome,
            "description": ferramenta.descricao,
            "parameters": {
                "type": "object",
                "properties": json.loads(ferramenta.params),
                "required": [...]
            }
        }
    }
```

### Output Destinations

- **LLM**: Resultado retorna para contexto do agente
- **USER**: Envia via WhatsApp (texto, imagem, etc.)
- **BOTH**: Faz ambos (útil para confirmações)

### CURL como Fonte da Verdade

Para ferramentas WEB, o `curl_command` é a **única fonte da verdade**:
- Parse é feito em tempo de execução
- Não há campos separados (url, method, headers, body)
- Facilita edição e debugging

### Substituição de Variáveis em JSON

Cuidado com regex! Sistema usa padrão específico:

```python
# ✅ Substitui
{nome}
{var.API_KEY}
{env.TOKEN}
{resultado.data.id}

# ❌ Não substitui (preserva JSON)
{"name": "João"}  # Chaves do JSON não são substituídas
```

---

## 🚀 Quick Start

### Criar Ferramenta via Wizard

1. Acesse `/ferramentas/wizard/step1`
2. Preencha os 7 steps
3. Finalize e teste

### Vincular a um Agente

```python
# Via interface
/agentes/{id}/ferramentas
→ Selecione ferramentas (máx. 20)

# Via API
POST /api/agentes/{id}/ferramentas
{
    "ferramentas": [1, 2, 5]
}
```

### Testar Ferramenta

```python
# Via código
from ferramenta.ferramenta_service import FerramentaService

resultado = await FerramentaService.executar_ferramenta(
    db,
    "buscar_cep",
    {"cep": "01310100"}
)
```

---

**Módulo criado por:** Fluxi Team  
**Versão:** 1.0.0  
**Última atualização:** 2025

