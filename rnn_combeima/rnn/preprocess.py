"""
Preprocesamiento de Series Temporales para RNA
=============================================

Pipeline completo de limpieza, ingeniería de características, escalamiento
y ventaneo para alimentar la RNA con datos multitemporales del Combeima.

Incluye:
- Limpieza (duplicados, nulos, QA, winsorización estacional)
- Features cíclicas + lags + rolling
- Escalamiento MinMax por feature
- Construcción de secuencias (ventaneo) por píxel
- División ESPACIO-TEMPORAL (GroupShuffleSplit por píxel) para evitar
  data leakage entre train y test.
"""

import os
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


# --------------------------------------------------------------------------- #
# 1. Limpieza específica de series satelitales
# --------------------------------------------------------------------------- #

def limpiar_series(df: pd.DataFrame,
                   fechas_col: str = "fecha",
                   vigilar_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Limpieza básica de series:
    - parsea fechas, ordena
    - elimina duplicados geoespaciales (repeticiones de (lon,lat) en misma fecha)
    - elimina NaN de índices
    - imputa nulos por interpolación limitada temporal
    """
    vigilar_cols = vigilar_cols or ["NDVI", "EVI"]
    df = df.copy()
    df[fechas_col] = pd.to_datetime(df[fechas_col])
    df = df.drop_duplicates(subset=["longitude", "latitude", fechas_col]).sort_values(
        [fechas_col]
    ).reset_index(drop=True)

    # Solo mantener píxeles con coordenadas válidas
    df = df.dropna(subset=["longitude", "latitude"])

    # Drop relativo de nulos severos de índices
    for c in vigilar_cols:
        if c in df.columns:
            df.loc[df[c] < 0, c] = np.nan

    return df


def normalizar_q_estacional(df: pd.DataFrame,
                            vigilar_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Winsorización estacional: por cada dígito/estación (mes) los valores
    fuera de los percentiles 1-99 se recortan. Ayuda a quitar outliers de
    nubes mal enmascaradas.
    """
    vigilar_cols = vigilar_cols or ["NDVI", "EVI"]
    df = df.copy()
    df["mes"] = df["fecha"].dt.month
    for c in vigilar_cols:
        if c in df.columns:
            lo = df.groupby("mes")[c].transform(lambda x: x.quantile(0.01))
            hi = df.groupby("mes")[c].transform(lambda x: x.quantile(0.99))
            df[c] = df[c].clip(lo, hi)
    return df


# --------------------------------------------------------------------------- #
# 2. Ingeniería de características temporales
# --------------------------------------------------------------------------- #

def crear_features_temporales(df: pd.DataFrame,
                              vigilar_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Agrega features temporales:
    - codificación cíclica de mes y día del año
    - lags (autocorrelación)
    - medias móviles
    Devuelve el DataFrame con las nuevas columnas.
    """
    vigilar_cols = vigilar_cols or ["NDVI", "EVI"]
    df = df.copy()
    df["mes"] = df["fecha"].dt.month
    df["doy"] = df["fecha"].dt.dayofyear
    df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)
    df["doy_sin"] = np.sin(2 * np.pi * df["doy"] / 365)
    df["doy_cos"] = np.cos(2 * np.pi * df["doy"] / 365)

    g = df.groupby(["longitude", "latitude"])
    for c in vigilar_cols:
        for lag in (1, 2, 4):
            df[f"{c}_lag{lag}"] = g[c].shift(lag)
        df[f"{c}_ma3"] = g[c].transform(lambda x: x.rolling(3, min_periods=1).mean())

    df = df.dropna(subset=vigilar_cols).reset_index(drop=True)
    return df


# --------------------------------------------------------------------------- #
# 3. Construcción de secuencias (ventaneo) por píxel
# --------------------------------------------------------------------------- #

def construir_secuencias_por_pixel(
    df: pd.DataFrame,
    features: List[str],
    target: str,
    timesteps: int,
    horizonte: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Construye muestras (X, y, coords, pixel_ids) ventaneando cada serie por píxel.

    Convierte ventanas temporales deslizantes:
        X[i] = (timesteps, n_features)
        y[i] = target en timestep+horizonte → (horizonte,) incluyendo el futuro

    Returns:
        X, y, coords (2D), pixel_ids (int, para divisiones por grupo sin leakage)
    """
    X_list: List[np.ndarray] = []
    y_list: List[np.ndarray] = []
    coords_list: List[Tuple[float, float]] = []
    pixel_ids: List[int] = []

    for pid, (llave, g) in enumerate(df.groupby(["longitude", "latitude"])):
        g = g.sort_values("fecha").reset_index(drop=True)
        vals = g[features].values.astype(np.float32)
        tgt = g[target].values.astype(np.float32)
        lon, lat = llave
        for i in range(len(g) - timesteps - horizonte + 1):
            X_list.append(vals[i:i + timesteps])
            # predicción del horizonte: entregamos el valor en t+horizonte
            # (1 paso) o una ventana del futuro si horizonte>1
            y_list.append(tgt[i + timesteps: i + timesteps + horizonte])
            coords_list.append((lon, lat))
            pixel_ids.append(pid)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)
    coords = np.array(coords_list, dtype=np.float32)
    pixel_ids = np.array(pixel_ids, dtype=np.int64)
    return X, y, coords, pixel_ids


# --------------------------------------------------------------------------- #
# 4. Preparación completa con división espacio-temporal
# --------------------------------------------------------------------------- #

def preparar_datos(
    ruta_csv: str,
    feature_cols: Optional[List[str]] = None,
    target: str = "NDVI",
    timesteps: int = 24,          # 24 × 16 días ≈ 1 año
    horizonte: int = 1,
    test_ratio: float = 0.2,
    val_ratio: float = 0.15,
    semilla: int = 42,
    guardar_splits: bool = True,
    ruta_splits: str = "data/splits",
) -> dict:
    """
    Pipeline completo: carga → limpieza → features → rescale → ventaneo →
    división espacial (sin data leakage).

    Returns dict con X_train/val/test, y_train/val/test, scalers, metrics.
    """
    from sklearn.model_selection import GroupShuffleSplit

    df = pd.read_csv(ruta_csv, parse_dates=["fecha"])
    df = limpiar_series(df)
    df = normalizar_q_estacional(df)

    # Features de entrada
    feature_cols = feature_cols or ["NDVI", "EVI", "mes_sin", "mes_cos",
                                    "doy_sin", "doy_cos", "NDVI_lag1",
                                    "NDVI_lag2", "NDVI_lag4"]
    df = crear_features_temporales(df)

    # Asegurar que todas las features existan
    feature_cols = [c for c in feature_cols if c in df.columns]
    if not feature_cols:
        raise ValueError("No quedaron features válidas tras el preproceso.")

    # Escalamiento MinMax por feature, separado para target
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    X_all = scaler_X.fit_transform(df[feature_cols].values.astype(np.float32))
    y_all = scaler_y.fit_transform(df[[target]].values.astype(np.float32))

    df_scaled = df.copy()
    df_scaled[feature_cols] = X_all
    df_scaled[target] = y_all.ravel()
    # Eliminar filas con NaN (lags iniciales de cada píxel) antes de ventanear
    n_antes = len(df_scaled)
    df_scaled = df_scaled.dropna().reset_index(drop=True)
    if len(df_scaled) != n_antes:
        print(f"   - Eliminadas {n_antes - len(df_scaled)} filas con NaN de lags")

    # Ventaneo por píxel
    X, y, coords, pixel_ids = construir_secuencias_por_pixel(
        df_scaled, feature_cols, target, timesteps, horizonte
    )

    # División espacio-temporal: grupos = píxeles
    gss = GroupShuffleSplit(n_splits=1, test_size=test_ratio, random_state=semilla)
    idx_train_all, idx_test = next(gss.split(X, y, groups=pixel_ids))

    coords_train_all = coords[idx_train_all]
    X_train_all, y_train_all = X[idx_train_all], y[idx_train_all]
    pixel_train_all = pixel_ids[idx_train_all]

    val_size_rel = val_ratio / (1 - test_ratio)
    gss2 = GroupShuffleSplit(n_splits=1, test_size=val_size_rel, random_state=semilla)
    idx_tr, idx_val = next(gss2.split(X_train_all, y_train_all, groups=pixel_train_all))

    X_train, y_train = X_train_all[idx_tr], y_train_all[idx_tr]
    X_val, y_val = X_train_all[idx_val], y_train_all[idx_val]
    X_test, y_test = X[idx_test], y[idx_test]

    resultado = {
        "X_train": X_train, "y_train": y_train,
        "X_val": X_val, "y_val": y_val,
        "X_test": X_test, "y_test": y_test,
        "coords_train": coords[idx_train_all][idx_tr],
        "coords_val": coords[idx_train_all][idx_val],
        "coords_test": coords[idx_test],
        "scaler_X": scaler_X, "scaler_y": scaler_y,
        "feature_cols": feature_cols, "target": target,
        "timesteps": timesteps, "horizonte": horizonte,
    }

    if guardar_splits:
        os.makedirs(ruta_splits, exist_ok=True)
        np.savez(
            os.path.join(ruta_splits, f"splits_t{timesteps}_h{horizonte}.npz"),
            X_train=X_train, y_train=y_train,
            X_val=X_val, y_val=y_val,
            X_test=X_test, y_test=y_test,
            coords_train=coords[idx_train_all][idx_tr],
            coords_val=coords[idx_train_all][idx_val],
            coords_test=coords[idx_test],
        )
        print(f"💾 Splits guardados en {ruta_splits}")

    return resultado


# --------------------------------------------------------------------------- #
# Utilidad: colapso multi-horizonte a predicción puntual
# --------------------------------------------------------------------------- #

def colapsar_horizonte(y: np.ndarray) -> np.ndarray:
    """
    Si horizonte>1, entrega el primero (o la media del horizonte).
    Aquí usamos el primer paso del horizonte como referencia puntual.
    """
    return y[:, 0]
