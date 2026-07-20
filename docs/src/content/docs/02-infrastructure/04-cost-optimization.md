---
title: Optimización de Costos Azure
description: Estrategias detalladas para reducir costos de infraestructura cloud.
order: 4
---

# Plan de Optimización de Costos Azure

> **Costo Original Estimado:** $7,200/mes
> **Costo Optimizado:** $2,200 - $2,800/mes (**~65% ahorro**)

## Estrategias de Optimización

### Spot Instances para GPU (Ahorro: ~$2,130/mes)

| Modo | SKU | Precio/hr | Costo/mes | Ahorro |
|------|-----|-----------|-----------|--------|
| On-Demand | NC6s_v3 | $4.17 | $3,043.20 | — |
| **Spot (Low)** | NC6s_v3 | **$1.25** | **$912.50** | **70%** |

**Riesgo:** Desalojo con 30s aviso. Mitigación con checkpoints automáticos cada 15 min y cola RabbitMQ.

### Local LLM en lugar de Azure OpenAI (Ahorro: ~$2,700/mes)

| Modelo | Parámetros | Costo |
|--------|------------|-------|
| GPT-4 (Azure) | ~1.7T | $3,000/mes |
| **Llama 3.2** (Ollama) | 8B | **$0** |
| **Mistral 7B** (Ollama) | 7B | **$0** |

### ML Compute Cluster (Ahorro: ~$400/mes)

Auto-escalado de 0 a 4 nodos con shutdown por inactividad.

### PostgreSQL Unificado (Ahorro: ~$600/mes)

Consolidación de Neo4j + PostgreSQL en PostgreSQL + PostGIS + pgRouting.

### Storage Tiering (Ahorro: ~$40/mes)

Lifecycle management automático: Hot → Cool → Cold → Archive.

### Azure Functions (Ahorro: ~$120/mes)

Migración de endpoints simples a funciones serverless.
