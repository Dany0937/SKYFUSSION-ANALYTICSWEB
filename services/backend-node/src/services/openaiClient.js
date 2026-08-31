import OpenAI from 'openai';
import { createLogger } from '../utils/logger.js';
import config from '../config/externalApis.js';

const logger = createLogger('services:openai');

export class OpenAIClient {
  constructor() {
    this.client = null;
    this.initialized = false;
  }

  initialize() {
    if (this.initialized) return;

    if (!config.openai.apiKey || config.openai.apiKey === 'sk-your_openai_api_key_here') {
      logger.warn('OpenAI API key not configured, using mock mode');
      this.mockMode = true;
      this.initialized = true;
      return;
    }

    this.client = new OpenAI({
      apiKey: config.openai.apiKey,
      timeout: config.openai.timeout,
      maxRetries: config.openai.maxRetries
    });

    this.mockMode = false;
    this.initialized = true;
    logger.info('OpenAI client initialized', { model: config.openai.model });
  }

  async analyzeReport(data) {
    this.ensureInitialized();

    if (this.mockMode) {
      return this.mockAnalysis(data);
    }

    try {
      const prompt = this.buildReportPrompt(data);

      const response = await this.client.chat.completions.create({
        model: config.openai.model,
        messages: [
          {
            role: 'system',
            content: `Eres un hidrólogo experto en análisis de recursos hídricos y cambio climático en Colombia. 
Debes generar reportes técnicos basados en datos de sensores remotos, mediciones de caudal, y análisis espectral.
Responde SIEMPRE en español con terminología técnica precisa.
Estructura tus respuestas usando la jerarquía de alertas: verde (normal), amarillo (vigilancia), naranja (alerta), rojo (emergencia).`
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: config.openai.temperature,
        max_tokens: config.openai.maxTokens,
        response_format: { type: 'json_object' }
      });

      const content = response.choices[0]?.message?.content;
      if (!content) throw new Error('Empty response from OpenAI');

      return JSON.parse(content);
    } catch (error) {
      logger.error('OpenAI analysis failed', { error: error.message });
      throw error;
    }
  }

  async generateRecommendations(analysisResults) {
    this.ensureInitialized();

    if (this.mockMode) {
      return this.mockRecommendations(analysisResults);
    }

    try {
      const response = await this.client.chat.completions.create({
        model: config.openai.model,
        messages: [
          {
            role: 'system',
            content: 'Eres un asesor en gestión de recursos hídricos. Genera recomendaciones accionables basadas en datos de monitoreo.'
          },
          {
            role: 'user',
            content: `Basado en el siguiente análisis, genera recomendaciones técnicas y de gestión:\n\n${JSON.stringify(analysisResults, null, 2)}`
          }
        ],
        temperature: 0.3,
        max_tokens: 2048,
        response_format: { type: 'json_object' }
      });

      const content = response.choices[0]?.message?.content;
      if (!content) throw new Error('Empty response from OpenAI');

      return JSON.parse(content);
    } catch (error) {
      logger.error('OpenAI recommendations failed', { error: error.message });
      throw error;
    }
  }

  async classifyAlert(ndviValues, flowData, precipitationData) {
    this.ensureInitialized();

    if (this.mockMode) {
      return this.mockAlertClassification(ndviValues, flowData, precipitationData);
    }

    try {
      const response = await this.client.chat.completions.create({
        model: config.openai.model,
        messages: [
          {
            role: 'system',
            content: 'Clasifica alertas hídricas en verde/amarillo/naranja/rojo basado en datos multivaribles.'
          },
          {
            role: 'user',
            content: JSON.stringify({
              ndvi: ndviValues,
              caudal: flowData,
              precipitacion: precipitationData
            })
          }
        ],
        temperature: 0.1,
        max_tokens: 1024,
        response_format: { type: 'json_object' }
      });

      const content = response.choices[0]?.message?.content;
      return content ? JSON.parse(content) : this.mockAlertClassification(ndviValues, flowData, precipitationData);
    } catch (error) {
      logger.error('OpenAI alert classification failed', { error: error.message });
      return this.mockAlertClassification(ndviValues, flowData, precipitationData);
    }
  }

  buildReportPrompt(data) {
    return `Genera un reporte técnico de recursos hídricos con los siguientes datos:

Zona de estudio: ${data.zoneName || 'No especificada'}
Período de análisis: ${data.period || 'No especificado'}
Índices espectrales: ${JSON.stringify(data.indices || {})}
Mediciones de caudal: ${JSON.stringify(data.measurements || [])}
Alertas activas: ${JSON.stringify(data.activeAlerts || [])}
Análisis histórico: ${JSON.stringify(data.historicalAnalysis || {})}

Formato de respuesta JSON requerido:
{
  "resumen_ejecutivo": "string",
  "analisis_tecnico": {
    "indices_espectrales": "string",
    "caudal": "string",
    "tendencia": "string"
  },
  "nivel_alerta": "verde|amarillo|naranja|rojo",
  "recomendaciones": ["string"],
  "metricas_clave": {
    "ndvi_promedio": "number",
    "caudal_promedio": "number",
    "tendencia_mensual": "string"
  }
}`;
  }

  mockAnalysis(data) {
    logger.info('Mock analysis report generated');
    return {
      resumen_ejecutivo: 'Análisis preliminar de recursos hídricos',
      analisis_tecnico: {
        indices_espectrales: 'NDVI within expected range for the region',
        caudal: 'Flow rates show seasonal variation',
        tendencia: 'Stable tendency with minor variations'
      },
      nivel_alerta: 'verde',
      recomendaciones: ['Continuar monitoreo rutinario', 'Actualizar estaciones de medición'],
      metricas_clave: {
        ndvi_promedio: data.indices?.ndvi?.mean || 0.5,
        caudal_promedio: 15.2,
        tendencia_mensual: 'Estable'
      }
    };
  }

  mockRecommendations(analysisResults) {
    return {
      acciones_inmediatas: ['Verificar instrumentación en campo', 'Revisar series históricas'],
      acciones_mediano_plazo: ['Actualizar modelo hidrológico', 'Ampliar red de monitoreo'],
      prioridad: 'media',
      impacto_estimado: 'Reducción de incertidumbre en 30%'
    };
  }

  mockAlertClassification(ndviValues, flowData, precipitationData) {
    const ndvi = ndviValues?.mean || ndviValues?.ndvi || 0.5;
    let level = 'verde';
    if (ndvi < 0.2) level = 'rojo';
    else if (ndvi < 0.3) level = 'naranja';
    else if (ndvi < 0.4) level = 'amarillo';

    return {
      nivel_alerta: level,
      confianza: 0.85,
      factores_contribuyentes: ['Análisis basado en datos espectrales'],
      recomendacion: 'Monitoreo continuo recomendado'
    };
  }

  ensureInitialized() {
    if (!this.initialized) {
      this.initialize();
    }
  }
}

export const openAIClient = new OpenAIClient();
export default openAIClient;
