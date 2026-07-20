---
title: OracleAgent
description: Entrenamiento y ejecución de modelos LSTM-CNN para predicción ambiental.
order: 4
---

# OracleAgent

Responsable del entrenamiento y ejecución de modelos de inteligencia artificial. Utiliza redes neuronales híbridas LSTM-CNN para predecir variables ambientales.

## Funciones

- Entrenamiento de redes neuronales
- Predicción de escenarios
- Inferencias en tiempo real
- Evaluación de precisión
- Pronósticos ambientales
- Clasificación de alertas

## Tecnologías

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| TensorFlow | 2.15+ | Framework de deep learning |
| Python | 3.11+ | Lenguaje de ejecución |
| LSTM-CNN | — | Modelo híbrido para series temporales + imágenes |

## Eventos

| Tipo | Dirección | Descripción |
|------|-----------|-------------|
| `analysis:completed` | Entrada | Resultados del análisis listos |
| `prediction:completed` | Salida | Predicción generada con nivel de alerta |

## Métricas de Éxito

| Métrica | Objetivo |
|---------|----------|
| R² | > 0.80 |
| RMSE | < 0.15 |
| Precisión de alertas | > 85% |

## Implementación

```
agents/python/oracle_agent/
├── agent.py             # OracleAgent + AlertSystem
├── lstm_cnn_model.py    # Model definition (TensorFlow)
└── requirements.txt
```
