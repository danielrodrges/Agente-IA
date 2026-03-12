# Módulo RAG 📚

## 📖 Visão Geral

O módulo `rag` implementa Retrieval-Augmented Generation usando ChromaDB e OpenAI embeddings, permitindo criar bases de conhecimento para os agentes.

## 🎯 Objetivo

- Criar bases de conhecimento personalizadas
- Processar documentos (PDF, TXT, DOC)
- Gerar embeddings e chunks
- Busca semântica
- Integração transparente com agentes

## 📂 Principais Componentes

### Model (rag_model.py)

**Tabela: `rags`**

| Campo | Descrição |
|-------|-----------|
| `nome` | Nome da base |
| `provider` | openai, cohere, huggingface, google |
| `modelo_embed` | Modelo de embeddings |
| `chunk_size` | Tamanho do chunk (padrão: 1000) |
| `chunk_overlap` | Sobreposição (padrão: 200) |
| `top_k` | Resultados retornados (padrão: 3) |
| `api_key_embed` | API key do provider |
| `treinado` | Se possui chunks |
| `total_chunks` | Quantidade de chunks |
| `storage_path` | Diretório ChromaDB |

### Service (rag_service.py)

**CRUD:**
- `criar()` - Cria RAG
- `processar_upload()` - Processa arquivos (PDF/TXT/DOC)
- `adicionar_texto()` - Adiciona texto direto

**Busca:**
- `buscar()` - **CORE**: Busca semântica
- `obter_chunks()` - Lista chunks
- `deletar_chunk()` - Remove chunk

### Custom Service (rag_custom_service.py)

**RAGCustomService:**
- Implementação própria com ChromaDB e OpenAI embeddings
- ChromaDB + OpenAI embeddings
- Chunking inteligente
- Busca por similaridade

## 🔄 Fluxo

### 1️⃣ Criar e Treinar

```python
# 1. Criar RAG
rag = RAGService.criar(db, RAGCriar(
    nome="Documentação Empresa",
    provider="openai",
    modelo_embed="text-embedding-3-small",
    chunk_size=1000,
    chunk_overlap=200,
    top_k=3,
    api_key_embed="sk-..."
))

# 2. Adicionar documentos
RAGService.processar_upload(
    db,
    rag_id=rag.id,
    arquivo=upload_file,
    titulo="Manual do Produto"
)
# → Gera chunks
# → Cria embeddings
# → Armazena em ChromaDB

# 3. RAG agora está treinado
```

### 2️⃣ Vincular a Agente

```python
# Vincular RAG ao agente
AgenteService.atualizar(
    db,
    agente_id=1,
    AgenteAtualizar(rag_id=rag.id)
)

# Sistema adiciona automaticamente ferramenta:
# buscar_base_conhecimento(query, num_resultados)
```

### 3️⃣ Usar em Conversa

```
Usuario: "Qual o prazo de garantia do produto?"

Agente (automaticamente):
1. Chama buscar_base_conhecimento(query="prazo de garantia")
2. RAG busca nos documentos
3. Retorna top 3 contextos mais relevantes
4. LLM usa contextos para responder

Agente: "De acordo com o manual, o produto tem
garantia de 12 meses a partir da data de compra..."
```

## 💡 Providers Suportados

### OpenAI
```python
provider="openai"
modelo_embed="text-embedding-3-small"  # Recomendado
# ou: text-embedding-3-large, text-embedding-ada-002
```

### Cohere
```python
provider="cohere"
modelo_embed="embed-multilingual-v3.0"
```

### HuggingFace
```python
provider="huggingface"
modelo_embed="sentence-transformers/all-mpnet-base-v2"
```

### Google
```python
provider="google"
modelo_embed="models/embedding-001"
```

## 📊 Métricas (rag_metrica_service.py)

Registra automaticamente:
- Total de buscas
- Queries mais comuns
- Tempo médio de busca
- Agente que buscou
- Cliente que solicitou

---

**Módulo:** rag  
**Tecnologias:** ChromaDB, OpenAI Embeddings  
**Formatos suportados:** PDF, TXT, DOC, DOCX

