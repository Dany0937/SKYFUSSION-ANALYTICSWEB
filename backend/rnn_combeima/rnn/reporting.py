"""
Análisis y Reporte de Resultados de Experimentos
================================================

Consolida los resultados de múltiples corridas y genera:
- Ranking de modelos por horizonte
- Comparación con baselines (persistence, media estacional)
- Reporte final CSV/JSON
"""

import os
import json
from glob import glob
from typing import Optional

import numpy as np
import pandas as pd


def consolidar_resultados(raiz: str = "experiments") -> pd.DataFrame:
    """Recorre todas las corridas y consolida los resumen.csv + métricas."""
    dfs = []
    for f in glob(os.path.join(raiz, "**", "summary.csv"), recursive=True):
        dfs.append(pd.read_csv(f))
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def separar_por_fuente(df: pd.DataFrame) -> dict:
    """Separa resultados nuevos por fuente sin mezclar sintéticos y reales."""
    if df.empty or "fuente" not in df.columns:
        return {"sin_fuente": df}
    return {
        str(fuente): grupo.copy()
        for fuente, grupo in df.groupby("fuente", dropna=False)
    }


def ranking_por_metrica(df: pd.DataFrame, metrica: str = "rmse",
                        ascendente: bool = True) -> pd.DataFrame:
    """Ranking de experimentos según métrica."""
    if df.empty or metrica not in df.columns:
        return df
    return df.sort_values(metrica, ascending=ascendente)


def comparar_baselines(df: pd.DataFrame, col_metrica: str = "rmse") -> pd.DataFrame:
    """
    Añade baselines teóricos de referencia para el contexto NDVI:
    - Persistence (estimar t+1 con último valor): RMSE ≈ desviación diaria
    - Media estacional: RMSE ≈ amplitud estacional/2
    Se comparan contra el mejor modelo por horizonte.
    """
    if df.empty:
        return df
    filas = []
    for h, g in df.groupby("horizonte"):
        mejor = g.loc[g[col_metrica].idxmin()]
        filas.append({
            "tipo": "mejor_modelo", "horizonte": h,
            **{col_metrica: mejor[col_metrica], "id": mejor["id"]},
        })
        # Baseline persistence teórico NDVI: varianza típica ≈ 0.02
        filas.append({"tipo": "baseline_persistence", "horizonte": h,
                      col_metrica: 0.02, "id": "persistence"})
        filas.append({"tipo": "baseline_media_estacional", "horizonte": h,
                      col_metrica: 0.05, "id": "media_estacional"})
    return pd.DataFrame(filas)


def guardar_reporte(df: pd.DataFrame, ruta: str = "reports/resumen_experimentos.csv") -> None:
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    df.to_csv(ruta, index=False)
    print(f"📄 Reporte guardado en {ruta}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--raiz", default="experiments")
    parser.add_argument("--metrica", default="rmse")
    args = parser.parse_args()

    df = consolidar_resultados(args.raiz)
    if df.empty:
        print("No hay resultados aún. Ejecuta primero train.py.")
    else:
        print("=== RESULTADOS CONSOLIDADOS ===")
        print(df.to_string(index=False))
        print("\n=== RANKING POR", args.metrica.upper(), "===")
        print(ranking_por_metrica(df, args.metrica).head(10).to_string(index=False))
        guardar_reporte(df)
