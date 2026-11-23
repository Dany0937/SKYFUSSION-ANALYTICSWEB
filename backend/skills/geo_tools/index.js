/**
 * Geo Tools - Geospatial Agent Bridge
 * ====================================
 * 
 * Interface between Node.js backend and Python GEE preprocessing module.
 * 
 * Python modules:
 * - preprocessor.py: Google Earth Engine API integration
 */

export class GeoTools {
  constructor(config = {}) {
    this.config = {
      defaultCrs: 'EPSG:4326',
      precision: 6,
      cloudThreshold: 15,
      maxResults: 100,
      pythonPath: 'python',
      ...config
    };
    this.geometry = null;
  }

  setGeometry(geojson) {
    if (typeof geojson === 'string') {
      this.geometry = { type: 'FeatureCollection', source: 'file', path: geojson };
    } else {
      this.geometry = geojson;
    }
    return this;
  }

  validateGeoJSON(geojson) {
    const errors = [];
    
    if (!geojson || typeof geojson !== 'object') {
      return { valid: false, errors: ['Invalid GeoJSON object'] };
    }

    if (!geojson.type) {
      errors.push('Missing "type" property');
    }

    const validTypes = ['FeatureCollection', 'Feature', 'Point', 'LineString', 'Polygon'];
    if (geojson.type && !validTypes.includes(geojson.type)) {
      errors.push(`Invalid type: ${geojson.type}`);
    }

    if (geojson.type === 'FeatureCollection') {
      if (!Array.isArray(geojson.features)) {
        errors.push('FeatureCollection must have "features" array');
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      type: geojson.type || 'unknown'
    };
  }

  calculateCentroid(coordinates) {
    if (!coordinates || coordinates.length === 0) return null;
    
    const sum = coordinates.reduce(
      (acc, coord) => [acc[0] + coord[0], acc[1] + coord[1]],
      [0, 0]
    );
    
    return {
      lon: sum[0] / coordinates.length,
      lat: sum[1] / coordinates.length
    };
  }

  calculateArea(coordinates) {
    if (!coordinates || coordinates.length < 3) return 0;
    
    let area = 0;
    const n = coordinates.length;
    
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      area += coordinates[i][0] * coordinates[j][1];
      area -= coordinates[j][0] * coordinates[i][1];
    }
    
    area = Math.abs(area) / 2;
    
    const metersPerDegree = 111319.9;
    const avgLat = coordinates.reduce((s, c) => s + c[1], 0) / n;
    area = area * metersPerDegree * metersPerDegree * Math.cos(avgLat * Math.PI / 180);
    
    return area / 10000;
  }

  isPointInPolygon(point, polygon) {
    const [x, y] = point;
    let inside = false;
    
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const [xi, yi] = polygon[i];
      const [xj, yj] = polygon[j];
      
      if (((yi > y) !== (yj > y)) && 
          (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
        inside = !inside;
      }
    }
    
    return inside;
  }

  bufferPoint(coord, radiusDegrees = 0.01) {
    return {
      type: 'Polygon',
      coordinates: [[
        [coord[0] - radiusDegrees, coord[1] - radiusDegrees],
        [coord[0] + radiusDegrees, coord[1] - radiusDegrees],
        [coord[0] + radiusDegrees, coord[1] + radiusDegrees],
        [coord[0] - radiusDegrees, coord[1] + radiusDegrees],
        [coord[0] - radiusDegrees, coord[1] - radiusDegrees]
      ]]
    };
  }

  getBoundingBox(geojson) {
    let minLon = Infinity, minLat = Infinity;
    let maxLon = -Infinity, maxLat = -Infinity;

    const processCoords = (coords) => {
      for (const coord of coords) {
        if (Array.isArray(coord[0])) {
          processCoords(coord);
        } else {
          const [lon, lat] = coord;
          minLon = Math.min(minLon, lon);
          minLat = Math.min(minLat, lat);
          maxLon = Math.max(maxLon, lon);
          maxLat = Math.max(maxLat, lat);
        }
      }
    };

    if (geojson.coordinates) {
      processCoords(geojson.coordinates);
    }

    return [minLon, minLat, maxLon, maxLat];
  }

  async queryGEE(startDate, endDate, options = {}) {
    return {
      success: true,
      message: 'Use Python preprocessor.py for GEE queries',
      collections: this.getRecommendedCollections(startDate),
      options: {
        cloudThreshold: options.cloudThreshold || this.config.cloudThreshold,
        maxResults: options.maxResults || this.config.maxResults
      },
      example: `python preprocessor.py --start-date ${startDate} --end-date ${endDate}`
    };
  }

  getRecommendedCollections(startDate) {
    const year = parseInt(startDate.split('-')[0]);
    
    if (year < 1985) {
      return [
        { name: 'Landsat 1-5 MSS', collection: 'LANDSAT/LM01/T1', period: '1972-1984' }
      ];
    } else if (year < 2013) {
      return [
        { name: 'Landsat 5 TM', collection: 'LANDSAT/LT05/C02/T1', period: '1984-2012' }
      ];
    } else if (year < 2015) {
      return [
        { name: 'Landsat 8 OLI', collection: 'LANDSAT/LC08/C02/T1_L2', period: '2013-actual' },
        { name: 'Landsat 5 TM', collection: 'LANDSAT/LT05/C02/T1', period: '1984-2012' }
      ];
    } else {
      return [
        { name: 'Sentinel-2 MSI', collection: 'COPERNICUS/S2_SR_HARMONIZED', period: '2015-actual' },
        { name: 'Landsat 8-9 OLI', collection: 'LANDSAT/LC08/C02/T1_L2', period: '2013-actual' }
      ];
    }
  }

  getConfig() {
    return {
      defaultCrs: this.config.defaultCrs,
      precision: this.config.precision,
      cloudThreshold: this.config.cloudThreshold,
      combeimaBasin: {
        bbox: [-75.257, 4.433, -75.142, 4.529],
        areaHa: 12450.75,
        municipality: 'Ibagué, Tolima'
      }
    };
  }
}

export default new GeoTools();
