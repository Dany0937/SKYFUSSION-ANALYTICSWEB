import { Ano } from '../models/Ano.js';
import { MedicionCaudal } from '../models/MedicionCaudal.js';
import { createLogger } from '../utils/logger.js';
import { eventBus, EVENTS } from './eventBus.js';

const logger = createLogger('services:ingestion');

export class IngestionService {
  constructor() {
    this.ingestionBuffer = [];
    this.bufferSize = 100;
    this.flushInterval = 5000;
    this.startFlushTimer();
  }

  startFlushTimer() {
    this.flushTimer = setInterval(() => {
      this.flushBuffer();
    }, this.flushInterval);
  }

  stopFlushTimer() {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
  }

  async flushBuffer() {
    if (this.ingestionBuffer.length === 0) return;

    const batch = [...this.ingestionBuffer];
    this.ingestionBuffer = [];

    logger.info('Flushing ingestion buffer', { count: batch.length });

    for (const item of batch) {
      try {
        await this.processMeasurement(item);
      } catch (error) {
        logger.error('Error processing buffered measurement', { error: error.message });
      }
    }

    eventBus.emit(EVENTS.DATA_INGESTED, { count: batch.length });
  }

  async processMeasurement(data) {
    const { anoId, anoNumero, medicion } = data;

    let year = await Ano.findByYear(anoNumero);
    
    if (!year) {
      year = await Ano.create({ numero: anoNumero });
      logger.info('Created new year', { anoId: year.id, numero: anoNumero });
    }

    const measurement = await MedicionCaudal.create({
      ...medicion,
      anoId: year.id
    });

    return measurement;
  }

  bufferMeasurement(data) {
    this.ingestionBuffer.push(data);

    if (this.ingestionBuffer.length >= this.bufferSize) {
      this.flushBuffer();
    }

    return { buffered: true, bufferSize: this.ingestionBuffer.length };
  }

  async ingestBatch(measurements) {
    const results = [];
    
    for (const item of measurements) {
      try {
        const result = await this.processMeasurement(item);
        results.push({ success: true, data: result });
      } catch (error) {
        results.push({ success: false, error: error.message });
      }
    }

    eventBus.emit(EVENTS.DATA_INGESTED, { count: results.length });

    return {
      processed: results.filter(r => r.success).length,
      failed: results.filter(r => !r.success).length,
      results
    };
  }

  async createYear(data) {
    return Ano.create(data);
  }

  async getAllYears() {
    return Ano.findAll();
  }

  async getYearById(id) {
    return Ano.findById(id);
  }

  async getYearMeasurements(anoId, options = {}) {
    return MedicionCaudal.findByAno(anoId, options);
  }

  async getMeasurementsByDateRange(anoId, startDate, endDate) {
    return MedicionCaudal.findByDateRange(anoId, startDate, endDate);
  }

  async getMeasurementStatistics(anoId) {
    return MedicionCaudal.getStatistics(anoId);
  }

  getBufferStatus() {
    return {
      currentSize: this.ingestionBuffer.length,
      maxSize: this.bufferSize,
      flushIntervalMs: this.flushInterval
    };
  }
}

export const ingestionService = new IngestionService();
