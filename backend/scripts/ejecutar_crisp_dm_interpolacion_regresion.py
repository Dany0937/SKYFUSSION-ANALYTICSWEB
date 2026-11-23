"""
Ejecutor de Pipeline CRISP-DM: Interpolación y Regresión Lineal
==============================================================
Skyfusion Analytics - Cuenca del Río Combeima
Orquesta las 6 fases de la metodología CRISP-DM con soporte para:
1. Serie temporal multitemporal completa (2015-2024).
2. Serie reducida representativa de MÁXIMO 15 DATOS (Mes a Mes vs Año a Año).
"""

import os
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# Añadir skills al path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "skills" / "ml_tools"))

from spectral_interpolator import SpectralTemporalInterpolator
from crisp_linear_regression import CrispLinearRegressor

def main():
    print("=" * 75)
    print("INICIO DEL PIPELINE CRISP-DM: INTERPOLACIÓN Y REGRESIÓN LINEAL")
    print("Skyfusion Analytics · Cuenca del Río Combeima")
    print("=" * 75)

    reports_dir = ROOT_DIR / "reports" / "crisp_dm"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # FASE 1: BUSINESS UNDERSTANDING
    # -------------------------------------------------------------
    print("\n[FASE 1: BUSINESS UNDERSTANDING]")
    print("- Problema: Pérdida de continuidad en el monitoreo satelital debido a nubosidad recurrente")
    print("  en la cuenca alta del río Combeima.")
    print("- Requerimiento Operativo: Análisis con serie reducida de máximo 15 datos para reportes ejecutivos.")
    print("- Objetivo 1: Reconstruir series continuas de NDVI mediante interpolación matemática.")
    print("- Objetivo 2: Estimar la tendencia mensual y multianual mediante regresión lineal.")

    # -------------------------------------------------------------
    # FASE 2: DATA UNDERSTANDING
    # -------------------------------------------------------------
    print("\n[FASE 2: DATA UNDERSTANDING]")
    data_raw_path = ROOT_DIR / "rnn_combeima" / "data" / "raw" / "series_multisensor_combeima.csv"
    if not data_raw_path.exists():
        data_raw_path = ROOT_DIR / "rnn_combeima" / "data" / "raw" / "series_sinteticas_combima.csv"

    df_raw = pd.read_csv(data_raw_path)
    df_raw["fecha"] = pd.to_datetime(df_raw["fecha"])
    df_raw = df_raw.sort_values("fecha").reset_index(drop=True)

    print(f"- Fuente de datos: {data_raw_path.name}")
    print(f"- Total observaciones: {len(df_raw)} registros")
    print(f"- Rango temporal: {df_raw['fecha'].min().date()} a {df_raw['fecha'].max().date()}")

    # -------------------------------------------------------------
    # FASE 3: DATA PREPARATION (INTERPOLACIÓN GENERAL Y SERIE 15 DATOS)
    # -------------------------------------------------------------
    print("\n[FASE 3: DATA PREPARATION - INTERPOLACIÓN]")
    interpolator = SpectralTemporalInterpolator(date_col="fecha")

    # 3.1 Serie Completa
    serie_temporal = df_raw.groupby("fecha")[["NDVI", "EVI"]].mean().reset_index()
    df_eval_interp = interpolator.evaluate_methods(serie_temporal["NDVI"], gap_percentage=0.20, gap_block_size=3)
    df_eval_interp.to_csv(reports_dir / "tabla_metrica_interpolacion.csv", index=False)
    serie_interpolada = interpolator.interpolate_dataframe(serie_temporal, value_cols=["NDVI", "EVI"], method="time")

    # 3.2 Serie Reducida de MÁXIMO 15 DATOS: Muestreo Mes a Mes (15 meses continuos)
    df_15m = interpolator.resample_to_max_points(
        df_raw,
        max_points=15,
        mode="mes_a_mes",
        numeric_cols=["NDVI", "EVI"]
    )
    print(f"\n✔ Serie Mes a Mes generada ({len(df_15m)} datos):")
    print(df_15m[["fecha", "NDVI", "EVI"]].to_string(index=False))

    # Simular huecos por nubosidad en la serie de 15 meses (ej. mes 4 y mes 11)
    df_15m_huecos = df_15m.copy()
    indices_huecos = [3, 10] # 2 meses nublados
    df_15m_huecos.loc[indices_huecos, "NDVI"] = np.nan

    # Interpolar con diferentes métodos
    s_lineal_15 = interpolator.interpolate_series(df_15m_huecos["NDVI"], method="linear")
    s_pchip_15 = interpolator.interpolate_series(df_15m_huecos["NDVI"], method="pchip")

    # Tabla comparativa de interpolación en 15 datos
    tabla_15 = pd.DataFrame({
        "fecha": df_15m["fecha"].dt.strftime("%Y-%m"),
        "NDVI_Real": df_15m["NDVI"].round(4),
        "Con_Nubes_NaN": df_15m_huecos["NDVI"].round(4),
        "Interp_Lineal": s_lineal_15.round(4),
        "Interp_PCHIP": s_pchip_15.round(4)
    })
    tabla_15_path = reports_dir / "tabla_interpolacion_15_puntos.csv"
    tabla_15.to_csv(tabla_15_path, index=False)
    print(f"\n✔ Tabla de interpolación de 15 datos guardada en: {tabla_15_path}")

    # Gráfico de la serie de 15 datos
    plt.figure(figsize=(11, 5), dpi=150)
    plt.plot(tabla_15["fecha"], tabla_15["NDVI_Real"], 'o--', color='#64748b', alpha=0.5, label='NDVI Real (Verdad Terreno)')
    plt.plot(tabla_15["fecha"], s_lineal_15, 's-', color='#0284c7', lw=1.8, label='Interpolación Lineal')
    plt.plot(tabla_15["fecha"], s_pchip_15, '^-', color='#10b981', lw=1.8, label='Interpolación PCHIP (Preserva Curvatura)')
    # Resaltar huecos
    for ih in indices_huecos:
        plt.axvspan(ih - 0.25, ih + 0.25, color='#fbbf24', alpha=0.25, label='Mes Nublado (Imputado)' if ih == indices_huecos[0] else "")
    plt.title('Interpolación en Serie Reducida de 15 Meses — Cuenca del Río Combeima', fontweight='bold', fontsize=12)
    plt.xlabel('Periodo Mensual')
    plt.ylabel('Índice NDVI')
    plt.xticks(rotation=45)
    plt.legend(loc='lower left')
    plt.tight_layout()
    plot_15_path = reports_dir / "interpolacion_15_puntos_mes_a_mes.png"
    plt.savefig(plot_15_path)
    plt.close()
    print(f"✔ Gráfico de 15 datos guardado en: {plot_15_path}")

    # -------------------------------------------------------------
    # FASE 4: MODELING (REGRESIÓN LINEAL EN 15 DATOS Y COMPLETA)
    # -------------------------------------------------------------
    print("\n[FASE 4: MODELING - REGRESIÓN LINEAL]")
    # Regresión Lineal sobre la serie de 15 meses (Tendencia mensual pura)
    df_15m["t_step"] = np.arange(len(df_15m))
    reg_15 = CrispLinearRegressor(model_type="simple", scale_features=False)
    reg_15.fit(df_15m[["t_step"]], df_15m["NDVI"])
    eval_15 = reg_15.evaluate(df_15m[["t_step"]], df_15m["NDVI"])

    print("--- Regresión Lineal Simple en Serie de 15 Meses ---")
    print(f"R²: {eval_15['r2']} | RMSE: {eval_15['rmse']} | Pendiente mensual: {eval_15['coeficientes']['t_step']}")
    print(f"Intercepto: {eval_15['intercepto']}")

    # Regresión Lineal Múltiple sobre la serie completa
    serie_interpolada["dia_juliano"] = serie_interpolada["fecha"].dt.dayofyear
    serie_interpolada["t_step"] = (serie_interpolada["fecha"] - serie_interpolada["fecha"].min()).dt.days
    serie_interpolada["sen_estacional"] = np.sin(2 * np.pi * serie_interpolada["dia_juliano"] / 365.25)
    serie_interpolada["cos_estacional"] = np.cos(2 * np.pi * serie_interpolada["dia_juliano"] / 365.25)

    features_reg = ["t_step", "EVI", "sen_estacional", "cos_estacional"]
    X = serie_interpolada[features_reg]
    y = serie_interpolada["NDVI"]
    split_point = int(len(serie_interpolada) * 0.8)
    X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
    y_train, y_test = y.iloc[:split_point], y.iloc[split_point:]

    reg_multiple = CrispLinearRegressor(model_type="multiple", scale_features=True)
    reg_multiple.fit(X_train, y_train)
    eval_multiple = reg_multiple.evaluate(X_test, y_test)

    # -------------------------------------------------------------
    # FASE 5: EVALUATION (MÉTRICAS Y DIAGNÓSTICO)
    # -------------------------------------------------------------
    print("\n[FASE 5: EVALUATION]")
    resumen_eval = {
        "Serie_15_Meses_Tendencia": eval_15,
        "Serie_Completa_Multiple": eval_multiple
    }
    metricas_path = reports_dir / "metricas_regresion.json"
    with open(metricas_path, "w", encoding="utf-8") as f:
        json.dump(resumen_eval, f, indent=2)
    print(f"✔ Métricas guardadas en: {metricas_path}")

    # -------------------------------------------------------------
    # FASE 6: DEPLOYMENT
    # -------------------------------------------------------------
    print("\n[FASE 6: DEPLOYMENT]")
    alerta_despliegue = {
        "timestamp_ejecucion": pd.Timestamp.now().isoformat(),
        "cuenca": "Río Combeima (Tolima)",
        "resolucion_reducida": "15 meses continuos (mes a mes)",
        "pendiente_mensual_ndvi": eval_15["coeficientes"]["t_step"],
        "r2_serie_15m": eval_15["r2"],
        "rmse_serie_15m": eval_15["rmse"],
        "acciones_agentes": {
            "OracleAgent": "Usar la serie de 15 meses interpolada para alimentar la ventana temporal de predicción hidrológica.",
            "ReportingAgent": "Generar ficha técnica ejecutiva de 1 página con los 15 meses para la mesa técnica de Ibagué."
        }
    }
    despliegue_path = reports_dir / "alerta_despliegue_skyfusion.json"
    with open(despliegue_path, "w", encoding="utf-8") as f:
        json.dump(alerta_despliegue, f, indent=2)
    print(f"✔ Artefacto de despliegue generado en: {despliegue_path}")

    print("\n" + "=" * 75)
    print("PIPELINE CRISP-DM CON SERIE DE 15 DATOS COMPLETADO CON ÉXITO")
    print("=" * 75)

if __name__ == "__main__":
    main()
