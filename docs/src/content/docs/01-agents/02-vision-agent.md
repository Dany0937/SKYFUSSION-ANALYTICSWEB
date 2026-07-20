---
title: VisionAgent
description: Procesamiento geoespacial, índices espectrales y segmentación de imágenes.
order: 3
---

# VisionAgent

Realiza el procesamiento geoespacial y la extracción de características. Procesa imágenes satelitales para calcular índices de vegetación, agua y realizar segmentaciones.

## Funciones

- Corrección de imágenes (calibración radiométrica)
- Cálculo de NDVI, NDWI, EVI, NDBI, MNDWI
- Operaciones morfológicas
- Segmentación de agua/vegetación
- Generación de capas raster
- Extracción de variables ambientales

## Tecnologías

- Python
- OpenCV
- Rasterio
- GDAL
- NumPy

## Eventos

| Tipo | Dirección | Descripción |
|------|-----------|-------------|
| `data:ingested` | Entrada | Imágenes listas para procesar |
| `analysis:completed` | Salida | Análisis finalizado con resultados |

## Índices Soportados

| Índice | Fórmula | Aplicación |
|--------|---------|------------|
| NDVI | (NIR - Red) / (NIR + Red) | Vigor vegetal |
| NDWI | (Green - NIR) / (Green + NIR) | Cuerpos de agua |
| EVI | 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1) | Vegetación (corregido atmósfera) |
| NDBI | (SWIR - NIR) / (SWIR + NIR) | Áreas urbanas |
| MNDWI | (Green - SWIR) / (Green + SWIR) | Agua (precisión mejorada) |

## Implementación

```
agents/python/vision_agent/
├── agent.py
├── processors/
│   ├── indices.py       # NDVI, NDWI, EVI, NDBI, MNDWI
│   ├── calibration.py   # Calibración radiométrica
│   ├── morphology.py    # Operaciones morfológicas
│   ├── segmentation.py  # Segmentación agua/vegetación
│   └── raster_io.py     # GeoTIFF read/write
└── requirements.txt
```
