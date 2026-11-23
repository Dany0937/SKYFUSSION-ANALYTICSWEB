# Skyfusion Analytics - Backend API

## Overview

Backend API para Skyfusion Analytics - Plataforma de monitoreo de cuencas hidrográficas.

## Tech Stack

- **Node.js 20.x LTS** - Runtime
- **Express.js 4.18.x** - HTTP Framework
- **Neo4j 5.18** - Graph Database
- **TypeScript** - (Future migration)

## Project Structure

```
backend-node/
├── src/
│   ├── controllers/     # HTTP request handlers
│   ├── services/        # Business logic layer
│   ├── models/          # Database models (Neo4j)
│   ├── routes/          # API route definitions
│   │   └── v1/          # API v1 endpoints
│   ├── middleware/      # Express middleware
│   ├── utils/           # Utility functions
│   ├── config/          # Configuration
│   └── scripts/         # Database scripts
├── tests/               # Unit tests
├── logs/                # Application logs
└── package.json
```

## Quick Start

### Prerequisites

- Node.js 20.x
- Neo4j 5.18+

### Installation

```bash
cd services/backend-node
npm install
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your Neo4j credentials.

### Initialize Database

```bash
npm run db:init
```

### Run Development Server

```bash
npm run dev
```

### Run Production Server

```bash
npm start
```

## API Endpoints

### Health Check
- `GET /api/v1/health` - Check API status

### Zones
- `POST /api/v1/zones` - Create zone (GeoJSON)
- `GET /api/v1/zones` - List all zones
- `GET /api/v1/zones/:id` - Get zone by ID
- `POST /api/v1/zones/:id/stations` - Add station to zone

### Stations
- `POST /api/v1/stations` - Create station
- `GET /api/v1/stations` - List all stations
- `GET /api/v1/stations/nearby` - Find nearby stations
- `PATCH /api/v1/stations/:id/status` - Update station status

### Measurements
- `POST /api/v1/measurements/years` - Create year
- `GET /api/v1/measurements/years` - List all years
- `GET /api/v1/measurements/years/:id/measurements` - List measurements
- `GET /api/v1/measurements/years/:id/statistics` - Get statistics
- `POST /api/v1/measurements/ingest` - Ingest single measurement
- `POST /api/v1/measurements/ingest/batch` - Batch ingest

### Alerts
- `POST /api/v1/alerts/classify` - Classify alert
- `GET /api/v1/alerts/active` - Get active alerts
- `GET /api/v1/alerts/history` - Get alert history

## Event System

The backend uses an EventEmitter-based event system for eventual consistency:

```javascript
import { eventBus, EVENTS } from './services/eventBus';

eventBus.on(EVENTS.MEASUREMENT_CREATED, (data) => {
  console.log('New measurement:', data);
});

eventBus.publish(EVENTS.SYNC_REQUIRED, { source: 'sensor-1' });
```

## License

PROPRIETARY - Skyfusion Team
