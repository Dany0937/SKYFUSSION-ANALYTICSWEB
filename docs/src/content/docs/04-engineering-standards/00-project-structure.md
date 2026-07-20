---
title: Estructura del Proyecto
description: Organización de directorios y componentes del repositorio.
order: 1
---

# Estructura del Proyecto

```
Skyfusion-Analytics/
├── README.md
├── docker-compose.yml             # Orquestación de servicios
│
├── services/
│   └── backend-node/              # API Node.js (Express + Neo4j)
│       ├── src/
│       │   ├── controllers/       # Request handlers
│       │   ├── services/          # Business logic, eventBus
│       │   ├── models/            # Database models
│       │   ├── routes/            # API routes
│       │   ├── middleware/        # Express middleware
│       │   ├── utils/             # Utilities
│       │   ├── config/            # Configuration
│       │   └── app.js             # Entry point
│       └── package.json
│
├── agents/                        # Agentes inteligentes
│   ├── orchestrator.js            # Orchestrator (Node.js)
│   ├── data-ingestion-agent.js
│   ├── analysis-agent.js
│   ├── prediction-agent.js
│   └── python/                    # Agentes Python
│       ├── Dockerfile
│       ├── base/                  # Capa base compartida
│       ├── geospatial_agent/      # GEE download
│       ├── vision_agent/          # Raster/Vision processing
│       ├── oracle_agent/          # LSTM-CNN prediction
│       └── reporting_agent/       # LLM report generation
│
├── skills/                        # Módulos reutilizables
│   ├── geo_tools/                 # Cálculos geoespaciales
│   ├── vision_tools/              # Visión computacional
│   └── ml_tools/                  # ML utilities
│
├── shared/events/                 # Esquemas de eventos
├── data/                          # Almacenamiento de datos
├── docs/                          # Documentación (Astro + Starlight)
├── nginx/                         # Configuración reverse proxy
├── monitoring/                    # Prometheus + Grafana
├── config/                        # Configuración compartida
├── .github/                       # GitHub workflows
└── .devcontainer/                 # Dev Container
```
