# Vision Tools - Skyfusion Analytics

Módulo de procesamiento de imágenes satelitales para análisis de morfología fluvial.

## Componentes

### river_morphology.py

Análisis de variabilidad y alteraciones morfológicas del río Combeima (1969-2023).

#### Características

- **NDWI**: Índice de Diferencia Normalizada de Agua
- **Segmentación**: Detección de cauces mediante umbralización
- **Bordes Canny**: Detección de bordes del río
- **Skeletonización**: Extracción de línea central
- **Perfil de anchos**: Análisis de variación longitudinal
- **Comparación multitemporal**: Detección de cambios erosión/deposición

#### Uso

```python
from river_morphology import RiverMorphologyAnalyzer, load_satellite_bands

# Cargar bandas desde archivos TIF
green_band, nir_band = load_satellite_bands('green.tif', 'nir.tif')

# Inicializar analizador
analyzer = RiverMorphologyAnalyzer(
    ndwi_threshold=0.0,
    canny_low=50,
    canny_high=150
)

# Analizar una época
result = analyzer.analyze_epoch(green_band, nir_band)

# Comparar épocas
comparison = analyzer.compare_epochs(result_1969, result_2023)

# Generar reporte
report = analyzer.generate_report(comparison, "1969", "2023")
```

## Requisitos

```
numpy>=1.24.0
opencv-python>=4.8.0
rasterio>=1.3.0  # Opcional, para cargar TIF
```

## Autor

Skyfusion Analytics Team - Hydrographic Analysis Division
