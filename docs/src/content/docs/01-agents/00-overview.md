---
title: Sistema de Agentes — Visión General
description: Sistema de agentes inteligentes autogestionados con comunicación basada en eventos.
order: 1
---

# Sistema de Agentes Autogestionados

La plataforma implementa un sistema basado en **Agentes Inteligentes Autogestionados**, donde cada agente ejecuta una única responsabilidad de negocio y responde automáticamente a los eventos publicados en un bus de mensajería.

Este enfoque elimina las dependencias directas entre módulos y permite que el procesamiento ocurra de forma distribuida y asíncrona.

## Principios

Cada agente:
- Se ejecuta como un proceso independiente
- Escucha eventos específicos
- Ejecuta una tarea especializada
- Publica un nuevo evento cuando finaliza
- No necesita conocer la existencia de otros agentes

## Regla de Oro

> Ningún agente debe conocer la estructura interna de otro; solo deben reaccionar a los eventos del Orchestrator.

## Flujo General

1. Se inicia una solicitud desde el frontend
2. El Backend publica un evento inicial en RabbitMQ
3. El **GeospatialAgent** descarga las imágenes desde GEE
4. El **VisionAgent** procesa la información (NDVI/NDWI)
5. El **OracleAgent** realiza las predicciones
6. El **ReportingAgent** genera el reporte
7. El Backend notifica al usuario vía WebSocket

Todo el flujo ocurre sin llamadas directas entre agentes.

## Protocolo de Comunicación

La comunicación entre agentes se realiza exclusivamente mediante el **Event Bus (RabbitMQ)**. Los agentes se suscriben a colas específicas y publican resultados en colas de salida.
