"""
Extracción Multitemporal Multisensor desde Google Earth Engine
===============================================================

Extrae series temporales de índices espectrales (NDVI, EVI, NDWI) del
área del río Combeima (Ibagué, Tolima) usando múltiples sensores:

- MODIS        (MODIS/061/MOD13A2, 1 km, 16 días)   → serie larga 2015-2024
- Landsat 8 L2 (LANDSAT/LC08/C02/T1_L2, 30 m)       → resolución media
- Sentinel-2   (COPERNICUS/S2_SR_HARMONIZED, 10 m)  → alta resolución

Correcciones frente a versiones anteriores (verificación de API/metadatos):
- MODIS NDVI/EVI se multiplican por 0.0001 (escala del producto int16).
- La banda de calidad de MOD13A2 es `SummaryQA` (no existe `QA_PIXEL`).
- Sentinel-2 disponible desde 2017-01-01 (no 2015).
- Landsat C2 L2 SR usa factor 0.0000275 y offset -0.2.
- Máscaras QA aplicadas en el servidor (evita NaN locales).
- `aggregate_array` para fechas y `toBands()+sampleRegions` para muestreo →
  extracción con pocas llamadas de red.

Autenticación: `ee.Initialize(project=...)` si la cuenta lo requiere
(proyecto Cloud con Earth Engine API, obligatorio para cuentas post-2023).
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import ee
    TENER_GEE = True
except ImportError:
    TENER_GEE = False
    ee = None

from config.experiments import GEE_CONFIG, SENSORES, ZONAS


# --------------------------------------------------------------------------- #
# Conexión y autenticación
# --------------------------------------------------------------------------- #

def inicializar_gee(proyecto: Optional[str] = None) -> None:
    """
    Inicializa la sesión de Earth Engine.

    Args:
        proyecto: ID del proyecto Google Cloud. Si es None se usa
                  GEE_CONFIG['proyecto_id'] si está definido.
    """
    if not TENER_GEE:
        raise RuntimeError(
            "La librería 'earthengine-api' no está instalada. "
            "Ejecuta: pip install earthengine-api\n"
            "Y autentica: earthengine authenticate"
        )
    proyecto = proyecto or (GEE_CONFIG.get("proyecto_id") or None)

    try:
        if ee.data._initialized:  # noqa: SLF001
            print(f"✔ GEE ya inicializado. Proyecto: {proyecto or 'default'}")
            return
    except Exception:  # noqa: BLE001
        pass

    try:
        if proyecto:
            ee.Initialize(project=proyecto)
        else:
            ee.Initialize()
        print(f"✔ Conexión GEE establecida. Proyecto: {proyecto or 'default'}")
    except Exception as e:  # noqa: BLE001
        _guiar_error_auth(str(e))
        raise


def _guiar_error_auth(msg: str) -> None:
    """Imprime guía accionable según el error de inicialización."""
    print("✖ No se pudo inicializar GEE.")
    if "authorize access" in msg.lower():
        print("  → Autentícate una vez:")
        print("      earthengine authenticate")
        print("    o en Python:")
        print("      import ee; ee.Authenticate()")
    elif "project" in msg.lower() or "not enabled" in msg.lower():
        print("  → Tu cuenta requiere proyecto Google Cloud con Earth Engine API:")
        print("      1) https://console.cloud.google.com → crea/elige un proyecto")
        print("      2) Activa la API 'Earth Engine API'")
        print("      3)  earthengine set_project TU_PROYECTO ")
        print("      4) Completa config/experiments.py → GEE_CONFIG['proyecto_id']")
    elif "has not been activated" in msg.lower() or "register" in msg.lower():
        print("  → Tu cuenta no tiene Earth Engine activo aún.")
        print("      Regístrate en: https://earthengine.google.com/")


def bbox_a_geometria(bbox: List[float]) -> ee.Geometry.Rectangle:
    """Convierte [lon_min, lat_min, lon_max, lat_max] en ee.Geometry.Rectangle."""
    return ee.Geometry.Rectangle(bbox)


# --------------------------------------------------------------------------- #
# Preparación de imágenes por sensor (QA + escala + índices) en el servidor
# --------------------------------------------------------------------------- #

def _mascara_qa_sensor(imagen: ee.Image, sensor: str) -> ee.Image:
    """Aplica máscara QA válida a una imagen según el sensor."""
    qa_band = SENSORES[sensor]["qa"]
    qa = imagen.select(qa_band).toInt()

    if sensor == "modis":
        # SummaryQA: 0=good, 1=marginal, 2=snow/ice, 3=cloudy
        ok = qa.lte(1)
    elif sensor == "sentinel2":
        # SCL: 2=dark, 4=veg, 5=bare, 6=water (excluye nubes/sombra/nieve)
        ok = qa.inList([2, 4, 5, 6])
    elif sensor == "landsat":
        # QA_PIXEL: bit6=clear, sin cloud(3)/shadow(4)/snow(5)
        clear = qa.bitwiseAnd(1 << 6).eq(1 << 6)
        nocnly = qa.bitwiseAnd((1 << 3) | (1 << 4) | (1 << 5)).eq(0)
        ok = clear.And(nocnly)
    else:
        ok = ee.Image.constant(1)

    return imagen.updateMask(ok)


def _crowder_indices_sensor(coleccion: ee.ImageCollection, sensor: str) -> ee.ImageCollection:
    """
    Devuelve la colección con las bandas de interés por sensor,
    QA aplicado y escala/índices sobre el valor crudo:

    - modis     : NDVI, EVI (×0.0001), SummaryQA
    - sentinel2 : NDVI, NDWI, SCL (derivados de B4/B8/B3 ×0.0001)
    - landsat   : NDVI, QA_PIXEL (SR_B4/SR_B5 ×0.0000275 - 0.2)
    """

    def _una(imagen: ee.Image) -> ee.Image:
        img = _mascara_qa_sensor(imagen, sensor)

        if sensor == "modis":
            ndvi = img.select("NDVI").toFloat().multiply(0.0001).rename("NDVI")
            evi = img.select("EVI").toFloat().multiply(0.0001).rename("EVI")
            res = ndvi.addBands(evi).addBands(img.select("SummaryQA"))

        elif sensor == "sentinel2":
            b4 = img.select("B4").toFloat().multiply(0.0001)
            b8 = img.select("B8").toFloat().multiply(0.0001)
            b3 = img.select("B3").toFloat().multiply(0.0001)
            ndvi = b8.subtract(b4).divide(b8.add(b4)).rename("NDVI")
            ndwi = b3.subtract(b8).divide(b3.add(b8)).rename("NDWI")
            res = ndvi.addBands(ndwi).addBands(img.select("SCL"))

        elif sensor == "landsat":
            b4 = img.select("SR_B4").toFloat().multiply(0.0000275).add(-0.2)
            b5 = img.select("SR_B5").toFloat().multiply(0.0000275).add(-0.2)
            ndvi = b5.subtract(b4).divide(b5.add(b4)).rename("NDVI")
            res = ndvi.addBands(img.select("QA_PIXEL"))
        else:
            res = imagen

        # Un valor sentinel evita que `toBands()` descarte un punto completo
        # cuando una fecha individual queda enmascarada por QA.
        return res.select(res.bandNames().removeAll(["constant"])).unmask(-9999)

    return coleccion.map(_una)


# --------------------------------------------------------------------------- #
# Extracción de la serie temporal por sensor (una sola llamada de red)
# --------------------------------------------------------------------------- #

def construir_serie_sensor(
    zona: str,
    sensor: str,
    fecha_inicio: str,
    fecha_fin: str,
    n_muestras: int = 300,
) -> pd.DataFrame:
    """
    Extrae la serie temporal de índices para un sensor sobre la zona usando
    `toBands()` (apila todas las fechas como bandas) + `sampleRegions`.

    Returns:
        DataFrame con columnas: fecha, longitude, latitude, <bandas>...
    """
    if sensor not in SENSORES:
        raise ValueError(f"Sensor '{sensor}' no configurado.")

    spec = SENSORES[sensor]
    region = bbox_a_geometria(ZONAS[zona]["bbox"])

    coleccion = (
        ee.ImageCollection(spec["coleccion"])
        .filterBounds(region)
        .filterDate(fecha_inicio, fecha_fin)
    )

    n_total = int(coleccion.size().getInfo())
    if n_total == 0:
        print(f"  ⚠ {sensor}: sin imágenes en {fecha_inicio}..{fecha_fin}")
        return pd.DataFrame()
    print(f"  🛰 {sensor}: {n_total} imágenes en el rango solicitado")

    # ----- Metadatos: fechas del sistema (una sola llamada) -----
    fechas_ms = [int(t) for t in coleccion.aggregate_array("system:time_start").getInfo()]
    n_fechas = len(fechas_ms)

    # Preparar bandas de interés + QA + escala
    preparada = _crowder_indices_sensor(coleccion, sensor)

    # Apilar todas las fechas → bandas tipo '<fecha>_<banda>
    apilada = preparada.toBands()
    nombres_banda = apilada.bandNames().getInfo()
    n_campos = max(len(nombres_banda) // max(n_fechas, 1), 1)

    # Puntos de muestreo espacial dentro de la cuenca
    puntos = ee.FeatureCollection.randomPoints(region=region, points=n_muestras, seed=42)

    muestras = apilada.sampleRegions(
        collection=puntos,
        scale=spec["escala"],
        geometries=True,
    )
    features = muestras.getInfo().get("features", [])
    print(f"  📍 {len(features)} puntos muestreados a {spec['escala']} m")

    # ----- Ensamblado del DataFrame -----
    registros: List[Dict] = []
    for f in features:
        props = f.get("properties", {})
        geometria = f.get("geometry") or {}
        coords = geometria.get("coordinates") or []
        if len(coords) != 2:
            continue
        lon, lat = float(coords[0]), float(coords[1])

        for i, nombre in enumerate(nombres_banda):
            if not isinstance(nombre, str):
                continue
            # Índice lógico de la fecha en la agrupación de toBands
            k = i // n_campos
            if k >= n_fechas:
                continue
            fecha = pd.to_datetime(fechas_ms[k], unit="ms")
            bandas_conocidas = ("NDVI", "EVI", "NDWI", "SummaryQA", "SCL")
            banda = next(
                (b for b in bandas_conocidas if nombre.endswith(f"_{b}")),
                nombre.rsplit("_", 1)[-1],
            )
            valor = props.get(nombre)
            if valor is None or float(valor) <= -9998:
                continue
            registros.append({
                "fecha": fecha,
                "longitude": lon,
                "latitude": lat,
                banda: float(valor),
            })

    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)
    # Compactar una fila por (fecha, punto) con una columna por banda
    pivote = df.pivot_table(
        index=["fecha", "longitude", "latitude"],
        aggfunc="first",
    ).reset_index()
    pivote = pivote.sort_values(["longitude", "latitude", "fecha"]).reset_index(drop=True)
    return pivote


# --------------------------------------------------------------------------- #
# Verificación de extracción multitemporal
# --------------------------------------------------------------------------- #

def verificar_extraccion(df: Optional[pd.DataFrame], zona: str) -> Dict[str, object]:
    """
    Verifica que la extracción sea verdaderamente multitemporal:
    - número de fechas únicas por píxel (>1 confirma multitemporal)
    - rango temporal cubierto
    - tamaño total
    """
    if df is None or df.empty:
        return {"estado": "VACÍO", "detalle": "No hay datos extraídos."}

    fechas_por_pixel = df.groupby(["longitude", "latitude"])["fecha"].nunique()

    return {
        "estado": "OK",
        "zona": zona,
        "filas_total": int(len(df)),
        "pixeles_unicos": int(df[["longitude", "latitude"]].drop_duplicates().shape[0]),
        "fechas_unicas_total": int(df["fecha"].nunique()),
        "rango_temporal": [
            str(df["fecha"].min().date()),
            str(df["fecha"].max().date()),
        ],
        "media_fechas_por_pixel": float(fechas_por_pixel.mean()),
        "min_fechas_por_pixel": int(fechas_por_pixel.min()),
        "max_fechas_por_pixel": int(fechas_por_pixel.max()),
        "nulos_por_banda": {
            c: int(df[c].isna().sum())
            for c in df.columns
            if c not in ("fecha", "longitude", "latitude")
        },
        "promedio_ndvi_muestreo": float(df["NDVI"].mean()) if "NDVI" in df.columns else None,
    }


# --------------------------------------------------------------------------- #
# Función principal
# --------------------------------------------------------------------------- #

def extraer_combeima(
    fecha_inicio: str = "2015-01-01",
    fecha_fin: str = "2024-12-31",
    n_puntos: int = 300,
    sensores: Optional[List[str]] = None,
    guardar: bool = True,
    ruta_salida: str = "data/raw/series_multisensor_combeima.csv",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Función principal: extrae series multitemporales multisensor de la cuenca
    del Combeima y genera un reporte de verificación.

    Returns:
        (df_series, df_verificacion)
    """
    if not TENER_GEE:
        print("⚠ No se encontró 'ee'. Instala earthengine-api y autentica.")
        return pd.DataFrame(), pd.DataFrame()

    inicializar_gee()

    sensores = sensores or ["modis"]
    dfs: List[pd.DataFrame] = []
    verificaciones: List[Dict] = []

    for sensor in sensores:
        df = construir_serie_sensor(
            zona="combeima",
            sensor=sensor,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            n_muestras=n_puntos,
        )
        if not df.empty:
            df["sensor"] = sensor
            dfs.append(df)
            verif = verificar_extraccion(df, "combeima")
            verif["sensor"] = sensor
            verificaciones.append(verif)
            print(f"✔ {sensor}: {len(df)} filas")

    if not dfs:
        print("❌ No se extrajo ningún dato.")
        return pd.DataFrame(), pd.DataFrame(verificaciones)

    df_serie = pd.concat(dfs, ignore_index=True)

    if guardar:
        os.makedirs(os.path.dirname(ruta_salida) or ".", exist_ok=True)
        df_serie.to_csv(ruta_salida, index=False)
        print(f"💾 Serie guardada en {ruta_salida}")

    df_verif = pd.DataFrame(verificaciones)
    return df_serie, df_verif


if __name__ == "__main__":
    serie, verificacion = extraer_combeima()
    print("\n=== VERIFICACIÓN DE EXTRACCIÓN MULTITEMPORAL ===")
    if not verificacion.empty:
        print(verificacion.to_string(index=False))