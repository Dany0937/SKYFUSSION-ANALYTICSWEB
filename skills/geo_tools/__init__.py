"""
Geo Tools - Skyfusion Analytics
================================

Módulo de herramientas geoespaciales para adquisición y 
procesamiento de datos satelitales de la cuenca del Río Combeima.

Módulos:
- preprocessor: Integración con Google Earth Engine
- event_bus: Sistema de mensajería de eventos

Uso:

    # Inicialización básica
    from preprocessor import GEEAuthenticator, SatelliteDataPreprocessor
    
    GEEAuthenticator.initialize()
    preprocessor = SatelliteDataPreprocessor()
    
    # Consulta de imágenes
    result = preprocessor.query_images("1985-01-01", "1985-12-31")
    
    # Con emisión de eventos
    from preprocessor import preprocess_combeima_basin
    result = preprocess_combeima_basin(
        start_date="1985-01-01",
        end_date="1985-12-31",
        emit_events=True
    )
"""

from .preprocessor import (
    GEEAuthenticator,
    GEEConfig,
    CombeimaBasinProvider,
    SatelliteDataPreprocessor,
    SatelliteCollection,
    ImageCollectionConfig,
    QueryResult,
    ProcessingStats,
    preprocess_combeima_basin
)

from .event_bus import (
    GeoEventEmitter,
    SkyfusionEvent,
    EventStore,
    LocalEventBus,
    RedisEventBus,
    get_event_emitter
)

__version__ = "1.0.0"
__author__ = "Skyfusion Analytics - Geospatial Division"

__all__ = [
    # GEE Preprocessor
    "GEEAuthenticator",
    "GEEConfig",
    "CombeimaBasinProvider",
    "SatelliteDataPreprocessor",
    "SatelliteCollection",
    "ImageCollectionConfig",
    "QueryResult",
    "ProcessingStats",
    "preprocess_combeima_basin",
    # Event Bus
    "GeoEventEmitter",
    "SkyfusionEvent",
    "EventStore",
    "LocalEventBus",
    "RedisEventBus",
    "get_event_emitter"
]
