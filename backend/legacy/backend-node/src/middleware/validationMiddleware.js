import Joi from 'joi';
import { AppError } from './errorHandler.js';

const schemas = {
  createZone: Joi.object({
    type: Joi.string().valid('FeatureCollection').required(),
    features: Joi.array().items(Joi.object({
      type: Joi.string().valid('Feature').required(),
      geometry: Joi.object().required(),
      properties: Joi.object()
    })).min(1).required()
  }),

  createStation: Joi.object({
    name: Joi.string().min(1).max(100).required(),
    type: Joi.string().valid('weather', 'hydrological', 'air').required(),
    lat: Joi.number().min(-4.2).max(13).required(),
    lon: Joi.number().min(-79).max(-66).required(),
    status: Joi.string().valid('active', 'inactive', 'maintenance')
  }),

  createMeasurement: Joi.object({
    anoNumero: Joi.number().integer().min(2000).max(2100).required(),
    medicion: Joi.object({
      valor: Joi.number().required(),
      unidad: Joi.string().valid('m3/s', 'l/s', 'mm'),
      calidad: Joi.string().valid('valid', 'suspect', 'invalid'),
      timestamp: Joi.string().isoDate()
    }).required()
  }),

  classifyAlert: Joi.object({
    ndvi: Joi.number().min(-1).max(1),
    currentFlow: Joi.number().min(0),
    historicalFlowMean: Joi.number().min(0),
    precipitacion24h: Joi.number().min(0),
    zoneId: Joi.string().uuid()
  })
};

export function validate(schemaName) {
  return (req, res, next) => {
    const schema = schemas[schemaName];
    if (!schema) {
      return next(new AppError(`Unknown validation schema: ${schemaName}`, 500));
    }

    const { error, value } = schema.validate(req.body, {
      abortEarly: false,
      stripUnknown: true
    });

    if (error) {
      const errors = error.details.map(detail => detail.message);
      return next(new AppError(errors.join(', '), 400));
    }

    req.body = value;
    next();
  };
}

export { schemas };
