---
title: Métricas de Éxito
description: Criterios de aceptación para modelos ML y calidad del sistema.
order: 5
---

# Métricas de Éxito

## Modelo LSTM-CNN

| Métrica | Objetivo | Método de Medición |
|---------|----------|-------------------|
| R² | > 0.80 | Comparación predicción vs observación |
| RMSE | < 0.15 | Error cuadrático medio normalizado |
| MAE | < 0.10 | Error absoluto medio |
| Precisión de alertas | > 85% | Matriz de confusión en validación |

## Calidad del Sistema

| Métrica | Objetivo |
|---------|----------|
| Disponibilidad API | > 99.5% |
| Latencia promedio API | < 200ms |
| Tiempo de procesamiento de imágenes | < 5 min por escena |
| Tiempo de generación de reportes | < 30 seg |

## Monitoreo

- **Prometheus** para métricas del sistema
- **Grafana** para dashboards visuales
- **Log Analytics** para logging centralizado (máx 2 GB/día)
- **Budget Alerts** en Azure para control de costos

## Cobertura de Pruebas

| Tipo | Cobertura Mínima |
|------|------------------|
| Unitarias (Node.js) | > 80% |
| Unitarias (Python) | > 75% |
| Integración API | > 90% de endpoints |
| E2E (flujo crítico) | 100% del flujo principal |
