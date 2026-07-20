---
title: Despliegue en Azure
description: Infraestructura cloud, componentes Azure y estrategias de despliegue.
order: 3
---

# Despliegue en Azure

La infraestructura está diseñada para ejecutarse completamente sobre Microsoft Azure utilizando contenedores Docker.

## Componentes Azure

| Componente | Propósito |
|------------|-----------|
| **Azure Virtual Machine (GPU Series)** | Servidor principal con aceleración GPU para entrenar modelos IA y procesamiento geoespacial |
| **Azure Blob Storage** | Repositorio de imágenes satelitales, GeoTIFF, resultados y reportes |
| **Azure OpenAI Service** | Generación inteligente de reportes (alternativa a Ollama local) |
| **Container Registry** | Almacenamiento de imágenes Docker |

## Azure VM (GPU Series)

Servidor principal encargado de alojar los contenedores de la plataforma.

**Funciones:**
- Ejecutar Docker
- Proveer aceleración mediante GPU (NVIDIA V100)
- Entrenar modelos de IA
- Ejecutar procesamiento geoespacial

## Optimización de Costos

El plan de optimización reduce el costo de ~$7,200/mes a ~$2,200-$2,800/mes mediante:

1. **Spot Instances** para GPU (ahorro ~$2,130/mes)
2. **Local LLM (Ollama)** en lugar de Azure OpenAI (ahorro ~$3,000/mes)
3. **PostgreSQL unificado** en lugar de Neo4j + PostgreSQL (ahorro ~$595/mes)
4. **Azure Functions** para backend ligero (ahorro ~$120/mes)
5. **ML Compute Cluster** con auto-scale (ahorro ~$238/mes)
6. **Storage tiering** con lifecycle management (ahorro ~$40/mes)
