import { Station } from '../models/Station.js';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('controllers:station');

export class StationController {
  static async create(req, res) {
    try {
      const stationData = {
        name: req.body.name,
        type: req.body.type,
        lat: req.body.lat,
        lon: req.body.lon,
        status: req.body.status || 'active'
      };

      const station = await Station.create(stationData);
      
      logger.info('Station created via API', { stationId: station.id });
      
      res.status(201).json({
        success: true,
        data: station
      });
    } catch (error) {
      logger.error('Error creating station', { error: error.message });
      res.status(500).json({
        error: 'Failed to create station',
        message: error.message
      });
    }
  }

  static async getAll(req, res) {
    try {
      const stations = await Station.findAll();
      
      res.json({
        success: true,
        data: stations,
        count: stations.length
      });
    } catch (error) {
      logger.error('Error fetching stations', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch stations',
        message: error.message
      });
    }
  }

  static async getById(req, res) {
    try {
      const station = await Station.findById(req.params.id);
      
      if (!station) {
        return res.status(404).json({
          error: 'Station not found'
        });
      }

      res.json({
        success: true,
        data: station
      });
    } catch (error) {
      logger.error('Error fetching station', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch station',
        message: error.message
      });
    }
  }

  static async findNearby(req, res) {
    try {
      const { lon, lat, radius } = req.query;
      
      if (!lon || !lat) {
        return res.status(400).json({
          error: 'lon and lat query parameters are required'
        });
      }

      const stations = await Station.findNearby(
        parseFloat(lon),
        parseFloat(lat),
        parseInt(radius) || 5000
      );
      
      res.json({
        success: true,
        data: stations,
        count: stations.length
      });
    } catch (error) {
      logger.error('Error finding nearby stations', { error: error.message });
      res.status(500).json({
        error: 'Failed to find nearby stations',
        message: error.message
      });
    }
  }

  static async findByZone(req, res) {
    try {
      const stations = await Station.findByZone(req.params.zoneId);
      
      res.json({
        success: true,
        data: stations,
        count: stations.length
      });
    } catch (error) {
      logger.error('Error fetching zone stations', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch zone stations',
        message: error.message
      });
    }
  }

  static async updateStatus(req, res) {
    try {
      const { status } = req.body;
      
      if (!status || !['active', 'inactive', 'maintenance'].includes(status)) {
        return res.status(400).json({
          error: 'Valid status is required (active, inactive, maintenance)'
        });
      }

      const station = await Station.updateStatus(req.params.id, status);
      
      if (!station) {
        return res.status(404).json({
          error: 'Station not found'
        });
      }

      res.json({
        success: true,
        data: station
      });
    } catch (error) {
      logger.error('Error updating station status', { error: error.message });
      res.status(500).json({
        error: 'Failed to update station status',
        message: error.message
      });
    }
  }
}
