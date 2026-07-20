---
title: Reglas del Sistema de Agentes
description: Protocolo de comunicación, independencia y ciclo de vida de los agentes.
order: 4
---

# Reglas del Sistema de Agentes

## Protocolo de Comunicación

Todos los agentes se comunican exclusivamente mediante el **Event Bus (RabbitMQ)**.

### Reglas

1. **Ningún agente debe conocer la estructura interna de otro**
2. **Solo reaccionan a los eventos del Orchestrator**
3. **Cada agente publica un único tipo de evento de salida**
4. **Los eventos son inmutables** — una vez publicados no se modifican

## Ciclo de Vida

```
     ┌──────────┐
     │  'idle'  │
     └────┬─────┘
          │ initialize()
          ▼
     ┌──────────┐
     │ 'ready'  │
     └────┬─────┘
          │ Evento de entrada
          ▼
     ┌─────────────┐
     │ 'processing'│
     └──────┬───────┘
            │ Evento de salida
            ▼
        'ready'
```

## Eventos del Sistema

| Evento | Emisor | Receptor | Descripción |
|--------|--------|----------|-------------|
| `analysis:requested` | Backend | GeospatialAgent | Solicitar análisis |
| `data:ingested` | GeospatialAgent | VisionAgent | Datos listos |
| `analysis:completed` | VisionAgent | OracleAgent | Análisis listo |
| `prediction:completed` | OracleAgent | ReportingAgent | Predicción lista |
| `report:ready` | ReportingAgent | Backend | Reporte generado |

## Tolerancia a Fallos

- Si un agente falla, el evento permanece en la cola para reintento
- El Orchestrator monitorea el estado de todos los agentes (`idle`, `ready`, `processing`)
- Checkpoints automáticos cada 15 min para recuperación de modelos ML
