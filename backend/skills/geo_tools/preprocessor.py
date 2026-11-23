"""
Google Earth Engine Preprocessor for Skyfusion Analytics
=====================================================

Geospatial Agent para adquisición de imágenes satelitales multitemporales
de la cuenca del Río Combeima (1969-2023).

Funcionalidades:
- Descarga de imágenes Landsat 1-5 MSS (1969-1984)
- Descarga de imágenes Landsat 4-9 TM/OLI (1984-actual)
- Descarga de imágenes Sentinel-2 MSI (2015-actual)
- Filtrado por nubosidad < 15%
- Compilación de series temporales
- Cálculo de índices espectrales (NDVI, NDWI)
- Emisión de eventos: IMAGENES_HISTORICAS_LISTAS
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

import ee

from event_bus import get_event_emitter, GeoEventEmitter, SkyfusionEvent, EventStore


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)


class SatelliteCollection(Enum):
    """Enumeración de colecciones satelitales disponibles."""
    LANDSAT_MSS = "landsat_mss"
    LANDSAT_TM = "landsat_tm"
    LANDSAT_OLI = "landsat_oli"
    SENTINEL_2 = "sentinel_2"


@dataclass
class GEEConfig:
    """Configuración para conexión con GEE."""
    service_account: Optional[str] = None
    key_path: Optional[str] = None
    project: Optional[str] = None
    asset_root: Optional[str] = None


@dataclass
class ImageCollectionConfig:
    """Configuración para una colección de imágenes."""
    collection_id: str
    bands: List[str]
    band_names: List[str]
    cloud_property: str
    max_cloud_percent: float
    scale: int
    start_year: int
    end_year: int


@dataclass
class QueryResult:
    """Resultado de una consulta a GEE."""
    collection_name: str
    image_count: int
    date_range: Tuple[str, str]
    images: List[Dict[str, Any]]
    geometry: Dict
    cloud_filter_stats: Dict[str, int]
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        return result


@dataclass
class ProcessingStats:
    """Estadísticas del procesamiento de series temporales."""
    total_years: int
    years_with_data: int
    years_without_data: int
    total_images: int
    filtered_by_cloud: int
    collections_used: List[str]
    processing_time_seconds: float
    errors: List[Dict[str, str]]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class GEEAuthenticator:
    """
    Manejador de autenticación para Google Earth Engine.
    
    Soporta dos modos de autenticación:
    1. Cuenta de servicio (recomendado para producción)
    2. Autenticación por credenciales de usuario
    """
    
    _initialized = False
    logger = logging.getLogger(__name__)
    
    @classmethod
    def initialize(
        cls,
        config: Optional[GEEConfig] = None,
        service_account: Optional[str] = None,
        key_path: Optional[str] = None
    ) -> bool:
        """
        Inicializa la conexión con GEE.
        
        Args:
            config: Objeto de configuración GEEConfig
            service_account: Email de cuenta de servicio
            key_path: Ruta al archivo de clave JSON
            
        Returns:
            True si la autenticación fue exitosa
        """
        if cls._initialized:
            cls.logger.info("GEE ya está inicializado")
            return True
            
        try:
            if config and config.service_account and config.key_path:
                credentials = ee.ServiceAccountCredentials(
                    config.service_account,
                    config.key_path
                )
                ee.Initialize(credentials)
            elif service_account and key_path:
                credentials = ee.ServiceAccountCredentials(
                    service_account,
                    key_path
                )
                ee.Initialize(credentials)
            else:
                ee.Initialize()
                
            cls._initialized = True
            cls.logger.info(f"GEE inicializado correctamente - Proyecto: {ee.data.getProject()}")
            
            return True
            
        except Exception as e:
            cls.logger.error(f"Error inicializando GEE: {str(e)}")
            cls.logger.info("Pasos para autenticación manual:")
            cls.logger.info("  1. pip install earthengine-api")
            cls.logger.info("  2. earthengine authenticate")
            cls.logger.info("  3. ee.Initialize()")
            
            return False
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Verifica si GEE está inicializado."""
        return cls._initialized


class CombeimaBasinProvider:
    """
    Proveedor de datos geoespaciales para la cuenca del Río Combeima.
    
    Define el área de estudio y provee utilities para
    consultas a colecciones satelitales.
    """
    
    COMBEIMA_BASIN_GEOJSON = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}
        },
        "bbox": [-75.257, 4.433, -75.142, 4.529],
        "features": [{
            "type": "Feature",
            "id": "combeima_basin",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-75.257, 4.433],
                    [-75.142, 4.433],
                    [-75.142, 4.529],
                    [-75.257, 4.529],
                    [-75.257, 4.433]
                ]]
            },
            "properties": {
                "id": "combeima_basin",
                "nombre": "Cuenca Alta Río Combeima",
                "area_hectareas": 12450.75,
                "departamento": "Tolima",
                "municipio": "Ibagué",
                "pais": "Colombia",
                "elevacion_min_m": 800,
                "elevacion_max_m": 4200,
                "fuente": "IGAC 1:25000"
            }
        }]
    }
    
    @classmethod
    def get_geometry(cls, geojson_path: Optional[str] = None) -> ee.Geometry:
        """
        Obtiene la geometría de la cuenca del Combeima.
        
        Args:
            geojson_path: Ruta opcional a archivo GeoJSON externo
            
        Returns:
            Objeto ee.Geometry con el límite de la cuenca
        """
        if geojson_path and os.path.exists(geojson_path):
            with open(geojson_path, 'r') as f:
                geojson = json.load(f)
        else:
            geojson = cls.COMBEIMA_BASIN_GEOJSON
            
        feature = geojson.get('features', [{}])[0]
        geometry = feature.get('geometry', {})
        
        return ee.Geometry(geometry)
    
    @classmethod
    def get_bounds(cls) -> Tuple[float, float, float, float]:
        """Retorna el bounding box de la cuenca."""
        return (-75.257, 4.433, -75.142, 4.529)
    
    @classmethod
    def get_info(cls) -> Dict:
        """Retorna información de la cuenca."""
        return cls.COMBEIMA_BASIN_GEOJSON["features"][0]["properties"]


class SatelliteDataPreprocessor:
    """
    Preprocesador de datos satelitales multitemporales.
    
    Proporciona métodos para:
    - Consultar colecciones satelitales según período histórico
    - Filtrar por nubosidad (< 15%)
    - Calcular compuestos temporales
    - Exportar índices espectrales
    """
    
    COLLECTION_CONFIGS: Dict[SatelliteCollection, ImageCollectionConfig] = {
        SatelliteCollection.LANDSAT_MSS: ImageCollectionConfig(
            collection_id="LANDSAT/LM01/T1",
            bands=["B4", "B5", "B6", "B7"],
            band_names=["green", "red", "nir", "nir2"],
            cloud_property="CLOUD_COVER",
            max_cloud_percent=15,
            scale=60,
            start_year=1972,
            end_year=1984
        ),
        SatelliteCollection.LANDSAT_TM: ImageCollectionConfig(
            collection_id="LANDSAT/LT05/C02/T1",
            bands=["B1", "B2", "B3", "B4", "B5", "B7"],
            band_names=["blue", "green", "red", "nir", "swir1", "swir2"],
            cloud_property="CLOUD_COVER_LAND",
            max_cloud_percent=15,
            scale=30,
            start_year=1984,
            end_year=2012
        ),
        SatelliteCollection.LANDSAT_OLI: ImageCollectionConfig(
            collection_id="LANDSAT/LC08/C02/T1_L2",
            bands=["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"],
            band_names=["blue", "green", "red", "nir", "swir1", "swir2", "cirrus"],
            cloud_property="CLOUD_COVER_LAND",
            max_cloud_percent=15,
            scale=30,
            start_year=2013,
            end_year=2030
        ),
        SatelliteCollection.SENTINEL_2: ImageCollectionConfig(
            collection_id="COPERNICUS/S2_SR_HARMONIZED",
            bands=["B2", "B3", "B4", "B8", "B11", "B12"],
            band_names=["blue", "green", "red", "nir", "swir1", "swir2"],
            cloud_property="CLOUDY_PIXEL_PERCENTAGE",
            max_cloud_percent=15,
            scale=10,
            start_year=2015,
            end_year=2030
        )
    }
    
    def __init__(
        self,
        geometry: Optional[ee.Geometry] = None,
        emit_events: bool = True
    ) -> None:
        """
        Inicializa el preprocesador.
        
        Args:
            geometry: Geometría del área de estudio
            emit_events: Si debe emitir eventos al bus
        """
        if not GEEAuthenticator.is_initialized():
            GEEAuthenticator.initialize()
            
        self.geometry = geometry or CombeimaBasinProvider.get_geometry()
        self.logger = logging.getLogger(__name__)
        
        self.event_emitter: Optional[GeoEventEmitter] = None
        if emit_events:
            try:
                self.event_emitter = get_event_emitter()
                self.logger.info("Event emitter configurado")
            except Exception as e:
                self.logger.warning(f"No se pudo inicializar event emitter: {e}")
    
    def _get_collection_for_year(self, year: int) -> List[SatelliteCollection]:
        """
        Determina qué colecciones satelitales usar según el año.
        
        Args:
            year: Año de consulta
            
        Returns:
            Lista de colecciones disponibles para el año
        """
        available_collections = []
        
        for collection, config in self.COLLECTION_CONFIGS.items():
            if config.start_year <= year <= config.end_year:
                available_collections.append(collection)
                
        if not available_collections:
            available_collections = [SatelliteCollection.LANDSAT_OLI]
            
        return available_collections
    
    def _get_collection_config(
        self,
        collection: SatelliteCollection
    ) -> ImageCollectionConfig:
        """Obtiene configuración para una colección."""
        return self.COLLECTION_CONFIGS[collection]
    
    def query_images(
        self,
        start_date: str,
        end_date: str,
        year: Optional[int] = None,
        max_results: int = 100
    ) -> QueryResult:
        """
        Consulta imágenes satelitales para el período especificado.
        
        Args:
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            year: Año específico para determinar colección
            max_results: Máximo número de imágenes a retornar
            
        Returns:
            Objeto QueryResult con las imágenes encontradas
        """
        if year is None:
            year = int(start_date.split('-')[0])
            
        collections = self._get_collection_for_year(year)
        
        all_images = []
        total_images = 0
        filtered_by_cloud = 0
        collections_data = []
        
        for collection in collections:
            config = self._get_collection_config(collection)
            
            try:
                img_collection = ee.ImageCollection(config.collection_id)
                
                pre_filter_count = img_collection.filterDate(
                    start_date, end_date
                ).filterBounds(self.geometry).size().getInfo()
                total_images += pre_filter_count
                
                filtered = img_collection.filterDate(start_date, end_date)
                filtered = filtered.filterBounds(self.geometry)
                filtered = filtered.filter(
                    ee.Filter.lt(config.cloud_property, config.max_cloud_percent)
                )
                filtered = filtered.sort('system:time_start', False)
                filtered = filtered.limit(max_results)
                
                post_filter_count = filtered.size().getInfo()
                filtered_by_cloud += pre_filter_count - post_filter_count
                
                collections_data.append({
                    "collection": collection.value,
                    "geeCollectionId": config.collection_id,
                    "preFilterCount": pre_filter_count,
                    "postFilterCount": post_filter_count,
                    "cloudProperty": config.cloud_property,
                    "maxCloudPercent": config.max_cloud_percent
                })
                
                image_list = filtered.getInfo()
                
                if image_list and 'features' in image_list:
                    for img in image_list['features']:
                        cloud_cover = img['properties'].get(config.cloud_property, 0)
                        all_images.append({
                            'id': img['id'],
                            'collection': collection.value,
                            'date': img['properties'].get('system:time_start'),
                            'cloud_cover': cloud_cover,
                            'scale': config.scale
                        })
                        
                self.logger.info(
                    f"  {collection.value}: {post_filter_count} imágenes "
                    f"(filtradas: {pre_filter_count - post_filter_count})"
                )
                         
            except Exception as e:
                self.logger.error(f"Error consultando {collection.value}: {str(e)}")
                collections_data.append({
                    "collection": collection.value,
                    "error": str(e)
                })
                continue
                
        all_images.sort(key=lambda x: x.get('date', 0), reverse=True)
        
        cloud_filter_stats = {
            "totalImages": total_images,
            "afterCloudFilter": len(all_images),
            "filteredByCloud": filtered_by_cloud,
            "filterPercent": round(filtered_by_cloud / total_images * 100, 2) if total_images > 0 else 0
        }
        
        return QueryResult(
            collection_name=', '.join([c.value for c in collections]),
            image_count=len(all_images),
            date_range=(start_date, end_date),
            images=all_images[:max_results],
            geometry=self.geometry.getInfo(),
            cloud_filter_stats=cloud_filter_stats
        )
    
    def get_annual_composite(
        self,
        year: int,
        collection: Optional[SatelliteCollection] = None
    ) -> Optional[ee.Image]:
        """
        Genera un compuesto anual para el año especificado.
        
        Args:
            year: Año del compuesto
            collection: Colección específica a usar
            
        Returns:
            Imagen compuesto o None si no hay datos
        """
        if collection is None:
            collections = self._get_collection_for_year(year)
            collection = collections[0] if collections else SatelliteCollection.LANDSAT_OLI
            
        config = self._get_collection_config(collection)
        
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        img_collection = ee.ImageCollection(config.collection_id)
        
        filtered = img_collection.filterDate(start_date, end_date)
        filtered = filtered.filterBounds(self.geometry)
        filtered = filtered.filter(
            ee.Filter.lt(config.cloud_property, config.max_cloud_percent)
        )
        
        if filtered.size().getInfo() == 0:
            self.logger.warning(f"No images found for year {year}")
            return None
            
        composite = filtered.median()
        composite = composite.clip(self.geometry)
        
        return composite
    
    def calculate_indices(
        self,
        image: ee.Image,
        indices: Optional[List[str]] = None
    ) -> ee.Image:
        """
        Calcula índices espectrales sobre una imagen.
        
        Args:
            image: Imagen de entrada
            indices: Lista de índices a calcular ['ndvi', 'ndwi', 'evi']
            
        Returns:
            Imagen con bandas de índices calculados
        """
        indices = indices or ['ndvi', 'ndwi']
        
        result = image
        
        if 'ndvi' in indices:
            for nir_band, red_band in [('B5', 'B4'), ('SR_B5', 'SR_B4'), ('B8', 'B4')]:
                try:
                    ndvi = image.normalizedDifference([nir_band, red_band]).rename('NDVI')
                    result = result.addBand(ndvi)
                    break
                except:
                    continue
                    
        if 'ndwi' in indices:
            for green_band, nir_band in [('B3', 'B5'), ('B3', 'B8')]:
                try:
                    ndwi = image.normalizedDifference([green_band, nir_band]).rename('NDWI')
                    result = result.addBand(ndwi)
                    break
                except:
                    continue
                    
        return result
    
    def get_multitemporal_series(
        self,
        start_year: int,
        end_year: int,
        indices: Optional[List[str]] = None,
        emit_events: bool = True
    ) -> Tuple[Dict[int, Dict[str, Any]], ProcessingStats]:
        """
        Obtiene serie temporal multianual de índices espectrales.
        
        Args:
            start_year: Año inicial
            end_year: Año final
            indices: Índices a calcular
            emit_events: Si debe emitir eventos
            
        Returns:
            Tupla de (diccionario con datos por año, estadísticas)
        """
        results = {}
        stats = ProcessingStats(
            total_years=end_year - start_year + 1,
            years_with_data=0,
            years_without_data=0,
            total_images=0,
            filtered_by_cloud=0,
            collections_used=[],
            processing_time_seconds=0,
            errors=[]
        )
        
        start_time = datetime.now()
        
        for year in range(start_year, end_year + 1):
            year_start = datetime.now()
            collections = self._get_collection_for_year(year)
            
            for col in collections:
                if col.value not in stats.collections_used:
                    stats.collections_used.append(col.value)
            
            try:
                result = self.query_images(
                    f"{year}-01-01",
                    f"{year}-12-31",
                    year=year
                )
                
                stats.total_images += result.cloud_filter_stats["totalImages"]
                stats.filtered_by_cloud += result.cloud_filter_stats["filteredByCloud"]
                
                composite = self.get_annual_composite(year)
                
                if composite is None:
                    results[year] = {
                        'available': False,
                        'error': 'No images found after cloud filter'
                    }
                    stats.years_without_data += 1
                    continue
                    
                indices_image = self.calculate_indices(composite, indices)
                
                stats_region = indices_image.reduceRegion(
                    reducer=ee.Reducer.mean().combine(
                        reducer2=ee.Reducer.stdDev(),
                        sharedInputs=True
                    ),
                    geometry=self.geometry,
                    scale=30,
                    bestEffort=True
                ).getInfo()
                
                results[year] = {
                    'available': True,
                    'stats': stats_region,
                    'images_used': result.image_count,
                    'collections': [c.value for c in collections]
                }
                stats.years_with_data += 1
                
                year_time = (datetime.now() - year_start).total_seconds()
                self.logger.info(
                    f"Año {year}: ✓ {result.image_count} imágenes - "
                    f"Tiempo: {year_time:.2f}s"
                )
                
            except Exception as e:
                results[year] = {
                    'available': False,
                    'error': str(e)
                }
                stats.errors.append({
                    'year': year,
                    'error': str(e)
                })
                stats.years_without_data += 1
                self.logger.error(f"Año {year}: ✗ Error - {str(e)}")
        
        stats.processing_time_seconds = (datetime.now() - start_time).total_seconds()
        
        return results, stats


def preprocess_combeima_basin(
    geojson_path: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    output_dir: str = "./data/geospatial",
    emit_events: bool = True,
    event_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Función principal para preprocesar datos de la cuenca del Combeima.
    
    Args:
        geojson_path: Ruta al archivo GeoJSON de la cuenca
        start_date: Fecha de inicio (YYYY-MM-DD)
        end_date: Fecha de fin (YYYY-MM-DD)
        output_dir: Directorio de salida para datos
        emit_events: Si debe emitir eventos al bus
        event_config: Configuración para el bus de eventos
        
    Returns:
        Diccionario con resultados del procesamiento
    """
    logger = logging.getLogger(__name__)
    
    if not GEEAuthenticator.is_initialized():
        if not GEEAuthenticator.initialize():
            return {"success": False, "error": "GEE initialization failed"}
            
    print("\n" + "=" * 60)
    print("SKYFUSION ANALYTICS - GEE DATA PREPROCESSOR")
    print("Cuenca del Río Combeima, Ibagué, Colombia")
    print("=" * 60)
    
    geometry = CombeimaBasinProvider.get_geometry(geojson_path)
    preprocessor = SatelliteDataPreprocessor(geometry, emit_events=emit_events)
    
    event_emitter = None
    if emit_events:
        try:
            event_config = event_config or {}
            event_emitter = get_event_emitter(event_config)
        except Exception as e:
            logger.warning(f"No se pudo inicializar event emitter: {e}")
    
    basin_info = CombeimaBasinProvider.get_info()
    
    os.makedirs(output_dir, exist_ok=True)
    
    if start_date and end_date:
        year = int(start_date.split('-')[0])
        collections = preprocessor._get_collection_for_year(year)
        
        print(f"\n📡 Consultando colecciones para {year}:")
        for col in collections:
            print(f"   - {col.value}")
            
        result = preprocessor.query_images(start_date, end_date, year)
        
        print(f"\n📊 Resultados:")
        print(f"   Imágenes encontradas: {result.image_count}")
        print(f"   Filtradas por nubosidad: {result.cloud_filter_stats['filteredByCloud']}")
        print(f"   Rango de fechas: {result.date_range[0]} a {result.date_range[1]}")
        
        output_file = os.path.join(output_dir, f"query_{year}.json")
        
        output_data = {
            'metadata': {
                'query_date': datetime.now().isoformat(),
                'basin': basin_info,
                'cloud_filter_applied': True,
                'max_cloud_percent': 15
            },
            'query_result': result.to_dict()
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
            
        print(f"   ✓ Resultados guardados en {output_file}")
        
        if event_emitter:
            try:
                event_emitter.emit_historical_images_ready(
                    date_range=result.date_range,
                    collections_used=[c.value for c in collections],
                    image_count=result.image_count,
                    cloud_filter_applied=True,
                    max_cloud_percent=15.0,
                    basin_info=basin_info,
                    processing_metrics={
                        "filteredByCloud": result.cloud_filter_stats['filteredByCloud'],
                        "filterPercent": result.cloud_filter_stats['filterPercent']
                    }
                )
                print("   ✓ Evento IMAGENES_HISTORICAS_LISTAS emitido")
            except Exception as e:
                logger.error(f"Error emitiendo evento: {e}")
        
        return {
            "success": True,
            "year": year,
            "collections": [c.value for c in collections],
            "image_count": result.image_count,
            "output_file": output_file,
            "cloud_filter_stats": result.cloud_filter_stats
        }
        
    else:
        print(f"\n📊 Generando serie temporal multianual (1969-2023)...")
        print(f"   Filtro de nubosidad: < 15%")
        
        series, stats = preprocessor.get_multitemporal_series(
            start_year=1969,
            end_year=2023,
            indices=['ndvi', 'ndwi'],
            emit_events=emit_events
        )
        
        available_years = [y for y, data in series.items() if data.get('available')]
        
        print(f"\n✅ Procesamiento completado:")
        print(f"   Años con datos: {stats.years_with_data}/{stats.total_years}")
        print(f"   Total imágenes: {stats.total_images}")
        print(f"   Filtradas por nubosidad: {stats.filtered_by_cloud}")
        print(f"   Tiempo total: {stats.processing_time_seconds:.2f}s")
        
        if stats.errors:
            print(f"   Errores: {len(stats.errors)}")
        
        output_file = os.path.join(output_dir, "multitemporal_series.json")
        
        output_data = {
            'metadata': {
                'processing_date': datetime.now().isoformat(),
                'basin': basin_info,
                'period': {'start': 1969, 'end': 2023},
                'cloud_filter_applied': True,
                'max_cloud_percent': 15,
                'stats': stats.to_dict()
            },
            'series': series
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
            
        print(f"   ✓ Serie temporal guardada en {output_file}")
        
        if event_emitter:
            try:
                event_emitter.emit_historical_images_ready(
                    date_range=("1969-01-01", "2023-12-31"),
                    collections_used=stats.collections_used,
                    image_count=stats.total_images,
                    cloud_filter_applied=True,
                    max_cloud_percent=15.0,
                    basin_info=basin_info,
                    processing_metrics={
                        "yearsProcessed": stats.total_years,
                        "yearsWithData": stats.years_with_data,
                        "yearsWithoutData": stats.years_without_data,
                        "filteredByCloud": stats.filtered_by_cloud,
                        "processingTimeSeconds": stats.processing_time_seconds,
                        "errors": len(stats.errors)
                    }
                )
                print("   ✓ Evento IMAGENES_HISTORICAS_LISTAS emitido")
            except Exception as e:
                logger.error(f"Error emitiendo evento: {e}")
        
        return {
            "success": True,
            "total_years": stats.total_years,
            "available_years": stats.years_with_data,
            "total_images": stats.total_images,
            "filtered_by_cloud": stats.filtered_by_cloud,
            "period": f"{min(available_years)}-{max(available_years)}" if available_years else "N/A",
            "output_file": output_file,
            "stats": stats.to_dict()
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Preprocesador de datos geoespaciales para Skyfusion Analytics"
    )
    
    parser.add_argument(
        "--geojson",
        type=str,
        default=None,
        help="Ruta al archivo GeoJSON de la cuenca"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Fecha de inicio (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="Fecha de fin (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data/geospatial",
        help="Directorio de salida"
    )
    parser.add_argument(
        "--no-events",
        action="store_true",
        help="No emitir eventos"
    )
    parser.add_argument(
        "--event-backend",
        type=str,
        choices=["local", "redis", "rabbitmq"],
        default="local",
        help="Backend de eventos a usar"
    )
    parser.add_argument(
        "--auth-service-account",
        type=str,
        default=None,
        help="Email de cuenta de servicio"
    )
    parser.add_argument(
        "--auth-key-path",
        type=str,
        default=None,
        help="Ruta al archivo de clave JSON"
    )
    
    args = parser.parse_args()
    
    if args.auth_service_account and args.auth_key_path:
        GEEAuthenticator.initialize(
            service_account=args.auth_service_account,
            key_path=args.auth_key_path
        )
    
    event_config = {
        'backend': args.event_backend,
        'local': {'storage_dir': './data/events'}
    }
    
    result = preprocess_combeima_basin(
        geojson_path=args.geojson,
        start_date=args.start_date,
        end_date=args.end_date,
        output_dir=args.output_dir,
        emit_events=not args.no_events,
        event_config=event_config
    )
    
    if result.get("success"):
        print("\n✨ Procesamiento completado exitosamente")
    else:
        print(f"\n❌ Error: {result.get('error')}")
