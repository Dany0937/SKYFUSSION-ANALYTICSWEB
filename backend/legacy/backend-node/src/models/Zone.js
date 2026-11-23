import { getSession } from '../config/database.js';
import { v4 as uuidv4 } from 'uuid';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('models:Zone');

export class Zone {
  static labels = ['Zone'];

  static async create(data) {
    const session = await getSession();
    const id = data.id || uuidv4();

    try {
      const result = await session.run(
        `CREATE (z:Zone {
          id: $id,
          name: $name,
          areaHa: $areaHa,
          boundaryPolygon: $boundaryPolygon,
          createdAt: datetime(),
          tipoZona: $tipoZona,
          elevacionMinM: $elevacionMinM,
          elevacionMaxM: $elevacionMaxM
        })
        RETURN z`,
        {
          id,
          name: data.name,
          areaHa: data.areaHa,
          boundaryPolygon: JSON.stringify(data.boundaryPolygon),
          tipoZona: data.tipoZona || 'estudio_hidrologico',
          elevacionMinM: data.elevacionMinM || null,
          elevacionMaxM: data.elevacionMaxM || null
        }
      );

      logger.info('Zone created', { id, name: data.name });
      return this.formatZone(result.records[0].get('z'));
    } finally {
      await session.close();
    }
  }

  static async findAll() {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (z:Zone) RETURN z ORDER BY z.createdAt DESC`
      );

      return result.records.map(record => this.formatZone(record.get('z')));
    } finally {
      await session.close();
    }
  }

  static async findById(id) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (z:Zone {id: $id}) RETURN z`,
        { id }
      );

      if (result.records.length === 0) return null;
      return this.formatZone(result.records[0].get('z'));
    } finally {
      await session.close();
    }
  }

  static async findStations(zoneId) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (z:Zone {id: $zoneId})-[:CONTAINS]->(s:Station) RETURN s`,
        { zoneId }
      );

      return result.records.map(record => ({
        id: record.get('s').properties.id,
        name: record.get('s').properties.name,
        type: record.get('s').properties.type,
        lat: record.get('s').properties.lat,
        lon: record.get('s').properties.lon,
        status: record.get('s').properties.status
      }));
    } finally {
      await session.close();
    }
  }

  static async addStation(zoneId, stationData) {
    const session = await getSession();

    try {
      const stationId = stationData.id || uuidv4();
      
      await session.run(
        `MATCH (z:Zone {id: $zoneId})
         CREATE (s:Station {
           id: $stationId,
           name: $name,
           type: $type,
           lat: $lat,
           lon: $lon,
           status: $status
         })
         CREATE (z)-[:CONTAINS]->(s)`,
        {
          zoneId,
          stationId,
          name: stationData.name,
          type: stationData.type,
          lat: stationData.lat,
          lon: stationData.lon,
          status: stationData.status || 'active'
        }
      );

      logger.info('Station added to zone', { zoneId, stationId });
      return { id: stationId, ...stationData };
    } finally {
      await session.close();
    }
  }

  static formatZone(node) {
    const props = node.properties;
    return {
      id: props.id,
      name: props.name,
      areaHa: props.areaHa,
      boundaryPolygon: JSON.parse(props.boundaryPolygon || '{}'),
      tipoZona: props.tipoZona,
      elevacionMinM: props.elevacionMinM,
      elevacionMaxM: props.elevacionMaxM,
      createdAt: props.createdAt.toString()
    };
  }
}
