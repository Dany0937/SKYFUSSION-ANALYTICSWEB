# Plan de Integración: Backend → APIs Externas → Agentes

## Archivos a crear (7) y modificar (5)

### FASE 1: Infraestructura de Comunicación

**1.1 CREAR: services/backend-node/src/config/externalApis.js**
```javascript
import dotenv from 'dotenv';
import { createLogger } from '../utils/logger.js';

dotenv.config();
const logger = createLogger('config:external');

export const externalApiConfig = {
  rabbitmq: {
    host: process.env.RABBITMQ_HOST || 'localhost',
    port: parseInt(process.env.RABBITMQ_PORT || '5672'),
    user: process.env.RABBITMQ_USER || 'skyfusion',
    password: process.env.RABBITMQ_PASS || 'skyfusion_mq',
    exchange: 'skyfusion_events',
    exchangeType: 'topic',
    queuePrefix: 'backend'
  },
  gee: {
    serviceAccount: process.env.GEE_SERVICE_ACCOUNT || '',
    keyPath: process.env.GEE_KEY_PATH || '',
    project: process.env.GEE_PROJECT || 'skyfusion-analytics'
  },
  openai: {
    apiKey: process.env.OPENAI_API_KEY || '',
    model: process.env.OPENAI_MODEL || 'gpt-4',
    maxTokens: parseInt(process.env.OPENAI_MAX_TOKENS || '2000'),
    temperature: parseFloat(process.env.OPENAI_TEMPERATURE || '0.7')
  }
};
```

**1.2 CREAR: services/backend-node/src/services/rabbitmqClient.js**
- Clase `RabbitMQClient` con:
  - `connect()` - Conexión al broker, declara exchange `skyfusion_events`
  - `publish(eventType, payload)` - Publica evento
  - `subscribe(eventType, handler)` - Consume eventos
  - `disconnect()` - Cierra conexión
- Manejador de reconexión automática con backoff exponencial

**1.3 MODIFICAR: services/backend-node/.env**
- Agregar credenciales: RABBITMQ, GEE, OPENAI

**1.4 MODIFICAR: services/backend-node/package.json**
- Agregar dependencias: `amqplib`, `openai`

### FASE 2: API Clients Externos

**2.1 CREAR: services/backend-node/src/services/geeClient.js**
- Clase `GEEClientBridge` que:
  - Envía `analysis:requested` a RabbitMQ
  - Escucha `data:ingested` para recibir resultados
  - Timeout de 120s por request
  - Guarda scenes en Neo4j

**2.2 CREAR: services/backend-node/src/services/openaiClient.js**
- Clase `OpenAIClient` con:
  - `generateReport(metrics, alerts, zoneInfo)` → texto narrativo
  - `summarizeAlert(alertData)` → resumen ejecutivo

**2.3 CREAR: services/backend-node/src/services/agentOrchestrator.js**
- Clase `AgentOrchestrator` que:
  - Mantiene estado de pipelines activos (Map<requestId, PipelineState>)
  - Ejecuta secuencia: GEE → Vision → Oracle → Report
  - Maneja timeouts, reintentos, y errores por agente
  - Emite eventos de progreso

### FASE 3: Modelos Neo4j

**3.1 CREAR: services/backend-node/src/models/Scene.js**
```cypher
(:Scene {
  id, sceneId, collection, date, cloudCover,
  ndviMean, ndviStd, ndwiMean, ndwiStd,
  bands[], scale, blobUrl, ingestedAt
})
-[:BELONGS_TO]->(:Zone)
-[:OBSERVED_ON]->(:Ano)
```

**3.2 CREAR: services/backend-node/src/models/Prediction.js**
```cypher
(:Prediction {
  id, flowMean, flowStd, confidenceLower, confidenceUpper,
  alertLevel, modelVersion, createdAt
})
-[:FOR_ZONE]->(:Zone)
-[:FOR_YEAR]->(:Ano)
```

**3.3 CREAR: services/backend-node/src/models/Report.js**
```cypher
(:Report {
  id, title, narrative, metrics, recommendations,
  alertLevel, modelUsed, createdAt
})
-[:FOR_ZONE]->(:Zone)
```

### FASE 4: API Endpoints

**4.1 CREAR: services/backend-node/src/controllers/pipelineController.js**
- `startPipeline(req, res)` - Inicia pipeline completo
- `getPipelineStatus(req, res)` - Estado de pipeline
- `queryGeospatial(req, res)` - Solo GEE directo
- `generateReport(req, res)` - Reporte IA

**4.2 CREAR: services/backend-node/src/routes/v1/pipeline.js**
```javascript
router.post('/analyze', pipelineController.startPipeline);
router.get('/:requestId/status', pipelineController.getPipelineStatus);
router.post('/geospatial/query', pipelineController.queryGeospatial);
router.post('/reports/generate', pipelineController.generateReport);
```

**4.3 MODIFICAR: services/backend-node/src/routes/index.js**
- Agregar: `router.use('/pipeline', pipelineRouter);`

**4.4 MODIFICAR: services/backend-node/src/app.js**
- Agregar conexión RabbitMQ al startup
- Inicializar agentOrchestrator en el lifecycle

---

## Pipeline Completo (flujo de datos)

```
POST /api/v1/pipeline/analyze
  │
  ▼
AgentOrchestrator.startPipeline(zoneId, dates)
  │
  ├─► [RabbitMQ] analysis:requested
  │     └─► Geospatial Agent → GEE → scenes
  │     └─► [RabbitMQ] data:ingested
  │     └─► Backend guarda Scene[] en Neo4j
  │
  ├─► [RabbitMQ] analysis:requested (vision)
  │     └─► Vision Agent → NDVI/NDWI
  │     └─► [RabbitMQ] imagery:processed
  │     └─► Backend actualiza Scene con índices
  │
  ├─► [RabbitMQ] prediction:requested
  │     └─► Oracle Agent → LSTM → caudal
  │     └─► [RabbitMQ] prediction:completed
  │     └─► Backend guarda Prediction en Neo4j
  │
  ├─► [OpenAI API] generateReport()
  │     └─► Backend guarda Report en Neo4j
  │
  └─► Response 200 { requestId, status: "completed", results }
```

---

## Criterios de Éxito

```bash
# Códigos de estado HTTP correctos
POST /api/v1/pipeline/analyze → 202 Accepted { requestId }
GET  /api/v1/pipeline/:id     → 200 OK { status, results }

# RabbitMQ conectado
backend: [INFO] RabbitMQ connected to skyfusion_events

# Pipeline completo en < 5s (modo mock)
pipeline_xxx → Geospatial(ok) → Vision(ok) → Oracle(ok) → Report(ok)

# Datos en Neo4j
MATCH (s:Scene) RETURN count(s)  →  > 0
MATCH (p:Prediction) RETURN p    →  { flowMean > 0 }
MATCH (r:Report) RETURN r        →  { narrative != null }
```

---

## Dependencias a instalar

```bash
cd services/backend-node
npm install amqplib openai
```
