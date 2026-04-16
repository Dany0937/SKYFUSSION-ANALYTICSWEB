# Skyfusion Analytics - Project Structure

## Overview

Skyfusion Analytics es una plataforma SaaS para análisis multitemporal y predicción ambiental enfocada en el monitoreo de cuencas hidrográficas.

## Directory Structure

```
Skyfusion-Analytics/
├── README.md                      # Project documentation
├── LICENSE                        # License file
│
├── services/                      # Microservices
│   └── backend-node/              # Node.js API (Express + Neo4j)
│       ├── src/
│       │   ├── controllers/       # Request handlers
│       │   ├── services/          # Business logic
│       │   ├── models/            # Database models
│       │   ├── routes/            # API routes
│       │   ├── middleware/        # Express middleware
│       │   ├── utils/             # Utilities
│       │   ├── config/            # Configuration
│       │   └── app.js             # Application entry
│       └── package.json
│
├── agents/                        # Agent-based components
│   ├── orchestrator.js           # Main orchestrator
│   ├── data-ingestion-agent.js   # Data ingestion agent
│   ├── analysis-agent.js          # Analysis agent
│   └── prediction-agent.js        # ML prediction agent
│
├── skills/                       # Reusable skill modules
│   ├── geo_tools/                # Geospatial tools
│   │   ├── index.js
│   │   └── package.json
│   ├── vision_tools/              # Computer vision tools
│   │   ├── index.js
│   │   └── package.json
│   └── ml_tools/                  # Machine learning tools
│       ├── index.js
│       └── package.json
│
├── shared/                       # Shared resources
│   └── events/                   # Event schemas and types
│
├── data/                         # Data storage
│   └── raw/                      # Raw data files
│
├── docs/                         # Additional documentation
│
├── .github/                      # GitHub workflows
│
└── .devcontainer/                # VS Code dev container
```

## Architecture

### Backend (Node.js)

- **Express.js** - HTTP API framework
- **Neo4j** - Graph database for geospatial relationships
- **EventEmitter** - Internal event system for consistency

### Agents

Autonomous components that handle specific responsibilities:

1. **Data Ingestion Agent** - Handles data ingestion from sensors
2. **Analysis Agent** - Performs NDVI/NDWI calculations
3. **Prediction Agent** - ML-based flow predictions

### Skills

Reusable modules that agents can utilize:

1. **geo_tools** - Geospatial calculations and validation
2. **vision_tools** - Image processing (placeholder)
3. **ml_tools** - Machine learning utilities (placeholder)

## Getting Started

See `services/backend-node/README.md` for backend setup instructions.

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend | Node.js | 20.x |
| API | Express.js | 4.18.x |
| Database | Neo4j | 5.18 |
| Python | Python | 3.11+ |
| ML | TensorFlow | 2.15+ |
| Vision | OpenCV | 4.9+ |

## License

PROPRIETARY - All rights reserved
