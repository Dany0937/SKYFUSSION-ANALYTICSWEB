# Skyfusion Analytics - Shared Events Module

## Event Bus para Arquitectura de Microservicios

Módulo compartido entre Python (Geospatial Agent) y Node.js (Backend API) para el sistema de mensajería de eventos.

## Estructura

```
shared/events/
├── eventBus.js      # Implementación del bus de eventos
├── schemas.js       # Definiciones de esquemas de eventos
├── consumer.js      # Consumidor de eventos para Node.js
└── README.md        # Este archivo
```

## Tipos de Eventos

| Evento | Descripción | Payload |
|--------|-------------|---------|
| `IMAGENES_HISTORICAS_LISTAS` | Imágenes satelitales disponibles | dateRange, collections, imageCount |
| `IMAGEN_INDIVIDUAL_PROCESADA` | Imagen procesada individualmente | imageId, collection, cloudCover |
| `GEOSPATIAL_AGENT_ERROR` | Error en agente geoespacial | errorType, message, context |

## Uso en Node.js

### Consumer de Eventos

```javascript
import EventConsumer from './shared/events/consumer.js';

const consumer = new EventConsumer({
  watchDir: './data/events',
  backend: 'local'
});

await consumer.start();
```

### Bus de Eventos Directo

```javascript
import { createEventBus, EVENT_TYPES } from './shared/events/eventBus.js';

const eventBus = createEventBus({
  backend: 'local',
  storageDir: './data/events'
});

// Escuchar eventos
eventBus.onEvent(EVENT_TYPES.IMAGENES_HISTORICAS_LISTAS, (event) => {
  console.log('Imágenes disponibles:', event.payload.dataAvailability.imageCount);
});

// Emitir evento
eventBus.emit(EVENT_TYPES.MEASUREMENT_CREATED, { value: 42 });
```

## Backends Soportados

- **local**: File-based (desarrollo)
- **redis**: Redis Pub/Sub (producción)
- **rabbitmq**: RabbitMQ (producción)

## Variables de Entorno

```bash
EVENT_BACKEND=local
EVENT_DIR=./data/events
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Integración Python → Node.js

1. Python Geospatial Agent emite evento a `data/events/`
2. Evento se guarda en archivo `.jsonl`
3. Node.js Consumer detecta nuevo evento
4. Consumer procesa y emite a subscribers internos
5. Agentes downstream son notificados

## Autor

Skyfusion Analytics Team - Architecture Division
