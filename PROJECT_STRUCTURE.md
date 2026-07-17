# Skyfusion Analytics - Project Structure

## Overview

Skyfusion Analytics es una plataforma SaaS para análisis multitemporal y predicción ambiental enfocada en el monitoreo de cuencas hidrográficas.

## Directory Structure

```
Skyfusion-Analytics/
├── README.md                      # Project documentation
├── LICENSE                        # License file
├── docker-compose.yml             # Docker Compose (all services + agents)
│
├── services/                      # Microservices
│   └── backend-node/              # Node.js API (Express + Neo4j)
│       ├── src/
│       │   ├── controllers/       # Request handlers
│       │   ├── services/          # Business logic, eventBus, ingestion
│       │   ├── models/            # Database models
│       │   ├── routes/            # API routes
│       │   ├── middleware/        # Express middleware
│       │   ├── utils/             # Utilities
│       │   ├── config/            # Configuration
│       │   └── app.js             # Application entry
│       └── package.json
│
├── agents/                        # Agent-based components
│   ├── orchestrator.js           # Main orchestrator (Node.js)
│   ├── data-ingestion-agent.js   # Data ingestion agent (Node.js)
│   ├── analysis-agent.js          # Analysis agent (Node.js)
│   ├── prediction-agent.js        # ML prediction agent (Node.js)
│   │
│   └── python/                    # Python agents (Azure architecture)
│       ├── Dockerfile             # Multi-stage Docker build
│       ├── .env.example           # Environment template
│       │
│       ├── base/                  # Shared Python base layer
│       │   ├── __init__.py
│       │   ├── agent_base.py      # Abstract BaseAgent class
│       │   ├── event_bus.py       # RabbitMQ / EventEmitter client
│       │   ├── config.py          # YAML + ENV config loader
│       │   ├── logger.py          # JSON structured logging
│       │   └── health.py          # Health checks + metrics
│       │
│       ├── geospatial_agent/      # GEE satellite imagery download
│       │   ├── __init__.py
│       │   ├── agent.py           # GeospatialAgent (main)
│       │   ├── gee_client.py      # Earth Engine API wrapper
│       │   ├── downloader.py      # Async download manager
│       │   ├── metadata.py        # Scene metadata organizer
│       │   └── requirements.txt
│       │
│       ├── vision_agent/          # Raster/Vision processing
│       │   ├── __init__.py
│       │   ├── agent.py           # VisionAgent (main)
│       │   ├── processors/
│       │   │   ├── indices.py     # NDVI, NDWI, EVI, NDBI, MNDWI
│       │   │   ├── calibration.py # Radiometric calibration
│       │   │   ├── morphology.py  # Morphological operations
│       │   │   ├── segmentation.py# Water/vegetation segmentation
│       │   │   └── raster_io.py   # GeoTIFF read/write
│       │   └── requirements.txt
│       │
│       ├── oracle_agent/          # ML prediction (LSTM-CNN)
│       │   ├── __init__.py
│       │   ├── agent.py           # OracleAgent + AlertSystem
│       │   ├── lstm_cnn_model.py  # TensorFlow model definition
│       │   └── requirements.txt
│       │
│       └── reporting_agent/       # LLM report generation
│           ├── __init__.py
│           ├── agent.py           # ReportingAgent (multi-provider)
│           └── requirements.txt
│
├── skills/                       # Reusable skill modules
│   ├── geo_tools/                # Geospatial calculations
│   │   ├── index.js
│   │   └── package.json
│   ├── vision_tools/              # Computer vision (placeholder)
│   │   ├── index.js
│   │   └── package.json
│   └── ml_tools/                  # Machine learning utilities
│       ├── index.js
│       └── package.json
│
├── shared/                       # Shared resources
│   └── events/                   # Event schemas and types
│
├── data/                         # Data storage
│   ├── raw/                      # Raw data files
│   └── processed/                # Processed outputs
│
├── docs/                         # Documentation
│   ├── AGENTS_STRUCTURE.md       # Agent structure reference
│   ├── AGENTS_COMPLETE_STRUCTURE.md # Full multi-agent architecture
│   └── README.md                 # Doc index
│
├── models/                       # Trained ML models
│
├── nginx/                        # Reverse proxy config
│   ├── nginx.conf
│   └── ssl/                      # TLS certificates
│
├── monitoring/                   # Observability
│   ├── prometheus.yml
│   └── grafana/
│       └── dashboards/
│
├── config/                       # Shared configuration
│   └── agents.yaml               # Agent orchestration config
│
├── .github/                      # GitHub workflows
│
└── .devcontainer/                # VS Code dev container
```

## Architecture

### Backend (Node.js)

- **Express.js** - HTTP API framework
- **Neo4j 5.18** - Graph database for geospatial relationships
- **PostgreSQL 16 + PostGIS 3.4** - Relational + spatial data
- **RabbitMQ** - Message broker for event-driven communication
- **EventEmitter** - Internal event system (Node.js)

### Python Agents (Azure Architecture)

Autonomous components with unique responsibility, communicating via RabbitMQ:

| Agent | Type | Responsibility | Input Event | Output Event |
|-------|------|---------------|-------------|--------------|
| **GeospatialAgent** | Python | GEE satellite download & ingestion | `analysis:requested` | `data:ingested` |
| **VisionAgent** | Python | NDVI/NDWI/EVI calculation + segmentation | `data:ingested` | `analysis:completed` |
| **OracleAgent** | Python | LSTM-CNN prediction + alert classification | `analysis:completed` | `prediction:completed` |
| **ReportingAgent** | Python | LLM-based report generation | `prediction:completed` | `report:ready` |

### Node.js Agents

| Agent | Responsibility | Skills Used |
|-------|----------------|-------------|
| **DataIngestionAgent** | IoT sensor data ingestion | `geo_tools` |
| **AnalysisAgent** | NDVI/NDWI calculations | `geo_tools`, `vision_tools` |
| **PredictionAgent** | ML-based flow predictions | `ml_tools` |
| **AgentOrchestrator** | Pipeline orchestration + agent lifecycle | All |

### Skills

Reusable modules that agents can utilize:

1. **geo_tools** - Geospatial calculations and GeoJSON validation
2. **vision_tools** - Image processing utilities
3. **ml_tools** - Machine learning utilities

## Getting Started

### Prerequisites

- Node.js 20.x
- Python 3.11+
- Docker + Docker Compose
- Neo4j 5.18 (or AuraDB)
- RabbitMQ 3.13 (or cloud AMQP)

### Quick Start

```bash
# Backend
cd services/backend-node
npm install
npm run dev

# Python agents (dev mode - local event emitter)
cd agents/python
pip install -r geospatial_agent/requirements.txt
python -m geospatial_agent.agent

# Full stack (Docker)
docker compose --profile all up -d
```

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend API | Node.js | 20.x |
| HTTP Framework | Express.js | 4.18.x |
| Graph Database | Neo4j | 5.18 |
| Relational DB | PostgreSQL + PostGIS | 16 |
| Message Broker | RabbitMQ | 3.13 |
| Python Runtime | Python | 3.11+ |
| ML Framework | TensorFlow | 2.15+ |
| Computer Vision | OpenCV | 4.9+ |
| Satellite Imagery | Google Earth Engine | API |
| LLM (Local) | Ollama (Llama 3.2) | Latest |
| Container | Docker | 24+ |
| Orchestration | Docker Compose | 2.x |
| Monitoring | Prometheus + Grafana | Latest |

## License

PROPRIETARY - Skyfusion Team
