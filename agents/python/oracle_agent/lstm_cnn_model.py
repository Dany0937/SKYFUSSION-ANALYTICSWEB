import numpy as np
from typing import Any


class HybridLSTMCNNModel:
    def __init__(self, config: dict | None = None):
        self.config = config or {
            'input_steps': 72,
            'output_steps': 24,
            'n_features': 7,
            'lstm_units_1': 128,
            'lstm_units_2': 64,
            'cnn_filters': 64,
            'kernel_size': 3,
            'dense_units': 32,
            'dropout_rate': 0.2,
            'learning_rate': 0.001,
        }
        self.model = None
        self.history = None

    def build(self):
        import tensorflow as tf
        from tensorflow.keras.layers import (
            LSTM, Dense, Conv1D, Dropout,
            Bidirectional, LayerNormalization,
        )
        from tensorflow.keras.models import Model

        inputs = tf.keras.Input(
            shape=(self.config['input_steps'], self.config['n_features']),
            name='input_layer',
        )

        x = Bidirectional(
            LSTM(self.config['lstm_units_1'], return_sequences=True, dropout=self.config['dropout_rate']),
            name='bi_lstm_1',
        )(inputs)

        x = Bidirectional(
            LSTM(self.config['lstm_units_2'], return_sequences=False, dropout=self.config['dropout_rate']),
            name='bi_lstm_2',
        )(x)

        x = tf.keras.layers.Reshape((1, self.config['lstm_units_2'] * 2), name='reshape')(x)

        x = Conv1D(
            filters=self.config['cnn_filters'],
            kernel_size=self.config['kernel_size'],
            activation='relu',
            padding='same',
            name='conv1d',
        )(x)

        x = Dropout(self.config['dropout_rate'], name='dropout_cnn')(x)
        x = Dense(self.config['dense_units'], activation='relu', name='dense_1')(x)
        x = LayerNormalization(name='layer_norm')(x)

        flow_output = Dense(self.config['output_steps'], activation='linear', name='flow_prediction')(x)
        uncertainty = Dense(self.config['output_steps'], activation='softplus', name='uncertainty')(x)
        alert_output = Dense(4, activation='softmax', name='alert_classification')(x)

        model = Model(inputs=inputs, outputs=[flow_output, uncertainty, alert_output])
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.config['learning_rate']),
            loss={
                'flow_prediction': 'mse',
                'uncertainty': 'mse',
                'alert_classification': 'sparse_categorical_crossentropy',
            },
            loss_weights={
                'flow_prediction': 1.0,
                'uncertainty': 0.1,
                'alert_classification': 0.5,
            },
            metrics={
                'flow_prediction': ['mae', 'mse'],
                'alert_classification': ['accuracy'],
            },
        )

        self.model = model
        return model

    def prepare_sequences(self, X: np.ndarray, y: np.ndarray) -> tuple:
        sequences_x, sequences_y = [], []
        for i in range(len(X) - self.config['input_steps'] - self.config['output_steps'] + 1):
            sequences_x.append(X[i:i + self.config['input_steps']])
            sequences_y.append(y[i + self.config['input_steps']:i + self.config['input_steps'] + self.config['output_steps']])
        return np.array(sequences_x), np.array(sequences_y)

    def train(self, X_train, y_train, X_val=None, y_val=None, callbacks=None):
        if self.model is None:
            self.build()

        X_seq, y_seq = self.prepare_sequences(X_train, y_train)
        validation_data = None
        if X_val is not None:
            X_val_seq, y_val_seq = self.prepare_sequences(X_val, y_val)
            validation_data = (X_val_seq, {
                'flow_prediction': y_val_seq,
                'uncertainty': y_val_seq * 0.1,
                'alert_classification': np.zeros((len(y_val_seq), self.config['output_steps'])),
            })

        import tensorflow as tf
        default_callbacks = [
            tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            tf.keras.callbacks.ModelCheckpoint('models/best_model.keras', monitor='val_loss', save_best_only=True),
        ]

        self.history = self.model.fit(
            X_seq,
            {
                'flow_prediction': y_seq,
                'uncertainty': y_seq * 0.1,
                'alert_classification': np.zeros((len(y_seq), self.config['output_steps'])),
            },
            validation_data=validation_data,
            epochs=self.config.get('epochs', 100),
            batch_size=self.config.get('batch_size', 32),
            callbacks=callbacks or default_callbacks,
            verbose=1,
        )

        return self.history

    def predict(self, X_input: np.ndarray) -> dict:
        if self.model is None:
            raise ValueError('Model not built or trained')

        X_seq = X_input.reshape(1, self.config['input_steps'], self.config['n_features'])
        flow, uncertainty, alert = self.model.predict(X_seq, verbose=0)

        alert_classes = ['green', 'yellow', 'orange', 'red']
        predicted_alert = alert_classes[int(np.argmax(alert[0][0]))]

        return {
            'flow_prediction': flow[0].tolist(),
            'uncertainty': uncertainty[0].tolist(),
            'confidence_interval': [
                (flow[0] - 1.96 * uncertainty[0]).tolist(),
                (flow[0] + 1.96 * uncertainty[0]).tolist(),
            ],
            'predicted_alert': predicted_alert,
            'alert_probabilities': alert[0][0].tolist(),
        }

    def summary(self) -> str:
        if self.model:
            string_list = []
            self.model.summary(print_fn=lambda x: string_list.append(x))
            return '\n'.join(string_list)
        return 'Model not built'
