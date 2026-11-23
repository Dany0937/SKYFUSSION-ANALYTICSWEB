"""
ML Tools Module - Skyfusion Analytics
===================================

Oracle Agent para predicción de caudal en el Río Combeima.

Componentes:
- caudal_predictor.py: Modelo LSTM para predicción de series temporales
- validation.py: Métricas de evaluación (RMSE, MAE, R²)
- data_preprocessing.py: Preprocesamiento de datos con Pandas/Scikit-learn
- train.py: Pipeline de entrenamiento completo
- example_usage.py: Ejemplo de uso

Uso Básico:

    from caudal_predictor import CaudalPredictor, create_default_model
    from data_preprocessing import TemporalDataPreprocessor
    from validation import ModelValidator

    # Preprocesar datos
    preprocessor = TemporalDataPreprocessor(sequence_length=72)
    data = preprocessor.prepare_data(features=['caudal', 'precip', 'ancho'], target='caudal')
    
    # Crear y entrenar modelo
    model = create_default_model(sequence_length=72, n_features=3)
    history = model.train(X_train, y_train, X_val, y_val)
    
    # Predecir
    prediction = model.predict(X_new)
    
    # Validar
    validator = ModelValidator()
    metrics = validator.validate(y_true, y_pred)
    print(f"RMSE: {metrics.rmse}, R²: {metrics.r2_score}")
"""

from .caudal_predictor import (
    CaudalPredictor,
    ModelConfig,
    TrainingHistory,
    create_default_model
)

from .validation import (
    ModelValidator,
    ValidationMetrics,
    ResidualDiagnostics,
    cross_validate
)

from .data_preprocessing import (
    TemporalDataPreprocessor,
    PreprocessedData,
    load_and_preprocess_demo
)

__version__ = "1.0.0"
__author__ = "Skyfusion Analytics - ML Division"

__all__ = [
    "CaudalPredictor",
    "ModelConfig", 
    "TrainingHistory",
    "create_default_model",
    "ModelValidator",
    "ValidationMetrics",
    "ResidualDiagnostics",
    "cross_validate",
    "TemporalDataPreprocessor",
    "PreprocessedData",
    "load_and_preprocess_demo"
]
