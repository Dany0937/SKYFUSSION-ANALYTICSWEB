from agents.python.base import BaseAgent, Event, get_logger

logger = get_logger('reporting_agent')


class ReportingAgent(BaseAgent):
    def __init__(self, config: dict):
        super().__init__('ReportingAgent', config)
        self._input_event = 'prediction:completed'
        self._llm_provider = config.get('llm_provider', 'local')
        self._template_path = config.get('template_path', 'templates')
        self._llm_client = None

    async def initialize(self) -> 'ReportingAgent':
        await super().initialize()
        self._llm_client = await self._init_llm()
        logger.info(f'ReportingAgent ready (provider: {self._llm_provider})')
        return self

    async def _init_llm(self):
        match self._llm_provider:
            case 'azure_openai':
                return AzureOpenAIClient(self.config.get('azure_openai', {}))
            case 'anthropic':
                return AnthropicClient(self.config.get('anthropic', {}))
            case 'local':
                return LocalLLMClient(self.config.get('local_llm', {}))
            case _:
                return MockLLMClient()

    async def handle_event(self, event: Event):
        payload = event.payload
        request_id = payload.get('request_id', '')
        flow_prediction = payload.get('flow_prediction', [])
        alert = payload.get('alert', {})
        ndvi_mean = payload.get('ndvi_mean', 0)
        confidence_interval = payload.get('confidence_interval', [[], []])
        model_type = payload.get('model_type', 'unknown')

        logger.info(f'Generating report for request {request_id}')

        report_sections = await asyncio_gather_safe([
            self._generate_executive_summary(payload),
            self._generate_technical_analysis(payload),
            self._generate_predictions_section(payload),
            self._generate_alert_section(payload),
            self._generate_recommendations(payload),
        ])

        report = {
            'request_id': request_id,
            'generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            'title': f'Reporte Ambiental - Cuenca Combeima - {__import__("datetime").datetime.utcnow().strftime("%Y-%m-%d")}',
            'sections': {
                'executive_summary': report_sections[0],
                'technical_analysis': report_sections[1],
                'predictions': report_sections[2],
                'alert_status': report_sections[3],
                'recommendations': report_sections[4],
            },
            'raw_data': {
                'flow_prediction': flow_prediction[:10],
                'confidence_interval': {
                    'lower': confidence_interval[0][:10] if confidence_interval else [],
                    'upper': confidence_interval[1][:10] if confidence_interval else [],
                },
                'ndvi_mean': ndvi_mean,
                'alert_level': alert.get('level', 'green'),
                'model_type': model_type,
            },
        }

        report['narrative'] = await self._llm_client.generate_narrative(report)

        await self.emit('report:ready', report)
        logger.info(f'Report generated for request {request_id}')

    async def _generate_executive_summary(self, payload: dict) -> dict:
        alert = payload.get('alert', {})
        level = alert.get('level', 'green')
        ndvi = payload.get('ndvi_mean', 0)

        summary = {
            'title': 'Resumen Ejecutivo',
            'alert_level': level,
            'ndvi_status': self._describe_ndvi(ndvi),
            'risk_assessment': self._assess_risk(level),
        }

        context = {
            'alert_level': level,
            'ndvi': round(ndvi, 3),
            'ndvi_description': summary['ndvi_status'],
            'risk': summary['risk_assessment'],
        }
        summary['generated_text'] = await self._llm_client.generate('executive_summary', context)
        return summary

    def _describe_ndvi(self, ndvi: float) -> str:
        if ndvi >= 0.6: return 'Saludable'
        if ndvi >= 0.3: return 'Moderado'
        if ndvi >= 0.1: return 'Bajo'
        return 'Crítico'

    def _assess_risk(self, level: str) -> str:
        match level:
            case 'green': return 'Bajo - Condiciones normales'
            case 'yellow': return 'Moderado - Monitoreo requerido'
            case 'orange': return 'Alto - Acción necesaria'
            case 'red': return 'Crítico - Emergencia'
            case _: return 'Desconocido'

    async def _generate_technical_analysis(self, payload: dict) -> dict:
        ndvi = payload.get('ndvi_mean', 0)
        alert_scores = payload.get('alert', {}).get('component_scores', {})

        return {
            'title': 'Análisis Técnico',
            'ndvi_analysis': {
                'mean_value': round(ndvi, 4),
                'interpretation': self._describe_ndvi(ndvi),
                'recommendation': 'Monitoreo continuo' if ndvi > 0.3 else 'Intervención recomendada',
            },
            'component_scores': alert_scores,
        }

    async def _generate_predictions_section(self, payload: dict) -> dict:
        flow = payload.get('flow_prediction', [])
        ci = payload.get('confidence_interval', [[], []])

        return {
            'title': 'Predicciones de Caudal',
            'horizon_hours': len(flow),
            'prediction_summary': {
                'min': round(min(flow), 2) if flow else 0,
                'max': round(max(flow), 2) if flow else 0,
                'mean': round(sum(flow) / len(flow), 2) if flow else 0,
            },
            'confidence_bounds': {
                'lower_min': min(ci[0]) if ci and ci[0] else 0,
                'upper_max': max(ci[1]) if ci and len(ci) > 1 and ci[1] else 0,
            },
        }

    async def _generate_alert_section(self, payload: dict) -> dict:
        alert = payload.get('alert', {})
        return {
            'title': 'Estado de Alertas',
            'current_level': alert.get('level', 'green'),
            'score': alert.get('score', 1.0),
            'message': alert.get('message', ''),
            'recommended_actions': alert.get('recommended_actions', []),
        }

    async def _generate_recommendations(self, payload: dict) -> dict:
        alert = payload.get('alert', {})
        level = alert.get('level', 'green')
        ndvi = payload.get('ndvi_mean', 0)

        recommendations = []

        if ndvi < 0.3:
            recommendations.append({
                'priority': 'ALTA',
                'area': 'Cobertura Vegetal',
                'action': 'Implementar programa de reforestación en zonas críticas',
                'timeline': 'Corto plazo (1-3 meses)',
            })

        if level in ('orange', 'red'):
            recommendations.append({
                'priority': 'URGENTE',
                'area': 'Gestión Hídrica',
                'action': 'Activar protocolo de racionamiento y restricción de uso',
                'timeline': 'Inmediato',
            })
            recommendations.append({
                'priority': 'ALTA',
                'area': 'Comunicación',
                'action': 'Emitir alerta a comunidad y entidades gubernamentales',
                'timeline': 'Inmediato',
            })

        if level == 'yellow':
            recommendations.append({
                'priority': 'MEDIA',
                'area': 'Monitoreo',
                'action': 'Aumentar frecuencia de monitoreo a diario',
                'timeline': 'Esta semana',
            })

        recommendations.append({
            'priority': 'BAJA',
            'area': 'Prevención',
            'action': 'Actualizar modelos predictivos con datos recientes',
            'timeline': 'Mensual',
        })

        return {
            'title': 'Recomendaciones',
            'items': recommendations,
        }


class AzureOpenAIClient:
    def __init__(self, config: dict):
        self.api_key = config.get('api_key', '')
        self.endpoint = config.get('endpoint', '')
        self.deployment = config.get('deployment', 'gpt-4')
        self.api_version = config.get('api_version', '2024-02-15-preview')
        self._client = None

    async def generate(self, template: str, context: dict) -> str:
        return f'[Azure OpenAI - {self.deployment}] Report generated with context: {context}'

    async def generate_narrative(self, report: dict) -> str:
        return (
            f'Basado en el análisis multitemporal de la cuenca del río Combeima, '
            f'se observa un nivel de alerta {report["raw_data"]["alert_level"]} con '
            f'un NDVI promedio de {report["raw_data"]["ndvi_mean"]:.3f}. '
            f'Las predicciones de caudal para las próximas {report["sections"]["predictions"]["horizon_hours"]} horas '
            f'indican un flujo promedio de {report["sections"]["predictions"]["prediction_summary"]["mean"]} m³/s. '
            f'Se recomienda seguir las acciones detalladas en el reporte.'
        )


class AnthropicClient:
    def __init__(self, config: dict):
        self.api_key = config.get('api_key', '')

    async def generate(self, template: str, context: dict) -> str:
        return f'[Anthropic Claude] Analysis for {template}: {context}'

    async def generate_narrative(self, report: dict) -> str:
        return (
            f'Análisis detallado de la cuenca del Combeima. '
            f'Nivel de alerta: {report["raw_data"]["alert_level"].upper()}. '
            f'NDVI: {report["raw_data"]["ndvi_mean"]:.3f}. '
            f'Se requieren acciones basadas en las predicciones del modelo {report["raw_data"]["model_type"]}.'
        )


class LocalLLMClient:
    def __init__(self, config: dict):
        self.model = config.get('model', 'llama3.2')
        self.endpoint = config.get('endpoint', 'http://localhost:11434')

    async def generate(self, template: str, context: dict) -> str:
        return f'[Local LLM - {self.model}] Generated {template}'

    async def generate_narrative(self, report: dict) -> str:
        return (
            f'Reporte generado localmente para la cuenca del Combeima. '
            f'Nivel de alerta: {report["raw_data"]["alert_level"]}. '
            f'Caudal promedio predicho: {report["sections"]["predictions"]["prediction_summary"]["mean"]} m³/s.'
        )


class MockLLMClient:
    async def generate(self, template: str, context: dict) -> str:
        return f'[MOCK] {template}: condiciones normales'

    async def generate_narrative(self, report: dict) -> str:
        alert = report['raw_data']['alert_level'].upper()
        ndvi = report['raw_data']['ndvi_mean']
        return (
            f'REPORTE AMBIENTAL - CUENCA COMBEIMA\n'
            f'=============================\n'
            f'Nivel de Alerta: {alert}\n'
            f'NDVI Promedio: {ndvi:.3f}\n'
            f'Estado: El sistema hídrico presenta condiciones acordes a la temporada.\n'
            f'Acción Recomendada: Continuar con monitoreo estándar.'
        )


async def asyncio_gather_safe(coros):
    import asyncio
    return await asyncio.gather(*coros, return_exceptions=True)
