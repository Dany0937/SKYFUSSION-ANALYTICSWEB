"""
Modelos de Red Neuronal Recurrente (RNA) — predicción multitemporal
==================================================================

Implementa 5 arquitecturas de RNA para predicción de series NDVI/EVI
del río Combeima, todas compatibles con la misma interfaz de entrada:

    Input:  (batch, timesteps, features)
    Output: (batch, horizonte)  — predicción multicampo del NDVI futuro

Arquitecturas disponibles:
- gru             → GRU apilado
- lstm            → LSTM apilado
- bigru           → GRU bidireccional
- gru_attention   → GRU + mecanismo de atención sobre timesteps
- tcn             → Red convolucional temporal (convoluciones dilatadas)

Todas permiten configurar unidades por capa, dropout, lr y reg. L2,
y devuelven tanto un modelo Keras como una estructura de resumen.
"""

from typing import Dict, Any

import numpy as np

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, regularizers


def _units_lista(config: Dict[str, Any]) -> list:
    """Unidades recurrentes por capa (lista)."""
    unidades = config.get("unidades", [64, 32])
    if isinstance(unidades, int):
        unidades = [unidades]
    return unidades


# --------------------------------------------------------------------------- #
# Bloques reutilizables
# --------------------------------------------------------------------------- #

class AttentionLayer(layers.Layer):
    """Capa de atención sobre la dimensión temporal (self-attention simple)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self, input_shape):
        self.attention_w = self.add_weight(
            shape=(input_shape[-1], 1),
            initializer="random_normal",
            trainable=True,
            name="attention_w",
        )
        self.attention_b = self.add_weight(
            shape=(input_shape[1], 1),
            initializer="zeros",
            trainable=True,
            name="attention_b",
        )
        super().build(input_shape)

    def call(self, inputs):
        # inputs: (batch, timesteps, features)
        e = tf.squeeze(tf.tensordot(inputs, self.attention_w, axes=1), -1)  # (b, t)
        e = e + tf.squeeze(self.attention_b, -1)
        alphas = keras.activations.softmax(e, axis=-1)  # (b, t)
        contexto = tf.reduce_sum(inputs * tf.expand_dims(alphas, -1), axis=1)
        return contexto, alphas


def _bloque_regularizacion(x, dropout: float):
    x = layers.Dropout(dropout)(x)
    return x


# --------------------------------------------------------------------------- #
# Constructor principal por arquitectura
# --------------------------------------------------------------------------- #

def crear_modelo(
    arquitectura: str,
    timesteps: int,
    n_features: int,
    horizonte: int,
    config: Dict[str, Any],
) -> keras.Model:
    """
    Crea el modelo Keras según la arquitectura y config solicitadas.

    Args:
        arquitectura: clave en ARQUITECTURAS_RNN
        timesteps:    longitud de la secuencia de entrada
        n_features:   número de features por timestep
        horizonte:    pasos a predecir
        config:       dict de hiperparámetros (unidades, dropout, lr, etc.)

    Returns:
        modelo Keras compilado
    """
    if arquitectura not in ("gru", "lstm", "bigru", "gru_attention", "tcn"):
        raise ValueError(f"Arquitectura desconocida: {arquitectura}")

    dropout = config.get("dropout", 0.3)
    lr = config.get("lr", 1e-3)
    seed = config.get("seed", 42)
    keras.utils.set_random_seed(seed)

    inputs = layers.Input(shape=(timesteps, n_features), name="entrada")

    if arquitectura == "tcn":
        x = _build_tcn(inputs, config, dropout)
    else:
        x = _build_recurrent(inputs, arquitectura, config, dropout)

    # Cabeza de regresión multicampo
    x = layers.Dense(max(8, horizonte * 2), activation="relu",
                     kernel_regularizer=regularizers.l2(config.get("l2", 1e-4)))(x)
    x = layers.Dropout(dropout * 0.5)(x)
    salida = layers.Dense(horizonte, activation="linear", name="salida")(x)

    modelo = keras.Model(inputs=inputs, outputs=salida)
    modelo.compile(
        optimizer=keras.optimizers.Adam(learning_rate=lr, clipnorm=1.0),
        loss="huber",
        metrics=["mae", "mse", keras.metrics.RootMeanSquaredError(name="rmse")],
    )
    return modelo


def _build_recurrent(inputs, arquitectura: str, config: Dict[str, Any], dropout: float):
    """Construye el bloque recurrente (gru/lstm/bigru/attention)."""
    unidades = _units_lista(config)
    tipo_base = "gru" if arquitectura in ("bigru", "gru_attention") else arquitectura
    recurrente = {"gru": layers.GRU, "lstm": layers.LSTM}[tipo_base]
    n_layers = len(unidades)

    x = inputs
    kernel_reg = regularizers.l2(config.get("l2", 1e-4))

    for i, u in enumerate(unidades):
        return_seq = (i < n_layers - 1) or arquitectura == "gru_attention"
        if arquitectura == "bigru":
            x = layers.Bidirectional(
                recurrente(u, return_sequences=return_seq,
                           kernel_regularizer=kernel_reg,
                           name=f"bi_{arquitectura}_{i}")
            )(x)
        else:
            x = recurrente(u, return_sequences=return_seq,
                           kernel_regularizer=kernel_reg,
                           name=f"{arquitectura}_{i}")(x)
        if return_seq or arquitectura == "gru_attention":
            x = layers.BatchNormalization()(x)
            x = _bloque_regularizacion(x, dropout)
        else:
            x = layers.BatchNormalization()(x)

    if arquitectura == "gru_attention":
        x, _alphas = AttentionLayer()(x)

    return x


def _build_tcn(inputs, config: Dict[str, Any], dropout: float):
    """Construye un bloque TCN (convoluciones causales dilatadas)."""
    filters = config.get("filters", 64)
    kernel_size = config.get("kernel_size", 3)
    dilations = config.get("dilations", [1, 2, 4, 8])
    kernel_reg = regularizers.l2(config.get("l2", 1e-4))

    x = inputs
    for i, d in enumerate(dilations):
        # Convolución causal
        x = layers.Conv1D(
            filters=filters,
            kernel_size=kernel_size,
            dilation_rate=d,
            padding="causal",
            activation="relu",
            kernel_regularizer=kernel_reg,
            name=f"tcn_conv_{i}",
        )(x)
        x = layers.BatchNormalization()(x)
        x = _bloque_regularizacion(x, dropout)

    # Última capa reduce a filtros y luego GlobalMaxPool
    x = layers.GlobalMaxPooling1D()(x)
    return x


# --------------------------------------------------------------------------- #
# Utilidades de serialización de arquitectura
# --------------------------------------------------------------------------- #

def resumen_arquitectura(arquitectura: str, config: Dict[str, Any]) -> str:
    """Devuelve una cadena human-readable de la config de la arquitectura."""
    if arquitectura == "tcn":
        return (f"TCN filters={config.get('filters')} kernel={config.get('kernel_size')} "
                f"dilations={config.get('dilations')} dropout={config.get('dropout')}")
    unidades = _units_lista(config)
    capas_str = " -> ".join([f"{u} {arquitectura.upper()}" for u in unidades])
    if arquitectura == "bigru":
        capas_str = capas_str.replace(arquitectura.upper(), "BiGRU")
    return f"{capas_str} (dropout={config.get('dropout')})"


def contar_parametros(modelo: keras.Model) -> int:
    """Devuelve el número total de parámetros entrenables."""
    return int(np.sum([tf.size(v).numpy() for v in modelo.trainable_variables]))
