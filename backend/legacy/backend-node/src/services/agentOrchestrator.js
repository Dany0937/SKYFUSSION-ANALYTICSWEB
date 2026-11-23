import { v4 as uuidv4 } from 'uuid';
import { createLogger } from '../utils/logger.js';
import { eventBus, EVENTS } from './eventBus.js';
import { rabbitMQClient, AGENT_EVENTS } from './rabbitmqClient.js';
import { geeClient } from './geeClient.js';
import { openAIClient } from './openaiClient.js';
import config from '../config/externalApis.js';

const logger = createLogger('services:orchestrator');

export class AgentOrchestrator {
  constructor() {
    this.activePipelines = new Map();
    this.completedPipelines = [];
    this.maxCompleted = 100;
    this.agentStatuses = new Map();
  }

  async startPipeline(pipelineConfig) {
    const pipelineId = pipelineConfig.pipelineId || uuidv4();
    const startTime = Date.now();

    logger.info('Pipeline started', { pipelineId, type: pipelineConfig.type });

    const pipeline = {
      id: pipelineId,
      type: pipelineConfig.type || 'full_analysis',
      zoneId: pipelineConfig.zoneId,
      config: pipelineConfig,
      steps: [],
      status: 'running',
      startTime,
      errors: []
    };

    this.activePipelines.set(pipelineId, pipeline);

    eventBus.emit(EVENTS.PIPELINE_STARTED, {
      request_id: pipelineId,
      zone_id: pipelineConfig.zoneId,
      timestamp: new Date().toISOString()
    });

    try {
      switch (pipeline.type) {
        case 'full_analysis':
          await this.executeFullAnalysis(pipeline);
          break;
        case 'satellite_only':
          await this.executeSatelliteAnalysis(pipeline);
          break;
        case 'report_only':
          await this.executeReportGeneration(pipeline);
          break;
        case 'prediction':
          await this.executePrediction(pipeline);
          break;
        default:
          await this.executeFullAnalysis(pipeline);
      }

      pipeline.status = 'completed';
      pipeline.duration = Date.now() - startTime;

      eventBus.emit(EVENTS.PIPELINE_COMPLETED, {
        request_id: pipelineId,
        duration: pipeline.duration,
        zone_id: pipelineConfig.zoneId
      });

      logger.info('Pipeline completed', {
        pipelineId,
        duration: pipeline.duration,
        steps: pipeline.steps.length
      });
    } catch (error) {
      pipeline.status = 'failed';
      pipeline.error = error.message;
      pipeline.duration = Date.now() - startTime;

      eventBus.emit(EVENTS.PIPELINE_ERROR, {
        request_id: pipelineId,
        error: error.message,
        zone_id: pipelineConfig.zoneId
      });

      logger.error('Pipeline failed', { pipelineId, error: error.message });
    }

    this.completedPipelines.unshift(pipeline);
    if (this.completedPipelines.length > this.maxCompleted) {
      this.completedPipelines = this.completedPipelines.slice(0, this.maxCompleted);
    }
    this.activePipelines.delete(pipelineId);

    return pipeline;
  }

  async executeFullAnalysis(pipeline) {
    const zoneId = pipeline.zoneId;
    const geometry = pipeline.config.geometry;
    const dateRange = this.resolveDateRange(pipeline.config);

    pipeline.steps.push({ name: 'satellite_ingestion', status: 'running', startedAt: new Date().toISOString() });

    const satelliteData = await this.runStep('satellite_ingestion', async () => {
      await this.publishAgentEvent(AGENT_EVENTS.ANALYSIS_REQUESTED, {
        request_id: pipeline.id,
        zone_id: zoneId,
        action: 'satellite_ingestion',
        geometry,
        date_range: dateRange
      });

      return geeClient.getSentinelComposite(geometry, dateRange.start, dateRange.end);
    });

    pipeline.steps[pipeline.steps.length - 1] = { ...pipeline.steps[pipeline.steps.length - 1], status: 'completed', result: { sceneCount: satelliteData.sceneCount } };

    await this.publishAgentEvent(AGENT_EVENTS.DATA_INGESTED, {
      request_id: pipeline.id,
      zone_id: zoneId,
      data_type: 'satellite_composite',
      indices: satelliteData.indices
    });

    pipeline.steps.push({ name: 'ndvi_timeseries', status: 'running', startedAt: new Date().toISOString() });

    const ndviSeries = await this.runStep('ndvi_timeseries', async () => {
      const start = new Date(dateRange.start);
      start.setFullYear(start.getFullYear() - 2);
      return geeClient.getNDVITimeSeries(geometry, start.toISOString().split('T')[0], dateRange.end);
    });

    pipeline.steps[pipeline.steps.length - 1] = { ...pipeline.steps[pipeline.steps.length - 1], status: 'completed', result: { points: ndviSeries.series?.length || 0 } };

    pipeline.steps.push({ name: 'elevation_analysis', status: 'running', startedAt: new Date().toISOString() });

    const elevationData = await this.runStep('elevation_analysis', async () => {
      return geeClient.getSRTMElevation(geometry);
    });

    pipeline.steps[pipeline.steps.length - 1] = { ...pipeline.steps[pipeline.steps.length - 1], status: 'completed', result: { meanElevation: elevationData.meanElevation } };

    pipeline.steps.push({ name: 'ai_analysis', status: 'running', startedAt: new Date().toISOString() });

    const aiReport = await this.runStep('ai_analysis', async () => {
      return openAIClient.analyzeReport({
        zoneName: pipeline.config.zoneName || zoneId,
        period: `${dateRange.start} - ${dateRange.end}`,
        indices: satelliteData.indices,
        historicalAnalysis: ndviSeries.summary
      });
    });

    pipeline.steps[pipeline.steps.length - 1] = { ...pipeline.steps[pipeline.steps.length - 1], status: 'completed', result: { alertLevel: aiReport.nivel_alerta } };

    await this.publishAgentEvent(AGENT_EVENTS.REPORT_GENERATED, {
      request_id: pipeline.id,
      zone_id: zoneId,
      report: aiReport,
      indices: satelliteData.indices,
      ndvi_series: ndviSeries,
      elevation: elevationData
    });

    pipeline.result = {
      satelliteData,
      ndviSeries,
      elevationData,
      aiReport
    };

    return pipeline;
  }

  async executeSatelliteAnalysis(pipeline) {
    const geometry = pipeline.config.geometry;
    const dateRange = this.resolveDateRange(pipeline.config);

    pipeline.steps.push({ name: 'satellite_ingestion', status: 'running', startedAt: new Date().toISOString() });

    const satelliteData = await geeClient.getSentinelComposite(geometry, dateRange.start, dateRange.end);

    pipeline.steps[pipeline.steps.length - 1] = { ...pipeline.steps[pipeline.steps.length - 1], status: 'completed' };

    pipeline.steps.push({ name: 'ndvi_timeseries', status: 'running', startedAt: new Date().toISOString() });

    const ndviSeries = await geeClient.getNDVITimeSeries(geometry, dateRange.start, dateRange.end);

    pipeline.steps[pipeline.steps.length - 1] = { ...pipeline.steps[pipeline.steps.length - 1], status: 'completed' };

    pipeline.result = { satelliteData, ndviSeries };
    return pipeline;
  }

  async executeReportGeneration(pipeline) {
    const zoneId = pipeline.zoneId;
    const data = pipeline.config.data;

    pipeline.steps.push({ name: 'ai_report', status: 'running', startedAt: new Date().toISOString() });

    const report = await openAIClient.analyzeReport({
      zoneName: pipeline.config.zoneName || zoneId,
      period: data.period || 'No especificado',
      indices: data.indices,
      measurements: data.measurements
    });

    pipeline.steps[pipeline.steps.length - 1] = { ...pipeline.steps[pipeline.steps.length - 1], status: 'completed' };

    await this.publishAgentEvent(AGENT_EVENTS.REPORT_GENERATED, {
      request_id: pipeline.id,
      zone_id: zoneId,
      report
    });

    pipeline.result = { report };
    return pipeline;
  }

  async executePrediction(pipeline) {
    const geometry = pipeline.config.geometry;
    const dateRange = this.resolveDateRange(pipeline.config);

    pipeline.steps.push({ name: 'historical_data', status: 'running', startedAt: new Date().toISOString() });

    const ndviSeries = await geeClient.getNDVITimeSeries(geometry, dateRange.start, dateRange.end);

    pipeline.steps[pipeline.steps.length - 1] = { ...pipeline.steps[pipeline.steps.length - 1], status: 'completed' };

    await this.publishAgentEvent(AGENT_EVENTS.PREDICTION_REQUESTED, {
      request_id: pipeline.id,
      zone_id: pipeline.zoneId,
      series: ndviSeries.series,
      config: pipeline.config
    });

    pipeline.result = { ndviSeries };
    return pipeline;
  }

  async runStep(stepName, fn) {
    try {
      const result = await fn();
      return result;
    } catch (error) {
      logger.error(`Pipeline step failed: ${stepName}`, { error: error.message });
      throw error;
    }
  }

  async publishAgentEvent(event, payload) {
    try {
      await rabbitMQClient.publish(event, payload);
    } catch (error) {
      logger.warn('Agent event publish failed, using in-memory bridge', {
        event,
        error: error.message
      });
      eventBus.emit(this.mapAgentEventToInternal(event), payload);
    }
  }

  mapAgentEventToInternal(agentEvent) {
    const mapping = {
      [AGENT_EVENTS.ANALYSIS_REQUESTED]: EVENTS.ANALYSIS_REQUESTED,
      [AGENT_EVENTS.DATA_INGESTED]: EVENTS.DATA_INGESTED,
      [AGENT_EVENTS.PREDICTION_REQUESTED]: EVENTS.PREDICTION_REQUESTED,
      [AGENT_EVENTS.PREDICTION_COMPLETED]: EVENTS.PREDICTION_COMPLETED,
      [AGENT_EVENTS.REPORT_GENERATED]: EVENTS.REPORT_READY
    };
    return mapping[agentEvent] || agentEvent;
  }

  resolveDateRange(config) {
    if (config.startDate && config.endDate) {
      return { start: config.startDate, end: config.endDate };
    }

    const end = new Date();
    const start = new Date();
    start.setFullYear(start.getFullYear() - (config.dateRangeYears || 1));

    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0]
    };
  }

  getPipeline(pipelineId) {
    return this.activePipelines.get(pipelineId) ||
      this.completedPipelines.find(p => p.id === pipelineId) ||
      null;
  }

  listPipelines(filter = {}) {
    let pipelines = [...this.completedPipelines];

    if (filter.status) {
      pipelines = pipelines.filter(p => p.status === filter.status);
    }

    if (filter.zoneId) {
      pipelines = pipelines.filter(p => p.zoneId === filter.zoneId);
    }

    const activeList = Array.from(this.activePipelines.values());

    return {
      active: activeList.map(p => ({
        id: p.id,
        type: p.type,
        status: p.status,
        zoneId: p.zoneId,
        startTime: p.startTime,
        steps: p.steps.length
      })),
      completed: pipelines.slice(0, 20).map(p => ({
        id: p.id,
        type: p.type,
        status: p.status,
        duration: p.duration,
        zoneId: p.zoneId,
        startTime: p.startTime
      }))
    };
  }

  getAgentStatuses() {
    return Array.from(this.agentStatuses.entries()).map(([agentId, status]) => ({
      agentId,
      ...status
    }));
  }

  async shutdown() {
    for (const [id] of this.activePipelines) {
      const pipeline = this.activePipelines.get(id);
      pipeline.status = 'cancelled';
      pipeline.error = 'Orchestrator shutting down';
      logger.warn('Pipeline cancelled due to shutdown', { pipelineId: id });
    }

    this.activePipelines.clear();
    logger.info('Agent orchestrator shut down');
  }
}

export const agentOrchestrator = new AgentOrchestrator();
export default agentOrchestrator;
