"""
Motor de Entrenamiento y Evaluación de Experimentos RNA
=======================================================

Ejecuta la matriz de experimentos definida en config/experiments.py:
para cada experimento (arquitectura × config × horizonte × zona):

1. Prepara los datos (o reutiliza splits cacheados)
2. Construye el modelo RNA correspondiente
3. Entrena con callbacks (early stopping, reduceLR, checkpoint)
4. Evalúa en test con métricas (MAE, RMSE, R², SMAPE)
5. Genera curvas de aprendizaje y comparación final

El resultado es una tabla comparativa journeys (experiments/summary.csv)
y grátis de todos los modelos.
"""

import os
import json
import time
from datetime import datetime
from copy import deepcopy
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

import tensorflow as tf
from tensorflow import keras

import sys

# Asegurar import del paquete rnn y config
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config.experiments import (  # noqa: E402
    ARQUITECTURAS_RNN, HORIZONTES_PASOS, ZONAS,
    expandir_lote, Experimento,
)
from rnn.models import crear_modelo, resumen_arquitectura, contar_parametros  # noqa: E402
from rnn.preprocess import preparar_datos  # noqa: E402


BASE_DATOS = os.path.join(ROOT, "data", "raw", "series_multisensor_combeima.csv")
BASE_EXP = os.path.join(ROOT, "experiments")


def _meticas(pred: np.ndarray, real: np.ndarray) -> Dict[str, float]:
    """Métricas en escala original (después de desescalar)."""
    pred = np.asarray(pred, dtype=np.float64).reshape(-1)
    real = np.asarray(real, dtype=np.float64).reshape(-1)
    errores = real - pred

    mae = float(np.mean(np.abs(errores)))
    rmse = float(np.sqrt(np.mean(errores ** 2)))
    r2 = float(1.0 - np.sum(errores ** 2) / (np.sum((real - np.mean(real)) ** 2) + 1e-12))
    smape = float(100 * np.mean(2 * np.abs(pred - real) /
                                (np.abs(real) + np.abs(pred) + 1e-12)))
    return {"mae": mae, "rmse": rmse, "r2": r2, "smape": smape}


def _callbacks(exp_id: str, epochs: int, dir_out: str) -> list:
    os.makedirs(dir_out, exist_ok=True)
    return [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=min(8, epochs // 2),
            restore_best_weights=True, mode="min",
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=4, min_lr=1e-6, mode="min",
        ),
        keras.callbacks.ModelCheckpoint(
            os.path.join(dir_out, f"{exp_id}.keras"),
            monitor="val_loss", save_best_only=True, mode="min",
        ),
        keras.callbacks.CSVLogger(os.path.join(dir_out, f"{exp_id}_train.csv")),
    ]


def ejecutar_un_experimento(
    exp: Experimento,
    datos: Dict[str, np.ndarray],
    dir_run: str,
    fuente: str = "desconocida",
) -> Dict:
    """
    Entrena y evalúa un experimento individual. devuelve dict de resultados.
    """
    t_inicio = time.time()

    X_train, y_train = datos["X_train"], datos["y_train"]
    X_val, y_val = datos["X_val"], datos["y_val"]
    X_test, y_test = datos["X_test"], datos["y_test"]
    scaler_y = datos["scaler_y"]
    timesteps = datos["timesteps"]

    n_features = X_train.shape[-1]
    horizonte = exp.horizonte

    # Config del modelo: garantizar timesteps/horizonte consistentes
    cfg_modelo = deepcopy(exp.config)
    cfg_modelo["seed"] = exp.seed

    modelo = crear_modelo(
        arquitectura=exp.arquitectura,
        timesteps=timesteps,
        n_features=n_features,
        horizonte=horizonte,
        config=cfg_modelo,
    )

    n_params = contar_parametros(modelo)

    print(f"\n🚀 EXPERIMENTO: {exp.id}")
    print(f"   Arquitectura: {exp.arquitectura}")
    print(f"   Config: {resumen_arquitectura(exp.arquitectura, exp.config)}")
    print(f"   Horizonte: {horizonte} pasos | Parámetros: {n_params}")

    dir_exp = os.path.join(dir_run, exp.id)
    os.makedirs(dir_exp, exist_ok=True)

    callbacks = _callbacks(exp.id, exp.epochs, dir_exp)

    historial = modelo.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=exp.epochs,
        batch_size=exp.config.get("batch_size", 32),
        callbacks=callbacks,
        verbose=0,
    )

    # Evaluación
    y_pred = modelo.predict(X_test, verbose=0)

    # Desescalar al rango original
    y_pred_orig = scaler_y.inverse_transform(y_pred.reshape(-1, 1)).reshape(
        y_pred.shape
    )
    y_test_orig = scaler_y.inverse_transform(y_test.reshape(-1, 1)).reshape(
        y_test.shape
    )

    # Para horizonte>1: evaluar el primer paso como referencia puntual
    metricas = _meticas(y_pred_orig[:, 0], y_test_orig[:, 0])

    # Curvas de aprendizaje → CSV
    hist_df = pd.DataFrame(historial.history)
    hist_df.to_csv(os.path.join(dir_exp, "history.csv"), index=False)

    mejor_val = float(historial.history["val_loss"][np.argmin(
        historial.history["val_loss"])]) if historial.history.get("val_loss") else None

    resultado = {
        "id": exp.id,
        "arquitectura": exp.arquitectura,
        "horizonte": exp.horizonte,
        "zona": exp.zona,
        "fuente": fuente,
        "epochs": exp.epochs,
        "params": n_params,
        "config_json": json.dumps(exp.config),
        "mae": metricas["mae"],
        "rmse": metricas["rmse"],
        "r2": metricas["r2"],
        "smape": metricas["smape"],
        "mejor_val_loss": mejor_val,
        "tiempo_seg": round(time.time() - t_inicio, 1),
        "dir": dir_exp,
    }

    # Guardar resultado individual
    with open(os.path.join(dir_exp, "resultado.json"), "w") as f:
        json.dump(resultado, f, indent=2, default=str)

    print(f"   ✔ MAE={metricas['mae']:.4f} RMSE={metricas['rmse']:.4f} "
          f"R²={metricas['r2']:.4f} SMAPE={metricas['smape']:.2f}% "
          f"({resultado['tiempo_seg']}s)")
    return resultado


def ejecutar_lote(
    nombre_lote: str,
    epochs_override: Optional[int] = None,
    lote_solo: Optional[List[str]] = None,
    semilla: int = 42,
    usar_datos_reales: bool = False,
) -> pd.DataFrame:
    """
    Ejecuta todo el lote de experimentos y devuelve tabla comparativa.

    Args:
        nombre_lote: clave en config.experiments.LOTES
        epochs_override: forzar épocas (por defecto uso lote)
        lote_solo: lista opcional de ids de experimento a ejecutar
        semilla: semilla global
        usar_datos_reales: False → genera datos sintéticos de prueba
                            True  → requiere datos reales de GEE extraídos
    """
    experimentos = expandir_lote(nombre_lote, epochs_override, semilla)
    if lote_solo:
        experimentos = [e for e in experimentos if e.id in lote_solo]
    print(f"📋 Lote '{nombre_lote}': {len(experimentos)} experimentos")

    # Preparar datos una sola vez (por el primer exp que defina timesteps/horizonte)
    # Usamos un dataset base. Idealmente separar por horizonte, aquí usamos el
    # primer horizonte del lote para generar splits y re-ventaneamos según
    # horizonte de cada experimento.

    datos_por_horizonte: Dict[int, Dict] = {}
    if usar_datos_reales:
        ruta = BASE_DATOS
        uso = "REALES (GEE)"
    else:
        ruta = _generar_datos_sinteticos()
        uso = "SINTÉTICOS (prueba)"

    print(f"ℹ Fuente de datos: {uso} → {ruta}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_run = os.path.join(BASE_EXP, f"run_{stamp}__{nombre_lote}")
    os.makedirs(dir_run, exist_ok=True)

    resultados = []
    for exp in experimentos:
        # Preparar datos por horizonte (cachear)
        if exp.horizonte not in datos_por_horizonte:
            datos_por_horizonte[exp.horizonte] = preparar_datos(
                ruta_csv=ruta,
                target="NDVI",
                timesteps=24,
                horizonte=exp.horizonte,
                semilla=semilla,
                guardar_splits=False,
            )
        datos = datos_por_horizonte[exp.horizonte]
        res = ejecutar_un_experimento(exp, datos, dir_run, fuente=uso)
        resultados.append(res)

    df_res = pd.DataFrame(resultados)
    ruta_sum = os.path.join(dir_run, "summary.csv")
    df_res.to_csv(ruta_sum, index=False)
    print(f"\n✅ Resumen guardado en {ruta_sum}")
    return df_res


# --------------------------------------------------------------------------- #
# Datos sintéticos de prueba (para verificar el pipeline sin GEE autenticado)
# --------------------------------------------------------------------------- #

def _generar_datos_sinteticos() -> str:
    """Genera datos sintéticos multitemporales con señal estacional realista."""
    ruta = os.path.join(ROOT, "data", "raw", "series_sinteticas_combima.csv")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    from config.experiments import ZONAS

    bbox = ZONAS["combeima"]["bbox"]
    if os.path.exists(ruta):
        existente = pd.read_csv(ruta, usecols=["longitude", "latitude"])
        dentro_roi = (
            existente["longitude"].between(bbox[0], bbox[2]).all()
            and existente["latitude"].between(bbox[1], bbox[3]).all()
        )
        if dentro_roi:
            return ruta
        print("⚠ Dataset sintético fuera del ROI configurado; se regenerará.")

    rng = np.random.default_rng(42)
    # 40 píxeles, 10 años cada 16 días
    fechas = pd.date_range("2015-01-01", "2024-12-31", freq="16D")
    filas = []
    for p in range(40):
        lon = rng.uniform(bbox[0], bbox[2])
        lat = rng.uniform(bbox[1], bbox[3])
        fase = rng.uniform(0, 2 * np.pi)
        amp = rng.uniform(0.15, 0.45)
        base = rng.uniform(0.35, 0.7)
        for i, dt in enumerate(fechas):
            doy = dt.dayofyear
            # señal estacional + tendencia leve + ruido
            ndvi = base + amp * np.sin(2 * np.pi * (doy / 365) + fase) + \
                   rng.normal(0, 0.02)
            ndvi = float(np.clip(ndvi, 0.05, 0.95))
            evi = float(np.clip(ndvi * 0.75 + rng.normal(0, 0.02), 0, 0.9))
            filas.append({
                "fecha": dt, "longitude": lon, "latitude": lat,
                "NDVI": ndvi, "EVI": evi,
            })
    df = pd.DataFrame(filas)
    df.to_csv(ruta, index=False)
    print(f"🧪 Datos sintéticos generados: {ruta} ({len(df)} filas)")
    return ruta


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ejecutar lote de experimentos RNA")
    parser.add_argument("--lote", default="smoke", help="lote: smoke/basico/completo/todos")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--reales", action="store_true",
                        help="usar datos reales de GEE (requiere extracción)")
    args = parser.parse_args()

    tabla = ejecutar_lote(args.lote, args.epochs, usar_datos_reales=args.reales)
    print("\n=== TABLA COMPARATIVA ===")
    cols = ["id", "arquitectura", "horizonte", "mae", "rmse", "r2", "smape", "tiempo_seg"]
    print(tabla[[c for c in cols if c in tabla.columns]].to_string(index=False))
