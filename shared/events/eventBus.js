/**
 * Skyfusion Analytics - Event Bus Service
 * ======================================
 * 
 * Sistema de eventos para la arquitectura de microservicios.
 * 
 * Soporta:
 * - Modo Local: File-based event store (para desarrollo)
 * - Modo Redis: Pub/Sub para producción
 * - Modo RabbitMQ: Message broker para producción
 * 
 * Evento principal: IMAGENES_HISTORICAS_LISTAS
 */

import fs from 'fs';
import path from 'path';
import { EventEmitter } from 'events';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const EVENT_TYPES = {
  IMAGENES_HISTORICAS_LISTAS: 'IMAGENES_HISTORICAS_LISTAS',
  IMAGEN_INDIVIDUAL_PROCESADA: 'IMAGEN_INDIVIDUAL_PROCESADA',
  GEOSPATIAL_AGENT_ERROR: 'GEOSPATIAL_AGENT_ERROR',
  MEASUREMENT_CREATED: 'measurement:created',
  ZONE_CREATED: 'zone:created',
  ALERT_GENERATED: 'alert:generated',
  ANALYSIS_COMPLETED: 'analysis:completed',
  PREDICTION_COMPLETED: 'prediction:completed',
  DATA_INGESTED: 'data:ingested'
};

export const BACKENDS = {
  LOCAL: 'local',
  REDIS: 'redis',
  RABBITMQ: 'rabbitmq'
};

class EventStore {
  constructor(config = {}) {
    this.storageDir = config.storageDir || path.join(process.cwd(), 'data', 'events');
    this.ensureStorageDir();
  }

  ensureStorageDir() {
    if (!fs.existsSync(this.storageDir)) {
      fs.mkdirSync(this.storageDir, { recursive: true });
    }
  }

  getFilename(date = new Date()) {
    const dateStr = date.toISOString().split('T')[0].replace(/-/g, '');
    return path.join(this.storageDir, `events_${dateStr}.jsonl`);
  }

  append(event) {
    const filename = this.getFilename();
    const line = JSON.stringify(event) + '\n';
    fs.appendFileSync(filename, line);
  }

  readEvents(options = {}) {
    const { eventType, since, limit = 100 } = options;
    const events = [];
    const today = new Date();
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      
      if (since && date < since) break;
      
      const filename = this.getFilename(date);
      if (fs.existsSync(filename)) {
        const content = fs.readFileSync(filename, 'utf-8');
        const lines = content.trim().split('\n').filter(l => l);
        
        for (const line of lines) {
          try {
            const event = JSON.parse(line);
            if (eventType && event.event_type !== eventType) continue;
            events.push(event);
          } catch (e) {
            // Skip invalid lines
          }
        }
      }
    }

    return events.slice(-limit);
  }

  getLastEvent(eventType = null) {
    const events = this.readEvents({ eventType, limit: 1 });
    return events[0] || null;
  }
}

export class LocalEventBus extends EventEmitter {
  constructor(config = {}) {
    super();
    this.eventStore = new EventStore(config);
  }

  emit(eventType, payload, metadata = {}) {
    const event = {
      event_id: this.generateId(),
      event_type: eventType,
      timestamp: new Date().toISOString(),
      source: 'node_backend',
      version: '1.0.0',
      payload,
      metadata
    };

    this.eventStore.append(event);
    super.emit(eventType, event);
    super.emit('*', event);

    return event;
  }

  generateId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  onEvent(eventType, handler) {
    this.on(eventType, handler);
    return () => this.off(eventType, handler);
  }

  onAny(handler) {
    this.on('*', handler);
    return () => this.off('*', handler);
  }
}

export class RedisEventBus extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = config;
    this.channel = config.channel || 'skyfusion:events';
    this.redis = null;
    this.localStore = new EventStore(config);
    this.connected = false;
  }

  async connect() {
    try {
      const { createClient } = await import('redis');
      
      this.redis = createClient({
        socket: {
          host: this.config.host || 'localhost',
          port: this.config.port || 6379
        }
      });

      this.redis.on('error', (err) => {
        console.error('Redis error:', err);
        this.connected = false;
      });

      await this.redis.connect();
      this.connected = true;
      
      this.redis.subscribe(this.channel, (message) => {
        try {
          const event = JSON.parse(message);
          this.emit(event.event_type, event);
          this.emit('*', event);
        } catch (e) {
          console.error('Error parsing Redis message:', e);
        }
      });

      console.log('Connected to Redis');
      return true;
    } catch (error) {
      console.warn('Redis connection failed, falling back to local:', error.message);
      this.connected = false;
      return false;
    }
  }

  async emit(eventType, payload, metadata = {}) {
    const event = {
      event_id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      event_type: eventType,
      timestamp: new Date().toISOString(),
      source: 'node_backend',
      version: '1.0.0',
      payload,
      metadata
    };

    this.localStore.append(event);

    if (this.connected && this.redis) {
      try {
        await this.redis.publish(this.channel, JSON.stringify(event));
      } catch (e) {
        console.error('Error publishing to Redis:', e);
      }
    }

    return event;
  }
}

export class EventBusFactory {
  static create(backend = BACKENDS.LOCAL, config = {}) {
    switch (backend) {
      case BACKENDS.REDIS:
        return new RedisEventBus(config);
      default:
        return new LocalEventBus(config);
    }
  }
}

export function createEventBus(config = {}) {
  const backend = config.backend || process.env.EVENT_BACKEND || BACKENDS.LOCAL;
  return EventBusFactory.create(backend, config);
}

export default createEventBus;
