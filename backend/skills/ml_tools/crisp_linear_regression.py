"""
CRISP-DM Linear Regression Module for Skyfusion Analytics
=========================================================
Modulos de Modelado y Evaluacion (CRISP-DM Fases 4 y 5)
Implementa regresion lineal simple, multiple y regularizada (Ridge / Lasso)
con pipeline de escalado sin data leakage y bateria completa de diagnosticos
estadisticos de residuos.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt

class CrispLinearRegressor:
    """
    Regresor lineal estructurado bajo el marco CRISP-DM.
    """
    
    def __init__(
        self,
        model_type: str = "multiple",
        alpha: float = 1.0,
        scale_features: bool = True,
        random_state: int = 42
    ):
        self.model_type = model_type
        self.alpha = alpha
        self.scale_features = scale_features
        self.random_state = random_state
        
        # Seleccion de estimador
        if model_type in ["simple", "multiple"]:
            self.base_estimator = LinearRegression()
        elif model_type == "ridge":
            self.base_estimator = Ridge(alpha=alpha, random_state=random_state)
        elif model_type == "lasso":
            self.base_estimator = Lasso(alpha=alpha, random_state=random_state)
        else:
            raise ValueError(f"Tipo de modelo no valido: {model_type}")
            
        if scale_features:
            self.pipeline = Pipeline([
                ("scaler", StandardScaler()),
                ("regressor", self.base_estimator)
            ])
        else:
            self.pipeline = Pipeline([
                ("regressor", self.base_estimator)
            ])
            
        self.fitted = False
        self.feature_names_: List[str] = []
        self.coefficients_: Dict[str, float] = {}
        self.intercept_: float = 0.0

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """
        Ajusta el modelo sobre el conjunto de entrenamiento.
        """
        self.feature_names_ = list(X.columns)
        self.pipeline.fit(X, y)
        
        reg = self.pipeline.named_steps["regressor"]
        self.intercept_ = float(reg.intercept_)
        coefs = reg.coef_
        if np.ndim(coefs) > 1:
            coefs = coefs.flatten()
        self.coefficients_ = {col: round(float(c), 5) for col, c in zip(self.feature_names_, coefs)}
        self.fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.fitted:
            raise RuntimeError("El modelo no ha sido entrenado. Llame a fit() primero.")
        return self.pipeline.predict(X)

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Fase 5 CRISP-DM: Evaluacion cuantitativa del modelo.
        """
        y_true = np.asarray(y)
        y_pred = self.predict(X)
        n = len(y_true)
        p = len(self.feature_names_)
        
        residuals = y_true - y_pred
        r2 = float(r2_score(y_true, y_pred))
        adj_r2 = float(1 - (1 - r2) * (n - 1) / max(n - p - 1, 1))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        mae = float(mean_absolute_error(y_true, y_pred))
        mape = float(np.mean(np.abs(residuals / np.maximum(np.abs(y_true), 1e-6))) * 100)
        
        # Diagnostico de residuos
        mean_res = float(np.mean(residuals))
        std_res = float(np.std(residuals))
        
        # Test Shapiro-Wilk de normalidad (en muestra de hasta 5000)
        sample_res = residuals if n <= 2000 else np.random.choice(residuals, 2000, replace=False)
        shapiro_stat, shapiro_p = stats.shapiro(sample_res)
        
        # Test Durbin-Watson para autocorrelacion
        diff = np.diff(residuals)
        dw = float(np.sum(diff ** 2) / np.maximum(np.sum(residuals ** 2), 1e-9))
        
        # Criterios de Informacion AIC / BIC
        sse = np.sum(residuals ** 2)
        aic = float(n * np.log(max(sse / n, 1e-9)) + 2 * p)
        bic = float(n * np.log(max(sse / n, 1e-9)) + p * np.log(n))
        
        metrics = {
            "n_muestras": n,
            "n_features": p,
            "r2": round(r2, 4),
            "r2_ajustado": round(adj_r2, 4),
            "rmse": round(rmse, 4),
            "mae": round(mae, 4),
            "mape_pct": round(mape, 2),
            "aic": round(aic, 2),
            "bic": round(bic, 2),
            "diagnostico_residuos": {
                "media_residuos": round(mean_res, 5),
                "desv_est_residuos": round(std_res, 4),
                "shapiro_pvalue": round(float(shapiro_p), 5),
                "residuos_normales": bool(shapiro_p > 0.05),
                "durbin_watson": round(dw, 3),
                "autocorrelacion_detectada": bool(dw < 1.5 or dw > 2.5)
            },
            "coeficientes": self.coefficients_,
            "intercepto": round(self.intercept_, 5)
        }
        return metrics

    def plot_diagnostics(self, X: pd.DataFrame, y: pd.Series, output_path: str):
        """
        Genera graficos de diagnostico de residuos de 4 paneles.
        """
        y_true = np.asarray(y)
        y_pred = self.predict(X)
        residuals = y_true - y_pred
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 9), dpi=150)
        
        # 1. Real vs Predicho
        axes[0, 0].scatter(y_true, y_pred, alpha=0.5, color="#0284c7", edgecolor="none")
        min_v = min(np.min(y_true), np.min(y_pred))
        max_v = max(np.max(y_true), np.max(y_pred))
        axes[0, 0].plot([min_v, max_v], [min_v, max_v], 'r--', lw=1.5, label="Identidad (1:1)")
        axes[0, 0].set_title("Valores Reales vs Predichos", fontweight="bold")
        axes[0, 0].set_xlabel("Valor Real")
        axes[0, 0].set_ylabel("Valor Predicho")
        axes[0, 0].legend()
        
        # 2. Residuos vs Predicho (Homocedasticidad)
        axes[0, 1].scatter(y_pred, residuals, alpha=0.5, color="#10b981", edgecolor="none")
        axes[0, 1].axhline(0, color="crimson", linestyle="--", lw=1.5)
        axes[0, 1].set_title("Residuos vs Valores Predichos", fontweight="bold")
        axes[0, 1].set_xlabel("Valor Predicho")
        axes[0, 1].set_ylabel("Residuo")
        
        # 3. Histograma de Residuos + KDE
        axes[1, 0].hist(residuals, bins=30, density=True, alpha=0.6, color="#6366f1", edgecolor="white")
        kde_x = np.linspace(np.min(residuals), np.max(residuals), 100)
        kde_y = stats.norm.pdf(kde_x, np.mean(residuals), np.std(residuals))
        axes[1, 0].plot(kde_x, kde_y, color="#312e81", lw=2, label="Normal Teórica")
        axes[1, 0].set_title("Distribución de Residuos", fontweight="bold")
        axes[1, 0].set_xlabel("Residuo")
        axes[1, 0].legend()
        
        # 4. Q-Q Plot
        stats.probplot(residuals, dist="norm", plot=axes[1, 1])
        axes[1, 1].set_title("Normal Q-Q Plot", fontweight="bold")
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
