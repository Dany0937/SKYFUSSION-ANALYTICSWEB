---
title: API Reference — Visión General
description: Documentación técnica de los endpoints REST de la API Node.js (Capa 4).
order: 1
---

# API Reference

La API REST es implementada por el backend Node.js + Express y expone los servicios de la plataforma.

## Base URL

```
http://localhost:3000/api/v1
```

## Autenticación

Todas las solicitudes deben incluir un token JWT en el header `Authorization: Bearer <token>`.

## Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/demo/metrics` | Métricas en tiempo real |
| GET | `/api/v1/zones` | Listar zonas |
| POST | `/api/v1/zones` | Crear zona |
| GET | `/api/v1/stations` | Listar estaciones |
| POST | `/api/v1/stations` | Crear estación |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/alerts` | Alertas activas |

## Tecnologías

| Tecnología | Versión |
|------------|---------|
| Node.js | 20.x |
| Express | 4.18.x |
| Neo4j Driver | 5.18 |
| PostgreSQL + PostGIS | 16 |
| RabbitMQ | 3.13 |
