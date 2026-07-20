---
title: Visión General de la Arquitectura
description: Arquitectura Híbrida por Capas + Event-Driven para procesamiento geoespacial y analítica ambiental.
order: 1
---

# Arquitectura de Software — Visión General

**Versión:** 1.0
**Tipo de Arquitectura:** Híbrida (Layered + Event-Driven)

El sistema implementa una **Arquitectura Híbrida** que combina dos estilos arquitectónicos:

- **Arquitectura por Capas (Layered Architecture)** para organizar la lógica de negocio, procesamiento y presentación.
- **Arquitectura Orientada a Eventos (Event-Driven Architecture)** para permitir la comunicación asíncrona entre agentes inteligentes especializados.

Esta combinación proporciona una solución modular, escalable y desacoplada, facilitando el procesamiento distribuido de imágenes satelitales, análisis mediante inteligencia artificial y generación automática de reportes.

## Arquitectura de 6 Capas

```
┌─────────────────────────────────────────────┐
│ Capa 5 - Presentación (React)               │
├─────────────────────────────────────────────┤
│ Capa 4 - Backend API (Node.js + Express)    │
├─────────────────────────────────────────────┤
│ Capa 3 - Agentes IA / ML                    │
├─────────────────────────────────────────────┤
│ Capa 2 - Procesamiento Geoespacial          │
├─────────────────────────────────────────────┤
│ Capa 1 - Adquisición de Datos (GEE)         │
├─────────────────────────────────────────────┤
│ Capa 0 - Infraestructura                    │
└─────────────────────────────────────────────┘
```

## Principios de Diseño

- **Bajo Acoplamiento:** Cada capa solo se comunica con la capa adyacente.
- **Alta Cohesión:** Cada capa tiene una responsabilidad única y bien definida.
- **Comunicación Vertical Estricta:** Una capa nunca salta a otra no adyacente.
- **Versiones Fijadas:** Todas las tecnologías usan versiones específicas para evitar conflictos de despliegue.
