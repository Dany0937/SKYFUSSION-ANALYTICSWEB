"""
Geo Tools - Skyfusion Analytics
================================

Módulo de herramientas geoespaciales para adquisición y 
procesamiento de datos satelitales de la cuenca del Río Combeima.

Módulos:
- preprocessor: Integración con Google Earth Engine

Uso:

    from preprocessor import (
        GEEAuthenticator,
        SatelliteDataPreprocessor,
        CombeimaBasinProvider,
        preprocess_combeima_basin
    )
    
    GEEAuthenticator.initialize()
    
    preprocessor = SatelliteDataPreprocessor()
    result = preprocessor.query_images("1985-01-01", "1985-12-31")
"""

from .preprocessor import (
    GEEAuthenticator,
    GEEConfig,
    CombeimaBasinProvider,
    SatelliteDataPreprocessor,
    SatelliteCollection,
    ImageCollectionConfig,
    QueryResult,
    preprocess_combeima_basin
)

__version__ = "1.0.0"
__author__ = "Skyfusion Analytics - Geospatial Division"

__all__ = [
    "GEEAuthenticator",
    "GEEConfig",
    "CombeimaBasinProvider",
    "SatelliteDataPreprocessor",
    "SatelliteCollection",
    "ImageCollectionConfig",
    "QueryResult",
    "preprocess_combeima_basin"
]
