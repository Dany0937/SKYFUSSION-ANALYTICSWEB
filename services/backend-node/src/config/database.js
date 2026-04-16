import neo4j from 'neo4j-driver';
import dotenv from 'dotenv';
import { createLogger } from '../utils/logger.js';

dotenv.config();

const logger = createLogger('database');

const config = {
  uri: process.env.NEO4J_URI || 'bolt://localhost:7687',
  auth: {
    username: process.env.NEO4J_USER || 'neo4j',
    password: process.env.NEO4J_PASSWORD || 'password'
  },
  database: process.env.NEO4J_DATABASE || 'neo4j',
  maxConnectionPoolSize: 50,
  connectionAcquisitionTimeout: 10000
};

let driver = null;

export async function initializeDatabase() {
  try {
    driver = neo4j.driver(config.uri, config.auth, {
      maxConnectionPoolSize: config.maxConnectionPoolSize,
      connectionAcquisitionTimeout: config.connectionAcquisitionTimeout
    });

    await driver.verifyConnectivity();
    logger.info('Neo4j connection established successfully', {
      uri: config.uri,
      database: config.database
    });

    await createConstraints();
    return driver;
  } catch (error) {
    logger.error('Failed to initialize Neo4j connection', { error: error.message });
    throw error;
  }
}

async function createConstraints() {
  const session = driver.session({ database: config.database });
  
  try {
    await session.run(`
      CREATE CONSTRAINT ano_id_unique IF NOT EXISTS
      FOR (a:Ano) REQUIRE a.id IS UNIQUE
    `);
    
    await session.run(`
      CREATE CONSTRAINT medicion_id_unique IF NOT EXISTS
      FOR (m:MedicionCaudal) REQUIRE m.id IS UNIQUE
    `);
    
    await session.run(`
      CREATE CONSTRAINT zone_id_unique IF NOT EXISTS
      FOR (z:Zone) REQUIRE z.id IS UNIQUE
    `);
    
    await session.run(`
      CREATE CONSTRAINT station_id_unique IF NOT EXISTS
      FOR (s:Station) REQUIRE s.id IS UNIQUE
    `);
    
    logger.info('Database constraints created successfully');
  } finally {
    await session.close();
  }
}

export function getDriver() {
  if (!driver) {
    throw new Error('Database not initialized. Call initializeDatabase() first.');
  }
  return driver;
}

export async function getSession() {
  const driver = getDriver();
  return driver.session({ database: config.database });
}

export async function closeDatabase() {
  if (driver) {
    await driver.close();
    logger.info('Neo4j connection closed');
  }
}

export { neo4j };
