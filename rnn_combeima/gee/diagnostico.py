"""
Diagnóstico de Google Earth Engine — Verificación de Extracción
================================================================

Verifica, en orden, cada componente necesario para extraer series
multitemporales del río Combeima:

  1. SDK earthengine-api instalado
  2. Credenciales guardadas en disco
  3. Autenticación (ee.Initialize)
  4. Proyecto Cloud asociado (ee.data.getAssetRoots)
  5. Acceso a cada colección (size)
  6. Bandas disponibles por colección (metadatos)
  7. Rango temporal real de cada colección (metadatos)
  8. Solape del ROI (cuenca Combeima) con cada colección

Uso:
    python -m gee.diagnostico            # desde la carpeta rnn_combeima
    python rnn_combeima/gee/diagnostico.py
    python rnn_combeima/gee/diagnostico.py --proyecto tu-proyecto-gcp

Nota: si no está autenticado, muestra los pasos exactos para hacerlo
(incluyendo crear/habilitar el proyecto Cloud si la cuenta lo requiere).
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, Optional


def _estado_ok(texto: str = "OK") -> str:
    return f"[ ✔ ] {texto}"


def _estado_fail(texto: str) -> str:
    return f"[ ✖ ] {texto}"


def verificar_sdk() -> bool:
    """1. ¿Está instalado earthengine-api?"""
    print("\n1) SDK earthengine-api")
    try:
        import ee  # noqa: F401
        print(_estado_ok(f"earthengine-api instalado (v{ee.__version__})"))
        return True
    except ImportError:
        print(_estado_fail("No está instalado. Ejecuta:"))
        print("      pip install earthengine-api")
        return False


def verificar_credenciales() -> Optional[str]:
    """2. ¿Existen credenciales guardadas en el perfil del usuario?"""
    print("\n2) Credenciales guardadas")
    home = os.path.expanduser("~")
    candidatos = [
        os.path.join(home, ".config", "earthengine", "credentials"),
        os.path.join(home, ".config", "earthengine"),
        os.path.join(home, ".earthengine", "credentials"),
        os.path.join(home, ".earthengine"),
        os.path.join(os.environ.get("APPDATA", ""), "earthengine", "credentials"),
        os.path.join(os.environ.get("APPDATA", ""), "earthengine"),
    ]
    ruta_creds = None
    for c in candidatos:
        if os.path.isdir(c):
            for f in os.listdir(c):
                if "credential" in f.lower():
                    ruta_creds = os.path.join(c, f)
                    break
        elif os.path.isfile(c):
            ruta_creds = c
        if ruta_creds:
            break

    if ruta_creds:
        print(_estado_ok(f"Credenciales encontradas: {ruta_creds}"))
        return ruta_creds

    print(_estado_fail("Sin credenciales en las rutas estándar de Earth Engine"))
    print("      Ejecuta:  earthengine authenticate")
    print("      o        python -c \"import ee; ee.Authenticate()\"")
    print("      Esto abre el navegador → autoriza con tu cuenta de Google")
    print("      (usa la misma cuenta registrada en https://earthengine.google.com/)")
    return None


def verificar_autenticacion(proyecto: Optional[str] = None) -> bool:
    """3. ¿ee.Initialize() funciona con las credenciales actuales?"""
    print("\n3) Autenticación (ee.Initialize)")
    import ee

    try:
        if proyecto:
            ee.Initialize(project=proyecto)
        else:
            # Sin proyecto explícito: el SDK usa el default de la credencial
            ee.Initialize()
        print(_estado_ok(f"Conexión GEE establecida (proyecto='{proyecto or 'default'}')"))
        return True
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        print(_estado_fail(f"No se pudo inicializar: {msg[:220]}"))
        if "register for Earth Engine" in msg.lower() or "access" in msg.lower():
            print("      Puede que tu cuenta no tenga acceso a Earth Engine aún.")
            print("      Regístrate/acepta en: https://earthengine.google.com/")
        if "project" in msg.lower() or "not enabled" in msg.lower():
            print("      Tu cuenta requiere un proyecto Google Cloud con Earth Engine habilitado.")
            print("      Pasos: 1) https://console.cloud.google.com → crea/elige proyecto")
            print("              2) Activa la API 'Earth Engine API'")
            print("              3) earthengine set_project TU_PROYECTO")
        return False


def verificar_proyecto() -> None:
    """4. Proyecto Cloud asociado (asset roots)."""
    print("\n4) Proyecto Cloud / Asset roots")
    import ee

    try:
        roots = ee.data.getAssetRoots()
        if roots:
            for r in roots:
                print(_estado_ok(f"Root de assets: {r.get('id')} ({r.get('type')})"))
        else:
            print(_estado_fail("Sin asset roots. Asocia un proyecto con:"))
            print("      earthengine set_project TU_PROYECTO")
    except Exception as e:  # noqa: BLE001
        print(_estado_fail(f"No se pudieron consultar asset roots: {str(e)[:180]}"))


def verificar_colecciones(region) -> None:
    """5-8. Acceso a colecciones, bandas, fechas y solape con el ROI."""
    print("\n5-8) Colecciones, bandas, fechas y ROI")
    import ee

    sensores_prueba = {
        "MODIS (MOD13A2)": {
            "id": "MODIS/061/MOD13A2",
            "bandas_esperadas": ["NDVI", "EVI", "SummaryQA"],
        },
        "Sentinel-2 SR": {
            "id": "COPERNICUS/S2_SR_HARMONIZED",
            "bandas_esperadas": ["B3", "B4", "B8", "B8A", "SCL"],
        },
        "Landsat 8 L2": {
            "id": "LANDSAT/LC08/C02/T1_L2",
            "bandas_esperadas": ["SR_B4", "SR_B5", "QA_PIXEL"],
        },
    }

    for nombre, spec in sensores_prueba.items():
        try:
            coleccion = ee.ImageCollection(spec["id"]).filterDate("2015-01-01", "2024-12-31")
            n = int(coleccion.size().getInfo())
            print(_estado_ok(f"{nombre}: {n} imágenes 2015-2024"))

            # Solape con el ROI
            n_roi = int(coleccion.filterBounds(region).size().getInfo())
            print(_estado_ok(f"   → {n_roi} imágenes intersectando la cuenca Combeima"))

            # Metadatos: bandas de la primera imagen
            primera = coleccion.first()
            if primera:
                bandas = primera.bandNames().getInfo()
                fecha = primera.date().format("YYYY-MM-dd").getInfo()
                print(_estado_ok(f"   → primera fecha: {fecha}"))
                faltantes = [b for b in spec["bandas_esperadas"] if b not in bandas]
                if faltantes:
                    print(_estado_fail(f"   → faltan bandas esperadas: {faltantes}"))
                    print(f"   → bandas reales ({len(bandas)}): {bandas[:14]}...")
                else:
                    print(_estado_ok(f"   → bandas esperadas presentes: {spec['bandas_esperadas']}"))
            else:
                print(_estado_fail("   → colección vacía en el rango (sin metadatos)"))
        except Exception as e:  # noqa: BLE001
            print(_estado_fail(f"{nombre}: {str(e)[:180]}"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnóstico de acceso a GEE")
    parser.add_argument("--proyecto", type=str, default=None,
                        help="ID del proyecto Google Cloud (si tu cuenta lo requiere)")
    args = parser.parse_args()

    print("=" * 64)
    print("DIAGNÓSTICO GEE — Extracción multitemporal Río Combeima")
    print("=" * 64)

    if not verificar_sdk():
        sys.exit(1)

    verificar_credenciales()
    if not verificar_autenticacion(args.proyecto):
        print("\n[ RESUMEN ] Corre la autenticación y vuelve a ejecutar este script.")
        sys.exit(1)

    verificar_proyecto()

    # ROI: cuenca Combeima (bbox de config/experiments.ZONAS)
    bbox = [-75.6560, 4.3950, -75.2130, 4.6500]
    import ee
    region = ee.Geometry.Rectangle(bbox)
    print(f"\nROI (cuenca Combeima): {bbox}")

    verificar_colecciones(region)

    print("\n[ RESUMEN ] Diagnóstico completado.")
    print("Si todos los pasos muestran ✔, ejecuta:")
    print("   python scripts/via_completa.py --extraer --sensores modis,sentinel2,landsat")


if __name__ == "__main__":
    main()