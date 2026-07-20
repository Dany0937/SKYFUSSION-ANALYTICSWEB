---
title: Métricas en Tiempo Real
description: Endpoint para obtener métricas ambientales en tiempo real.
order: 2
---

# GET /api/v1/demo/metrics

Obtiene las métricas ambientales más recientes del sistema.

## Request

```http
GET /api/v1/demo/metrics
Authorization: Bearer <token>
```

## Response

```json
{
  "success": true,
  "data": {
    "ndvi": 0.75,
    "ndwi": 0.32,
    "temperature": 24.5,
    "humidity": 68,
    "precipitation": 12.4,
    "flow_rate": 45.2,
    "alert_level": "normal",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Códigos de Respuesta

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 401 | No autorizado |
| 500 | Error interno |
