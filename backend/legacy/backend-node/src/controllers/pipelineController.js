import { agentOrchestrator } from '../services/agentOrchestrator.js';
import { Scene } from '../models/Scene.js';
import { Prediction } from '../models/Prediction.js';
import { Report } from '../models/Report.js';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('controllers:pipeline');

export class PipelineController {
  static async startPipeline(req, res) {
    try {
      const { zoneId, zoneName, geometry, type, startDate, endDate, dateRangeYears, data } = req.body;

      if (!geometry) {
        return res.status(400).json({
          error: 'geometry is required'
        });
      }

      const pipeline = await agentOrchestrator.startPipeline({
        zoneId,
        zoneName,
        geometry,
        type: type || 'full_analysis',
        startDate,
        endDate,
        dateRangeYears,
        data
      });

      res.status(201).json({
        success: true,
        data: {
          pipelineId: pipeline.id,
          status: pipeline.status,
          type: pipeline.type,
          steps: pipeline.steps.map(s => ({
            name: s.name,
            status: s.status
          }))
        }
      });
    } catch (error) {
      logger.error('Error starting pipeline', { error: error.message });
      res.status(500).json({
        error: 'Failed to start pipeline',
        message: error.message
      });
    }
  }

  static async getPipelineStatus(req, res) {
    try {
      const pipeline = agentOrchestrator.getPipeline(req.params.id);

      if (!pipeline) {
        return res.status(404).json({
          error: 'Pipeline not found'
        });
      }

      res.json({
        success: true,
        data: pipeline
      });
    } catch (error) {
      logger.error('Error fetching pipeline', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch pipeline',
        message: error.message
      });
    }
  }

  static async listPipelines(req, res) {
    try {
      const { status, zoneId } = req.query;
      const pipelines = agentOrchestrator.listPipelines({ status, zoneId });

      res.json({
        success: true,
        data: pipelines
      });
    } catch (error) {
      logger.error('Error listing pipelines', { error: error.message });
      res.status(500).json({
        error: 'Failed to list pipelines',
        message: error.message
      });
    }
  }

  static async getScenes(req, res) {
    try {
      const { zoneId } = req.params;
      const scenes = await Scene.findByZone(zoneId);

      res.json({
        success: true,
        data: scenes,
        count: scenes.length
      });
    } catch (error) {
      logger.error('Error fetching scenes', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch scenes',
        message: error.message
      });
    }
  }

  static async getLatestScenes(req, res) {
    try {
      const { zoneId } = req.params;
      const limit = parseInt(req.query.limit, 10) || 10;
      const scenes = await Scene.findLatestByZone(zoneId, limit);

      res.json({
        success: true,
        data: scenes,
        count: scenes.length
      });
    } catch (error) {
      logger.error('Error fetching latest scenes', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch latest scenes',
        message: error.message
      });
    }
  }

  static async getPredictions(req, res) {
    try {
      const { zoneId } = req.params;
      const predictions = await Prediction.findByZone(zoneId);

      res.json({
        success: true,
        data: predictions,
        count: predictions.length
      });
    } catch (error) {
      logger.error('Error fetching predictions', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch predictions',
        message: error.message
      });
    }
  }

  static async getReports(req, res) {
    try {
      const { zoneId } = req.params;
      const reports = await Report.findByZone(zoneId);

      res.json({
        success: true,
        data: reports,
        count: reports.length
      });
    } catch (error) {
      logger.error('Error fetching reports', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch reports',
        message: error.message
      });
    }
  }

  static async getLatestReport(req, res) {
    try {
      const { zoneId } = req.params;
      const reports = await Report.findLatestByZone(zoneId, 1);

      if (!reports || reports.length === 0) {
        return res.status(404).json({
          error: 'No reports found for this zone'
        });
      }

      res.json({
        success: true,
        data: reports[0]
      });
    } catch (error) {
      logger.error('Error fetching latest report', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch latest report',
        message: error.message
      });
    }
  }

  static async getAgentStatus(req, res) {
    try {
      const agents = agentOrchestrator.getAgentStatuses();

      res.json({
        success: true,
        data: agents
      });
    } catch (error) {
      logger.error('Error fetching agent status', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch agent status',
        message: error.message
      });
    }
  }
}
