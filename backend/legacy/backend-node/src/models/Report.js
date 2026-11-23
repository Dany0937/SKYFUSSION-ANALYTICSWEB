import { getSession } from '../config/database.js';
import { v4 as uuidv4 } from 'uuid';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('models:Report');

export class Report {
  static async create(data) {
    const session = await getSession();
    const id = data.id || uuidv4();

    try {
      const result = await session.run(
        `CREATE (r:Report {
          id: $id,
          zoneId: $zoneId,
          pipelineId: $pipelineId,
          title: $title,
          type: $type,
          summary: $summary,
          content: $content,
          alertLevel: $alertLevel,
          recommendations: $recommendations,
          metrics: $metrics,
          generatedAt: datetime($generatedAt),
          createdAt: datetime(),
          metadata: $metadata
        })
        RETURN r`,
        {
          id,
          zoneId: data.zoneId,
          pipelineId: data.pipelineId || '',
          title: data.title || 'Reporte de Análisis Hídrico',
          type: data.type || 'full_analysis',
          summary: data.summary || '',
          content: JSON.stringify(data.content || {}),
          alertLevel: data.alertLevel || 'verde',
          recommendations: JSON.stringify(data.recommendations || []),
          metrics: JSON.stringify(data.metrics || {}),
          generatedAt: data.generatedAt || new Date().toISOString(),
          metadata: JSON.stringify(data.metadata || {})
        }
      );

      logger.info('Report created', { id, zoneId: data.zoneId, type: data.type });
      return this.format(result.records[0].get('r'));
    } finally {
      await session.close();
    }
  }

  static async findByZone(zoneId, options = {}) {
    const session = await getSession();

    try {
      const query = `MATCH (z:Zone {id: $zoneId})-[:HAS_REPORT]->(r:Report) RETURN r ORDER BY r.generatedAt DESC`;
      const result = await session.run(query, { zoneId });

      return result.records.map(record => this.format(record.get('r')));
    } finally {
      await session.close();
    }
  }

  static async findById(id) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (r:Report {id: $id}) RETURN r`,
        { id }
      );

      if (result.records.length === 0) return null;
      return this.format(result.records[0].get('r'));
    } finally {
      await session.close();
    }
  }

  static async findLatestByZone(zoneId, limit = 5) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (r:Report {zoneId: $zoneId})
         RETURN r
         ORDER BY r.generatedAt DESC
         LIMIT $limit`,
        { zoneId, limit: parseInt(limit, 10) }
      );

      return result.records.map(record => this.format(record.get('r')));
    } finally {
      await session.close();
    }
  }

  static async findByAlertLevel(level) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (r:Report {alertLevel: $level}) RETURN r ORDER BY r.generatedAt DESC`,
        { level }
      );

      return result.records.map(record => this.format(record.get('r')));
    } finally {
      await session.close();
    }
  }

  static format(node) {
    const props = node.properties;
    return {
      id: props.id,
      zoneId: props.zoneId,
      pipelineId: props.pipelineId,
      title: props.title,
      type: props.type,
      summary: props.summary,
      content: JSON.parse(props.content || '{}'),
      alertLevel: props.alertLevel,
      recommendations: JSON.parse(props.recommendations || '[]'),
      metrics: JSON.parse(props.metrics || '{}'),
      generatedAt: props.generatedAt ? props.generatedAt.toString() : null,
      createdAt: props.createdAt ? props.createdAt.toString() : null,
      metadata: JSON.parse(props.metadata || '{}')
    };
  }
}
