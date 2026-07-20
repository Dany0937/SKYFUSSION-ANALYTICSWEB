---
title: Capa 0 — Infraestructura
description: Base tecnológica sobre la que funciona toda la solución — contenedores, redes, persistencia y cloud.
order: 2
---

# Capa 0 – Infraestructura

Es la base tecnológica sobre la que funciona toda la solución. Proporciona los recursos de ejecución, almacenamiento y despliegue.

## Responsabilidades

- Contenedores Docker
- Redes
- Persistencia
- Balanceo
- Infraestructura Cloud
- Automatización del despliegue

## Tecnologías

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Docker | 24+ | Contenedores |
| Docker Compose | 2.x | Orquestación local |
| Azure | — | Infraestructura cloud |
| GitHub Actions | — | CI/CD |

## Componentes

### Docker

Contenedor de ejecución de todos los servicios.

**Beneficios:**
- Reproducibilidad
- Portabilidad
- Escalabilidad
- Aislamiento de servicios

### Nginx Proxy

Puerta de entrada de la plataforma.

**Funciones:**
- HTTPS
- Balanceador de carga
- Reverse Proxy
- Seguridad
- Redirección de solicitudes

### Azure Blob Storage

Repositorio central para el almacenamiento de archivos.

**Contenido:**
- Imágenes Sentinel
- Imágenes Landsat
- GeoTIFF
- Resultados de análisis
- Reportes generados

### PostgreSQL + PostGIS

Base de datos relacional con soporte geoespacial.

**Utilización:**
- Información vectorial
- Consultas espaciales
- Geometrías
- Capas GIS

### Neo4j

Base de datos orientada a grafos.

**Utilización:**
- Relaciones entre cuencas
- Redes hidrográficas
- Estaciones meteorológicas
- Dependencias espaciales
