import { Zone } from '../models/Zone.js';
import { Station } from '../models/Station.js';
import { createLogger } from '../utils/logger.js';
import { eventBus, EVENTS } from './eventBus.js';

const logger = createLogger('services:geospatial');

export class GeospatialService {
  constructor() {
    this.subscribeToEvents();
  }

  subscribeToEvents() {
    eventBus.on(EVENTS.STATION_CREATED, (data) => {
      logger.info('Station event received', { stationId: data.stationId });
    });
  }

  async createZone(zoneData) {
    const zone = await Zone.create(zoneData);
    eventBus.emit(EVENTS.ZONE_CREATED, { zone });
    return zone;
  }

  async getAllZones() {
    return Zone.findAll();
  }

  async getZoneById(id) {
    return Zone.findById(id);
  }

  async getZoneStations(zoneId) {
    return Zone.findStations(zoneId);
  }

  async addStationToZone(zoneId, stationData) {
    const station = await Zone.addStation(zoneId, stationData);
    eventBus.emit(EVENTS.STATION_CREATED, { 
      zoneId, 
      stationId: station.id 
    });
    return station;
  }

  async getAllStations() {
    return Station.findAll();
  }

  async getStationById(id) {
    return Station.findById(id);
  }

  async findStationsNearby(lon, lat, radiusMeters = 5000) {
    return Station.findNearby(lon, lat, radiusMeters);
  }

  async findStationsByZone(zoneId) {
    return Station.findByZone(zoneId);
  }

  validateGeoJSON(geojson) {
    const errors = [];

    if (!geojson.type) {
      errors.push('Falta propiedad "type"');
    }

    if (!geojson.crs?.properties?.name?.includes('EPSG')) {
      errors.push('CRS debe estar en formato EPSG');
    }

    if (!geojson.features || !Array.isArray(geojson.features)) {
      errors.push('Falta array "features"');
      return { valid: false, errors };
    }

    geojson.features.forEach((feature, index) => {
      if (!feature.geometry) {
        errors.push(`Feature ${index}: Falta geometría`);
      }

      const coords = feature.geometry?.coordinates;
      if (coords) {
        const [lon, lat] = Array.isArray(coords[0]) ? coords[0] : coords;
        if (lat !== undefined && (lat < -4.2 || lat > 13 || lon < -79 || lon > -66)) {
          errors.push(`Feature ${index}: Coordenadas fuera de Colombia`);
        }
      }
    });

    return {
      valid: errors.length === 0,
      errors
    };
  }

  calculateAreaFromGeoJSON(geojson) {
    if (geojson.features?.[0]?.geometry?.type === 'Polygon') {
      return this.calculatePolygonArea(geojson.features[0].geometry.coordinates[0]);
    }
    return null;
  }

  calculatePolygonArea(coordinates) {
    let area = 0;
    const n = coordinates.length;

    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      area += coordinates[i][0] * coordinates[j][1];
      area -= coordinates[j][0] * coordinates[i][1];
    }

    return Math.abs(area / 2) * 111319.9 * 111319.9 * Math.cos(coordinates[0][1] * Math.PI / 180) / 10000;
  }
}

export const geospatialService = new GeospatialService();
