/**
 * Event Consumer - Consumes events from Python agent
 * =================================================
 * 
 * This script monitors the event store directory for events
 * emitted by the Python Geospatial Agent.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createEventBus, EVENT_TYPES, validateEvent } from './eventBus.js';
import { formatEventSummary } from './schemas.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class EventConsumer {
  constructor(config = {}) {
    this.eventBus = createEventBus(config);
    this.watchDir = config.watchDir || path.join(process.cwd(), 'data', 'events');
    this.lastReadPositions = new Map();
    this.watcher = null;
  }

  async start() {
    console.log('🚀 Starting Event Consumer...');
    console.log(`📁 Watching: ${this.watchDir}\n`);

    this.setupHandlers();

    if (process.env.WATCH_MODE !== 'false') {
      this.startWatching();
    }

    await this.processExistingEvents();
  }

  setupHandlers() {
    this.eventBus.onEvent(EVENT_TYPES.IMAGENES_HISTORICAS_LISTAS, (event) => {
      console.log('\n📡 Event received: IMAGENES_HISTORICAS_LISTAS');
      this.handleHistoricalImagesReady(event);
    });

    this.eventBus.onEvent(EVENT_TYPES.GEOSPATIAL_AGENT_ERROR, (event) => {
      console.log('\n⚠️ Event received: GEOSPATIAL_AGENT_ERROR');
      this.handleError(event);
    });

    this.eventBus.onAny((event) => {
      console.log(`[${event.event_type}] ${formatEventSummary(event)}`);
    });
  }

  handleHistoricalImagesReady(event) {
    const { dataAvailability, processingConfig, basin, processingMetrics } = event.payload || {};

    console.log('\n╔═══════════════════════════════════════════════════════════╗');
    console.log('║  IMAGENES_HISTORICAS_LISTAS                               ║');
    console.log('╠═══════════════════════════════════════════════════════════╣');
    console.log(`║  📅 Período: ${dataAvailability?.dateRange?.start || 'N/A'} - ${dataAvailability?.dateRange?.end || 'N/A'}`);
    console.log(`║  🛰️  Imágenes: ${dataAvailability?.imageCount || 0}`);
    console.log(`║  📚 Colecciones: ${(dataAvailability?.collectionsUsed || []).length}`);
    console.log('╠═══════════════════════════════════════════════════════════╣');
    console.log(`║  ☁️  Filtro nubosidad: ${processingConfig?.cloudFilterApplied ? 'Sí' : 'No'}`);
    console.log(`║  📊 Máximo nubosidad: ${processingConfig?.maxCloudPercent || 'N/A'}%`);
    console.log('╠═══════════════════════════════════════════════════════════╣');
    console.log(`║  🏞️  Cuenca: ${basin?.name || 'N/A'}`);
    console.log(`║  📐 Área: ${basin?.areaHa || 'N/A'} ha`);
    console.log('╠═══════════════════════════════════════════════════════════╣');
    
    if (processingMetrics) {
      console.log(`║  📈 Años procesados: ${processingMetrics.yearsProcessed || 'N/A'}`);
      console.log(`║  ✅ Años con datos: ${processingMetrics.yearsWithData || 'N/A'}`);
      console.log(`║  ⏱️  Tiempo: ${processingMetrics.processingTimeSeconds || 'N/A'}s`);
    }
    
    console.log('╚═══════════════════════════════════════════════════════════╝');

    this.triggerDownstreamProcessing(event);
  }

  handleError(event) {
    console.error('\n❌ Geospatial Agent Error:');
    console.error(`   Type: ${event.payload?.errorType}`);
    console.error(`   Message: ${event.payload?.message}`);
    if (event.payload?.context) {
      console.error(`   Context:`, event.payload.context);
    }
  }

  triggerDownstreamProcessing(event) {
    console.log('\n🔄 Triggering downstream processing...');
    
    const downstreamEvents = [
      { type: 'VISION_AGENT_TRIGGER', payload: { source: event } },
      { type: 'ML_INGESTION_TRIGGER', payload: { source: event } }
    ];

    for (const { type, payload } of downstreamEvents) {
      this.eventBus.emit(type, payload, { triggeredBy: event.event_id });
      console.log(`   ✓ Emitted: ${type}`);
    }
  }

  startWatching() {
    if (!fs.existsSync(this.watchDir)) {
      fs.mkdirSync(this.watchDir, { recursive: true });
    }

    this.watcher = fs.watch(this.watchDir, (eventType, filename) => {
      if (filename && filename.endsWith('.jsonl')) {
        this.processFile(filename);
      }
    });

    console.log(`👁️  Watching for new events...\n`);
  }

  async processExistingEvents() {
    console.log('📋 Processing existing events...');

    const files = fs.readdirSync(this.watchDir)
      .filter(f => f.endsWith('.jsonl'))
      .sort();

    for (const file of files) {
      await this.processFile(file);
    }
  }

  async processFile(filename) {
    const filepath = path.join(this.watchDir, filename);
    const key = filename;

    let lastPosition = this.lastReadPositions.get(key) || 0;

    try {
      const content = fs.readFileSync(filepath, 'utf-8');
      const lines = content.trim().split('\n').filter(l => l);

      if (lines.length > lastPosition) {
        const newLines = lines.slice(lastPosition);
        
        for (const line of newLines) {
          try {
            const event = JSON.parse(line);
            const validation = validateEvent(event);
            
            if (validation.valid || validation.warnings) {
              this.eventBus.emit(event.event_type, event.payload, event.metadata);
            }
          } catch (e) {
            // Skip invalid JSON
          }
        }

        this.lastReadPositions.set(key, lines.length);
      }
    } catch (e) {
      console.error(`Error processing file ${filename}:`, e.message);
    }
  }

  stop() {
    if (this.watcher) {
      this.watcher.close();
    }
    console.log('\n🛑 Event Consumer stopped');
  }
}

async function main() {
  const consumer = new EventConsumer({
    backend: process.env.EVENT_BACKEND || 'local',
    watchDir: process.env.EVENT_DIR || './data/events'
  });

  process.on('SIGINT', () => {
    consumer.stop();
    process.exit(0);
  });

  await consumer.start();
}

main().catch(console.error);
