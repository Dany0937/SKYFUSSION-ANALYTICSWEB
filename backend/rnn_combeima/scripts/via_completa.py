"""
Script principal del proyecto RNN Combeima
=========================================

Pasos principales (para revisar el flujo completo):
    1) autenticar:   python scripts/via_completa.py --autenticar
    2) extraer:      python scripts/via_completa.py --extraer
    3) verificar:    python scripts/via_completa.py --verificar
    4) entrenar:     python scripts/via_completa.py --entrenar --lote basico
    5) reporte:      python scripts/via_completa.py --reporte

Sin GEE autenticado, el entrenamiento usa datos sintéticos de prueba para
validar que el pipeline de RNA funciona de punta a punta.
"""

import os
import sys
import argparse

# Asegurar path
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def cmd_autenticar(proyecto=None):
    """Guía de autenticación de GEE, incl. proyecto Cloud (obligatorio post-2023)."""
    print("🔐 Autenticación de Google Earth Engine\n")
    print("Paso 1 — Autentícate una vez (abre el navegador):")
    print("    earthengine authenticate")
    print("    # o en Python:")
    print("    #    import ee; ee.Authenticate()")
    print()
    print("Paso 2 — Define tu proyecto Google Cloud (cuentas creadas desde 2023):")
    print("    1) https://console.cloud.google.com  →  crea o elige un proyecto")
    print("    2) Activa la API 'Earth Engine API' en ese proyecto")
    print("    3) Vincula el proyecto a GEE:")
    print("         earthengine set_project TU_PROYECTO")
    print()
    print("Paso 3 — Completa el ID en config/experiments.py  →  GEE_CONFIG['proyecto_id']")
    print("    (o pásalo aquí con   python scripts/via_completa.py --autenticar --proyecto miproyecto)\n")

    try:
        import ee
        print("✔ earthengine-api instalada (v2). Validando credenciales...")
        if proyecto:
            ee.Initialize(project=proyecto)
        else:
            ee.Initialize()
        print("   OK — credenciales guardadas y sesión iniciada.")
    except Exception as e:  # noqa: BLE001
        print(f"   ✖ No se pudo iniciar sesión: {str(e)[:200]}")
        print("   Vuelve a los pasos 1-3 y reintenta.")


def cmd_extraer(*, sensores=None, n_puntos=300):
    from gee.extractor import extraer_combeima
    serie, verif = extraer_combeima(n_puntos=n_puntos, sensores=sensores)
    return serie, verif


def cmd_verificar(ruta_csv=None):
    from gee.extractor import verificar_extraccion
    import pandas as pd
    ruta_csv = ruta_csv or os.path.join(ROOT, "data", "raw",
                                        "series_multisensor_combeima.csv")
    if not os.path.exists(ruta_csv):
        print(f"⚠ No existe {ruta_csv}. Corre --extraer primero.")
        return
    df = pd.read_csv(ruta_csv, parse_dates=["fecha"])
    verif = verificar_extraccion(df, "combeima")
    print("\n=== VERIFICACIÓN MULTITEMPORAL ===")
    for k, v in verif.items():
        print(f"   {k}: {v}")
    return verif


def cmd_entrenar(lote, epochs, reales):
    from rnn.train import ejecutar_lote
    tabla = ejecutar_lote(lote, epochs, usar_datos_reales=reales)
    print(tabla.to_string(index=False))
    return tabla


def cmd_reporte():
    from rnn.reporting import consolidar_resultados, ranking_por_metrica, guardar_reporte
    df = consolidar_resultados(os.path.join(ROOT, "experiments"))
    if df.empty:
        print("Sin resultados. Ejecuta --entrenar primero.")
        return
    print("=== CONSOLIDADO ===")
    print(df.to_string(index=False))
    rank = ranking_por_metrica(df, "rmse")
    print("\n=== RANKING RMSE ===")
    print(rank.head(15).to_string(index=False))
    guardar_reporte(df, os.path.join(ROOT, "reports", "resumen_final.csv"))


def main():
    parser = argparse.ArgumentParser(description="Pipeline RNN Río Combeima")
    parser.add_argument("--autenticar", action="store_true")
    parser.add_argument("--proyecto", type=str, default=None,
                        help="ID del proyecto Google Cloud para GEE")
    parser.add_argument("--extraer", action="store_true")
    parser.add_argument("--n-puntos", type=int, default=300)
    parser.add_argument("--sensores", type=str, default=None,
                        help="comma-separated: modis,sentinel2,landsat")
    parser.add_argument("--verificar", action="store_true")
    parser.add_argument("--entrenar", action="store_true")
    parser.add_argument("--lote", default="smoke")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--reales", action="store_true")
    parser.add_argument("--reporte", action="store_true")
    args = parser.parse_args()

    if args.autenticar:
        cmd_autenticar(proyecto=args.proyecto)
    if args.extraer:
        sensores = args.sensores.split(",") if args.sensores else None
        print("🔍 Extrayendo datos multitemporales del Combeima...")
        cmd_extraer(sensores=sensores, n_puntos=args.n_puntos)
    if args.verificar:
        cmd_verificar()
    if args.entrenar:
        print(f"🧠 Entrenando lote '{args.lote}'...")
        cmd_entrenar(args.lote, args.epochs, args.reales)
    if args.reporte:
        cmd_reporte()

    if not any([args.autenticar, args.extraer, args.verificar,
                args.entrenar, args.reporte]):
        parser.print_help()


if __name__ == "__main__":
    main()
