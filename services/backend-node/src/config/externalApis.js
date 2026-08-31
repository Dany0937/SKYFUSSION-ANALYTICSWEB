import { createLogger } from '../utils/logger.js';

const logger = createLogger('config:externalApis');

function loadConfig() {
  return {
    gee: {
      serviceAccountEmail: process.env.GEE_SERVICE_ACCOUNT_EMAIL,
      privateKeyPath: process.env.GEE_PRIVATE_KEY_PATH || './config/gee-private-key.json',
      project: process.env.GEE_PROJECT || 'skyfusion-analytics',
      collections: {
        sentinel2: 'COPERNICUS/S2_SR_HARMONIZED',
        landsat8: 'LANDSAT/LC08/C02/T1_L2',
        landsat9: 'LANDSAT/LC09/C02/T1_L2',
        srtm: 'USGS/SRTMGL1_003',
        modisNdvi: 'MODIS/061/MOD13Q1'
      },
      defaultScale: 10,
      maxPixels: 1e9,
      dateRangeDefault: { years: 2 },
      cloudCoverMax: 20
    },
    openai: {
      apiKey: process.env.OPENAI_API_KEY,
      model: process.env.OPENAI_MODEL || 'gpt-4o',
      maxTokens: parseInt(process.env.OPENAI_MAX_TOKENS, 10) || 4096,
      temperature: parseFloat(process.env.OPENAI_TEMPERATURE) || 0.2,
      timeout: 120000,
      maxRetries: 3
    },
    orchestrator: {
      defaultTimeoutMs: parseInt(process.env.ORCHESTRATOR_DEFAULT_TIMEOUT_MS, 10) || 300000,
      maxRetries: parseInt(process.env.ORCHESTRATOR_MAX_RETRIES, 10) || 3
    }
  };
}

const config = loadConfig();

export function validateExternalConfig() {
  const missing = [];

  if (!config.gee.serviceAccountEmail) {
    missing.push('GEE_SERVICE_ACCOUNT_EMAIL');
  }

  if (!config.openai.apiKey) {
    missing.push('OPENAI_API_KEY');
  }

  if (missing.length > 0) {
    logger.warn('External API configuration incomplete', { missingVars: missing });
    return { valid: false, missing };
  }

  logger.info('External API configuration validated');
  return { valid: true, missing: [] };
}

export default config;
