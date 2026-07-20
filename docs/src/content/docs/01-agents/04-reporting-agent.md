---
title: ReportingAgent
description: Generación automatizada de reportes usando modelos de lenguaje (LLM).
order: 5
---

# ReportingAgent

Transforma los resultados técnicos en reportes comprensibles para investigadores y usuarios finales mediante modelos de lenguaje.

## Funciones

- Interpretación de resultados
- Generación de narrativas
- Elaboración de conclusiones
- Construcción de reportes automáticos

## Tecnologías

| Tecnología | Propósito |
|------------|-----------|
| Ollama (Llama 3.2) | LLM local para generación de reportes (costo $0) |
| Azure OpenAI GPT-4 | LLM cloud para reportes críticos (costo $3,000/mes) |
| Anthropic Claude | Alternativa cloud |

## Eventos

| Tipo | Dirección | Descripción |
|------|-----------|-------------|
| `prediction:completed` | Entrada | Predicción lista para reportar |
| `report:ready` | Salida | Reporte generado y disponible |

## Implementación

```
agents/python/reporting_agent/
├── agent.py
└── requirements.txt
```
