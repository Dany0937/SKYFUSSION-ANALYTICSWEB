"""
Ejemplo de Uso - Caudal Predictor
==================================

Este script demuestra el flujo completo de:
1. Carga y preprocesamiento de datos
2. Entrenamiento del modelo LSTM
3. Validación y evaluación
4. Predicciones

Uso:
    python example_usage.py
"""

import numpy as np
import pandas as pd
import tempfile
import os

from data_preprocessing import TemporalDataPreprocessor
from caudal_predictor import CaudalPredictor, ModelConfig
from validation import ModelValidator


def generate_synthetic_data(
    n_samples: int = 2000,
    start_date: str = "1969-01-01",
    seed: int = 42
) -> tuple:
    """
    Genera datos sintéticos para demostración.
    
    En producción, usar datos reales del Río Combeima.
    """
    np.random.seed(seed)
    
    dates = pd.date_range(start=start_date, periods=n_samples, freq='D')
    
    t = np.arange(n_samples)
    seasonal = 10 * np.sin(2 * np.pi * t / 365)
    trend = 0.01 * t
    noise = np.random.randn(n_samples) * 2
    
    base_caudal = 50 + seasonal + trend + noise
    
    seasonal_precip = 20 * np.sin(2 * np.pi * (t + 30) / 365) + 30
    noise_precip = np.random.randn(n_samples) * 5
    precip = np.maximum(seasonal_precip + noise_precip, 0)
    
    river_width = 45 + 0.005 * t + 3 * np.sin(2 * np.pi * t / 365) + np.random.randn(n_samples) * 2
    
    df = pd.DataFrame({
        'fecha': dates,
        'caudal_m3s': base_caudal,
        'precipitacion_mm': precip,
        'ancho_rio': river_width
    })
    
    df.set_index('fecha', inplace=True)
    
    return df, df[['precipitacion_mm', 'ancho_rio']]


def main():
    """Función principal de demostración."""
    
    print("\n" + "=" * 60)
    print("SKYFUSION ANALYTICS - CAUDAL PREDICTOR DEMO")
    print("Río Combeima, Ibagué, Colombia")
    print("=" * 60)
    
    print("\n📊 Generando datos sintéticos (1969-2023)...")
    
    caudal_df, other_features = generate_synthetic_data(
        n_samples=2000,
        start_date="1969-01-01",
        seed=1969
    )
    
    print(f"   ✓ Generados {len(caudal_df)} registros")
    print(f"   ✓ Rango temporal: {caudal_df.index.min()} a {caudal_df.index.max()}")
    print(f"   ✓ Variables: caudal, precipitación, ancho río")
    
    print("\n🔧 Preprocesando datos...")
    
    preprocessor = TemporalDataPreprocessor(
        sequence_length=72,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15
    )
    
    preprocessor.dataframe = caudal_df.copy()
    preprocessor.handle_missing_values(method='interpolate')
    
    preprocessor.select_features(
        feature_columns=['caudal_m3s', 'precipitacion_mm', 'ancho_rio'],
        target_column='caudal_m3s'
    )
    preprocessor.normalize(method='minmax')
    
    n_features = len(preprocessor.feature_columns)
    
    print(f"   ✓ Features: {preprocessor.feature_columns}")
    print(f"   ✓ Target: {preprocessor.target_column}")
    
    data = preprocessor.prepare_data()
    
    print(f"   ✓ Datos preparados:")
    print(f"      X_train: {data.X_train.shape}")
    print(f"      X_val: {data.X_val.shape}")
    print(f"      X_test: {data.X_test.shape}")
    
    print("\n🧠 Construyendo modelo LSTM...")
    
    config = ModelConfig(
        sequence_length=72,
        n_features=n_features,
        output_steps=24,
        lstm_units_1=64,
        lstm_units_2=32,
        lstm_units_3=16,
        dropout_rate=0.2,
        batch_size=32,
        epochs=20
    )
    
    predictor = CaudalPredictor(config=config)
    predictor.build_model()
    
    print("   ✓ Modelo construido")
    print(f"   ✓ Total parámetros: {predictor.model.count_params():,}")
    
    print("\n📈 Entrenando modelo...")
    print("-" * 50)
    
    history = predictor.train(
        X_train=data.X_train,
        y_train=data.y_train,
        X_val=data.X_val,
        y_val=data.y_val,
        verbose=1
    )
    
    print("-" * 50)
    print(f"   ✓ Entrenamiento completado")
    print(f"   ✓ Mejor época: {history.best_epoch}")
    
    print("\n🔮 Realizando predicciones...")
    
    test_sample = data.X_test[0:5]
    predictions = []
    
    for i in range(len(test_sample)):
        pred = predictor.predict(test_sample[i:i+1])
        predictions.append(pred)
    
    y_pred_flat = np.array([p['flow_prediction'][0] for p in predictions]).flatten()
    y_true_flat = data.y_test[:5]
    
    if len(y_true_flat.shape) > 1:
        y_true_flat = y_true_flat[:, 0]
    
    y_pred_original = preprocessor.inverse_transform_target(y_pred_flat)
    y_true_original = preprocessor.inverse_transform_target(y_true_flat)
    
    print(f"   ✓ Predicciones realizadas")
    print(f"\n   Muestra de predicciones (m³/s):")
    print(f"   {'Hora':<8} {'Real':<12} {'Predicho':<12} {'Error':<10}")
    print(f"   {'-'*42}")
    for i, (real, predicho) in enumerate(zip(y_true_original[:5], y_pred_original[:5])):
        error = abs(real - predicho)
        print(f"   {i+1:<8} {real:<12.2f} {predicho:<12.2f} {error:<10.2f}")
    
    print("\n📊 Validando modelo...")
    
    y_pred_full = []
    for i in range(len(data.X_test)):
        pred = predictor.predict(data.X_test[i:i+1])
        y_pred_full.append(pred['flow_prediction'][0])
    
    y_pred_full = np.array(y_pred_full)
    y_true_full = data.y_test
    
    if len(y_true_full.shape) > 1:
        y_true_full = y_true_full[:, 0]
    
    validator = ModelValidator()
    metrics = validator.validate(y_true_full, y_pred_full)
    
    print(f"\n   ╔{'═'*40}╗")
    print(f"   ║{'MÉTRICAS DE EVALUACIÓN':^40}║")
    print(f"   ╠{'═'*40}╣")
    print(f"   ║ {'RMSE:':<20} {metrics.rmse:>15.4f} ║")
    print(f"   ║ {'MAE:':<20} {metrics.mae:>15.4f} ║")
    print(f"   ║ {'R²:':<20} {metrics.r2_score:>15.4f} ║")
    print(f"   ║ {'MAPE:':<18} {metrics.mape:>14.2f}%║")
    print(f"   ╚{'═'*40}╝")
    
    report = validator.generate_report()
    
    print(f"\n📝 Interpretación:")
    print(f"   {report['interpretation']}")
    
    print(f"\n💾 Estadísticas de diagnóstico:")
    diag = report['residuals_diagnostics']
    print(f"   - Normalidad residuos: {'✓' if diag['is_normal'] else '⚠'} (Shapiro p={diag['shapiro_pvalue']:.4f})")
    print(f"   - Autocorrelación: {'✓ Sin' if not diag['is_autocorrelated'] else '⚠ Con'} autocorrelación (DW={diag['durbin_watson']:.4f})")
    
    print("\n" + "=" * 60)
    print("✨ DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)


if __name__ == "__main__":
    main()
