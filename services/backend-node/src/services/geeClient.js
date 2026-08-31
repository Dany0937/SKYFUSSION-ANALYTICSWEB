import { createLogger } from '../utils/logger.js';
import config from '../config/externalApis.js';

const logger = createLogger('services:gee');

export class GEEClient {
  constructor() {
    this.initialized = false;
    this.ee = null;
    this.requestQueue = [];
    this.processingQueue = false;
  }

  async initialize() {
    if (this.initialized) return true;

    try {
      const ee = await import('@google/earthengine');

      const privateKey = this.loadPrivateKey();

      await new Promise((resolve, reject) => {
        ee.data.authenticateViaPrivateKey(
          privateKey,
          () => {
            ee.initialize(null, null, () => {
              this.ee = ee;
              this.initialized = true;
              resolve();
            }, reject);
          },
          reject
        );
      });

      logger.info('GEE client initialized', { project: config.gee.project });
      return true;
    } catch (error) {
      logger.error('GEE initialization failed', { error: error.message });
      return false;
    }
  }

  async loadPrivateKey() {
    try {
      const fs = await import('fs');
      const keyPath = config.gee.privateKeyPath;
      const keyContent = await fs.promises.readFile(keyPath, 'utf8');
      return JSON.parse(keyContent);
    } catch (error) {
      logger.warn('Could not load GEE private key file, using service account email', {
        error: error.message
      });
      return { client_email: config.gee.serviceAccountEmail };
    }
  }

  async getSentinelComposite(geometry, startDate, endDate, cloudCoverMax) {
    await this.ensureInitialized();
    const ee = this.ee;

    try {
      const collection = ee.ImageCollection(config.gee.collections.sentinel2)
        .filterBounds(ee.Geometry.Polygon(geometry))
        .filterDate(startDate, endDate)
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloudCoverMax || config.gee.cloudCoverMax));

      const composite = collection.median();

      const ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI');
      const ndwi = composite.normalizedDifference(['B3', 'B8']).rename('NDWI');
      const mndwi = composite.normalizedDifference(['B3', 'B11']).rename('MNDWI');

      const image = composite.addBands(ndvi).addBands(ndwi).addBands(mndwi);

      const url = await this.getTileUrl(image, geometry);
      const stats = await this.getRegionStats(image, geometry);
      const histogram = await this.getHistogram(image, geometry, 'NDVI');

      return {
        composite: { url, dateRange: { start: startDate, end: endDate } },
 indices: { ndvi: stats.ndvi, ndwi: stats.ndwi, mndwi: stats.mndwi },
        histogram,
        sceneCount: await this.getSceneCount(collection),
        scale: config.gee.defaultScale
      };
    } catch (error) {
      logger.error('Sentinel composite failed', { error: error.message });
      throw error;
    }
  }

  async getLandsatComposite(geometry, startDate, endDate, cloudCoverMax) {
    await this.ensureInitialized();
    const ee = this.ee;

    try {
      const collection = ee.ImageCollection(config.gee.collections.landsat8)
        .filterBounds(ee.Geometry.Polygon(geometry))
        .filterDate(startDate, endDate)
        .filter(ee.Filter.lte('CLOUD_COVER', cloudCoverMax || config.gee.cloudCoverMax));

      const composite = collection.median();
      const ndvi = composite.normalizedDifference(['B5', 'B4']).rename('NDVI');
      const ndwi = composite.normalizedDifference(['B3', 'B5']).rename('NDWI');

      const image = composite.addBands(ndvi).addBands(ndwi);

      const url = await this.getTileUrl(image, geometry);
      const stats = await this.getRegionStats(image, geometry);

      return {
        composite: { url, dateRange: { start: startDate, end: endDate } },
        indices: { ndvi: stats.ndvi, ndwi: stats.ndwi },
        sceneCount: await this.getSceneCount(collection),
        scale: 30
      };
    } catch (error) {
      logger.error('Landsat composite failed', { error: error.message });
      throw error;
    }
  }

  async getSRTMElevation(geometry) {
    await this.ensureInitialized();
    const ee = this.ee;

    try {
      const srtm = ee.Image(config.gee.collections.srtm);
      const elevation = srtm.clip(ee.Geometry.Polygon(geometry));

      const stats = await this.getRegionStats(
        elevation.addBands(srtm.select('elevation').gradient().rename('slope')),
        geometry
      );

      return {
        minElevation: stats.elevation?.min || 0,
        maxElevation: stats.elevation?.max || 0,
        meanElevation: stats.elevation?.mean || 0,
        meanSlope: stats.slope?.mean || 0,
        scale: 30
      };
    } catch (error) {
      logger.error('SRTM elevation failed', { error: error.message });
      throw error;
    }
  }

  async getNDVITimeSeries(geometry, startDate, endDate) {
    await this.ensureInitialized();
    const ee = this.ee;

    try {
      const collection = ee.ImageCollection(config.gee.collections.modisNdvi)
        .filterBounds(ee.Geometry.Polygon(geometry))
        .filterDate(startDate, endDate)
        .select('NDVI');

      const series = await new Promise((resolve, reject) => {
        collection.getRegion(ee.Geometry.Polygon(geometry), 250).getInfo((data, error) => {
          if (error) reject(error);
          else resolve(data);
        });
      });

      if (!series || series.length < 2) {
        return { series: [], summary: null };
      }

      const headers = series[0];
      const timeIndex = headers.indexOf('time');
      const ndviIndex = headers.indexOf('NDVI');

      const points = series.slice(1)
        .filter(row => row[ndviIndex] !== null)
        .map(row => ({
          date: new Date(row[timeIndex]).toISOString().split('T')[0],
          ndvi: parseFloat(row[ndviIndex].toFixed(4))
        }))
        .sort((a, b) => a.date.localeCompare(b.date));

      const values = points.map(p => p.ndvi);

      return {
        series: points,
        summary: {
          mean: parseFloat((values.reduce((a, b) => a + b, 0) / values.length).toFixed(4)),
          min: parseFloat(Math.min(...values).toFixed(4)),
          max: parseFloat(Math.max(...values).toFixed(4)),
          trend: this.calculateTrend(points)
        }
      };
    } catch (error) {
      logger.error('NDVI time series failed', { error: error.message });
      throw error;
    }
  }

  async exportToAsset(image, description, assetId, geometry) {
    await this.ensureInitialized();
    const ee = this.ee;

    try {
      const task = ee.batch.Export.image.toAsset({
        image: image.clip(ee.Geometry.Polygon(geometry)),
        description,
        assetId,
        scale: config.gee.defaultScale,
        maxPixels: config.gee.maxPixels
      });

      task.start();

      logger.info('GEE export task started', { description, assetId });
      return { taskId: task.id, status: 'started' };
    } catch (error) {
      logger.error('GEE export failed', { error: error.message });
      throw error;
    }
  }

  async ensureInitialized() {
    if (!this.initialized) {
      await this.initialize();
    }
  }

  async getTileUrl(image, geometry) {
    const ee = this.ee;
    return new Promise((resolve, reject) => {
      const visParams = {
        bands: ['B4', 'B3', 'B2'],
        min: 0,
        max: 3000,
        gamma: 1.4
      };

      const mapId = image.getMapId(visParams);
      resolve(mapId.urlFormat);
    });
  }

  async getRegionStats(image, geometry) {
    const ee = this.ee;

    return new Promise((resolve, reject) => {
      const scale = config.gee.defaultScale;
      const reducer = ee.Reducer.mean().combine({
        reducer2: ee.Reducer.minMax(),
        sharedInputs: true
      });

      const stats = image.reduceRegion({
        reducer,
        geometry: ee.Geometry.Polygon(geometry),
        scale,
        maxPixels: config.gee.maxPixels
      });

      stats.getInfo((data, error) => {
        if (error) reject(error);
        else {
          const result = {};
          Object.entries(data || {}).forEach(([key, value]) => {
            const parts = key.split('_');
            const band = parts[0];
            const stat = parts[1] || 'mean';
            if (!result[band]) result[band] = {};
            result[band][stat] = value;
          });
          resolve(result);
        }
      });
    });
  }

  async getHistogram(image, geometry, band) {
    const ee = this.ee;

    return new Promise((resolve, reject) => {
      const histogram = image.select(band).reduceRegion({
        reducer: ee.Reducer.histogram(50),
        geometry: ee.Geometry.Polygon(geometry),
        scale: config.gee.defaultScale,
        maxPixels: config.gee.maxPixels
      });

      histogram.getInfo((data, error) => {
        if (error) reject(error);
        else {
          const hist = data?.[`${band}_histogram`] || data?.[band]?.histogram;
          if (!hist) {
            resolve({ buckets: [], counts: [] });
            return;
          }
          resolve({
            buckets: hist.bucketMeans || [],
            counts: hist.histogram || []
          });
        }
      });
    });
  }

  async getSceneCount(collection) {
    return new Promise((resolve) => {
      collection.size().getInfo((count, error) => {
        if (error) resolve(0);
        else resolve(count);
      });
    });
  }

  calculateTrend(points) {
    if (points.length < 2) return 0;

    const n = points.length;
    const indices = points.map((_, i) => i);
    const values = points.map(p => p.ndvi);

    const sumX = indices.reduce((a, b) => a + b, 0);
    const sumY = values.reduce((a, b) => a + b, 0);
    const sumXY = indices.reduce((sum, x, i) => sum + x * values[i], 0);
    const sumX2 = indices.reduce((sum, x) => sum + x * x, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    return parseFloat(slope.toFixed(6));
  }
}

export const geeClient = new GEEClient();
export default geeClient;
