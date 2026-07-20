---
title: Capa 4 — Backend API
description: Núcleo de comunicación del sistema — REST API, autenticación, WebSockets y orquestación.
order: 6
---

# Capa 4 – Backend API

Esta capa representa el núcleo de comunicación del sistema. Centraliza todas las solicitudes provenientes del frontend y coordina la interacción entre los distintos servicios y agentes inteligentes.

## Responsabilidades

- Exponer servicios REST
- Gestionar autenticación
- Administrar usuarios
- Validar solicitudes
- Publicar eventos
- Orquestar procesos
- Enviar actualizaciones en tiempo real

## Tecnologías

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Node.js | 20.x | Entorno de ejecución |
| Express | 4.18.x | Framework HTTP |
| Socket.IO | — | WebSockets en tiempo real |
| RabbitMQ | 3.13 | Bus de eventos |

## Entradas

- Solicitudes HTTP desde el frontend
- Eventos de los agentes

## Salidas

- Respuestas REST
- Publicación de eventos al bus
- Comunicación con RabbitMQ

## Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/demo/metrics` | GET | Métricas en tiempo real |
| `/api/v1/zones` | CRUD | Gestión de zonas |
| `/api/v1/stations` | CRUD | Estaciones meteorológicas |
| `/api/v1/health` | GET | Health check |
| `/api/v1/alerts` | GET | Alertas ambientales |
