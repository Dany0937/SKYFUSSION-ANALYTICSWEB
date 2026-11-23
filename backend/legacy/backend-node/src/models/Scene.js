import { getSession } from '../config/database.js';
import { v4 as uuidv4 } from 'uuid';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('models:Scene');

export class Scene {
  static async create(data) {
    const session = await getSession();
    const id = data.id || uuidv4();

    try {
      const result = await session.run(
        `CREATE (s:Scene {
          id: $id,
          zoneId: $zoneId,
          source: $source,
          sceneId: $sceneId,
          cloudCover: $cloudCover,
          capturedAt: datetime($capturedAt),
          ingestedAt: datetime(),
          compositeType: $compositeType,
          indices: $indices,
          metadata: $metadata,
          status: $status
        })
        RETURN s`,
        {
          id,
          zoneId: data.zoneId,
          source: data.source || 'sentinel-2',
          sceneId: data.sceneId || '',
          cloudCover: data.cloudCover || 0,
          capturedAt: data.capturedAt || new Date().toISOString(),
          compositeType: data.compositeType || 'median',
          indices: JSON.stringify(data.indices || {}),
          metadata: JSON.stringify(data.metadata || {}),
          status: data.status || 'acquired'
        }
      );

      logger.info('Scene created', { id, zoneId: data.zoneId });
      return this.format(result.records[0].get('s'));
    } finally {
      await session.close();
    }
  }

  static async findByZone(zoneId, options = {}) {
    const session = await getSession();

    try {
      const query = `MATCH (z:Zone {id: $zoneId})-[:HAS_SCENE]->(s:Scene) RETURN s ORDER BY s.capturedAt DESC`;
      const result = await session.run(query, { zoneId });

      return result.records.map(record => this.format(record.get('s')));
    } finally {
      await session.close();
    }
  }

  static async findById(id) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (s:Scene {id: $id}) RETURN s`,
        { id }
      );

      if (result.records.length === 0) return null;
      return this.format(result.records[0].get('s'));
    } finally {
      await session.close();
    }
  }

  static async findLatestByZone(zoneId, limit = 10) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (s:Scene {zoneId: $zoneId})
         RETURN s
         ORDER BY s.capturedAt DESC
         LIMIT $limit`,
        { zoneId, limit: parseInt(limit, 10) }
      );

      return result.records.map(record => this.format(record.get('s')));
    } finally {
      await session.close();
    }
  }

  static format(node) {
    const props = node.properties;
    return {
      id: props.id,
      zoneId: props.zoneId,
      source: props.source,
      sceneId: props.sceneId,
      cloudCover: props.cloudCover,
      capturedAt: props.capturedAt ? props.capturedAt.toString() : null,
      ingestedAt: props.ingestedAt ? props.ingestedAt.toString() : null,
      compositeType: props.compositeType,
      indices: JSON.parse(props.indices || '{}'),
      metadata: JSON.parse(props.metadata || '{}'),
      status: props.status
    };
  }
}
