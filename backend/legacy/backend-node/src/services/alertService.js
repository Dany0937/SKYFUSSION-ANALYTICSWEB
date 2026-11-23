import { v4 as uuidv4 } from 'uuid';
import { createLogger } from '../utils/logger.js';
import { eventBus, EVENTS } from './eventBus.js';

const logger = createLogger('services:alert');

const ALERT_THRESHOLDS = {
  ndvi: { green: 0.6, yellow: 0.3, orange: 0.2, red: 0.0 },
  flowChange: { green: 0.1, yellow: 0.2, orange: 0.3, red: 0.5 },
  caudal: { min: 0.5, max: 50 },
  temperatura: { min: -5, max: 45 }
};

const ALERT_MESSAGES = {
  green: 'Condiciones normales. El sistema hídrico opera dentro de parámetros esperados.',
  yellow: 'Vigilancia recomendada. Se observan desviaciones moderadas que requieren monitoreo.',
  orange: 'Alerta activa. Condiciones adversas podrían escalar si continúan.',
  red: 'EMERGENCIA hídrica. Intervención inmediata recomendada.'
};

const RECOMMENDED_ACTIONS = {
  green: ['Continuar monitoreo rutinario', 'Reporte mensual standard'],
  yellow: ['Aumentar frecuencia de monitoreo', 'Notificar a equipo técnico'],
  orange: ['Emitir notificación a entidades', 'Activar plan de contingencia'],
  red: ['ACTIVAR PROTOCOLO DE EMERGENCIA', 'Notificar inmediatamente a Alcaldía']
};

export class AlertService {
  constructor() {
    this.activeAlerts = new Map();
    this.alertHistory = [];
    this.maxHistorySize = 1000;
  }

  classifyAlert(data) {
    const { ndvi, currentFlow, historicalFlowMean, precipitacion24h } = data;

    const scores = {
      ndviScore: this.scoreNdvi(ndvi),
      flowScore: this.scoreFlowChange(currentFlow, historicalFlowMean),
      precipitationScore: this.scorePrecipitacion(precipitacion24h)
    };

    const weights = { ndviScore: 0.4, flowScore: 0.35, precipitationScore: 0.25 };
    const totalScore = Object.keys(scores).reduce(
      (sum, key) => sum + scores[key] * weights[key],
      0
    );

    let level = 'green';
    if (totalScore < 0.25) level = 'red';
    else if (totalScore < 0.5) level = 'orange';
    else if (totalScore < 0.75) level = 'yellow';

    return {
      level,
      score: Math.round(totalScore * 1000) / 1000,
      componentScores: Object.fromEntries(
        Object.entries(scores).map(([k, v]) => [k, Math.round(v * 1000) / 1000])
      ),
      message: ALERT_MESSAGES[level],
      recommendedActions: RECOMMENDED_ACTIONS[level]
    };
  }

  scoreNdvi(ndvi) {
    if (ndvi >= ALERT_THRESHOLDS.ndvi.green) return 1.0;
    if (ndvi >= ALERT_THRESHOLDS.ndvi.yellow) return 0.75;
    if (ndvi >= ALERT_THRESHOLDS.ndvi.orange) return 0.5;
    if (ndvi >= ALERT_THRESHOLDS.ndvi.red) return 0.25;
    return 0.0;
  }

  scoreFlowChange(current, historical) {
    if (!historical) return 0.5;
    const changeRatio = Math.abs((current - historical) / historical);
    const thresholds = ALERT_THRESHOLDS.flowChange;

    if (changeRatio <= thresholds.green) return 1.0;
    if (changeRatio <= thresholds.yellow) return 0.75;
    if (changeRatio <= thresholds.orange) return 0.5;
    if (changeRatio <= thresholds.red) return 0.25;
    return 0.0;
  }

  scorePrecipitacion(precip24h) {
    if (precip24h >= 5 && precip24h <= 100) return 1.0;
    if (precip24h >= 2 && precip24h < 5) return 0.6;
    if (precip24h >= 0.5 && precip24h < 2) return 0.3;
    return 0.0;
  }

  generateAlert(zoneId, classification, metadata = {}) {
    const alert = {
      id: uuidv4(),
      zoneId,
      level: classification.level,
      score: classification.score,
      message: classification.message,
      componentScores: classification.componentScores,
      recommendedActions: classification.recommendedActions,
      timestamp: new Date().toISOString(),
      acknowledged: false,
      metadata
    };

    this.activeAlerts.set(alert.id, alert);
    this.alertHistory.push(alert);

    if (this.alertHistory.length > this.maxHistorySize) {
      this.alertHistory = this.alertHistory.slice(-this.maxHistorySize);
    }

    eventBus.emit(EVENTS.ALERT_GENERATED, alert);

    if (alert.level === 'red' || alert.level === 'orange') {
      logger.warn('Critical alert generated', {
        alertId: alert.id,
        level: alert.level,
        zoneId
      });
    }

    return alert;
  }

  getActiveAlerts(zoneId = null) {
    const alerts = Array.from(this.activeAlerts.values());
    
    if (zoneId) {
      return alerts.filter(a => a.zoneId === zoneId);
    }
    
    return alerts.sort((a, b) => {
      const priority = { red: 0, orange: 1, yellow: 2, green: 3 };
      return priority[a.level] - priority[b.level];
    });
  }

  getAlertHistory(options = {}) {
    let history = [...this.alertHistory];

    if (options.zoneId) {
      history = history.filter(a => a.zoneId === options.zoneId);
    }

    if (options.level) {
      history = history.filter(a => a.level === options.level);
    }

    if (options.since) {
      history = history.filter(a => a.timestamp >= options.since);
    }

    if (options.until) {
      history = history.filter(a => a.timestamp <= options.until);
    }

    return history.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  }

  acknowledgeAlert(alertId) {
    const alert = this.activeAlerts.get(alertId);
    
    if (!alert) {
      return null;
    }

    alert.acknowledged = true;
    alert.acknowledgedAt = new Date().toISOString();
    
    return alert;
  }

  resolveAlert(alertId) {
    return this.activeAlerts.delete(alertId);
  }

  checkThresholds(sensorType, value) {
    const thresholds = {
      caudal: ALERT_THRESHOLDS.caudal,
      temperatura: ALERT_THRESHOLDS.temperatura
    };

    const t = thresholds[sensorType];
    if (!t) return null;

    const isOutOfRange = value < t.min || value > t.max;
    
    if (isOutOfRange) {
      return {
        type: 'threshold_exceeded',
        sensorType,
        value,
        min: t.min,
        max: t.max,
        direction: value < t.min ? 'below' : 'above'
      };
    }

    return null;
  }
}

export const alertService = new AlertService();
