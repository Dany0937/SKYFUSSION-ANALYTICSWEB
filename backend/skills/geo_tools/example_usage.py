"""
Ejemplo de Uso - Geospatial Agent con Sistema de Eventos
=======================================================

Este script demuestra cómo usar el preprocessor con emisión de eventos.

Uso:
    python example_usage.py
"""

import os
import json
from preprocessor import (
    GEEAuthenticator,
    SatelliteDataPreprocessor,
    preprocess_combeima_basin,
    get_event_emitter
)


def main():
    print("\n" + "=" * 60)
    print("SKYFUSION ANALYTICS - GEOSPATIAL AGENT")
    print("Ejemplo de Uso con Sistema de Eventos")
    print("=" * 60)

    # Configurar logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s'
    )

    # 1. Inicializar GEE
    print("\n📡 Inicializando Google Earth Engine...")
    if not GEEAuthenticator.initialize():
        print("⚠️ GEE no disponible. Usando modo simulación.")
        return simulate_execution()

    # 2. Verificar configuración de eventos
    print("\n📋 Configuración de eventos:")
    emitter = get_event_emitter()
    print(f"   Backend: {emitter._bus.__class__.__name__}")
    print(f"   Storage: {emitter._bus.event_store.storageDir}")

    # 3. Consultar un año específico
    print("\n" + "-" * 60)
    print("ESCENARIO 1: Consulta de año específico")
    print("-" * 60)

    result = preprocess_combeima_basin(
        start_date="1985-01-01",
        end_date="1985-12-31",
        output_dir="./data/geospatial",
        emit_events=True
    )

    if result.get("success"):
        print(f"\n✅ Resultado: {result.get('image_count')} imágenes procesadas")

    # 4. Generar serie temporal (demo con años limitados)
    print("\n" + "-" * 60)
    print("ESCENARIO 2: Serie temporal (demo 3 años)")
    print("-" * 60)

    # En producción usar 1969-2023
    preprocessor = SatelliteDataPreprocessor()

    years_demo = [1980, 1985, 1990]

    for year in years_demo:
        print(f"\n📊 Procesando año {year}...")
        result = preprocessor.query_images(
            f"{year}-01-01",
            f"{year}-12-31",
            year=year
        )
        print(f"   ✓ {result.image_count} imágenes")

    # 5. Verificar evento emitido
    print("\n" + "-" * 60)
    print("VERIFICACIÓN DE EVENTOS")
    print("-" * 60)

    last_event = emitter.get_last_event(
        emitter.EVENT_TYPE_IMAGENES_HISTORICAS_LISTAS
    )

    if last_event:
        print("\n📨 Último evento IMAGENES_HISTORICAS_LISTAS:")
        print(json.dumps(last_event.to_dict(), indent=2, default=str))
    else:
        print("\n⚠️ No se encontraron eventos")

    print("\n" + "=" * 60)
    print("✨ Ejecución completada")
    print("=" * 60)


def simulate_execution():
    """Simula ejecución cuando GEE no está disponible."""
    print("\n🔧 Modo simulación (GEE no disponible)")

    emitter = get_event_emitter()

    print("\n📡 Emitiendo evento de demostración...")

    result = emitter.emit_historical_images_ready(
        date_range=("1985-01-01", "1985-12-31"),
        collections_used=[
            "LANDSAT/LM01/T1",
            "LANDSAT/LT05/C02/T1",
            "LANDSAT/LC08/C02/T1_L2"
        ],
        image_count=156,
        cloud_filter_applied=True,
        max_cloud_percent=15.0,
        basin_info={
            "id": "combeima_basin",
            "name": "Cuenca Alta Río Combeima",
            "areaHa": 12450.75
        },
        processing_metrics={
            "yearsProcessed": 1,
            "yearsWithData": 1,
            "filteredByCloud": 45,
            "filterPercent": 22.4
        }
    )

    if result:
        print("✅ Evento emitido exitosamente")
    else:
        print("⚠️ Evento guardado localmente")

    print("\n📂 Archivos generados:")
    import os
    from pathlib import Path

    event_dir = Path("./data/events")
    if event_dir.exists():
        for f in event_dir.glob("*.jsonl"):
            print(f"   - {f}")

    geo_dir = Path("./data/geospatial")
    if geo_dir.exists():
        for f in geo_dir.glob("*.json"):
            print(f"   - {f}")

    print("\n" + "=" * 60)
    print("✨ Simulación completada")
    print("=" * 60)


if __name__ == "__main__":
    main()
