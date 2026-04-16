# ML Tools - Skyfusion Analytics

## Oracle Agent - Predicción de Caudal LSTM

Módulo de Machine Learning para predicción de caudal en el Río Combeima utilizando redes neuronales LSTM.

## Estructura del Módulo

```
ml_tools/
├── __init__.py              # Paquete Python
├── caudal_predictor.py      # Modelo LSTM principal
├── data_preprocessing.py    # Preprocesamiento de datos
├── validation.py            # Métricas de evaluación
├── train.py                 # Pipeline de entrenamiento
├── example_usage.py         # Ejemplo de uso
├── requirements.txt         # Dependencias
└── README.md               # Este archivo
```

## Instalación de Dependencias

```bash
pip install numpy pandas scikit-learn tensorflow
```

## Uso Rápido

### 1. Preprocesamiento de Datos

```python
from data_preprocessing import TemporalDataPreprocessor

preprocessor = TemporalDataPreprocessor(
    sequence_length=72,
    train_ratio=0.7,
    val_ratio=0.15,
    test_ratio=0.15
)

data = preprocessor.prepare_data(
    feature_columns=['caudal_m3s', 'precipitacion_mm', 'ancho_rio'],
    target_column='caudal_m3s'
)
```

### 2. Entrenamiento del Modelo

```python
from caudal_predictor import create_default_model

model = create_default_model(
    sequence_length=72,
    n_features=3,
    output_steps=24
)

history = model.train(
    X_train=data.X_train,
    y_train=data.y_train,
    X_val=data.X_val,
    y_val=data.y_val
)
```

### 3. Validación

```python
from validation import ModelValidator

validator = ModelValidator()
metrics = validator.validate(y_true, y_pred)

print(f"RMSE: {metrics.rme:.4f}")
print(f"MAE: {metrics.mae:.4f}")
print(f"R²: {metrics.r2_score:.4f}")
```

### 4. Pipeline Completo de Entrenamiento

```bash
python train.py \
    --caudal data/caudal_combeima.csv \
    --precipitacion data/precipitacion_combeima.csv \
    --sequence-length 72 \
    --epochs 100 \
    --model-output ./models/caudal_model
```

## Arquitectura del Modelo

```
Input (72, 3)
    ↓
Bidirectional LSTM (128 units) + Dropout
    ↓
Bidirectional LSTM (64 units) + Dropout
    ↓
LSTM (32 units) + Dropout
    ↓
Dense (64) + LayerNorm + Dropout
    ↓
Dense (32)
    ↓
┌─────────────────────────────────────┐
│ flow_prediction (24)  │ MSE Loss   │
│ uncertainty (24)      │ MSE Loss   │
│ alert_classification (4)│ Cross-Ent │
└─────────────────────────────────────┘
```

## Variables de Entrada

| Variable | Descripción | Unidad |
|----------|-------------|--------|
| caudal_m3s | Caudal histórico | m³/s |
| precipitacion_mm | Precipitación | mm |
| ancho_rio | Ancho del río (Vision Agent) | píxeles |

## Métricas de Evaluación

- **RMSE**: Root Mean Squared Error
- **MAE**: Mean Absolute Error
- **R²**: Coefficient of Determination
- **MAPE**: Mean Absolute Percentage Error
- **Cobertura 95%**: Porcentaje de predicciones dentro del intervalo

## Configuración Recomendada

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| sequence_length | 72 | Horas de historial |
| output_steps | 24 | Horas a predecir |
| batch_size | 32 | Tamaño de batch |
| epochs | 100 | Máximo de épocas |
| patience | 15 | Early stopping |
| lstm_units | 128/64/32 | Capas LSTM |

## Autor

Skyfusion Analytics Team - Oracle Division
