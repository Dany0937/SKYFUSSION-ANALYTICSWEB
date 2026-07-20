---
title: Prácticas para el Desarrollo de Capas
description: Reglas de bajo acoplamiento, comunicación vertical y versiones fijadas.
order: 3
---

# Prácticas para el Desarrollo de Capas

## Bajo Acoplamiento

**Regla:** Una capa solo se comunica con la capa adyacente.

- La Capa 5 (Presentación) solo habla con la Capa 4 (Backend API)
- La Capa 4 solo habla con Capa 5 y Capa 3 (Agentes IA)
- La Capa 3 solo habla con Capa 4 y Capa 2 (Geoespacial)

Ninguna capa debe saltarse niveles intermedios.

## Comunicación Vertical Estricta

```
Capa 5 ←→ Capa 4 ←→ Capa 3 ←→ Capa 2 ←→ Capa 1 ←→ Capa 0
```

Cada capa expone una interfaz bien definida. Los cambios en una capa no deben afectar a las no adyacentes.

## Versiones Fijadas

Es obligatorio usar las versiones técnicas establecidas para evitar conflictos en el despliegue:

| Componente | Versión |
|------------|---------|
| Python | 3.10 |
| GDAL | 3.6.2 |
| Rasterio | 1.3.8 |
| Node.js | 20.x LTS |
| PostgreSQL | 16 |
| Neo4j | 5.18 |
| RabbitMQ | 3.13 |
| TensorFlow | 2.15+ |

## Pruebas por Capa

Cada capa debe tener pruebas unitarias que validen su interfaz sin depender de implementaciones concretas de otras capas. Usar mocks para las dependencias externas.
