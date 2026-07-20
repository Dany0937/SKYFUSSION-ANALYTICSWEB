---
title: Capa 2 — Procesamiento Geoespacial
description: Algoritmos científicos para transformar imágenes satelitales en información ambiental útil.
order: 4
---

# Capa 2 – Procesamiento Geoespacial

Implementa todos los algoritmos científicos necesarios para transformar las imágenes satelitales en información útil para el análisis ambiental.

## Responsabilidades

- Corrección de imágenes
- Procesamiento raster
- Filtrado de nubes
- Cálculo de NDVI
- Cálculo de NDWI
- Operaciones morfológicas
- Generación de productos intermedios

## Tecnologías

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| GDAL | 3.6.2 | Lectura/escritura de formatos raster y vectorial |
| Rasterio | 1.3.8 | Procesamiento de geoTIFF |
| OpenCV | 4.9+ | Operaciones morfológicas y segmentación |
| NumPy | — | Computación numérica |

## Índices Espectrales

### NDVI (Normalized Difference Vegetation Index)
Mide la densidad de vegetación usando las bandas NIR y Red.

### NDWI (Normalized Difference Water Index)
Detecta cuerpos de agua usando bandas Green y NIR.

### EVI (Enhanced Vegetation Index)
Versión mejorada del NDVI que corrige influencias atmosféricas.
