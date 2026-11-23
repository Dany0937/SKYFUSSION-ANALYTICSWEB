import { getSession } from '../config/database.js';
import { v4 as uuidv4 } from 'uuid';
import { createLogger } from '../utils/logger.js';
import { eventBus, EVENTS } from '../services/eventBus.js';

const logger = createLogger('models:MedicionCaudal');

export class MedicionCaudal {
  static labels = ['MedicionCaudal'];

  constructor(data) {
    this.id = data.id || uuidv4();
    this.valor = data.valor;
    this.unidad = data.unidad || 'm3/s';
    this.calidad = data.calidad || 'valid';
    this.timestamp = data.timestamp || new Date().toISOString();
    this.estacionId = data.estacionId;
    this.anoId = data.anoId;
  }

  static async create(data) {
    const session = await getSession();
    const medicion = new MedicionCaudal(data);

    try {
      const result = await session.run(
        `MATCH (a:Ano {id: $anoId})
         CREATE (m:MedicionCaudal {
           id: $id,
           valor: $valor,
           unidad: $unidad,
           calidad: $calidad,
           timestamp: datetime($timestamp)
         })
         CREATE (a)-[:TIENE_MEDICION]->(m)
         RETURN m`,
        {
          id: medicion.id,
          valor: medicion.valor,
          unidad: medicion.unidad,
          calidad: medicion.calidad,
          timestamp: medicion.timestamp,
          anoId: medicion.anoId
        }
      );

      logger.info('Flow measurement created', { 
        id: medicion.id, 
        valor: medicion.valor 
      });

      eventBus.emit(EVENTS.MEASUREMENT_CREATED, {
        type: 'MedicionCaudal',
        id: medicion.id,
        valor: medicion.valor,
        timestamp: medicion.timestamp
      });

      return medicion;
    } finally {
      await session.close();
    }
  }

  static async findByAno(anoId, options = {}) {
    const session = await getSession();
    const limit = options.limit || 100;
    const offset = options.offset || 0;

    try {
      const result = await session.run(
        `MATCH (a:Ano {id: $anoId})-[:TIENE_MEDICION]->(m:MedicionCaudal)
         RETURN m 
         ORDER BY m.timestamp DESC
         SKIP $offset
         LIMIT $limit`,
        { anoId, offset, limit }
      );

      return result.records.map(record => ({
        id: record.get('m').properties.id,
        valor: record.get('m').properties.valor,
        unidad: record.get('m').properties.unidad,
        calidad: record.get('m').properties.calidad,
        timestamp: record.get('m').properties.timestamp.toString()
      }));
    } finally {
      await session.close();
    }
  }

  static async findByDateRange(anoId, startDate, endDate) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (a:Ano {id: $anoId})-[:TIENE_MEDICION]->(m:MedicionCaudal)
         WHERE m.timestamp >= datetime($startDate) AND m.timestamp <= datetime($endDate)
         RETURN m
         ORDER BY m.timestamp ASC`,
        { anoId, startDate, endDate }
      );

      return result.records.map(record => ({
        id: record.get('m').properties.id,
        valor: record.get('m').properties.valor,
        unidad: record.get('m').properties.unidad,
        calidad: record.get('m').properties.calidad,
        timestamp: record.get('m').properties.timestamp.toString()
      }));
    } finally {
      await session.close();
    }
  }

  static async getStatistics(anoId) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (a:Ano {id: $anoId})-[:TIENE_MEDICION]->(m:MedicionCaudal)
         WHERE m.calidad = 'valid'
         RETURN avg(m.valor) as promedio,
                min(m.valor) as minimo,
                max(m.valor) as maximo,
                count(m) as total_mediciones`,
        { anoId }
      );

      if (result.records.length === 0) {
        return null;
      }

      const stats = result.records[0];
      return {
        promedio: stats.get('promedio'),
        minimo: stats.get('minimo'),
        maximo: stats.get('maximo'),
        totalMediciones: stats.get('total_mediciones').toInt()
      };
    } finally {
      await session.close();
    }
  }

  static async delete(id) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (m:MedicionCaudal {id: $id})
         DETACH DELETE m
         RETURN count(m) as deleted`,
        { id }
      );

      const deleted = result.records[0].get('deleted') > 0;
      
      if (deleted) {
        eventBus.emit(EVENTS.MEASUREMENT_DELETED, { type: 'MedicionCaudal', id });
      }
      
      return deleted;
    } finally {
      await session.close();
    }
  }
}
