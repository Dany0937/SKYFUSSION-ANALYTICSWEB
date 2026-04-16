"""
Validation Module for Caudal Prediction Model
==============================================

Métricas de evaluación para modelos de regresión de series temporales:
- RMSE (Root Mean Squared Error)
- MAE (Mean Absolute Error)
- R² (Coefficient of Determination)
- MAPE (Mean Absolute Percentage Error)
- Diagnóstico de residuos
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json


@dataclass
class ValidationMetrics:
    """Contenedor para métricas de validación."""
    rmse: float
    mae: float
    r2_score: float
    mape: float
    rmse_std: float
    predictions: np.ndarray
    actuals: np.ndarray
    residuals: np.ndarray
    confidence_intervals: Optional[np.ndarray] = None
    coverage_percentage: Optional[float] = None


@dataclass
class ResidualDiagnostics:
    """Diagnóstico de residuos del modelo."""
    mean_residual: float
    std_residual: float
    skewness: float
    kurtosis: float
    shapiro_stat: float
    shapiro_pvalue: float
    durbin_watson: float
    is_normal: bool
    is_autocorrelated: bool


class ModelValidator:
    """
    Validador de modelos de predicción de caudal.
    
    Proporciona métricas estándar de regresión y diagnóstico
    estadístico de los residuos.
    """

    def __init__(self, alpha: float = 0.05) -> None:
        """
        Inicializa el validador.
        
        Args:
            alpha: Nivel de significancia para pruebas estadísticas
        """
        self.alpha = alpha
        self.metrics: Optional[ValidationMetrics] = None
        self.diagnostics: Optional[ResidualDiagnostics] = None

    @staticmethod
    def calculate_rmse(
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Tuple[float, float]:
        """
        Calcula RMSE y su desviación estándar.
        
        RMSE = sqrt(mean((y_true - y_pred)²))
        
        Args:
            y_true: Valores reales
            y_pred: Valores predichos
            
        Returns:
            Tupla (rmse, rmse_std)
        """
        squared_errors = (y_true - y_pred) ** 2
        mse = np.mean(squared_errors)
        rmse = np.sqrt(mse)
        rmse_std = np.std(squared_errors) / (2 * rmse) if rmse > 0 else 0.0
        
        return float(rmse), float(rmse_std)

    @staticmethod
    def calculate_mae(
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> float:
        """
        Calcula MAE (Mean Absolute Error).
        
        MAE = mean(|y_true - y_pred|)
        
        Args:
            y_true: Valores reales
            y_pred: Valores predichos
            
        Returns:
            MAE
        """
        mae = np.mean(np.abs(y_true - y_pred))
        return float(mae)

    @staticmethod
    def calculate_r2(
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> float:
        """
        Calcula R² (Coefficient of Determination).
        
        R² = 1 - SS_res / SS_tot
        
        Args:
            y_true: Valores reales
            y_pred: Valores predichos
            
        Returns:
            R² score
        """
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        
        if ss_tot == 0:
            return 0.0
            
        r2 = 1 - (ss_res / ss_tot)
        return float(r2)

    @staticmethod
    def calculate_mape(
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> float:
        """
        Calcula MAPE (Mean Absolute Percentage Error).
        
        MAPE = mean(|y_true - y_pred| / |y_true|) * 100
        
        Args:
            y_true: Valores reales
            y_pred: Valores predichos
            
        Returns:
            MAPE en porcentaje
        """
        mask = np.abs(y_true) > 1e-8
        if not np.any(mask):
            return float('inf')
            
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        return float(mape)

    @staticmethod
    def calculate_residuals(
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> np.ndarray:
        """
        Calcula residuos.
        
        Args:
            y_true: Valores reales
            y_pred: Valores predichos
            
        Returns:
            Array de residuos
        """
        return y_true - y_pred

    @staticmethod
    def calculate_skewness(residuals: np.ndarray) -> float:
        """
        Calcula asimetría de residuos.
        
        Args:
            residuals: Array de residuos
            
        Returns:
            Coeficiente de asimetría
        """
        n = len(residuals)
        if n < 3:
            return 0.0
            
        mean_res = np.mean(residuals)
        std_res = np.std(residuals)
        
        if std_res == 0:
            return 0.0
            
        skewness = (n / ((n - 1) * (n - 2))) * np.sum(
            ((residuals - mean_res) / std_res) ** 3
        )
        
        return float(skewness)

    @staticmethod
    def calculate_kurtosis(residuals: np.ndarray) -> float:
        """
        Calcula curtosis de residuos.
        
        Args:
            residuals: Array de residuos
            
        Returns:
            Coeficiente de curtosis
        """
        n = len(residuals)
        if n < 4:
            return 0.0
            
        mean_res = np.mean(residuals)
        std_res = np.std(residuals)
        
        if std_res == 0:
            return 0.0
            
        kurtosis = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * np.sum(
            ((residuals - mean_res) / std_res) ** 4
        ) - (3 * (n - 1) ** 2) / ((n - 2) * (n - 3))
        
        return float(kurtosis)

    @staticmethod
    def shapiro_wilk_test(residuals: np.ndarray) -> Tuple[float, float]:
        """
        Test de Shapiro-Wilk para normalidad.
        
        Args:
            residuals: Array de residuos
            
        Returns:
            Tupla (estadístico, p-value)
        """
        n = len(residuals)
        
        if n < 3:
            return 0.0, 1.0
        if n > 5000:
            residuals = residuals[:5000]
            n = 5000
            
        sorted_res = np.sort(residuals)
        mean_res = np.mean(residuals)
        std_res = np.std(residuals)
        
        if std_res == 0:
            return 0.0, 0.0
        
        m = np.zeros(n)
        for i in range(1, (n // 2) + 1):
            m[i - 1] = (i - 0.375) / (n + 0.25)
            if n % 2 == 0 or i < n // 2:
                m[n - i] = -m[i - 1]
        
        std_normal = np.sqrt(n * np.sum(m ** 2))
        stat = np.sum(m * sorted_res) / std_res
        
        if stat < 0:
            stat = -stat
            
        p_value = max(0.001, min(1.0, 1 - stat))
        
        return float(stat), float(p_value)

    @staticmethod
    def durbin_watson(residuals: np.ndarray) -> float:
        """
        Calcula estadístico de Durbin-Watson.
        
        Detecta autocorrelación en residuos.
        Valores cercanos a 2 indican no autocorrelación.
        
        Args:
            residuals: Array de residuos
            
        Returns:
            Estadístico de Durbin-Watson
        """
        diff = np.diff(residuals)
        numerator = np.sum(diff ** 2)
        denominator = np.sum(residuals ** 2)
        
        if denominator == 0:
            return 2.0
            
        dw = numerator / denominator
        return float(dw)

    def validate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        confidence_intervals: Optional[np.ndarray] = None
    ) -> ValidationMetrics:
        """
        Ejecuta validación completa del modelo.
        
        Args:
            y_true: Valores reales
            y_pred: Valores predichos
            confidence_intervals: Intervalos de confianza [lower, upper]
            
        Returns:
            Objeto ValidationMetrics
        """
        y_true = np.array(y_true).flatten()
        y_pred = np.array(y_pred).flatten()
        
        if len(y_true) != len(y_pred):
            raise ValueError(
                f"Longitudes incompatibles: {len(y_true)} vs {len(y_pred)}"
            )
            
        rmse, rmse_std = self.calculate_rmse(y_true, y_pred)
        mae = self.calculate_mae(y_true, y_pred)
        r2 = self.calculate_r2(y_true, y_pred)
        mape = self.calculate_mape(y_true, y_pred)
        residuals = self.calculate_residuals(y_true, y_pred)
        
        coverage = None
        if confidence_intervals is not None:
            lower, upper = confidence_intervals[:, 0], confidence_intervals[:, 1]
            within_bounds = (y_true >= lower) & (y_true <= upper)
            coverage = float(np.mean(within_bounds) * 100)
        
        self.metrics = ValidationMetrics(
            rmse=rmse,
            mae=mae,
            r2_score=r2,
            mape=mape,
            rmse_std=rmse_std,
            predictions=y_pred,
            actuals=y_true,
            residuals=residuals,
            confidence_intervals=confidence_intervals,
            coverage_percentage=coverage
        )
        
        self.diagnostics = self._compute_diagnostics(residuals)
        
        return self.metrics

    def _compute_diagnostics(self, residuals: np.ndarray) -> ResidualDiagnostics:
        """
        Calcula diagnóstico completo de residuos.
        
        Args:
            residuals: Array de residuos
            
        Returns:
            Objeto ResidualDiagnostics
        """
        mean_res = np.mean(residuals)
        std_res = np.std(residuals)
        
        skewness = self.calculate_skewness(residuals)
        kurtosis = self.calculate_kurtosis(residuals)
        
        shapiro_stat, shapiro_pvalue = self.shapiro_wilk_test(residuals)
        
        dw = self.durbin_watson(residuals)
        
        is_normal = shapiro_pvalue > self.alpha
        is_autocorrelated = dw < 1.5 or dw > 2.5
        
        return ResidualDiagnostics(
            mean_residual=float(mean_res),
            std_residual=float(std_res),
            skewness=skewness,
            kurtosis=kurtosis,
            shapiro_stat=shapiro_stat,
            shapiro_pvalue=shapiro_pvalue,
            durbin_watson=dw,
            is_normal=is_normal,
            is_autocorrelated=is_autocorrelated
        )

    def get_metrics_dict(self) -> Dict[str, Any]:
        """
        Retorna métricas como diccionario.
        
        Returns:
            Diccionario con todas las métricas
        """
        if self.metrics is None:
            raise RuntimeError("Ejecute validate() primero")
            
        return {
            "rmse": round(self.metrics.rmse, 4),
            "rmse_std": round(self.metrics.rmse_std, 4),
            "mae": round(self.metrics.mae, 4),
            "r2_score": round(self.metrics.r2_score, 4),
            "mape": round(self.metrics.mape, 4),
            "coverage_95ci": round(self.metrics.coverage_percentage, 2) 
                if self.metrics.coverage_percentage else None
        }

    def get_diagnostics_dict(self) -> Dict[str, Any]:
        """
        Retorna diagnóstico de residuos como diccionario.
        
        Returns:
            Diccionario con diagnóstico
        """
        if self.diagnostics is None:
            raise RuntimeError("Ejecute validate() primero")
            
        return {
            "mean_residual": round(self.diagnostics.mean_residual, 6),
            "std_residual": round(self.diagnostics.std_residual, 4),
            "skewness": round(self.diagnostics.skewness, 4),
            "kurtosis": round(self.diagnostics.kurtosis, 4),
            "shapiro_stat": round(self.diagnostics.shapiro_stat, 4),
            "shapiro_pvalue": round(self.diagnostics.shapiro_pvalue, 4),
            "durbin_watson": round(self.diagnostics.durbin_watson, 4),
            "is_normal": self.diagnostics.is_normal,
            "is_autocorrelated": self.diagnostics.is_autocorrelated,
            "interpretation": self._interpret_diagnostics()
        }

    def _interpret_diagnostics(self) -> str:
        """Genera interpretación de los diagnósticos."""
        interpretations: List[str] = []
        
        if self.metrics:
            if self.metrics.r2_score >= 0.9:
                interpretations.append("Excelente ajuste del modelo (R² ≥ 0.9)")
            elif self.metrics.r2_score >= 0.7:
                interpretations.append("Buen ajuste del modelo (R² ≥ 0.7)")
            elif self.metrics.r2_score >= 0.5:
                interpretations.append("Ajuste moderado del modelo (R² ≥ 0.5)")
            else:
                interpretations.append("Ajuste débil del modelo (R² < 0.5)")
                
        if self.diagnostics:
            if self.diagnostics.is_normal:
                interpretations.append("Los residuos siguen una distribución normal")
            else:
                interpretations.append("⚠️ Los residuos NO siguen distribución normal")
                
            if self.diagnostics.is_autocorrelated:
                interpretations.append("⚠️ Se detecta autocorrelación en residuos")
            else:
                interpretations.append("✓ No hay autocorrelación significativa")
                
            if abs(self.diagnostics.skewness) > 1:
                interpretations.append("⚠️ Alta asimetría en residuos")
                
        return ". ".join(interpretations)

    def generate_report(self) -> Dict[str, Any]:
        """
        Genera reporte completo de validación.
        
        Returns:
            Diccionario con reporte completo
        """
        if self.metrics is None:
            raise RuntimeError("Ejecute validate() primero")
            
        return {
            "summary": self.get_metrics_dict(),
            "residuals_diagnostics": self.get_diagnostics_dict(),
            "interpretation": self._interpret_diagnostics()
        }

    def save_report(self, path: str) -> None:
        """
        Guarda el reporte de validación a archivo JSON.
        
        Args:
            path: Ruta del archivo
        """
        report = self.generate_report()
        
        with open(path, "w") as f:
            json.dump(report, f, indent=2, default=str)
            
        print(f"✅ Reporte guardado en {path}")


def cross_validate(
    model,
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    metric: str = "rmse"
) -> Dict[str, List[float]]:
    """
    Validación cruzada k-fold para series temporales.
    
    Args:
        model: Instancia del modelo a validar
        X: Datos de entrada
        y: Targets
        n_splits: Número de folds
        metric: Métrica a evaluar ('rmse', 'mae', 'r2')
        
    Returns:
        Diccionario con scores por fold
    """
    validator = ModelValidator()
    
    fold_size = len(X) // n_splits
    
    scores: Dict[str, List[float]] = {
        "rmse": [],
        "mae": [],
        "r2": []
    }
    
    for i in range(n_splits):
        test_start = i * fold_size
        test_end = test_start + fold_size if i < n_splits - 1 else len(X)
        
        X_test = X[test_start:test_end]
        y_test = y[test_start:test_end]
        
        X_train = np.concatenate([X[:test_start], X[test_end:]], axis=0)
        y_train = np.concatenate([y[:test_start], y[test_end:]], axis=0)
        
        model_copy = model.__class__(model.config)
        model_copy.build_model()
        model_copy.train(X_train, y_train, epochs=10, verbose=0)
        
        y_pred = model_copy.predict(X_test)["flow_prediction"]
        
        if len(y_pred.shape) > 1:
            y_pred = y_pred[:, 0]
        if len(y_test.shape) > 1:
            y_test = y_test[:, 0]
            
        metrics = validator.validate(y_test, y_pred)
        
        scores["rmse"].append(metrics.rmse)
        scores["mae"].append(metrics.mae)
        scores["r2"].append(metrics.r2_score)
        
        print(f"Fold {i+1}/{n_splits} - RMSE: {metrics.rme:.4f}, R²: {metrics.r2_score:.4f}")
    
    summary = {
        "rmse_mean": float(np.mean(scores["rmse"])),
        "rmse_std": float(np.std(scores["rmse"])),
        "mae_mean": float(np.mean(scores["mae"])),
        "r2_mean": float(np.mean(scores["r2"]))
    }
    
    print(f"\n📊 Resumen de validación cruzada:")
    print(f"   RMSE: {summary['rmse_mean']:.4f} ± {summary['rmse_std']:.4f}")
    print(f"   MAE: {summary['mae_mean']:.4f}")
    print(f"   R²: {summary['r2_mean']:.4f}")
    
    return {"folds": scores, "summary": summary}


if __name__ == "__main__":
    print("=" * 60)
    print("Skyfusion Analytics - Model Validator")
    print("Métricas de evaluación: RMSE, MAE, R²")
    print("=" * 60)
    
    np.random.seed(42)
    n_samples = 1000
    y_true = np.random.randn(n_samples) * 10 + 50
    y_pred = y_true + np.random.randn(n_samples) * 2
    
    validator = ModelValidator()
    metrics = validator.validate(y_true, y_pred)
    
    print(f"\n📊 Métricas de Validación:")
    print(f"   RMSE: {metrics.rmse:.4f}")
    print(f"   MAE: {metrics.mae:.4f}")
    print(f"   R²: {metrics.r2_score:.4f}")
    print(f"   MAPE: {metrics.mape:.4f}%")
    
    report = validator.generate_report()
    print(f"\n📝 Interpretación:")
    print(f"   {report['interpretation']}")
    
    print("\n✅ Validador cargado correctamente")
