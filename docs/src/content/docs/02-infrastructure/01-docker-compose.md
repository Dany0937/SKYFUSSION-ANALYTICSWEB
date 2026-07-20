---
title: Docker Compose
description: Orquestación de servicios y agentes con Docker Compose.
order: 1
---

# Docker Compose

La plataforma se despliega mediante Docker Compose, que orquesta todos los servicios, agentes y dependencias de infraestructura.

## Servicios

| Servicio | Contenedor | Puerto | Dependencias |
|----------|-----------|--------|-------------|
| `backend` | Node.js + Express | 3000 | neo4j, rabbitmq |
| `rabbitmq` | RabbitMQ 3.13 | 5672, 15672 | — |
| `neo4j` | Neo4j 5.18 | 7687, 7474 | — |
| `postgres` | PostgreSQL 16 + PostGIS | 5432 | — |
| `geospatial-agent` | Python (GEE) | — | rabbitmq |
| `vision-agent` | Python (OpenCV) | — | rabbitmq |
| `oracle-agent` | Python (TensorFlow) | — | rabbitmq |
| `reporting-agent` | Python (LLM) | — | rabbitmq |
| `nginx` | Nginx | 80, 443 | backend |

## Uso

```bash
# Iniciar todos los servicios
docker compose --profile all up -d

# Solo servicios principales (sin agentes Python)
docker compose up -d

# Ver logs
docker compose logs -f
```

## Reproducibilidad

El uso de Docker Compose garantiza que todos los desarrolladores y entornos de despliegue utilizan las mismas versiones de cada componente, evitando conflictos de dependencias.
