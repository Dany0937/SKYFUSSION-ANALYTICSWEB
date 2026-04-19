/**
 * Event Schema Definitions
 * ========================
 * 
 * Definiciones de esquemas para los eventos del sistema.
 */

export const EVENT_SCHEMAS = {
  IMAGENES_HISTORICAS_LISTAS: {
    type: 'object',
    required: ['event_id', 'event_type', 'timestamp', 'payload'],
    properties: {
      event_id: { type: 'string' },
      event_type: { const: 'IMAGENES_HISTORICAS_LISTAS' },
      timestamp: { type: 'string', format: 'date-time' },
      source: { type: 'string' },
      version: { type: 'string' },
      payload: {
        type: 'object',
        required: ['dataAvailability', 'processingConfig'],
        properties: {
          dataAvailability: {
            type: 'object',
            properties: {
              dateRange: {
                type: 'object',
                properties: {
                  start: { type: 'string' },
                  end: { type: 'string' }
                }
              },
              collectionsUsed: {
                type: 'array',
                items: { type: 'string' }
              },
              imageCount: { type: 'integer' }
            }
          },
          processingConfig: {
            type: 'object',
            properties: {
              cloudFilterApplied: { type: 'boolean' },
              maxCloudPercent: { type: 'number' }
            }
          },
          basin: {
            type: 'object',
            properties: {
              id: { type: 'string' },
              name: { type: 'string' },
              areaHa: { type: 'number' },
              bbox: { type: 'array', items: { type: 'number' } }
            }
          },
          processingMetrics: { type: 'object' }
        }
      }
    }
  },

  GEOSPATIAL_AGENT_ERROR: {
    type: 'object',
    required: ['event_id', 'event_type', 'timestamp', 'payload'],
    properties: {
      event_id: { type: 'string' },
      event_type: { const: 'GEOSPATIAL_AGENT_ERROR' },
      timestamp: { type: 'string', format: 'date-time' },
      payload: {
        type: 'object',
        required: ['errorType', 'message'],
        properties: {
          errorType: { type: 'string' },
          message: { type: 'string' },
          context: { type: 'object' },
          traceback: { type: 'string' }
        }
      }
    }
  }
};

export function validateEvent(event) {
  const schema = EVENT_SCHEMAS[event.event_type];
  if (!schema) {
    return { valid: true, warnings: ['Unknown event type'] };
  }

  const errors = [];

  for (const field of schema.required || []) {
    if (!(field in event)) {
      errors.push(`Missing required field: ${field}`);
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    schema: schema.type
  };
}

export function formatEventSummary(event) {
  switch (event.event_type) {
    case 'IMAGENES_HISTORICAS_LISTAS':
      const { imageCount, collectionsUsed } = event.payload?.dataAvailability || {};
      return `${imageCount || 0} imágenes de ${collectionsUsed?.length || 0} colecciones`;
    
    case 'GEOSPATIAL_AGENT_ERROR':
      return `Error: ${event.payload?.message || 'Unknown'}`;
    
    default:
      return event.event_type;
  }
}
