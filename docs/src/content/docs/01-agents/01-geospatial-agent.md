---
title: GeospatialAgent
description: Agente encargado de descargar imágenes satelitales desde Google Earth Engine.
order: 2
---

# GeospatialAgent

Es el agente encargado de obtener la información satelital desde Google Earth Engine. Su evento de entrada es `analysis:requested` y emite `data:ingested`.

## Funciones

- Consultar colecciones satelitales (Sentinel, Landsat)
- Filtrar por fechas
- Filtrar por porcentaje de nubes
- Descargar imágenes
- Organizar metadatos

## Tecnologías

- Python
- Google Earth Engine API

## Eventos

| Tipo | Dirección | Descripción |
|------|-----------|-------------|
| `analysis:requested` | Entrada | Solicitud de análisis desde el backend |
| `data:ingested` | Salida | Datos satelitales descargados y listos |

## Implementación

```
agents/python/geospatial_agent/
├── agent.py           # GeospatialAgent (main)
├── gee_client.py      # Earth Engine API wrapper
├── downloader.py      # Async download manager
├── metadata.py        # Scene metadata organizer
└── requirements.txt
```
