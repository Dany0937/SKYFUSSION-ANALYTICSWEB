import numpy as np
from agents.python.base import BaseAgent, Event, get_logger

logger = get_logger('oracle_agent')


class OracleAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__('OracleAgent', config)
        self._input_event = 'analysis:completed'
        self.input_steps = config.get('input_steps', 72)
        self.output_steps = config.get('output_steps', 24)
        self.n_features = config.get('n_features', 7)
        self.model_path = config.get('model_path', 'models/lstm_cnn_hybrid.keras')
        self._model = None
        self._alert_system = None

    async def initialize(self) -> 'OracleAgent':
        await super().initialize()
        self._model = await self._load_model()
        self._alert_system = AlertSystem()
        logger.info(f'OracleAgent ready (input_steps={self.input_steps}, output_steps={self.output_steps})')
        return self

    async def _load_model(self):
        try:
            import tensorflow as tf
            if tf.io.gfile.exists(self.model_path):
                model = tf.keras.models.load_model(self.model_path)
                logger.info(f'Model loaded from {self.model_path}')
                return model
        except Exception as e:
            logger.warning(f'Could not load TensorFlow model: {e}. Using mock predictor.')
        return None

    async def handle_event(self, event: Event):
        payload = event.payload
        request_id = payload.get('request_id', '')
        analysis_results = payload.get('results', [])

        logger.info(f'Running prediction for request {request_id}')

        features = self._extract_features(analysis_results)
        features_seq = self._prepare_sequence(features)

        if self._model:
            result = await self._predict_with_model(features_seq)
        else:
            result = self._predict_mock(features_seq)

        alert = self._alert_system.classify_alert(
            ndvi=result.get('ndvi_mean', 0.5),
            current_flow=result.get('flow_prediction', [0])[-1],
            historical_flow_mean=result.get('historical_flow_mean', 10.0),
            precipitation_24h=result.get('precipitation_24h', 5.0),
        )

        result['alert'] = alert
        result['request_id'] = request_id

        await self.emit('prediction:completed', result)
        logger.info(f'Prediction completed for request {request_id}')

    def _extract_features(self, results: list) -> np.ndarray:
        if not results:
            return np.zeros(self.n_features)

        ndvi_values = []
        ndwi_values = []
        for r in results:
            if 'indices' in r:
                if 'NDVI' in r['indices']:
                    ndvi_values.append(r['indices']['NDVI']['mean'])
                if 'NDWI' in r['indices']:
                    ndwi_values.append(r['indices']['NDWI']['mean'])

        return np.array([
            np.mean(ndvi_values) if ndvi_values else 0.5,
            np.mean(ndwi_values) if ndwi_values else 0.0,
            np.random.uniform(0, 50),  # caudal mock
            np.random.uniform(0, 30),  # precipitacion mock
            np.random.uniform(15, 30),  # temperatura mock
            np.random.uniform(40, 100),  # humedad mock
            np.random.uniform(0, 5),  # evapotranspiracion mock
        ])

    def _prepare_sequence(self, features: np.ndarray) -> np.ndarray:
        seq = np.tile(features, (self.input_steps, 1))
        seq += np.random.randn(self.input_steps, self.n_features) * 0.01
        return seq.reshape(1, self.input_steps, self.n_features)

    async def _predict_with_model(self, features_seq: np.ndarray) -> dict:
        import tensorflow as tf
        flow, uncertainty, alert_probs = self._model.predict(features_seq, verbose=0)

        return {
            'flow_prediction': flow[0].tolist(),
            'uncertainty': uncertainty[0].tolist(),
            'confidence_interval': [
                (flow[0] - 1.96 * uncertainty[0]).tolist(),
                (flow[0] + 1.96 * uncertainty[0]).tolist(),
            ],
            'alert_probabilities': alert_probs[0].tolist(),
            'ndvi_mean': float(features_seq[0, -1, 0]),
            'historical_flow_mean': 10.0,
            'precipitation_24h': float(features_seq[0, -1, 2]),
            'model_type': 'lstm_cnn_hybrid',
        }

    def _predict_mock(self, features_seq: np.ndarray) -> dict:
        base = features_seq[0, -1, 2]  # approximate flow from features
        predictions = [float(base + np.random.randn() * 2) for _ in range(self.output_steps)]
        uncertainty = [float(abs(np.random.randn()) * 0.5) for _ in range(self.output_steps)]

        return {
            'flow_prediction': predictions,
            'uncertainty': uncertainty,
            'confidence_interval': [
                [predictions[i] - 1.96 * uncertainty[i] for i in range(self.output_steps)],
                [predictions[i] + 1.96 * uncertainty[i] for i in range(self.output_steps)],
            ],
            'alert_probabilities': [0.7, 0.2, 0.08, 0.02],
            'ndvi_mean': float(features_seq[0, -1, 0]),
            'historical_flow_mean': 12.5,
            'precipitation_24h': float(features_seq[0, -1, 3]),
            'model_type': 'mock_lstm_cnn',
        }

    async def shutdown(self):
        await super().shutdown()


class AlertSystem:
    ALERT_THRESHOLDS = {
        'ndvi': {'green': 0.6, 'yellow': 0.3, 'orange': 0.2, 'red': 0.0},
        'flow_change': {'green': 0.1, 'yellow': 0.2, 'orange': 0.3, 'red': 0.5},
        'precipitation': {'green': (5, 100), 'yellow': (2, 5), 'orange': (0, 2), 'red': (0, 0.5)},
    }

    def classify_alert(
        self, ndvi: float, current_flow: float,
        historical_flow_mean: float, precipitation_24h: float,
    ) -> dict:
        scores = {
            'ndvi_score': self._score_ndvi(ndvi),
            'flow_score': self._score_flow_change(current_flow, historical_flow_mean),
            'precipitation_score': self._score_precipitation(precipitation_24h),
        }
        weights = {'ndvi_score': 0.4, 'flow_score': 0.35, 'precipitation_score': 0.25}
        total_score = sum(scores[k] * weights[k] for k in scores)

        if total_score >= 0.75:
            level = 'green'
        elif total_score >= 0.5:
            level = 'yellow'
        elif total_score >= 0.25:
            level = 'orange'
        else:
            level = 'red'

        return {
            'level': level,
            'score': round(total_score, 3),
            'component_scores': {k: round(v, 3) for k, v in scores.items()},
            'message': self._generate_message(level),
            'recommended_actions': self._get_recommended_actions(level),
        }

    def _score_ndvi(self, ndvi: float) -> float:
        t = self.ALERT_THRESHOLDS['ndvi']
        if ndvi >= t['green']: return 1.0
        if ndvi >= t['yellow']: return 0.75
        if ndvi >= t['orange']: return 0.5
        if ndvi >= t['red']: return 0.25
        return 0.0

    def _score_flow_change(self, current: float, historical: float) -> float:
        if historical == 0: return 0.5
        change = (current - historical) / historical
        t = self.ALERT_THRESHOLDS['flow_change']
        if change > t['green']: return 1.0
        if change > -t['yellow']: return 0.75
        if change > -t['orange']: return 0.5
        if change > -t['red']: return 0.25
        return 0.0

    def _score_precipitation(self, precip: float) -> float:
        t = self.ALERT_THRESHOLDS['precipitation']
        if t['green'][0] <= precip <= t['green'][1]: return 1.0
        if t['yellow'][0] <= precip < t['yellow'][1]: return 0.6
        if t['orange'][0] <= precip < t['orange'][1]: return 0.3
        return 0.0

    def _generate_message(self, level: str) -> str:
        messages = {
            'green': 'Condiciones normales. El sistema hídrico opera dentro de parámetros esperados.',
            'yellow': 'Vigilancia recomendada. Se observan desviaciones moderadas que requieren monitoreo.',
            'orange': 'Alerta activa. Condiciones adversas podrían escalar si continúan.',
            'red': 'EMERGENCIA hídrica. Intervención inmediata recomendada.',
        }
        return messages[level]

    def _get_recommended_actions(self, level: str) -> list:
        actions = {
            'green': ['Continuar monitoreo rutinario', 'Reporte mensual standard'],
            'yellow': ['Aumentar frecuencia de monitoreo', 'Notificar a equipo técnico', 'Revisar predicciones a 7 días'],
            'orange': ['Emitir notificación a entidades', 'Activar plan de contingencia', 'Evaluar restricciones de uso'],
            'red': ['ACTIVAR PROTOCOLO DE EMERGENCIA', 'Notificar inmediatamente a Alcaldía', 'Coordinar con Defensa Civil', 'Emitir alerta pública'],
        }
        return actions[level]
