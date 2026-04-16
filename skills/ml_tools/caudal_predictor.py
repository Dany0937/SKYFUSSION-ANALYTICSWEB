"""
Caudal Predictor - LSTM Neural Network for Flow Prediction
=========================================================

Módulo de predicción de caudal para el Río Combeima (1969-2023)
utilizando redes neuronales LSTM (Long Short-Term Memory).

Arquitectura:
- Capas LSTM Bidireccionales
- Dropout para regularización
- Capas Densas para predicción
- Múltiples salidas: predicción de caudal + intervalo de confianza
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import (
    LSTM,
    Dense,
    Dropout,
    Bidirectional,
    LayerNormalization,
    Input
)
from tensorflow.keras.models import Model, Sequential, load_model
from tensorflow.keras.callbacks import (
    EarlyStopping,
    ModelCheckpoint,
    ReduceLROnPlateau,
    TensorBoard,
    CSVLogger
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
import json
import pickle


@dataclass
class ModelConfig:
    """Configuración de hiperparámetros del modelo."""
    sequence_length: int = 72
    n_features: int = 3
    lstm_units_1: int = 128
    lstm_units_2: int = 64
    lstm_units_3: int = 32
    dropout_rate: float = 0.2
    l2_reg: float = 0.001
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    validation_split: float = 0.2
    output_steps: int = 24
    

@dataclass
class TrainingHistory:
    """Historial de entrenamiento."""
    history: Dict[str, list]
    final_metrics: Dict[str, float]
    best_epoch: int


class CaudalPredictor:
    """
    Modelo LSTM para predicción de caudal en el Río Combeima.
    
    Entrada: Secuencia de 72 horas de datos (caudal, precipitación, ancho río)
    Salida: Predicción de caudal a 24 horas + intervalo de confianza
    """

    def __init__(
        self,
        config: Optional[ModelConfig] = None,
        model_path: Optional[str] = None
    ) -> None:
        """
        Inicializa el predictor.
        
        Args:
            config: Configuración de hiperparámetros
            model_path: Ruta para cargar un modelo existente
        """
        self.config = config or ModelConfig()
        self.model: Optional[Model] = None
        self.history: Optional[TrainingHistory] = None
        self.model_path = model_path
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def build_model(self) -> Model:
        """
        Construye la arquitectura LSTM híbrida bidireccional.
        
        Arquitectura:
        Input -> BiLSTM(128) -> Dropout -> BiLSTM(64) -> Dropout -> 
        LSTM(32) -> Dense(32) -> LayerNorm -> Output
        
        Returns:
            Modelo Keras compilado
        """
        inputs = Input(
            shape=(self.config.sequence_length, self.config.n_features),
            name="input_sequence"
        )
        
        x = Bidirectional(
            LSTM(
                units=self.config.lstm_units_1,
                return_sequences=True,
                dropout=self.config.dropout_rate,
                recurrent_dropout=self.config.dropout_rate,
                kernel_regularizer=l2(self.config.l2_reg),
                name="bilstm_layer_1"
            ),
            name="bidirectional_1"
        )(inputs)
        
        x = Dropout(self.config.dropout_rate, name="dropout_1")(x)
        
        x = Bidirectional(
            LSTM(
                units=self.config.lstm_units_2,
                return_sequences=True,
                dropout=self.config.dropout_rate,
                recurrent_dropout=self.config.dropout_rate,
                kernel_regularizer=l2(self.config.l2_reg),
                name="bilstm_layer_2"
            ),
            name="bidirectional_2"
        )(x)
        
        x = Dropout(self.config.dropout_rate, name="dropout_2")(x)
        
        x = LSTM(
            units=self.config.lstm_units_3,
            return_sequences=False,
            dropout=self.config.dropout_rate,
            recurrent_dropout=self.config.dropout_rate,
            kernel_regularizer=l2(self.config.l2_reg),
            name="lstm_layer_3"
        )(x)
        
        x = Dense(64, activation="relu", name="dense_1")(x)
        x = LayerNormalization(name="layer_norm")(x)
        x = Dropout(self.config.dropout_rate, name="dropout_3")(x)
        
        x = Dense(32, activation="relu", name="dense_2")(x)
        
        flow_output = Dense(
            self.config.output_steps,
            activation="linear",
            name="flow_prediction"
        )(x)
        
        uncertainty_output = Dense(
            self.config.output_steps,
            activation="softplus",
            name="uncertainty"
        )(x)
        
        alert_output = Dense(
            4,
            activation="softmax",
            name="alert_classification"
        )(x)
        
        self.model = Model(
            inputs=inputs,
            outputs=[flow_output, uncertainty_output, alert_output],
            name="caudal_lstm_predictor"
        )
        
        self.model.compile(
            optimizer=Adam(learning_rate=self.config.learning_rate),
            loss={
                "flow_prediction": "mse",
                "uncertainty": "mse",
                "alert_classification": "sparse_categorical_crossentropy"
            },
            loss_weights={
                "flow_prediction": 1.0,
                "uncertainty": 0.1,
                "alert_classification": 0.5
            },
            metrics={
                "flow_prediction": ["mae", "mse"],
                "alert_classification": ["accuracy"]
            }
        )
        
        return self.model

    def summary(self) -> None:
        """Imprime el resumen del modelo."""
        if self.model is None:
            raise RuntimeError("Modelo no construido. Use build_model() primero.")
        self.model.summary()

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        callbacks_config: Optional[Dict[str, Any]] = None,
        verbose: int = 1
    ) -> TrainingHistory:
        """
        Entrena el modelo con los datos proporcionados.
        
        Args:
            X_train: Datos de entrada de entrenamiento
            y_train: Targets de entrenamiento
            X_val: Datos de validación (opcional)
            y_val: Targets de validación (opcional)
            callbacks_config: Configuración de callbacks
            verbose: Nivel de detalle (0, 1, 2)
            
        Returns:
            Objeto TrainingHistory con métricas
        """
        if self.model is None:
            self.build_model()
            
        callbacks = self._setup_callbacks(callbacks_config)
        
        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = (X_val, {
                "flow_prediction": y_val,
                "uncertainty": y_val * 0.1,
                "alert_classification": np.zeros((len(y_val), self.config.output_steps))
            })
        
        y_train_formatted = {
            "flow_prediction": y_train,
            "uncertainty": y_train * 0.1,
            "alert_classification": np.zeros((len(y_train), self.config.output_steps))
        }
        
        history = self.model.fit(
            X_train,
            y_train_formatted,
            validation_data=validation_data,
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
        
        best_epoch = np.argmin(history.history["val_loss"])
        
        self.history = TrainingHistory(
            history=dict(history.history),
            final_metrics={
                "loss": float(history.history["loss"][-1]),
                "val_loss": float(history.history["val_loss"][-1]),
                "flow_prediction_mae": float(history.history["flow_prediction_mae"][-1])
            },
            best_epoch=int(best_epoch) + 1
        )
        
        return self.history

    def _setup_callbacks(
        self,
        config: Optional[Dict[str, Any]] = None
    ) -> list:
        """
        Configura los callbacks de entrenamiento.
        
        Args:
            config: Configuración personalizada
            
        Returns:
            Lista de callbacks de Keras
        """
        callbacks = []
        
        callbacks.append(
            EarlyStopping(
                monitor="val_loss",
                patience=15,
                restore_best_weights=True,
                verbose=1
            )
        )
        
        callbacks.append(
            ReduceLROnPlateau(
                monitor="val_loss",
                factor=0.5,
                patience=5,
                min_lr=1e-6,
                verbose=1
            )
        )
        
        if config and config.get("checkpoint_path"):
            callbacks.append(
                ModelCheckpoint(
                    filepath=config["checkpoint_path"],
                    monitor="val_loss",
                    save_best_only=True,
                    verbose=1
                )
            )
            
        if config and config.get("tensorboard_dir"):
            callbacks.append(
                TensorBoard(
                    log_dir=config["tensorboard_dir"],
                    histogram_freq=1
                )
            )
            
        if config and config.get("csv_logger_path"):
            callbacks.append(
                CSVLogger(config["csv_logger_path"])
            )
            
        return callbacks

    def predict(
        self,
        X_input: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """
        Realiza predicciones con el modelo.
        
        Args:
            X_input: Datos de entrada (1, sequence_length, n_features)
            
        Returns:
            Diccionario con predicción, incertidumbre y alerta
        """
        if self.model is None:
            raise RuntimeError("Modelo no entrenado. Use train() primero.")
            
        if len(X_input.shape) == 2:
            X_input = X_input.reshape(1, X_input.shape[0], X_input.shape[1])
            
        flow_pred, uncertainty, alert_prob = self.model.predict(X_input, verbose=0)
        
        alert_classes = ["green", "yellow", "orange", "red"]
        predicted_alerts = [alert_classes[i] for i in np.argmax(alert_prob, axis=-1)]
        
        return {
            "flow_prediction": flow_pred[0],
            "uncertainty": uncertainty[0],
            "confidence_interval": np.stack([
                flow_pred[0] - 1.96 * uncertainty[0],
                flow_pred[0] + 1.96 * uncertainty[0]
            ], axis=-1),
            "alert_probabilities": alert_prob[0],
            "predicted_alerts": predicted_alerts
        }

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, float]:
        """
        Evalúa el modelo en datos de prueba.
        
        Args:
            X_test: Datos de prueba
            y_test: Targets de prueba
            
        Returns:
            Diccionario con métricas de evaluación
        """
        if self.model is None:
            raise RuntimeError("Modelo no entrenado")
            
        y_formatted = {
            "flow_prediction": y_test,
            "uncertainty": y_test * 0.1,
            "alert_classification": np.zeros((len(y_test), self.config.output_steps))
        }
        
        results = self.model.evaluate(X_test, y_formatted, verbose=0)
        
        return {
            "loss": results[0],
            "flow_prediction_loss": results[1],
            "flow_prediction_mae": results[3],
            "alert_accuracy": results[5] if len(results) > 5 else 0.0
        }

    def save_model(self, path: str) -> None:
        """
        Guarda el modelo y su configuración.
        
        Args:
            path: Ruta donde guardar el modelo
        """
        if self.model is None:
            raise RuntimeError("No hay modelo para guardar")
            
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        self.model.save(f"{path}.keras")
        
        config_dict = {
            "sequence_length": self.config.sequence_length,
            "n_features": self.config.n_features,
            "lstm_units_1": self.config.lstm_units_1,
            "lstm_units_2": self.config.lstm_units_2,
            "lstm_units_3": self.config.lstm_units_3,
            "dropout_rate": self.config.dropout_rate,
            "l2_reg": self.config.l2_reg,
            "learning_rate": self.config.learning_rate,
            "batch_size": self.config.batch_size,
            "output_steps": self.config.output_steps
        }
        
        with open(f"{path}_config.json", "w") as f:
            json.dump(config_dict, f, indent=2)
            
        if self.history:
            with open(f"{path}_history.pkl", "wb") as f:
                pickle.dump(self.history, f)
                
        print(f"✅ Modelo guardado en {path}")

    def load_model(self, path: str) -> None:
        """
        Carga un modelo guardado.
        
        Args:
            path: Ruta del modelo
        """
        if not os.path.exists(f"{path}.keras"):
            raise FileNotFoundError(f"Modelo no encontrado: {path}.keras")
            
        self.model = load_model(f"{path}.keras")
        
        config_path = f"{path}_config.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_dict = json.load(f)
            self.config = ModelConfig(**config_dict)
            
        print(f"✅ Modelo cargado desde {path}")


def create_default_model(
    sequence_length: int = 72,
    n_features: int = 3,
    output_steps: int = 24
) -> CaudalPredictor:
    """
    Factory function para crear un modelo con configuración por defecto.
    
    Args:
        sequence_length: Pasos temporales de entrada
        n_features: Número de características de entrada
        output_steps: Pasos a predecir
        
    Returns:
        Instancia de CaudalPredictor lista para entrenar
    """
    config = ModelConfig(
        sequence_length=sequence_length,
        n_features=n_features,
        output_steps=output_steps,
        lstm_units_1=128,
        lstm_units_2=64,
        lstm_units_3=32,
        dropout_rate=0.2,
        learning_rate=0.001,
        batch_size=32,
        epochs=100
    )
    
    predictor = CaudalPredictor(config=config)
    predictor.build_model()
    
    return predictor


if __name__ == "__main__":
    print("=" * 60)
    print("Skyfusion Analytics - Caudal LSTM Predictor")
    print("Río Combeima, Ibagué, Colombia (1969-2023)")
    print("=" * 60)
    
    print("\n[INFO] Creando modelo con configuración por defecto...")
    
    predictor = create_default_model(
        sequence_length=72,
        n_features=3,
        output_steps=24
    )
    
    print("\n[INFO] Resumen del modelo:")
    predictor.summary()
    
    print("\n✅ Modelo inicializado correctamente")
    print("[INFO] Para entrenar, use: predictor.train(X_train, y_train)")
