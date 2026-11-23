"""Módulo de parsing y validación geoespacial para Skyfussion Analytics.

Valida coordenadas puntuales, polígonos dibujados, archivos GeoJSON o KML recibidos
desde el frontend. Si no se suministra geometría, utiliza el polígono delimitador de
la cuenca alta del Río Combeima (Ibagué, Tolima, Colombia).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from shapely.geometry import Point, Polygon, MultiPolygon, shape
    from shapely.validation import make_valid
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False


# Polígono canónico de referencia de la Cuenca Alta del Río Combeima (EPSG:4326)
DEFAULT_COMBEIMA_COORDINATES = [
    [-75.32, 4.38],
    [-75.28, 4.45],
    [-75.22, 4.49],
    [-75.18, 4.53],
    [-75.14, 4.51],
    [-75.15, 4.44],
    [-75.20, 4.39],
    [-75.26, 4.35],
    [-75.32, 4.38],
]

DEFAULT_COMBEIMA_GEOJSON: Dict[str, Any] = {
    "type": "Polygon",
    "coordinates": [DEFAULT_COMBEIMA_COORDINATES],
}

DEFAULT_BASIN_AREA_HA = 12450.75  # Hectáreas referenciales de la cuenca alta


@dataclass
class ParsedGeometry:
    """Estructura estandarizada de geometría analizada."""
    geojson: Dict[str, Any]
    area_ha: float
    centroid: Tuple[float, float]  # (lon, lat)
    bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    is_default: bool = False
    geometry_type: str = "Polygon"


def _estimate_area_hectares(geom: Union[Polygon, MultiPolygon]) -> float:
    """Calcula el área aproximada en hectáreas a partir de coordenadas WGS84 cerca a latitud 4.4°."""
    # A latitud ~4.4° N:
    # 1° latitud ≈ 110,574 metros
    # 1° longitud ≈ 111,320 * cos(4.4°) ≈ 110,990 metros
    # 1 grado cuadrado ≈ 1.2272e10 m² = 1,227,200 ha
    sq_degrees = geom.area
    ha = sq_degrees * 1227200.0
    return round(ha, 2)


def parse_kml_coordinates(kml_text: str) -> Optional[List[List[float]]]:
    """Extrae coordenadas de una cadena KML con etiquetas <coordinates>."""
    match = re.search(r"<coordinates>(.*?)</coordinates>", kml_text, re.DOTALL | re.IGNORECASE)
    if not match:
        return None

    raw_coords = match.group(1).strip().split()
    points: List[List[float]] = []
    for item in raw_coords:
        parts = item.strip().split(",")
        if len(parts) >= 2:
            try:
                lon = float(parts[0])
                lat = float(parts[1])
                points.append([lon, lat])
            except ValueError:
                continue

    if len(points) >= 3:
        # Asegurar anillo cerrado
        if points[0] != points[-1]:
            points.append(points[0])
        return points
    return None


def parse_geometry(raw_geom: Any = None) -> ParsedGeometry:
    """Valida y normaliza cualquier entrada de geometría.

    Acepta:
    - None o diccionario vacío -> Retorna Cuenca Combeima por defecto.
    - Dict GeoJSON (Polygon, MultiPolygon, Feature, FeatureCollection).
    - Lista de coordenadas de polígono: [[lon, lat], ...].
    - Coordenadas puntuales [lon, lat] o {"lat": ..., "lon": ...} (crea buffer representativo).
    - Cadena de texto KML.
    """
    if not raw_geom:
        if HAS_SHAPELY:
            default_poly = Polygon(DEFAULT_COMBEIMA_COORDINATES)
            minx, miny, maxx, maxy = default_poly.bounds
            cx, cy = default_poly.centroid.x, default_poly.centroid.y
        else:
            lons = [p[0] for p in DEFAULT_COMBEIMA_COORDINATES]
            lats = [p[1] for p in DEFAULT_COMBEIMA_COORDINATES]
            minx, maxx = min(lons), max(lons)
            miny, maxy = min(lats), max(lats)
            cx, cy = sum(lons) / len(lons), sum(lats) / len(lats)

        return ParsedGeometry(
            geojson=DEFAULT_COMBEIMA_GEOJSON,
            area_ha=DEFAULT_BASIN_AREA_HA,
            centroid=(round(cx, 5), round(cy, 5)),
            bbox=[round(minx, 5), round(miny, 5), round(maxx, 5), round(maxy, 5)],
            is_default=True,
            geometry_type="Polygon",
        )

    # 1. Entrada KML como texto
    if isinstance(raw_geom, str) and ("<kml" in raw_geom or "<coordinates>" in raw_geom):
        coords = parse_kml_coordinates(raw_geom)
        if coords:
            raw_geom = {"type": "Polygon", "coordinates": [coords]}

    # 2. Entrada punto como dict {"lat": ..., "lng"/"lon": ...}
    if isinstance(raw_geom, dict) and "lat" in raw_geom and ("lng" in raw_geom or "lon" in raw_geom):
        lat = float(raw_geom["lat"])
        lon = float(raw_geom.get("lng", raw_geom.get("lon")))
        if HAS_SHAPELY:
            pt = Point(lon, lat)
            poly = pt.buffer(0.015)  # Buffer representativo ~1.6 km
            minx, miny, maxx, maxy = poly.bounds
            poly_geojson = poly.__geo_interface__
            area_ha = _estimate_area_hectares(poly)
        else:
            d = 0.015
            box_coords = [
                [lon - d, lat - d],
                [lon + d, lat - d],
                [lon + d, lat + d],
                [lon - d, lat + d],
                [lon - d, lat - d],
            ]
            minx, miny, maxx, maxy = lon - d, lat - d, lon + d, lat + d
            poly_geojson = {"type": "Polygon", "coordinates": [box_coords]}
            area_ha = round((2 * d) * (2 * d) * 1227200.0, 2)

        return ParsedGeometry(
            geojson=poly_geojson,
            area_ha=area_ha,
            centroid=(round(lon, 5), round(lat, 5)),
            bbox=[round(minx, 5), round(miny, 5), round(maxx, 5), round(maxy, 5)],
            is_default=False,
            geometry_type="Polygon",
        )

    # 3. Entrada lista de pares de coordenadas directa
    if isinstance(raw_geom, list):
        # Caso punto individual [lon, lat]
        if len(raw_geom) == 2 and isinstance(raw_geom[0], (int, float)):
            lon, lat = float(raw_geom[0]), float(raw_geom[1])
            if HAS_SHAPELY:
                pt = Point(lon, lat)
                poly = pt.buffer(0.015)
                minx, miny, maxx, maxy = poly.bounds
                poly_geojson = poly.__geo_interface__
                area_ha = _estimate_area_hectares(poly)
            else:
                d = 0.015
                box_coords = [
                    [lon - d, lat - d],
                    [lon + d, lat - d],
                    [lon + d, lat + d],
                    [lon - d, lat + d],
                    [lon - d, lat - d],
                ]
                minx, miny, maxx, maxy = lon - d, lat - d, lon + d, lat + d
                poly_geojson = {"type": "Polygon", "coordinates": [box_coords]}
                area_ha = round((2 * d) * (2 * d) * 1227200.0, 2)

            return ParsedGeometry(
                geojson=poly_geojson,
                area_ha=area_ha,
                centroid=(round(lon, 5), round(lat, 5)),
                bbox=[round(minx, 5), round(miny, 5), round(maxx, 5), round(maxy, 5)],
                is_default=False,
                geometry_type="Polygon",
            )
        # Caso lista de vértices de polígono [[lon, lat], ...]
        if len(raw_geom) >= 3 and isinstance(raw_geom[0], list):
            coords = list(raw_geom)
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            raw_geom = {"type": "Polygon", "coordinates": [coords]}

    # 4. Manejo de Feature o FeatureCollection de GeoJSON
    if isinstance(raw_geom, dict):
        if raw_geom.get("type") == "Feature":
            raw_geom = raw_geom.get("geometry", {})
        elif raw_geom.get("type") == "FeatureCollection":
            features = raw_geom.get("features", [])
            if features:
                raw_geom = features[0].get("geometry", {})

    # 5. Validación con Shapely (o fallback puro en caso de no tener shapely instalado)
    if HAS_SHAPELY:
        try:
            geom = shape(raw_geom)
            if not geom.is_valid:
                geom = make_valid(geom)

            if geom.is_empty:
                raise ValueError("Geometría vacía.")

            if isinstance(geom, Point):
                geom = geom.buffer(0.015)

            minx, miny, maxx, maxy = geom.bounds
            centroid_pt = geom.centroid

            calculated_area = _estimate_area_hectares(geom) if hasattr(geom, "area") else DEFAULT_BASIN_AREA_HA
            if calculated_area <= 0:
                calculated_area = DEFAULT_BASIN_AREA_HA

            return ParsedGeometry(
                geojson=geom.__geo_interface__,
                area_ha=calculated_area,
                centroid=(round(centroid_pt.x, 5), round(centroid_pt.y, 5)),
                bbox=[round(minx, 5), round(miny, 5), round(maxx, 5), round(maxy, 5)],
                is_default=False,
                geometry_type=geom.geom_type,
            )
        except Exception:
            pass

    # Fallback sin Shapely o ante error de shape
    if isinstance(raw_geom, dict) and "coordinates" in raw_geom:
        coords_list = raw_geom["coordinates"]
        ring = coords_list[0] if coords_list and isinstance(coords_list[0], list) and isinstance(coords_list[0][0], list) else coords_list
        if ring and len(ring) >= 3:
            lons = [p[0] for p in ring]
            lats = [p[1] for p in ring]
            minx, maxx = min(lons), max(lons)
            miny, maxy = min(lats), max(lats)
            cx, cy = sum(lons) / len(lons), sum(lats) / len(lats)
            # Fórmula de Gauss / Shoelace para área
            n = len(ring)
            area_deg2 = 0.5 * abs(sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1] for i in range(n)))
            area_ha = round(max(10.0, area_deg2 * 1227200.0), 2)
            return ParsedGeometry(
                geojson={"type": "Polygon", "coordinates": [ring]},
                area_ha=area_ha,
                centroid=(round(cx, 5), round(cy, 5)),
                bbox=[round(minx, 5), round(miny, 5), round(maxx, 5), round(maxy, 5)],
                is_default=False,
                geometry_type="Polygon",
            )

    # Fallback canónico Combeima
    lons = [p[0] for p in DEFAULT_COMBEIMA_COORDINATES]
    lats = [p[1] for p in DEFAULT_COMBEIMA_COORDINATES]
    return ParsedGeometry(
        geojson=DEFAULT_COMBEIMA_GEOJSON,
        area_ha=DEFAULT_BASIN_AREA_HA,
        centroid=(round(sum(lons) / len(lons), 5), round(sum(lats) / len(lats), 5)),
        bbox=[round(min(lons), 5), round(min(lats), 5), round(max(lons), 5), round(max(lats), 5)],
        is_default=True,
        geometry_type="Polygon",
    )
