import { ingestionService } from '../services/ingestionService.js';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('controllers:measurement');

export class MeasurementController {
  static async createYear(req, res) {
    try {
      const yearData = {
        numero: req.body.numero,
        estado: req.body.estado || 'activo'
      };

      const year = await ingestionService.createYear(yearData);
      
      logger.info('Year created via API', { anoId: year.id, numero: year.numero });
      
      res.status(201).json({
        success: true,
        data: year
      });
    } catch (error) {
      logger.error('Error creating year', { error: error.message });
      res.status(500).json({
        error: 'Failed to create year',
        message: error.message
      });
    }
  }

  static async getAllYears(req, res) {
    try {
      const years = await ingestionService.getAllYears();
      
      res.json({
        success: true,
        data: years,
        count: years.length
      });
    } catch (error) {
      logger.error('Error fetching years', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch years',
        message: error.message
      });
    }
  }

  static async getYearById(req, res) {
    try {
      const year = await ingestionService.getYearById(req.params.id);
      
      if (!year) {
        return res.status(404).json({
          error: 'Year not found'
        });
      }

      res.json({
        success: true,
        data: year
      });
    } catch (error) {
      logger.error('Error fetching year', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch year',
        message: error.message
      });
    }
  }

  static async getMeasurements(req, res) {
    try {
      const options = {
        limit: parseInt(req.query.limit) || 100,
        offset: parseInt(req.query.offset) || 0
      };

      const measurements = await ingestionService.getYearMeasurements(
        req.params.anoId,
        options
      );
      
      res.json({
        success: true,
        data: measurements,
        count: measurements.length,
        pagination: {
          limit: options.limit,
          offset: options.offset
        }
      });
    } catch (error) {
      logger.error('Error fetching measurements', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch measurements',
        message: error.message
      });
    }
  }

  static async getMeasurementsByDateRange(req, res) {
    try {
      const { startDate, endDate } = req.query;
      
      if (!startDate || !endDate) {
        return res.status(400).json({
          error: 'startDate and endDate query parameters are required'
        });
      }

      const measurements = await ingestionService.getMeasurementsByDateRange(
        req.params.anoId,
        startDate,
        endDate
      );
      
      res.json({
        success: true,
        data: measurements,
        count: measurements.length
      });
    } catch (error) {
      logger.error('Error fetching measurements by date range', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch measurements',
        message: error.message
      });
    }
  }

  static async getStatistics(req, res) {
    try {
      const statistics = await ingestionService.getMeasurementStatistics(req.params.anoId);
      
      if (!statistics) {
        return res.status(404).json({
          error: 'No measurements found for this year'
        });
      }

      res.json({
        success: true,
        data: statistics
      });
    } catch (error) {
      logger.error('Error fetching statistics', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch statistics',
        message: error.message
      });
    }
  }

  static async ingestMeasurement(req, res) {
    try {
      const { anoNumero, medicion } = req.body;
      
      if (!anoNumero || !medicion) {
        return res.status(400).json({
          error: 'anoNumero and medicion are required'
        });
      }

      const result = ingestionService.bufferMeasurement({
        anoId: null,
        anoNumero,
        medicion
      });
      
      res.status(202).json({
        success: true,
        message: 'Measurement buffered for processing',
        data: result
      });
    } catch (error) {
      logger.error('Error buffering measurement', { error: error.message });
      res.status(500).json({
        error: 'Failed to buffer measurement',
        message: error.message
      });
    }
  }

  static async ingestBatch(req, res) {
    try {
      const { measurements } = req.body;
      
      if (!Array.isArray(measurements)) {
        return res.status(400).json({
          error: 'measurements must be an array'
        });
      }

      const result = await ingestionService.ingestBatch(measurements);
      
      res.status(200).json({
        success: true,
        data: result
      });
    } catch (error) {
      logger.error('Error ingesting batch', { error: error.message });
      res.status(500).json({
        error: 'Failed to ingest batch',
        message: error.message
      });
    }
  }

  static async getBufferStatus(req, res) {
    try {
      const status = ingestionService.getBufferStatus();
      
      res.json({
        success: true,
        data: status
      });
    } catch (error) {
      logger.error('Error fetching buffer status', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch buffer status',
        message: error.message
      });
    }
  }
}
