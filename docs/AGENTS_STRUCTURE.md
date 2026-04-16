# Estructura de Agentes - Skyfusion Analytics

## Índice

1. [Visión General](#visión-general)
2. [Arquitectura de Agentes](#arquitectura-de-agentes)
3. [Agente de Ingesta de Datos](#agente-de-ingesta-de-datos)
4. [Agente de Análisis](#agente-de-análisis)
5. [Agente de Predicción](#agente-de-predicción)
6. [Comunicación entre Agentes](#comunicación-entre-agentes)

---

## Visión General

Los agentes son componentes autónomos que manejan responsabilidades específicas dentro de Skyfusion Analytics. Cada agente:

- Extiende `EventEmitter` para comunicación basada en eventos
- Utiliza un sistema de logging centralizado
- Implementa un ciclo de vida con estados (`idle`, `ready`, `processing`)
- Provee métodos de `initialize()`, operaciones específicas y `getStatus()`

---

## Arquitectura de Agentes

```
┌─────────────────────────────────────────────────────────┐
│                    PredictionAgent                       │
│  ├── predictionHorizon: 24                              │
│  ├── confidenceLevel: 0.95                              │
│  └── models: Map<string, Model>                         │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────┐
│                     AnalysisAgent                        │
│  ├── maxConcurrent: 3                                   │
│  └── timeout: 30000                                     │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────┐
│                 DataIngestionAgent                      │
│  ├── batchSize: 100                                     │
│  ├── flushInterval: 5000                                │
│  └── sources: Array<string>                             │
└─────────────────────────────────────────────────────────┘
```

---

## Agente de Ingesta de Datos

**Archivo:** `agents/data-ingestion-agent.js`

### Clase: `DataIngestionAgent`

#### Constructor
```javascript
constructor() {
  super();
  this.status = 'idle';
  this.sources = [];
}
```

#### Configuración por Defecto
| Parámetro | Tipo | Valor |
|-----------|------|-------|
| `batchSize` | number | 100 |
| `flushInterval` | number | 5000 |

#### Métodos

##### `initialize(config)`
Inicializa el agente con configuración personalizada.

```javascript
await agent.initialize({ batchSize: 200 });
```

##### `ingest(source, data)`
Procesa datos de una fuente específica.

```javascript
await agent.ingest('sensor_01', [...data]);
```

##### `getStatus()`
Retorna el estado actual del agente.

#### Eventos Emitidos
| Evento | Payload | Descripción |
|--------|---------|-------------|
| `data:ingested` | `{ source, count }` | Datos ingestionados exitosamente |

---

## Agente de Análisis

**Archivo:** `agents/analysis-agent.js`

### Clase: `AnalysisAgent`

#### Constructor
```javascript
constructor() {
  super();
  this.status = 'idle';
}
```

#### Configuración por Defecto
| Parámetro | Tipo | Valor |
|-----------|------|-------|
| `maxConcurrent` | number | 3 |
| `timeout` | number | 30000 |

#### Métodos

##### `initialize(config)`
Inicializa el agente con configuración personalizada.

```javascript
await agent.initialize({ maxConcurrent: 5 });
```

##### `analyze(data, analysisType)`
Ejecuta un tipo específico de análisis.

```javascript
await agent.analyze(data, 'NDVI');
```

##### `getStatus()`
Retorna el estado actual del agente.

#### Tipos de Análisis Soportados
- `NDVI` - Índice de Vegetación
- `NDWI` - Índice de Agua
- Custom (extensible)

#### Eventos Emitidos
| Evento | Payload | Descripción |
|--------|---------|-------------|
| `analysis:started` | `{ analysisType }` | Análisis iniciado |
| `analysis:completed` | `{ analysisType, success }` | Análisis completado |

---

## Agente de Predicción

**Archivo:** `agents/prediction-agent.js`

### Clase: `PredictionAgent`

#### Constructor
```javascript
constructor() {
  super();
  this.status = 'idle';
  this.models = new Map();
}
```

#### Configuración por Defecto
| Parámetro | Tipo | Valor |
|-----------|------|-------|
| `predictionHorizon` | number | 24 |
| `confidenceLevel` | number | 0.95 |

#### Métodos

##### `initialize(config)`
Inicializa el agente con configuración personalizada.

```javascript
await agent.initialize({ predictionHorizon: 48 });
```

##### `loadModel(modelName)`
Carga un modelo de predicción en memoria.

```javascript
await agent.loadModel('lstm_v1');
```

##### `predict(inputData, modelName)`
Genera predicciones usando el modelo especificado.

```javascript
const result = await agent.predict(data, 'lstm_v1');
// Returns: { success, predictions, confidenceInterval, alertLevel }
```

##### `getStatus()`
Retorna el estado actual del agente incluyendo modelos cargados.

#### Eventos Emitidos
| Evento | Payload | Descripción |
|--------|---------|-------------|
| `prediction:requested` | `{ modelName }` | Predicción solicitada |
| `prediction:completed` | `{ modelName }` | Predicción completada |

---

## Comunicación entre Agentes

### Sistema de Eventos

Todos los agentes heredan de `EventEmitter`:

```
Agent (EventEmitter)
├── status: string
├── initialize(config)
├── getStatus()
└── emit(event, payload)
```

### Flujo de Comunicación Típico

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

### Estados de Agente

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

---

## Tabla Comparativa de Agentes

| Agente | Responsabilidad | Eventos | Configuración |
|--------|----------------|---------|---------------|
| `DataIngestionAgent` | Ingesta de datos | `data:ingested` | `batchSize`, `flushInterval` |
| `AnalysisAgent` | Análisis NDVI/NDWI | `analysis:started`, `analysis:completed` | `maxConcurrent`, `timeout` |
| `PredictionAgent` | Predicciones ML | `prediction:requested`, `prediction:completed` | `predictionHorizon`, `confidenceLevel` |
