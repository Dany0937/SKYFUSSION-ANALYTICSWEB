import { EventEmitter } from 'events';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('eventBus');

export const EVENTS = {
  MEASUREMENT_CREATED: 'measurement:created',
  MEASUREMENT_DELETED: 'measurement:deleted',
  ZONE_CREATED: 'zone:created',
  ZONE_UPDATED: 'zone:updated',
  STATION_CREATED: 'station:created',
  ALERT_GENERATED: 'alert:generated',
  ANALYSIS_STARTED: 'analysis:started',
  ANALYSIS_COMPLETED: 'analysis:completed',
  PREDICTION_REQUESTED: 'prediction:requested',
  PREDICTION_COMPLETED: 'prediction:completed',
  SYNC_REQUIRED: 'sync:required',
  DATA_INGESTED: 'data:ingested'
};

class EventBus extends EventEmitter {
  constructor() {
    super();
    this.setMaxListeners(100);
    this.registerDefaultHandlers();
  }

  registerDefaultHandlers() {
    this.on(EVENTS.MEASUREMENT_CREATED, (data) => {
      logger.info('Event: Measurement created', { 
        type: data.type, 
        id: data.id 
      });
    });

    this.on(EVENTS.MEASUREMENT_DELETED, (data) => {
      logger.info('Event: Measurement deleted', { 
        type: data.type, 
        id: data.id 
      });
    });

    this.on(EVENTS.ALERT_GENERATED, (data) => {
      logger.warn('Event: Alert generated', { 
        level: data.level, 
        message: data.message 
      });
    });

    this.on(EVENTS.ANALYSIS_COMPLETED, (data) => {
      logger.info('Event: Analysis completed', { 
        analysisType: data.analysisType,
        zoneId: data.zoneId 
      });
    });

    this.on(EVENTS.SYNC_REQUIRED, (data) => {
      logger.info('Event: Sync required', { 
        source: data.source,
        timestamp: data.timestamp 
      });
    });
  }

  publish(event, payload) {
    this.emit(event, {
      ...payload,
      publishedAt: new Date().toISOString()
    });
  }

  subscribe(event, handler) {
    this.on(event, handler);
    return () => this.off(event, handler);
  }

  once(event, handler) {
    return new Promise((resolve) => {
      this.once(event, (data) => {
        handler(data);
        resolve(data);
      });
    });
  }

  waitFor(event, timeoutMs = 30000) {
    return Promise.race([
      this.once(event),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error(`Timeout waiting for ${event}`)), timeoutMs)
      )
    ]);
  }
}

export const eventBus = new EventBus();

export class EventStore {
  constructor() {
    this.events = [];
    this.maxStoredEvents = 1000;
  }

  record(event, data) {
    const record = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      event,
      data,
      recordedAt: new Date().toISOString()
    };

    this.events.push(record);

    if (this.events.length > this.maxStoredEvents) {
      this.events = this.events.slice(-this.maxStoredEvents);
    }

    return record;
  }

  getEvents(filter = {}) {
    let filtered = [...this.events];

    if (filter.event) {
      filtered = filtered.filter(e => e.event === filter.event);
    }

    if (filter.since) {
      filtered = filtered.filter(e => e.recordedAt >= filter.since);
    }

    if (filter.until) {
      filtered = filtered.filter(e => e.recordedAt <= filter.until);
    }

    return filtered;
  }

  clear() {
    this.events = [];
  }
}

export const eventStore = new EventStore();

eventBus.on('*', (data, event) => {
  eventStore.record(event, data);
});

export default eventBus;
