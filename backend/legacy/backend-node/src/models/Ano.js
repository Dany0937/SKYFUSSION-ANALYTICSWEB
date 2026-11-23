import { getSession } from '../config/database.js';
import { v4 as uuidv4 } from 'uuid';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('models:Ano');

export class Ano {
  static labels = ['Ano'];

  constructor(data) {
    this.id = data.id || uuidv4();
    this.numero = data.numero;
    this.estado = data.estado || 'activo';
    this.fechaCreacion = data.fechaCreacion || new Date().toISOString();
  }

  static async create(data) {
    const session = await getSession();
    const ano = new Ano(data);

    try {
      const result = await session.run(
        `CREATE (a:Ano {
          id: $id,
          numero: $numero,
          estado: $estado,
          fechaCreacion: datetime($fechaCreacion)
        })
        RETURN a`,
        {
          id: ano.id,
          numero: ano.numero,
          estado: ano.estado,
          fechaCreacion: ano.fechaCreacion
        }
      );

      logger.info('Year created', { id: ano.id, numero: ano.numero });
      return ano;
    } finally {
      await session.close();
    }
  }

  static async findAll() {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (a:Ano) RETURN a ORDER BY a.numero DESC`
      );

      return result.records.map(record => ({
        id: record.get('a').properties.id,
        numero: record.get('a').properties.numero,
        estado: record.get('a').properties.estado,
        fechaCreacion: record.get('a').properties.fechaCreacion.toString()
      }));
    } finally {
      await session.close();
    }
  }

  static async findById(id) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (a:Ano {id: $id}) RETURN a`,
        { id }
      );

      if (result.records.length === 0) {
        return null;
      }

      const record = result.records[0].get('a');
      return {
        id: record.properties.id,
        numero: record.properties.numero,
        estado: record.properties.estado,
        fechaCreacion: record.properties.fechaCreacion.toString()
      };
    } finally {
      await session.close();
    }
  }

  static async findByYear(year) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (a:Ano {numero: $numero}) RETURN a`,
        { numero: year }
      );

      if (result.records.length === 0) {
        return null;
      }

      const record = result.records[0].get('a');
      return {
        id: record.properties.id,
        numero: record.properties.numero,
        estado: record.properties.estado,
        fechaCreacion: record.properties.fechaCreacion.toString()
      };
    } finally {
      await session.close();
    }
  }

  static async delete(id) {
    const session = await getSession();

    try {
      const result = await session.run(
        `MATCH (a:Ano {id: $id})
         DETACH DELETE a
         RETURN count(a) as deleted`,
        { id }
      );

      return result.records[0].get('deleted') > 0;
    } finally {
      await session.close();
    }
  }
}
