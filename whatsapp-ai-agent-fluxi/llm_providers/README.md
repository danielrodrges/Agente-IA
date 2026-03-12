# Módulo LLM Providers

Este módulo gerencia provedores de LLM locais como LM Studio, llama.cpp e Ollama, permitindo integração com APIs OpenAI-compatíveis.

## Funcionalidades

- **Gerenciamento de Provedores**: Criar, editar e gerenciar provedores LLM
- **Teste de Conexão**: Testar conectividade e buscar modelos disponíveis
- **Suporte a Múltiplos Tipos**: LM Studio, llama.cpp e Ollama
- **Cache de Modelos**: Armazenar informações dos modelos disponíveis
- **Estatísticas**: Métricas de uso e performance
- **Interface Web**: Interface amigável para gerenciamento

## Tipos de Provedores Suportados

### LM Studio
- **URL Padrão**: `http://localhost:1234`
- **API**: OpenAI-compatível
- **Endpoints**: `/v1/models`, `/v1/chat/completions`

### llama.cpp
- **URL Padrão**: `http://localhost:8080`
- **API**: OpenAI-compatível
- **Endpoints**: `/v1/models`, `/v1/chat/completions`

### Ollama
- **URL Padrão**: `http://localhost:11434`
- **API**: Própria
- **Endpoints**: `/api/tags`, `/api/chat`

## Estrutura do Módulo

```
llm_providers/
├── __init__.py
├── llm_providers_schema.py      # Schemas Pydantic
├── llm_providers_model.py       # Modelos SQLAlchemy
├── llm_providers_service.py     # Lógica de negócio
├── llm_providers_router.py      # Rotas da API
├── llm_providers_frontend_router.py  # Rotas do frontend
└── README.md
```

## Endpoints da API

### Provedores
- `GET /api/provedores-llm/` - Listar todos os provedores
- `GET /api/provedores-llm/ativos` - Listar provedores ativos
- `GET /api/provedores-llm/{id}` - Obter provedor específico
- `POST /api/provedores-llm/` - Criar novo provedor
- `PUT /api/provedores-llm/{id}` - Atualizar provedor
- `DELETE /api/provedores-llm/{id}` - Deletar provedor

### Testes e Modelos
- `POST /api/provedores-llm/{id}/testar` - Testar conexão
- `GET /api/provedores-llm/{id}/modelos` - Listar modelos
- `POST /api/provedores-llm/{id}/requisicao` - Enviar requisição
- `GET /api/provedores-llm/{id}/estatisticas` - Obter estatísticas

## Interface Web

### Páginas Disponíveis
- `/provedores-llm/` - Lista de provedores
- `/provedores-llm/novo` - Criar novo provedor
- `/provedores-llm/{id}/editar` - Editar provedor
- `/provedores-llm/{id}/detalhes` - Detalhes do provedor
- `/provedores-llm/{id}/testar` - Testar provedor
- `/provedores-llm/{id}/modelos` - Modelos disponíveis
- `/provedores-llm/{id}/estatisticas` - Estatísticas

## Configuração

### Variáveis de Ambiente
Nenhuma configuração adicional é necessária. O módulo usa as configurações padrão do sistema.

### Banco de Dados
O módulo cria automaticamente as seguintes tabelas:
- `provedores_llm` - Informações dos provedores
- `estatisticas_provedores` - Métricas de uso
- `modelos_provedores` - Cache de modelos

## Uso

### Criar um Provedor

```python
from llm_providers.llm_providers_service import ProvedorLLMService
from llm_providers.llm_providers_schema import ProvedorLLMCriar

# Criar provedor LM Studio
provedor_data = ProvedorLLMCriar(
    nome="LM Studio Local",
    tipo="lm_studio",
    base_url="http://localhost:1234",
    descricao="LM Studio rodando localmente"
)

provedor = ProvedorLLMService.criar(db, provedor_data)
```

### Testar Conexão

```python
# Testar conexão e buscar modelos
resultado = await ProvedorLLMService.testar_conexao(db, provedor_id)
if resultado.sucesso:
    print(f"Encontrados {len(resultado.modelos)} modelos")
```

### Enviar Requisição

```python
from llm_providers.llm_providers_schema import RequisicaoLLM, ConfiguracaoProvedor

# Preparar requisição (texto simples)
requisicao = RequisicaoLLM(
    mensagens=[{"role": "user", "content": "Olá!"}],
    modelo="llama3.2",
    configuracao=ConfiguracaoProvedor(
        temperatura=0.7,
        max_tokens=1000
    )
)

# Enviar requisição
resposta = await ProvedorLLMService.enviar_requisicao(db, provedor_id, requisicao)
print(resposta.conteudo)
```

### Enviar Requisição com Imagem (Multimodal)

```python
# Preparar requisição com imagem
requisicao = RequisicaoLLM(
    mensagens=[{
        "role": "user", 
        "content": [
            {"type": "text", "text": "O que você vê nesta imagem?"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]
    }],
    modelo="llama3.2-vision",
    configuracao=ConfiguracaoProvedor(temperatura=0.7)
)
```

> **Nota**: O campo `content` aceita string (texto) ou lista (multimodal com imagens).

## Integração com OpenAI

O módulo é compatível com bibliotecas OpenAI existentes:

```python
from openai import OpenAI

# Configurar cliente para usar provedor local
client = OpenAI(
    base_url="http://localhost:1234/v1",  # LM Studio
    api_key="lm-studio"  # Chave opcional
)

# Usar normalmente
response = client.chat.completions.create(
    model="llama3.2",
    messages=[{"role": "user", "content": "Olá!"}]
)
```

## Monitoramento

O módulo coleta automaticamente:
- Total de requisições
- Requisições bem-sucedidas vs. com erro
- Tempo médio de resposta
- Modelos carregados
- Última atividade

## Troubleshooting

### Problemas Comuns

1. **Conexão recusada**: Verifique se o provedor está rodando
2. **Timeout**: Aumente o timeout nas configurações
3. **Modelo não encontrado**: Teste a conexão para atualizar modelos
4. **Erro de autenticação**: Verifique a API key se necessária

### Logs

O módulo usa o sistema de logging padrão do FastAPI. Verifique os logs para detalhes de erros.

## Contribuição

Para adicionar suporte a novos provedores:

1. Adicione o tipo no enum `TipoProvedorEnum`
2. Implemente a lógica de conexão no `testar_conexao()`
3. Implemente a lógica de requisição no `enviar_requisicao()`
4. Atualize a documentação
