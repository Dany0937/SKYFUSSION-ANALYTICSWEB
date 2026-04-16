import { alertService } from '../services/alertService.js';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('controllers:alert');

export class AlertController {
  static async classifyAlert(req, res) {
    try {
      const { ndvi, currentFlow, historicalFlowMean, precipitacion24h, zoneId } = req.body;
      
      const classification = alertService.classifyAlert({
        ndvi: ndvi ?? 0.5,
        currentFlow: currentFlow ?? 10,
        historicalFlowMean: historicalFlowMean ?? 10,
        precipitacion24h: precipitacion24h ?? 20
      });

      const alert = alertService.generateAlert(zoneId, classification, {
        inputData: { ndvi, currentFlow, historicalFlowMean, precipitacion24h }
      });

      res.json({
        success: true,
        data: {
          classification,
          alert
        }
      });
    } catch (error) {
      logger.error('Error classifying alert', { error: error.message });
      res.status(500).json({
        error: 'Failed to classify alert',
        message: error.message
      });
    }
  }

  static async getActiveAlerts(req, res) {
    try {
      const { zoneId } = req.query;
      const alerts = alertService.getActiveAlerts(zoneId);
      
      res.json({
        success: true,
        data: alerts,
        count: alerts.length
      });
    } catch (error) {
      logger.error('Error fetching active alerts', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch active alerts',
        message: error.message
      });
    }
  }

  static async getAlertHistory(req, res) {
    try {
      const options = {
        zoneId: req.query.zoneId,
        level: req.query.level,
        since: req.query.since,
        until: req.query.until
      };

      const history = alertService.getAlertHistory(options);
      
      res.json({
        success: true,
        data: history,
        count: history.length
      });
    } catch (error) {
      logger.error('Error fetching alert history', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch alert history',
        message: error.message
      });
    }
  }

  static async acknowledgeAlert(req, res) {
    try {
      const alert = alertService.acknowledgeAlert(req.params.id);
      
      if (!alert) {
        return res.status(404).json({
          error: 'Alert not found'
        });
      }

      res.json({
        success: true,
        data: alert
      });
    } catch (error) {
      logger.error('Error acknowledging alert', { error: error.message });
      res.status(500).json({
        error: 'Failed to acknowledge alert',
        message: error.message
      });
    }
  }

  static async resolveAlert(req, res) {
    try {
      const resolved = alertService.resolveAlert(req.params.id);
      
      if (!resolved) {
        return res.status(404).json({
          error: 'Alert not found or already resolved'
        });
      }

      res.json({
        success: true,
        message: 'Alert resolved successfully'
      });
    } catch (error) {
      logger.error('Error resolving alert', { error: error.message });
      res.status(500).json({
        error: 'Failed to resolve alert',
        message: error.message
      });
    }
  }
}
