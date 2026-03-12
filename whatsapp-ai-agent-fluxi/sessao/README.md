# Módulo Sessão 📱

## 📖 Visão Geral

O módulo `sessao` gerencia conexões WhatsApp usando a biblioteca Neonize. Cada sessão representa uma conta WhatsApp conectada que pode ter múltiplos agentes, **comandos personalizáveis** e **configurações de tipos de mensagem**.

## 🎯 Objetivo

- Conectar/desconectar contas WhatsApp
- Gerenciar QR Code e pareamento
- Receber e enviar mensagens
- Alternar entre agentes
- Auto-responder mensagens (toggle via `#ativar`/`#desativar`)
- Manter histórico de conversas
- **Comandos personalizáveis** por sessão
- **Tipos de mensagem configuráveis** (ações por tipo)

## 📂 Estrutura de Arquivos

```
sessao/
├── __init__.py
├── sessao_model.py              # Modelo principal (Sessao)
├── sessao_schema.py             # Schemas Pydantic
├── sessao_service.py            # Lógica de conexão WhatsApp
├── sessao_router.py             # Endpoints REST API
├── sessao_frontend_router.py    # Rotas de interface web
├── sessao_comando_model.py      # 🆕 Modelo de comandos
├── sessao_comando_service.py    # 🆕 Serviço de comandos
├── sessao_tipo_mensagem_model.py # Modelo de tipos de mensagem
├── sessao_tipo_mensagem_service.py # Serviço de tipos
└── README.md
```

## 🔧 Principais Componentes

### Model (sessao_model.py)

**Tabela: `sessoes`**

| Campo | Descrição |
|-------|-----------|
| `nome` | Nome único da sessão |
| `telefone` | Telefone conectado |
| `status` | desconectado, conectando, conectado, erro |
| `ativa` | Se está ativa |
| `auto_responder` | Responde automaticamente |
| `agente_ativo_id` | Agente atual respondendo |
| `qr_code` | QR Code para conexão |

**Relacionamentos:**
- `agentes` → Muitos agentes
- `comandos` → 🆕 Comandos personalizáveis
- `tipos_mensagem` → 🆕 Configurações por tipo

### 🆕 Comandos (sessao_comando_model.py)

**Tabela: `sessao_comandos`**

| Campo | Descrição |
|-------|-----------|
| `sessao_id` | FK para sessão |
| `comando_id` | Identificador (ativar, desativar, limpar...) |
| `gatilho` | Texto que ativa (#ativar, @ativar, etc.) |
| `ativo` | Se está habilitado |
| `resposta` | Mensagem personalizada |
| `descricao` | Aparece no #ajuda |

**Comandos Padrão:**

| ID | Gatilho | Função |
|----|---------|--------|
| `ativar` | `#ativar` | Liga o auto-responder da IA |
| `desativar` | `#desativar` | Desliga o auto-responder |
| `limpar` | `#limpar` | Apaga histórico de conversas |
| `ajuda` | `#ajuda` | Lista comandos disponíveis |
| `status` | `#status` | Mostra status da sessão |
| `listar` | `#listar` | Lista agentes disponíveis |
| `trocar_agente` | `#` | Prefixo para trocar agente (#01, #02) |

### 🆕 Tipos de Mensagem (sessao_tipo_mensagem_model.py)

**Tabela: `sessao_tipos_mensagem`**

| Campo | Descrição |
|-------|-----------|
| `sessao_id` | FK para sessão |
| `tipo` | texto, imagem, audio, video, documento |
| `acao` | processar, ignorar, resposta_fixa, transcricao_apenas |
| `resposta_fixa` | Resposta quando ação é resposta_fixa |

**Ações Disponíveis:**
- `processar` - Processa normalmente com IA
- `ignorar` - Ignora silenciosamente
- `resposta_fixa` - Envia resposta configurada
- `transcricao_apenas` - Transcreve áudio e envia (sem IA)

### Service (sessao_service.py)

**Funções Principais:**
- `conectar()` - Conecta sessão via QR Code ou Pair Code
- `desconectar()` - Desconecta sessão
- `reconectar_sessao()` - Reconecta automaticamente
- `enviar_mensagem()` - Envia mensagem via WhatsApp
- `processar_mensagem_webhook()` - Processa mensagem recebida

**GerenciadorSessoes:**
- Gerencia clientes Neonize ativos
- Mantém threads de conexão
- Cache de QR Codes

### 🆕 Serviço de Comandos (sessao_comando_service.py)

**Funções:**
- `criar_comandos_padrao()` - Cria comandos padrão para nova sessão
- `obter_comandos_dict()` - Retorna comandos indexados por ID
- `obter_por_gatilho()` - Encontra comando pelo texto (#ativar)
- `atualizar()` - Atualiza configuração de comando
- `gerar_ajuda()` - Gera texto do #ajuda dinamicamente

## 🔄 Fluxos

### Conexão WhatsApp
```
1. Criar Sessão → status: "desconectado"
2. Conectar → Gera QR Code → status: "conectando"
3. Escanear QR → status: "conectado"
4. Mensagem recebida → Verifica comando
5. Se não for comando → Auto-responder (se ativo)
6. Processa com agente_ativo → Responde
```

### Processamento de Comando
```
1. Mensagem: "#desativar"
2. SessaoComandoService.obter_por_gatilho() → encontra
3. Verifica comando.ativo == True
4. Executa: sessao.auto_responder = False
5. Envia resposta: "😴 IA Desativada!"
6. Retorna (não processa com LLM)
```

## 💡 Exemplos

### Conectar Sessão
```python
SessaoService.conectar(db, sessao_id)
# → Gera QR Code
```

### Enviar Mensagem
```python
await SessaoService.enviar_mensagem(
    db, sessao_id,
    telefone="+5511999999999",
    texto="Olá!",
    tipo="texto"
)
```

### Configurar Comando
```python
# Mudar gatilho de #ativar para @ativar
SessaoComandoService.atualizar(
    db,
    sessao_id=1,
    comando_id="ativar",
    gatilho="@ativar",
    resposta="🤖 IA ligada!"
)
```

### Verificar Comando
```python
comando = SessaoComandoService.obter_por_gatilho(
    db, sessao_id=1, texto="#status"
)
if comando:
    print(f"Comando encontrado: {comando.comando_id}")
```

## 🔗 Rotas Frontend

| Rota | Descrição |
|------|-----------|
| `/sessoes/{id}/comandos` | 🆕 Configurar comandos |
| `/sessoes/{id}/tipos-mensagem` | 🆕 Configurar tipos de mensagem |
| `/sessoes/{id}/detalhes` | Detalhes da sessão |
| `/sessoes/nova` | Criar nova sessão |

---

**Módulo:** sessao  
**Biblioteca:** Neonize (WhatsApp Web)  
**Atualizado:** Novembro 2025

