---
title: Orchestrator y Event Bus
description: Orquestación de agentes y comunicación mediante RabbitMQ.
order: 6
---

# Orchestrator y Event Bus

El **Orchestrator** es el componente central que coordina el ciclo de vida de los agentes y la comunicación mediante el bus de eventos.

## Arquitectura de Eventos

Todos los agentes heredan de `EventEmitter` y se comunican a través de RabbitMQ:

```
Agent (EventEmitter)
├── status: string
├── initialize(config)
├── getStatus()
└── emit(event, payload)
```

## Flujo de Comunicación

```javascript
// Suscripción a eventos
predictionAgent.on('prediction:completed', ({ modelName }) => {
  console.log(`Predicción completada con ${modelName}`);
});

// Encadenamiento de agentes
dataIngestionAgent.on('data:ingested', async ({ source, count }) => {
  await analysisAgent.analyze(data, 'NDVI');
  await predictionAgent.predict(data);
});
```

## Estados de Agente

```
     ┌──────────┐
     │  'idle'  │ ◄── Estado inicial
     └────┬─────┘
          │ initialize()
          ▼
     ┌──────────┐
     │ 'ready'  │ ◄── Listo para procesar
     └────┬─────┘
          │ Método de operación
          ▼
     ┌─────────────┐
     │ 'processing'│ ◄── Procesando
     └──────┬───────┘
            │ Completado
            ▼
        'ready'
```

## Agentes Node.js

| Agente | Responsabilidad | Skills |
|--------|----------------|--------|
| **DataIngestionAgent** | Ingesta de datos IoT | `geo_tools` |
| **AnalysisAgent** | Cálculos NDVI/NDWI | `geo_tools`, `vision_tools` |
| **PredictionAgent** | Predicciones ML | `ml_tools` |
| **AgentOrchestrator** | Orquestación + ciclo de vida | Todos |

## Skills Reutilizables

| Skill | Descripción |
|-------|-------------|
| `geo_tools` | Cálculos geoespaciales y validación GeoJSON |
| `vision_tools` | Utilidades de procesamiento de imágenes |
| `ml_tools` | Utilidades de machine learning |
