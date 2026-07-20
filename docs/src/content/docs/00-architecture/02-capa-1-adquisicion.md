---
title: Capa 1 — Adquisición de Datos
description: Obtención automática de imágenes satelitales desde Google Earth Engine.
order: 3
---

# Capa 1 – Adquisición de Datos

Esta capa obtiene automáticamente las imágenes satelitales necesarias para el procesamiento.

## Responsabilidades

- Consulta de Google Earth Engine
- Descarga automática
- Filtrado temporal
- Filtrado espacial
- Exportación de imágenes

## Tecnologías

| Tecnología | Propósito |
|------------|-----------|
| Google Earth Engine API | Acceso a Sentinel, Landsat y series históricas |
| Python | Scripts de consulta y descarga |

## Flujo de Trabajo

1. El **GeospatialAgent** recibe un evento `analysis:requested`
2. Consulta colecciones satelitales en GEE
3. Filtra por fechas y porcentaje de nubes
4. Descarga las imágenes seleccionadas
5. Organiza metadatos
6. Emite evento `DATA_INGESTED`
