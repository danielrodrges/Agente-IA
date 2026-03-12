# Módulo Mensagem 💬

## 📖 Visão Geral

O módulo `mensagem` armazena e gerencia todas as mensagens recebidas e enviadas no WhatsApp, incluindo histórico, contexto e métricas de processamento. Também processa **comandos personalizáveis** e gerencia o **auto-responder** da IA.

## 🎯 Objetivo

- Armazenar mensagens recebidas/enviadas
- Suporte a texto, imagens, áudios, vídeos, documentos
- Histórico de conversas por cliente
- Métricas de processamento (tokens, tempo)
- Registro de ferramentas usadas
- **Processamento de comandos** (#ativar, #desativar, #limpar, etc.)
- **Tipos de mensagem configuráveis** (ações por tipo)

## 📂 Principais Componentes

### Model (mensagem_model.py)

**Tabela: `mensagens`**

| Campo | Descrição |
|-------|-----------|
| `sessao_id` | FK para sessão |
| `telefone_cliente` | Telefone do cliente |
| `tipo` | texto, imagem, audio, video, documento |
| `direcao` | recebida, enviada |
| `conteudo_texto` | Texto da mensagem |
| `conteudo_imagem_base64` | Imagem em base64 |
| `resposta_texto` | Resposta do agente |
| `resposta_tokens_input/output` | Tokens consumidos |
| `resposta_tempo_ms` | Tempo de processamento |
| `ferramentas_usadas` | Tools executadas (JSON) |
| `processada` | Se foi processada |
| `respondida` | Se foi respondida |

### Service (mensagem_service.py)

**Funções:**
- `listar_por_sessao()` - Lista mensagens da sessão
- `listar_por_cliente()` - Lista conversas de um cliente
- `processar_mensagem_recebida()` - **MAIN**: Processa msg do WhatsApp
- `salvar_imagem()` - Salva e converte imagens

## 🔄 Fluxo de Processamento

```
1. Mensagem chega via WhatsApp
2. Evento MessageEv disparado
3. processar_mensagem_recebida()
   - Extrai dados (texto/imagem/audio)
   - Verifica tipo de mensagem e ação configurada
   - Verifica se é comando (#ativar, #desativar, etc.)
   - Se comando → executa e retorna
   - Se auto_responder=False → ignora
   - Cria registro no banco
   - Busca histórico (10 últimas)
   - Chama agente_ativo
   - Agente processa com LLM
   - Atualiza resposta_*
   - Marca como processada/respondida
4. Resposta enviada ao cliente
```

## 🎮 Comandos Personalizáveis

Comandos são processados via `SessaoComandoService` e podem ser configurados por sessão.

### Comandos Padrão

| Comando | Função |
|---------|--------|
| `#ativar` | Ativa o auto-responder da IA |
| `#desativar` | Desativa o auto-responder |
| `#limpar` | Apaga histórico de conversas |
| `#ajuda` | Lista comandos disponíveis |
| `#status` | Mostra status da sessão (IA ativa/inativa) |
| `#listar` | Lista agentes disponíveis |
| `#01`, `#02`... | Troca para agente específico |

### Configuração de Comandos

Cada comando pode ter:
- **Gatilho** - Texto que ativa (ex: `#ativar`, `@ativar`)
- **Ativo** - Se está habilitado
- **Resposta** - Mensagem personalizada
- **Descrição** - Aparece no `#ajuda`

### Fluxo de Comando

```python
1. Mensagem recebida: "#desativar"
2. SessaoComandoService.obter_por_gatilho() → encontra comando
3. Verifica comando.ativo == True
4. Executa ação (sessao.auto_responder = False)
5. Envia resposta personalizada
6. Retorna (não processa com LLM)
```

## 💡 Exemplo

```python
# Listar mensagens de um cliente
mensagens = MensagemService.listar_por_cliente(
    db,
    sessao_id=1,
    telefone_cliente="+5511999999999",
    limite=50
)

# Resultado inclui:
# - conteudo_texto
# - resposta_texto
# - ferramentas_usadas
# - resposta_tokens_*
# - resposta_tempo_ms
```

---

**Módulo:** mensagem  
**Suporta:** Texto, imagens, áudios, vídeos, documentos

