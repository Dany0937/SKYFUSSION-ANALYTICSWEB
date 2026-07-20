---
title: Capa 3 — Agentes de Inteligencia Artificial
description: Agentes autónomos responsables de visión computacional, ML y generación de conocimiento.
order: 5
---

# Capa 3 – Agentes de Inteligencia Artificial

Esta capa contiene los agentes autónomos responsables de ejecutar procesos especializados relacionados con visión computacional, aprendizaje automático y generación automática de conocimiento. Cada agente posee una única responsabilidad y opera de manera independiente.

## Responsabilidades

- Procesar eventos
- Ejecutar algoritmos especializados
- Compartir resultados mediante el bus de eventos
- Mantener independencia funcional

## Tecnologías

| Tecnología | Propósito |
|------------|-----------|
| Python | Lenguaje de ejecución |
| TensorFlow | Modelos de deep learning |
| OpenCV | Visión computacional |
| RabbitMQ | Bus de eventos |

## Beneficios

- Alta escalabilidad
- Procesamiento distribuido
- Bajo acoplamiento
- Fácil incorporación de nuevos agentes

## Agentes

| Agente | Responsabilidad | Evento de Entrada | Evento de Salida |
|--------|----------------|-------------------|------------------|
| **GeospatialAgent** | Descarga de imágenes GEE | `analysis:requested` | `data:ingested` |
| **VisionAgent** | Procesamiento NDVI/NDWI + segmentación | `data:ingested` | `analysis:completed` |
| **OracleAgent** | Predicción LSTM-CNN + clasificación de alertas | `analysis:completed` | `prediction:completed` |
| **ReportingAgent** | Generación de reportes con LLM | `prediction:completed` | `report:ready` |
