import neo4j from 'neo4j-driver';
import dotenv from 'dotenv';

dotenv.config();

const uri = process.env.NEO4J_URI || 'bolt://localhost:7687';
const user = process.env.NEO4J_USER || 'neo4j';
const password = process.env.NEO4J_PASSWORD || 'password';
const database = process.env.NEO4J_DATABASE || 'neo4j';

async function initializeDatabase() {
  console.log('🔧 Initializing Skyfusion Analytics Database...\n');
  console.log(`📍 Connection: ${uri}`);
  console.log(`👤 User: ${user}`);
  console.log(`🗄️  Database: ${database}\n`);

  const driver = neo4j.driver(uri, neo4j.auth.basic(user, password));

  try {
    await driver.verifyConnectivity();
    console.log('✅ Connection verified successfully!\n');

    const session = driver.session({ database });

    console.log('📊 Creating constraints and indexes...\n');

    const constraints = [
      'CREATE CONSTRAINT ano_id_unique IF NOT EXISTS FOR (a:Ano) REQUIRE a.id IS UNIQUE',
      'CREATE CONSTRAINT medicion_id_unique IF NOT EXISTS FOR (m:MedicionCaudal) REQUIRE m.id IS UNIQUE',
      'CREATE CONSTRAINT zone_id_unique IF NOT EXISTS FOR (z:Zone) REQUIRE z.id IS UNIQUE',
      'CREATE CONSTRAINT station_id_unique IF NOT EXISTS FOR (s:Station) REQUIRE s.id IS UNIQUE'
    ];

    for (const constraint of constraints) {
      try {
        await session.run(constraint);
        console.log(`   ✅ ${constraint.split('FOR')[1].split(')')[0].trim()}`);
      } catch (err) {
        if (err.message.includes('already exists')) {
          console.log(`   ⏭️  Already exists: ${constraint.split('FOR')[1].split(')')[0].trim()}`);
        } else {
          throw err;
        }
      }
    }

    console.log('\n📝 Creating initial data sample...\n');

    const sampleData = `
      // Create sample year
      CREATE (a:Ano {
        id: 'year-2026',
        numero: 2026,
        estado: 'activo',
        fechaCreacion: datetime()
      })

      // Create sample zone (Cuenca del Rio Combeima)
      CREATE (z:Zone {
        id: 'zone-combeima',
        name: 'Cuenca del Rio Combeima',
        areaHa: 12450.75,
        tipoZona: 'estudio_hidrologico',
        elevacionMinM: 800,
        elevacionMaxM: 4200,
        createdAt: datetime()
      })

      // Create sample stations
      CREATE (s1:Station {
        id: 'station-poblado',
        name: 'Estacion Poblado',
        type: 'hydrological',
        lat: 4.4810,
        lon: -75.1995,
        status: 'active'
      })

      CREATE (s2:Station {
        id: 'station-alto',
        name: 'Estacion Alto Combeima',
        type: 'weather',
        lat: 4.52,
        lon: -75.22,
        status: 'active'
      })

      // Create relationships
      WITH s1, s2, z
      CREATE (z)-[:CONTAINS]->(s1)
      CREATE (z)-[:CONTAINS]->(s2)
      CREATE (s1)-[:CONNECTS_TO {distance_km: 2.5}]->(s2)
    `;

    await session.run(sampleData);
    console.log('   ✅ Sample data created');

    await session.close();

    console.log('\n✨ Database initialization completed successfully!\n');
    console.log('📋 Sample entities created:');
    console.log('   • Year: 2026');
    console.log('   • Zone: Cuenca del Rio Combeima');
    console.log('   • Stations: 2 (Poblado, Alto Combeima)\n');

  } catch (error) {
    console.error('❌ Database initialization failed:', error.message);
    process.exit(1);
  } finally {
    await driver.close();
  }
}

initializeDatabase();
