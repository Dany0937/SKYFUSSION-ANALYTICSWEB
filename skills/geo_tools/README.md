# Geo Tools - Skyfusion Analytics

## Geospatial Agent - Google Earth Engine Integration

Módulo para adquisición y procesamiento de imágenes satelitales multitemporales de la cuenca del Río Combeima.

## Estructura del Módulo

```
geo_tools/
├── __init__.py              # Paquete Python
├── preprocessor.py          # Integración con GEE
├── index.js                 # Bridge Node.js
├── requirements.txt         # Dependencias
└── README.md              # Este archivo
```

## Colecciones Satelitales Soportadas

| Período | Satélite | Colección GEE | Resolución |
|---------|----------|---------------|------------|
| 1972-1984 | Landsat 1-5 MSS | `LANDSAT/LM01/T1` | 60m |
| 1984-2012 | Landsat 5 TM | `LANDSAT/LT05/C02/T1` | 30m |
| 2013-actual | Landsat 8-9 OLI | `LANDSAT/LC08/C02/T1_L2` | 30m |
| 2015-actual | Sentinel-2 MSI | `COPERNICUS/S2_SR_HARMONIZED` | 10m |

## Instalación

```bash
pip install earthengine-api pandas
earthengine authenticate --service_account=tu-cuenta@project.iam.gserviceaccount.com --key_file=key.json
```

## Uso Básico

### 1. Consulta de Imágenes

```python
from preprocessor import GEEAuthenticator, SatelliteDataPreprocessor, CombeimaBasinProvider

GEEAuthenticator.initialize()

preprocessor = SatelliteDataPreprocessor()

result = preprocessor.query_images(
    start_date="1985-01-01",
    end_date="1985-12-31",
    year=1985
)
```

### 2. Descarga por Año

```python
composite = preprocessor.get_annual_composite(year=1985)
indices = preprocessor.calculate_indices(composite, ['ndvi', 'ndwi'])
```

### 3. Serie Temporal Completa

```python
series = preprocessor.get_multitemporal_series(
    start_year=1969,
    end_year=2023,
    indices=['ndvi', 'ndwi']
)
```

## CLI

```bash
# Consulta específica
python preprocessor.py --start-date 1985-01-01 --end-date 1985-12-31

# Serie temporal completa
python preprocessor.py

# Con cuenta de servicio
python preprocessor.py \
    --auth-service-account tu-cuenta@project.iam.gserviceaccount.com \
    --auth-key-path ./key.json
```

## Filtrado de Nubosidad

Por defecto, se filtran imágenes con nubosidad > 15%:
- Landsat MSS: `CLOUD_COVER < 15`
- Landsat TM/OLI: `CLOUD_COVER_LAND < 15`
- Sentinel-2: `CLOUDY_PIXEL_PERCENTAGE < 15`

## Índices Espectrales

El módulo calcula automáticamente:
- **NDVI**: Índice de Vegetación de Diferencia Normalizada
- **NDWI**: Índice de Agua de Diferencia Normalizada

## Cuenca del Combeima

Coordenadas predefinidas (EPSG:4326):
```
Bounding Box: [-75.257, 4.433, -75.142, 4.529]
Área: 12,450.75 hectáreas
Municipio: Ibagué, Tolima, Colombia
```

## Autor

Skyfusion Analytics Team - Geospatial Division
