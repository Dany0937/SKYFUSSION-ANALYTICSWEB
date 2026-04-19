# Geo Tools - Skyfusion Analytics

## Geospatial Agent - Google Earth Engine Integration

Módulo para adquisición y procesamiento de imágenes satelitales multitemporales de la cuenca del Río Combeima (1969-2023).

## Características Principales

- **Consulta de colecciones satelitales**: Landsat 1-5 MSS, Landsat 4-9 TM/OLI, Sentinel-2 MSI
- **Filtrado de nubosidad**: Máximo 15% de nubosidad por imagen
- **Índices espectrales**: NDVI, NDWI
- **Sistema de eventos**: Emisión de `IMAGENES_HISTORICAS_LISTAS`

## Estructura del Módulo

```
geo_tools/
├── __init__.py              # Paquete Python
├── preprocessor.py          # Integración con GEE + emisión de eventos
├── event_bus.py             # Sistema de mensajería de eventos
├── requirements.txt         # Dependencias
└── README.md              # Este archivo
```

## Instalación

```bash
pip install earthengine-api pandas
earthengine authenticate
```

## Uso Básico

### 1. Consulta de Imágenes con Evento

```python
from preprocessor import (
    GEEAuthenticator,
    SatelliteDataPreprocessor,
    preprocess_combeima_basin
)

# Inicializar GEE
GEEAuthenticator.initialize()

# Procesar un año específico
result = preprocess_combeima_basin(
    start_date="1985-01-01",
    end_date="1985-12-31",
    emit_events=True
)
# Output: Evento IMAGENES_HISTORICAS_LISTAS emitido
```

### 2. Serie Temporal Completa

```python
result = preprocess_combeima_basin(
    emit_events=True
)
# Procesa 1969-2023 y emite evento con estadísticas
```

### 3. Uso Programático

```python
preprocessor = SatelliteDataPreprocessor()

# Consultar imágenes
result = preprocessor.query_images("2020-01-01", "2020-12-31")

# Compuesto anual
composite = preprocessor.get_annual_composite(year=2020)

# Índices espectrales
indices = preprocessor.calculate_indices(composite, ['ndvi', 'ndwi'])
```

## Sistema de Eventos

### Evento Principal: `IMAGENES_HISTORICAS_LISTAS`

```python
{
    "event_type": "IMAGENES_HISTORICAS_LISTAS",
    "timestamp": "2026-04-15T10:30:00Z",
    "payload": {
        "dataAvailability": {
            "dateRange": {"start": "1969-01-01", "end": "2023-12-31"},
            "collectionsUsed": ["LANDSAT/LM01/T1", "LANDSAT/LT05/C02/T1"],
            "imageCount": 1250
        },
        "processingConfig": {
            "cloudFilterApplied": True,
            "maxCloudPercent": 15
        },
        "basin": {
            "id": "combeima_basin",
            "name": "Cuenca Alta Río Combeima",
            "areaHa": 12450.75
        }
    }
}
```

### Configuración de Backend

```python
# Backend local (file-based, default)
event_emitter = get_event_emitter()

# Backend Redis
event_emitter = get_event_emitter({
    'backend': 'redis',
    'redis': {'host': 'redis.local', 'port': 6379}
})
```

### Variables de Entorno

```bash
GEO_EVENT_BACKEND=local          # local | redis | rabbitmq
REDIS_HOST=localhost
REDIS_PORT=6379
EVENT_STORAGE_DIR=./data/events
```

## Colecciones Satelitales

| Período | Satélite | Colección GEE | Resolución |
|---------|----------|---------------|------------|
| 1972-1984 | Landsat 1-5 MSS | `LANDSAT/LM01/T1` | 60m |
| 1984-2012 | Landsat 5 TM | `LANDSAT/LT05/C02/T1` | 30m |
| 2013-actual | Landsat 8-9 OLI | `LANDSAT/LC08/C02/T1_L2` | 30m |
| 2015-actual | Sentinel-2 MSI | `COPERNICUS/S2_SR_HARMONIZED` | 10m |

## Filtrado de Nubosidad

Por defecto, se filtran imágenes con nubosidad > 15%:
- Landsat MSS: `CLOUD_COVER < 15`
- Landsat TM/OLI: `CLOUD_COVER_LAND < 15`
- Sentinel-2: `CLOUDY_PIXEL_PERCENTAGE < 15`

## CLI

```bash
# Procesar año específico
python preprocessor.py --start-date 1985-01-01 --end-date 1985-12-31

# Procesar serie completa (1969-2023)
python preprocessor.py

# Sin emitir eventos
python preprocessor.py --no-events

# Con Redis
python preprocessor.py --event-backend redis
```

## Cuenca del Combeima

Coordenadas predefinidas (EPSG:4326):
```
Bounding Box: [-75.257, 4.433, -75.142, 4.529]
Área: 12,450.75 hectáreas
Municipio: Ibagué, Tolima, Colombia
```

## Integración con Node.js

Los eventos emitidos se almacenan en `./data/events/` y pueden ser consumidos por el backend Node.js:

```javascript
import { createEventBus, EVENT_TYPES } from './shared/events/eventBus.js';

const eventBus = createEventBus();

eventBus.onEvent(EVENT_TYPES.IMAGENES_HISTORICAS_LISTAS, (event) => {
    console.log('Nuevas imágenes disponibles:', event.payload.imageCount);
});
```

## Autor

Skyfusion Analytics Team - Geospatial Division
