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
"""

import os
import json
import ee
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum


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


class GEEAuthenticator:
    """
    Manejador de autenticación para Google Earth Engine.
    
    Soporta dos modos de autenticación:
    1. Cuenta de servicio (recomendado para producción)
    2. Autenticación por credenciales de usuario
    """
    
    _initialized = False
    
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
            print("[INFO] GEE ya está inicializado")
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
            print("[INFO] GEE inicializado correctamente")
            print(f"[INFO] Proyecto: {ee.data.getProject()}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error inicializando GEE: {str(e)}")
            
            print("\n[INFO] Para inicializar manualmente, ejecute:")
            print("  1. Instale earthengine-api: pip install earthengine-api")
            print("  2. Autentique: earthengine authenticate")
            print("  3. En su código: ee.Initialize()")
            
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
        """
        Retorna el bounding box de la cuenca.
        
        Returns:
            Tupla (min_lon, min_lat, max_lon, max_lat)
        """
        return (-75.257, 4.433, -75.142, 4.529)


class SatelliteDataPreprocessor:
    """
    Preprocesador de datos satelitales multitemporales.
    
    Proporciona métodos para:
    - Consultar colecciones satelitales según período histórico
    - Filtrar por nubosidad
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
    
    def __init__(self, geometry: Optional[ee.Geometry] = None) -> None:
        """
        Inicializa el preprocesador.
        
        Args:
            geometry: Geometría del área de estudio (opcional)
        """
        if not GEEAuthenticator.is_initialized():
            GEEAuthenticator.initialize()
            
        self.geometry = geometry or CombeimaBasinProvider.get_geometry()
        
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
        
        for collection in collections:
            config = self._get_collection_config(collection)
            
            try:
                img_collection = ee.ImageCollection(config.collection_id)
                
                filtered = img_collection.filterDate(start_date, end_date)
                filtered = filtered.filterBounds(self.geometry)
                filtered = filtered.filter(
                    ee.Filter.lt(config.cloud_property, config.max_cloud_percent)
                )
                filtered = filtered.sort('system:time_start', False)
                filtered = filtered.limit(max_results)
                
                image_list = filtered.getInfo()
                
                if image_list and 'features' in image_list:
                    for img in image_list['features']:
                        all_images.append({
                            'id': img['id'],
                            'collection': collection.value,
                            'date': img['properties'].get('system:time_start'),
                            'cloud_cover': img['properties'].get(config.cloud_property, 0),
                            'scale': config.scale
                        })
                        
            except Exception as e:
                print(f"[WARN] Error consultando {collection.value}: {str(e)}")
                continue
                
        all_images.sort(key=lambda x: x.get('date', 0), reverse=True)
        
        return QueryResult(
            collection_name=', '.join([c.value for c in collections]),
            image_count=len(all_images),
            date_range=(start_date, end_date),
            images=all_images[:max_results],
            geometry=self.geometry.getInfo()
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
            try:
                ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI')
                result = result.addBand(ndvi)
            except:
                try:
                    ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
                    result = result.addBand(ndvi)
                except:
                    try:
                        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
                        result = result.addBand(ndvi)
                    except:
                        pass
                        
        if 'ndwi' in indices:
            try:
                ndwi = image.normalizedDifference(['B3', 'B5']).rename('NDWI')
                result = result.addBand(ndwi)
            except:
                try:
                    ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI')
                    result = result.addBand(ndwi)
                except:
                    pass
                    
        return result
    
    def get_multitemporal_series(
        self,
        start_year: int,
        end_year: int,
        indices: Optional[List[str]] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Obtiene serie temporal multianual de índices espectrales.
        
        Args:
            start_year: Año inicial
            end_year: Año final
            indices: Índices a calcular
            
        Returns:
            Diccionario con datos por año
        """
        results = {}
        
        for year in range(start_year, end_year + 1):
            try:
                composite = self.get_annual_composite(year)
                
                if composite is None:
                    results[year] = {
                        'available': False,
                        'error': 'No images found'
                    }
                    continue
                    
                indices_image = self.calculate_indices(composite, indices)
                
                stats = indices_image.reduceRegion(
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
                    'stats': stats
                }
                
            except Exception as e:
                results[year] = {
                    'available': False,
                    'error': str(e)
                }
                
        return results


def preprocess_combeima_basin(
    geojson_path: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    output_dir: str = "./data/geospatial"
) -> Dict[str, Any]:
    """
    Función principal para preprocesar datos de la cuenca del Combeima.
    
    Args:
        geojson_path: Ruta al archivo GeoJSON de la cuenca
        start_date: Fecha de inicio (YYYY-MM-DD)
        end_date: Fecha de fin (YYYY-MM-DD)
        output_dir: Directorio de salida para datos
        
    Returns:
        Diccionario con resultados del procesamiento
    """
    if not GEEAuthenticator.is_initialized():
        if not GEEAuthenticator.initialize():
            return {"success": False, "error": "GEE initialization failed"}
            
    print("\n" + "=" * 60)
    print("SKYFUSION ANALYTICS - GEE DATA PREPROCESSOR")
    print("Cuenca del Río Combeima, Ibagué, Colombia")
    print("=" * 60)
    
    geometry = CombeimaBasinProvider.get_geometry(geojson_path)
    preprocessor = SatelliteDataPreprocessor(geometry)
    
    if start_date and end_date:
        year = int(start_date.split('-')[0])
        collections = preprocessor._get_collection_for_year(year)
        
        print(f"\n📡 Consultando colecciones para {year}:")
        for col in collections:
            print(f"   - {col.value}")
            
        result = preprocessor.query_images(start_date, end_date, year)
        
        print(f"\n📊 Resultados:")
        print(f"   Imágenes encontradas: {result.image_count}")
        print(f"   Rango de fechas: {result.date_range[0]} a {result.date_range[1]}")
        
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"query_{year}.json")
        
        with open(output_file, 'w') as f:
            json.dump({
                'query_result': {
                    'collection_name': result.collection_name,
                    'image_count': result.image_count,
                    'date_range': result.date_range,
                    'images': result.images
                }
            }, f, indent=2, default=str)
            
        print(f"   ✓ Resultados guardados en {output_file}")
        
        return {
            "success": True,
            "year": year,
            "collections": [c.value for c in collections],
            "image_count": result.image_count,
            "output_file": output_file
        }
        
    else:
        print("\n📊 Generando serie temporal multianual (1969-2023)...")
        
        series = preprocessor.get_multitemporal_series(
            start_year=1969,
            end_year=2023,
            indices=['ndvi', 'ndwi']
        )
        
        available_years = [y for y, data in series.items() if data.get('available')]
        
        print(f"\n✅ Años con datos disponibles: {len(available_years)}")
        print(f"   Período: {min(available_years)} - {max(available_years)}")
        
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "multitemporal_series.json")
        
        with open(output_file, 'w') as f:
            json.dump(series, f, indent=2, default=str)
            
        print(f"   ✓ Serie temporal guardada en {output_file}")
        
        return {
            "success": True,
            "total_years": 2023 - 1969 + 1,
            "available_years": len(available_years),
            "period": f"{min(available_years)}-{max(available_years)}",
            "output_file": output_file
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
    
    result = preprocess_combeima_basin(
        geojson_path=args.geojson,
        start_date=args.start_date,
        end_date=args.end_date,
        output_dir=args.output_dir
    )
    
    if result.get("success"):
        print("\n✨ Procesamiento completado exitosamente")
    else:
        print(f"\n❌ Error: {result.get('error')}")
