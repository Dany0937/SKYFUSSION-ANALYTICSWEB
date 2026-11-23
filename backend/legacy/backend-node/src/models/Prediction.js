import { getSession } from '../config/database.js';
import { v4 as uuidv4 } from 'uuid';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('models:Prediction');

export class Prediction {
  static async create(data) {
    const session = await getSession();
    const id = data.id || uuidv4();

    try {
      const result = await session.run(
        `CREATE (p:Prediction {
          id: $id,
          zoneId: $zoneId,
          type: $type,
          modelVersion: $modelVersion,
          parameters: $parameters,
          inputData: $inputData,
          results: $results,
          confidence: $confidence,
          requestedAt: datetime($requestedAt),
          completedAt: datetime($completedAt),
          status: $status,
          metrics: $metrics
        })
        RETURN p`,
        {
          id,
          zoneId: data.zoneId,
          type: data.type || 'ndvi_trend',
          modelVersion: data.modelVersion || '1.0',
          parameters: JSON.stringify(data.parameters || {}),
          inputData: JSON.stringify(data.inputData || {}),
          results: JSON.stringify(data.results || {}),
          confidence: data.confidence || 0,
          requestedAt: data.requestedAt || new Date().toISOString(),
          completedAt: data.completedAt || new Date().toISOString(),
          status: data.status || 'pending',
          metrics: JSON.stringify(data.metrics || {})
        }
      );

      logger.info('Prediction created', { id, zoneId: data.zoneId, type: data.type });
      return this.format(result.records[0].get('p'));
    } finally {
      await session.close();
    }
  }

  static async findByZone(zoneId, options = {}) {
    const session = await getSession();

    try {
      const query = `MATCH (z:Zone {id: $zoneId})-[:HAS_PREDICTION]->(p:Prediction) RETURN p ORDER BY p.requestedAt DESC`;
      const result = await session.run(query, { zoneId });

      return result.records.map(record => this.format(record.get('p')));
    } finally {
      await session.close();
    }
  }

  static async findById(id) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (p:Prediction {id: $id}) RETURN p`,
        { id }
      );

      if (result.records.length === 0) return null;
      return this.format(result.records[0].get('p'));
    } finally {
      await session.close();
    }
  }

  static async findByStatus(status) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (p:Prediction {status: $status}) RETURN p ORDER BY p.requestedAt DESC`,
        { status }
      );

      return result.records.map(record => this.format(record.get('p')));
    } finally {
      await session.close();
    }
  }

  static async updateStatus(id, status, results = null) {
    const session = await getSession();

    try {
      const params = { id, status };

      let query;
      if (results) {
        query = `MATCH (p:Prediction {id: $id})
                 SET p.status = $status,
                     p.results = $results,
                     p.completedAt = datetime()
                 RETURN p`;
        params.results = JSON.stringify(results);
      } else {
        query = `MATCH (p:Prediction {id: $id})
                 SET p.status = $status
                 RETURN p`;
      }

      const result = await session.run(query, params);

      if (result.records.length === 0) return null;
      logger.info('Prediction status updated', { id, status });
      return this.format(result.records[0].get('p'));
    } finally {
      await session.close();
    }
  }

  static format(node) {
    const props = node.properties;
    return {
      id: props.id,
      zoneId: props.zoneId,
      type: props.type,
      modelVersion: props.modelVersion,
      parameters: JSON.parse(props.parameters || '{}'),
      inputData: JSON.parse(props.inputData || '{}'),
      results: JSON.parse(props.results || '{}'),
      confidence: props.confidence,
      requestedAt: props.requestedAt ? props.requestedAt.toString() : null,
      completedAt: props.completedAt ? props.completedAt.toString() : null,
      status: props.status,
      metrics: JSON.parse(props.metrics || '{}')
    };
  }
}
