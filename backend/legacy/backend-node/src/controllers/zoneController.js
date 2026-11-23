import { geospatialService } from '../services/geospatialService.js';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('controllers:zone');

export class ZoneController {
  static async create(req, res) {
    try {
      const geoValidation = geospatialService.validateGeoJSON(req.body);
      
      if (!geoValidation.valid) {
        return res.status(400).json({
          error: 'Invalid GeoJSON',
          details: geoValidation.errors
        });
      }

      const zoneData = {
        name: req.body.properties?.nombre || 'Unnamed Zone',
        areaHa: req.body.properties?.area_hectareas || 
          geospatialService.calculateAreaFromGeoJSON(req.body),
        boundaryPolygon: req.body.features?.[0]?.geometry,
        tipoZona: req.body.properties?.tipo_zona,
        elevacionMinM: req.body.properties?.elevacion_min_m,
        elevacionMaxM: req.body.properties?.elevacion_max_m
      };

      const zone = await geospatialService.createZone(zoneData);
      
      logger.info('Zone created via API', { zoneId: zone.id });
      
      res.status(201).json({
        success: true,
        data: zone
      });
    } catch (error) {
      logger.error('Error creating zone', { error: error.message });
      res.status(500).json({
        error: 'Failed to create zone',
        message: error.message
      });
    }
  }

  static async getAll(req, res) {
    try {
      const zones = await geospatialService.getAllZones();
      
      res.json({
        success: true,
        data: zones,
        count: zones.length
      });
    } catch (error) {
      logger.error('Error fetching zones', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch zones',
        message: error.message
      });
    }
  }

  static async getById(req, res) {
    try {
      const zone = await geospatialService.getZoneById(req.params.id);
      
      if (!zone) {
        return res.status(404).json({
          error: 'Zone not found'
        });
      }

      res.json({
        success: true,
        data: zone
      });
    } catch (error) {
      logger.error('Error fetching zone', { error: error.message });
      res.status(500).json({
        error: 'Failed to fetch zone',
        message: error.message
      });
    }
  }

  static async getStations(req, res) {
    try {
      const stations = await geospatialService.getZoneStations(req.params.id);
      
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

  static async addStation(req, res) {
    try {
      const stationData = {
        name: req.body.name,
        type: req.body.type,
        lat: req.body.lat,
        lon: req.body.lon,
        status: req.body.status || 'active'
      };

      const station = await geospatialService.addStationToZone(
        req.params.id,
        stationData
      );
      
      res.status(201).json({
        success: true,
        data: station
      });
    } catch (error) {
      logger.error('Error adding station to zone', { error: error.message });
      res.status(500).json({
        error: 'Failed to add station',
        message: error.message
      });
    }
  }
}
