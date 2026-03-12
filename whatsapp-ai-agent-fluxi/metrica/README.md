# Módulo Métrica 📊

## 📖 Visão Geral

O módulo `metrica` fornece estatísticas e analytics sobre o uso do sistema, mensagens processadas, performance dos agentes e consumo de tokens.

## 🎯 Objetivo

- Métricas gerais do sistema
- Performance por sessão
- Estatísticas por período
- Taxa de resposta
- Consumo de tokens
- Tempo médio de processamento
- Clientes únicos

## 📂 Componentes

### Service (metrica_service.py)

**Funções Principais:**

#### **1. Métricas Gerais**
```python
MetricaService.obter_metricas_gerais(db)
```

Retorna:
```python
{
    "sessoes": {
        "total": 5,
        "ativas": 4,
        "conectadas": 3
    },
    "mensagens": {
        "total": 1250,
        "recebidas": 625,
        "enviadas": 625,
        "processadas": 620,
        "respondidas": 615
    },
    "performance": {
        "taxa_sucesso": 98.4,  # % de mensagens respondidas
        "clientes_unicos": 45
    }
}
```

#### **2. Métricas por Sessão**
```python
MetricaService.obter_metricas_sessao(db, sessao_id)
```

Retorna:
```python
{
    "mensagens": {
        "total": 250,
        "recebidas": 125,
        "respondidas": 120,
        "com_imagem": 15,
        "com_ferramentas": 45
    },
    "performance": {
        "taxa_resposta": 96.0,
        "tempo_medio_ms": 1250,
        "clientes_unicos": 12
    },
    "tokens": {
        "input_total": 45000,
        "output_total": 32000,
        "total": 77000
    }
}
```

#### **3. Métricas por Período**
```python
MetricaService.obter_metricas_periodo(
    db,
    sessao_id=1,  # opcional
    dias=7
)
```

Retorna estatísticas dos últimos N dias com gráficos de evolução.

## 📈 Métricas Calculadas

### Taxa de Sucesso
```
(mensagens_respondidas / mensagens_recebidas) * 100
```

### Tempo Médio
```
AVG(resposta_tempo_ms) WHERE respondida = True
```

### Tokens por Mensagem
```
AVG(resposta_tokens_input + resposta_tokens_output)
```

### Custo Estimado
```python
# OpenAI pricing
input_custo = (tokens_input / 1_000_000) * preco_input
output_custo = (tokens_output / 1_000_000) * preco_output
total = input_custo + output_custo
```

## 🖥️ Interface

### Páginas (metrica_frontend_router.py)

- `/metricas/` - Dashboard geral
- `/metricas/sessao/{id}` - Métricas da sessão
- `/metricas/periodo` - Estatísticas por período

**Visualizações:**
- Gráficos de mensagens por dia
- Taxa de resposta
- Tokens consumidos
- Top clientes
- Ferramentas mais usadas

## 💡 Exemplo de Uso

```python
# Dashboard principal
metricas = MetricaService.obter_metricas_gerais(db)

print(f"Taxa de sucesso: {metricas['performance']['taxa_sucesso']}%")
print(f"Total de clientes: {metricas['performance']['clientes_unicos']}")

# Métricas de uma sessão
metricas_sessao = MetricaService.obter_metricas_sessao(db, sessao_id=1)

print(f"Tokens consumidos: {metricas_sessao['tokens']['total']}")
print(f"Tempo médio: {metricas_sessao['performance']['tempo_medio_ms']}ms")
```

## 📊 Análises Disponíveis

- ✅ Total de mensagens (recebidas/enviadas)
- ✅ Taxa de sucesso de respostas
- ✅ Tempo médio de processamento
- ✅ Tokens consumidos (input/output)
- ✅ Clientes únicos atendidos
- ✅ Mensagens com imagens
- ✅ Mensagens com ferramentas
- ✅ Evolução temporal (gráficos)
- ✅ Comparação entre sessões

---

**Módulo:** metrica  
**Tipo:** Analytics & Monitoring

