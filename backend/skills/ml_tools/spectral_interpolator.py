"""
Spectral and Temporal Interpolator for Environmental Time Series
================================================================
Modulo de Preparacion de Datos (CRISP-DM Fase 3)
Aplica y evalua tecnicas de interpolacion para reconstruir series temporales
satelitales (Sentinel-2, MODIS, Landsat) y caudales con vacios por nubosidad.

Soporta agregacion y muestreo controlado a series compactas (maximo 15 datos)
mediante los modos:
- "mes_a_mes": Muestreo mensual continuo (ej. 12 a 15 meses representativos).
- "ano_a_ano": Muestreo anual historico (ej. 2015 a 2024 = 10 datos).
- "mes_interanual": Muestreo anual de un mes representativo (ej. cada mayo o agosto).

Metodos de interpolacion soportados:
- Linear: Interpolacion lineal continua
- Time: Ponderacion exacta por delta temporal (fechas irregulares)
- Spline Cúbico: Curvas suaves de tercer orden
- Polinomial: Aproximacion polinomica de grado n
- PCHIP: Piecewise Cubic Hermite Interpolating Polynomial
- Nearest: Vecino mas cercano
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from sklearn.metrics import mean_squared_error, mean_absolute_error

class SpectralTemporalInterpolator:
    """
    Interpolador de series temporales ambientales con evaluacion de calidad
    y soporte para series restringidas a un maximo de 15 observaciones.
    """
    
    METODOS_VALIDOS = ["linear", "time", "spline_cubic", "polynomial", "pchip", "nearest"]
    MODOS_MUESTREO = ["mes_a_mes", "ano_a_ano", "mes_interanual"]
    
    def __init__(self, date_col: str = "fecha"):
        self.date_col = date_col

    def resample_to_max_points(
        self,
        df: pd.DataFrame,
        max_points: int = 15,
        mode: str = "mes_a_mes",
        numeric_cols: Optional[List[str]] = None,
        target_month: int = 5
    ) -> pd.DataFrame:
        """
        Agrega y muestrea el DataFrame temporal a una serie reducida de hasta max_points.
        
        Args:
            df: DataFrame con columna de fecha
            max_points: Maximo de datos resultantes (default: 15)
            mode: "mes_a_mes", "ano_a_ano", o "mes_interanual"
            numeric_cols: Columnas a promediar (default: todas las numericas)
            target_month: Mes objetivo si mode='mes_interanual' (1..12, default: 5=Mayo)
            
        Returns:
            DataFrame agregado con <= max_points filas
        """
        if mode not in self.MODOS_MUESTREO:
            raise ValueError(f"Modo no valido. Opciones: {self.MODOS_MUESTREO}")
            
        df_copy = df.copy()
        df_copy[self.date_col] = pd.to_datetime(df_copy[self.date_col])
        df_copy = df_copy.sort_values(self.date_col)
        
        if numeric_cols is None:
            numeric_cols = df_copy.select_dtypes(include=[np.number]).columns.tolist()
            
        if mode == "mes_a_mes":
            # Agrupacion mensual
            df_copy["periodo_mes"] = df_copy[self.date_col].dt.to_period("M")
            grouped = df_copy.groupby("periodo_mes")[numeric_cols].mean().reset_index()
            grouped[self.date_col] = grouped["periodo_mes"].dt.to_timestamp()
            # Tomar los ultimos max_points
            res = grouped.tail(max_points).drop(columns=["periodo_mes"]).reset_index(drop=True)
            
        elif mode == "ano_a_ano":
            # Agrupacion anual
            df_copy["periodo_ano"] = df_copy[self.date_col].dt.year
            grouped = df_copy.groupby("periodo_ano")[numeric_cols].mean().reset_index()
            grouped[self.date_col] = pd.to_datetime(grouped["periodo_ano"].astype(str) + "-06-15")
            res = grouped.tail(max_points).drop(columns=["periodo_ano"]).reset_index(drop=True)
            
        elif mode == "mes_interanual":
            # Filtrar solo el mes indicado año a año
            df_mes = df_copy[df_copy[self.date_col].dt.month == target_month].copy()
            df_mes["periodo_ano"] = df_mes[self.date_col].dt.year
            grouped = df_mes.groupby("periodo_ano")[numeric_cols].mean().reset_index()
            grouped[self.date_col] = pd.to_datetime(grouped["periodo_ano"].astype(str) + f"-{target_month:02d}-15")
            res = grouped.tail(max_points).drop(columns=["periodo_ano"]).reset_index(drop=True)
            
        # Reordenar columnas para que date_col vaya de primero
        cols_final = [self.date_col] + [c for c in res.columns if c != self.date_col]
        return res[cols_final]

    def interpolate_series(
        self,
        series: pd.Series,
        method: str = "time",
        order: int = 3,
        dates: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        Interpola una serie univariada con el metodo indicado.
        """
        if method not in self.METODOS_VALIDOS:
            raise ValueError(f"Metodo no valido. Opciones: {self.METODOS_VALIDOS}")
        
        s = series.copy()
        
        if method == "linear":
            res = s.interpolate(method="linear")
        elif method == "time":
            if dates is not None:
                tmp = pd.DataFrame({"val": s.values, "date": pd.to_datetime(dates.values)})
                tmp = tmp.set_index("date")
                res = tmp["val"].interpolate(method="time").reset_index(drop=True)
                res.index = s.index
            else:
                res = s.interpolate(method="linear")
        elif method == "spline_cubic":
            res = s.interpolate(method="spline", order=order)
        elif method == "polynomial":
            res = s.interpolate(method="polynomial", order=min(order, 2))
        elif method == "nearest":
            res = s.interpolate(method="nearest")
        elif method == "pchip":
            valid_idx = s.dropna().index.values
            valid_vals = s.dropna().values
            if len(valid_idx) >= 3:
                interp = PchipInterpolator(valid_idx, valid_vals, extrapolate=True)
                all_idx = s.index.values
                res = pd.Series(interp(all_idx), index=s.index)
            else:
                res = s.interpolate(method="linear")
                
        # Manejo de extremos
        res = res.bfill().ffill()
        return res

    def interpolate_dataframe(
        self,
        df: pd.DataFrame,
        value_cols: List[str],
        method: str = "time"
    ) -> pd.DataFrame:
        """
        Aplica interpolacion a multiples columnas de un DataFrame.
        """
        out_df = df.copy()
        dates = pd.to_datetime(out_df[self.date_col]) if self.date_col in out_df.columns else None
        
        for col in value_cols:
            if col in out_df.columns:
                out_df[col] = self.interpolate_series(out_df[col], method=method, dates=dates)
        return out_df

    def evaluate_methods(
        self,
        clean_series: pd.Series,
        gap_percentage: float = 0.20,
        gap_block_size: int = 2,
        random_state: int = 42
    ) -> pd.DataFrame:
        """
        Evalua objetivamente los metodos de interpolacion introduciendo huecos artificiales.
        Ajustado para soportar tanto series largas como series cortas (10 a 15 datos).
        """
        np.random.seed(random_state)
        s_true = clean_series.dropna().copy()
        n = len(s_true)
        if n < 5:
            raise ValueError("La serie debe tener al menos 5 observaciones.")

        # Ajuste adaptativo de parametros para series pequenas
        block_size = 1 if n <= 15 else gap_block_size
        n_gaps = max(1, int(round((n * gap_percentage) / block_size)))
        
        masked_indices = []
        for _ in range(n_gaps):
            max_start = max(1, n - block_size - 1)
            start = np.random.randint(1, max_start + 1)
            for j in range(block_size):
                if (start + j) < n - 1:
                    masked_indices.append(start + j)
                    
        masked_indices = sorted(list(set(masked_indices)))
        if not masked_indices:
            masked_indices = [n // 2]
            
        s_masked = s_true.copy()
        s_masked.iloc[masked_indices] = np.nan
        
        metrics = []
        for met in ["linear", "time", "pchip", "nearest"]:
            s_rec = self.interpolate_series(s_masked, method=met)
            y_t = s_true.iloc[masked_indices].values
            y_p = s_rec.iloc[masked_indices].values
            
            rmse = np.sqrt(mean_squared_error(y_t, y_p))
            mae = mean_absolute_error(y_t, y_p)
            corr = np.corrcoef(y_t, y_p)[0, 1] if len(y_t) > 1 and np.std(y_p) > 0 and np.std(y_t) > 0 else 1.0
            var_ratio = np.var(y_p) / (np.var(y_t) + 1e-9)
            
            metrics.append({
                "metodo": met,
                "rmse": round(float(rmse), 4),
                "mae": round(float(mae), 4),
                "correlacion": round(float(corr), 4),
                "ratio_varianza": round(float(var_ratio), 4)
            })
            
        return pd.DataFrame(metrics).sort_values("rmse")
