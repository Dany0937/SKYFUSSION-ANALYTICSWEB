import { getSession } from '../config/database.js';
import { v4 as uuidv4 } from 'uuid';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('models:Station');

export class Station {
  static labels = ['Station'];

  static async create(data) {
    const session = await getSession();
    const id = data.id || uuidv4();

    try {
      const result = await session.run(
        `CREATE (s:Station {
          id: $id,
          name: $name,
          type: $type,
          lat: $lat,
          lon: $lon,
          status: $status,
          createdAt: datetime()
        })
        RETURN s`,
        {
          id,
          name: data.name,
          type: data.type,
          lat: data.lat,
          lon: data.lon,
          status: data.status || 'active'
        }
      );

      logger.info('Station created', { id, name: data.name });
      return this.formatStation(result.records[0].get('s'));
    } finally {
      await session.close();
    }
  }

  static async findAll() {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (s:Station) RETURN s ORDER BY s.name`
      );

      return result.records.map(record => this.formatStation(record.get('s')));
    } finally {
      await session.close();
    }
  }

  static async findById(id) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (s:Station {id: $id}) RETURN s`,
        { id }
      );

      if (result.records.length === 0) return null;
      return this.formatStation(result.records[0].get('s'));
    } finally {
      await session.close();
    }
  }

  static async findNearby(lon, lat, radiusMeters = 5000) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (s:Station)
         WHERE point.distance(
           point({longitude: s.lon, latitude: s.lat}),
           point({longitude: $lon, latitude: $lat})
         ) < $radiusMeters
         RETURN s, point.distance(
           point({longitude: s.lon, latitude: s.lat}),
           point({longitude: $lon, latitude: $lat})
         ) as distance`,
        { lon, lat, radiusMeters }
      );

      return result.records.map(record => ({
        ...this.formatStation(record.get('s')),
        distance: record.get('distance')
      }));
    } finally {
      await session.close();
    }
  }

  static async findByZone(zoneId) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (z:Zone {id: $zoneId})-[:CONTAINS]->(s:Station) RETURN s`,
        { zoneId }
      );

      return result.records.map(record => this.formatStation(record.get('s')));
    } finally {
      await session.close();
    }
  }

  static async updateStatus(id, status) {
    const session = await getSession();

    try {
      await session.run(
        `MATCH (s:Station {id: $id}) SET s.status = $status`,
        { id, status }
      );

      logger.info('Station status updated', { id, status });
      return this.findById(id);
    } finally {
      await session.close();
    }
  }

  static formatStation(node) {
    const props = node.properties;
    return {
      id: props.id,
      name: props.name,
      type: props.type,
      lat: props.lat,
      lon: props.lon,
      status: props.status,
      createdAt: props.createdAt?.toString()
    };
  }
}
