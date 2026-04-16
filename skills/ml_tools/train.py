"""
Training Pipeline - Caudal Prediction Model
==========================================

Pipeline completo de entrenamiento para el modelo LSTM de predicción de caudal.

Uso:
    python train.py --data data/caudal_combeima.csv
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
from datetime import datetime

from data_preprocessing import TemporalDataPreprocessor, PreprocessedData
from caudal_predictor import CaudalPredictor, ModelConfig, create_default_model
from validation import ModelValidator


def parse_arguments() -> argparse.Namespace:
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Entrenamiento de modelo LSTM para predicción de caudal"
    )
    
    parser.add_argument(
        "--caudal",
        type=str,
        required=True,
        help="Ruta al CSV de datos de caudal"
    )
    parser.add_argument(
        "--precipitacion",
        type=str,
        required=True,
        help="Ruta al CSV de datos de precipitación"
    )
    parser.add_argument(
        "--ancho-rio",
        type=str,
        default=None,
        help="Ruta opcional al CSV de ancho del río"
    )
    parser.add_argument(
        "--sequence-length",
        type=int,
        default=72,
        help="Longitud de secuencia temporal (default: 72)"
    )
    parser.add_argument(
        "--output-steps",
        type=int,
        default=24,
        help="Pasos de predicción (default: 24)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Número de épocas (default: 100)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Tamaño de batch (default: 32)"
    )
    parser.add_argument(
        "--model-output",
        type=str,
        default="./models/caudal_model",
        help="Ruta de salida del modelo"
    )
    parser.add_argument(
        "--logs-dir",
        type=str,
        default="./logs",
        help="Directorio para logs de TensorBoard"
    )
    
    return parser.parse_args()


def load_and_merge_data(
    caudal_path: str,
    precip_path: str,
    ancho_rio_path: str = None
) -> pd.DataFrame:
    """
    Carga y fusiona datos de múltiples fuentes.
    
    Args:
        caudal_path: Ruta CSV caudal
        precip_path: Ruta CSV precipitación
        ancho_rio_path: Ruta opcional CSV ancho río
        
    Returns:
        DataFrame combinado
    """
    print("\n📂 Cargando datos...")
    
    caudal_df = pd.read_csv(caudal_path, parse_dates=['fecha'])
    caudal_df.set_index('fecha', inplace=True)
    caudal_df.sort_index(inplace=True)
    print(f"   ✓ Caudal: {len(caudal_df)} registros")
    
    precip_df = pd.read_csv(precip_path, parse_dates=['fecha'])
    precip_df.set_index('fecha', inplace=True)
    precip_df.sort_index(inplace=True)
    print(f"   ✓ Precipitación: {len(precip_df)} registros")
    
    merged = caudal_df.join(precip_df, how='inner', lsuffix='_caudal', rsuffix='_precip')
    print(f"   ✓ Merge completado: {len(merged)} registros")
    
    if ancho_rio_path and os.path.exists(ancho_rio_path):
        ancho_df = pd.read_csv(ancho_rio_path, parse_dates=['fecha'])
        ancho_df.set_index('fecha', inplace=True)
        merged = merged.join(ancho_df, how='left')
        print(f"   ✓ Ancho río: {len(ancho_df)} registros")
    
    return merged


def prepare_data(config: dict, df: pd.DataFrame) -> PreprocessedData:
    """
    Preprocesa los datos para entrenamiento.
    
    Args:
        config: Configuración de preprocesamiento
        df: DataFrame con datos combinados
        
    Returns:
        Datos listos para entrenamiento
    """
    print("\n🔧 Preprocesando datos...")
    
    preprocessor = TemporalDataPreprocessor(
        sequence_length=config['sequence_length'],
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15
    )
    
    preprocessor.dataframe = df
    
    preprocessor.handle_missing_values(method='interpolate')
    
    print(f"   ✓ Valores faltantes tratados")
    
    if 'ancho_rio' in df.columns:
        features = ['caudal_m3s', 'precipitacion_mm', 'ancho_rio']
    else:
        features = ['caudal_m3s', 'precipitacion_mm']
    
    n_features = len(features)
    
    preprocessor.select_features(
        feature_columns=features,
        target_column='caudal_m3s'
    )
    print(f"   ✓ Features seleccionados: {features}")
    
    preprocessor.normalize(method='minmax')
    print(f"   ✓ Datos normalizados con MinMaxScaler")
    
    data = preprocessor.prepare_data()
    print(f"   ✓ Secuencias creadas:")
    print(f"      Train: {data.X_train.shape}")
    print(f"      Val: {data.X_val.shape}")
    print(f"      Test: {data.X_test.shape}")
    
    return data, preprocessor, n_features


def train_model(
    data: PreprocessedData,
    config: dict,
    n_features: int,
    logs_dir: str
) -> CaudalPredictor:
    """
    Entrena el modelo LSTM.
    
    Args:
        data: Datos preprocesados
        config: Configuración del modelo
        n_features: Número de features
        logs_dir: Directorio de logs
        
    Returns:
        Modelo entrenado
    """
    print("\n🧠 Construyendo modelo LSTM...")
    
    model_config = ModelConfig(
        sequence_length=config['sequence_length'],
        n_features=n_features,
        output_steps=config['output_steps'],
        epochs=config['epochs'],
        batch_size=config['batch_size']
    )
    
    predictor = CaudalPredictor(config=model_config)
    predictor.build_model()
    
    print(f"   Arquitectura:")
    print(f"      - Input: ({config['sequence_length']}, {n_features})")
    print(f"      - BiLSTM(128) -> BiLSTM(64) -> LSTM(32)")
    print(f"      - Output: ({config['output_steps']},)")
    
    print("\n📈 Entrenando modelo...")
    print("-" * 50)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    callbacks_config = {
        "checkpoint_path": f"{config['model_output']}_checkpoint.keras",
        "tensorboard_dir": f"{logs_dir}/tensorboard_{timestamp}",
        "csv_logger_path": f"{logs_dir}/training_{timestamp}.csv"
    }
    
    history = predictor.train(
        X_train=data.X_train,
        y_train=data.y_train,
        X_val=data.X_val,
        y_val=data.y_val,
        callbacks_config=callbacks_config,
        verbose=1
    )
    
    print("-" * 50)
    print(f"\n✅ Entrenamiento completado")
    print(f"   Mejor época: {history.best_epoch}")
    print(f"   Loss final: {history.final_metrics['loss']:.4f}")
    print(f"   Val Loss: {history.final_metrics['val_loss']:.4f}")
    
    return predictor


def evaluate_model(
    predictor: CaudalPredictor,
    data: PreprocessedData
) -> dict:
    """
    Evalúa el modelo en datos de prueba.
    
    Args:
        predictor: Modelo entrenado
        data: Datos de prueba
        
    Returns:
        Métricas de evaluación
    """
    print("\n📊 Evaluando modelo...")
    
    y_pred_all = []
    for i in range(len(data.X_test)):
        pred = predictor.predict(data.X_test[i:i+1])
        y_pred_all.append(pred['flow_prediction'][0])
    
    y_pred = np.array(y_pred_all)
    y_true = data.y_test
    
    validator = ModelValidator()
    metrics = validator.validate(y_true, y_pred)
    
    print(f"   RMSE: {metrics.rmse:.4f}")
    print(f"   MAE: {metrics.mae:.4f}")
    print(f"   R²: {metrics.r2_score:.4f}")
    print(f"   MAPE: {metrics.mape:.4f}%")
    
    report = validator.generate_report()
    
    return {
        "metrics": report["summary"],
        "diagnostics": report["residuals_diagnostics"],
        "interpretation": report["interpretation"]
    }


def main():
    """Función principal de entrenamiento."""
    
    print("=" * 60)
    print("Skyfusion Analytics - Caudal LSTM Training Pipeline")
    print("Río Combeima, Ibagué, Colombia (1969-2023)")
    print("=" * 60)
    
    args = parse_arguments()
    
    config = {
        'sequence_length': args.sequence_length,
        'output_steps': args.output_steps,
        'epochs': args.epochs,
        'batch_size': args.batch_size,
        'model_output': args.model_output
    }
    
    try:
        df = load_and_merge_data(
            args.caudal,
            args.precipitacion,
            args.ancho_rio
        )
        
        data, preprocessor, n_features = prepare_data(config, df)
        
        os.makedirs(os.path.dirname(args.model_output), exist_ok=True)
        os.makedirs(args.logs_dir, exist_ok=True)
        
        predictor = train_model(data, config, n_features, args.logs_dir)
        
        eval_results = evaluate_model(predictor, data)
        
        print("\n💾 Guardando modelo...")
        predictor.save_model(args.model_output)
        
        print("\n📝 Reporte de validación:")
        print("-" * 50)
        print(eval_results["interpretation"])
        print("-" * 50)
        
        import json
        with open(f"{args.model_output}_report.json", "w") as f:
            json.dump(eval_results, f, indent=2, default=str)
        print(f"\n✅ Reporte guardado en {args.model_output}_report.json")
        
        print("\n✨ Pipeline completado exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
