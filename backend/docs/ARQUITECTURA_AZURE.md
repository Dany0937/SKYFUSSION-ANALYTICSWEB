
# Arquitectura de Software y Despliegue en Azure

**Versión:** 1.0
**Tipo de Arquitectura:** Híbrida (Layered + Event-Driven)

---

# 1. Arquitectura de Software (Enfoque Híbrido)

El sistema implementa una **Arquitectura Híbrida** que combina dos estilos arquitectónicos:

- **Arquitectura por Capas (Layered Architecture)** para organizar la lógica de negocio, procesamiento y presentación.
- **Arquitectura Orientada a Eventos (Event-Driven Architecture)** para permitir la comunicación asíncrona entre agentes inteligentes especializados.

Esta combinación proporciona una solución modular, escalable y desacoplada, facilitando el procesamiento distribuido de imágenes satelitales, análisis mediante inteligencia artificial y generación automática de reportes.

---

# 1.1 Arquitectura de 6 Capas

La aplicación está organizada en seis niveles de abstracción donde el flujo de información asciende desde la infraestructura hasta la interfaz del usuario.

```text
┌─────────────────────────────────────────────┐
│ Capa 5 - Presentación (React)               │
├─────────────────────────────────────────────┤
│ Capa 4 - Backend API (Node.js + Express)    │
├─────────────────────────────────────────────┤
│ Capa 3 - Agentes IA / ML                    │
├─────────────────────────────────────────────┤
│ Capa 2 - Procesamiento Geoespacial          │
├─────────────────────────────────────────────┤
│ Capa 1 - Adquisición de Datos (GEE)         │
├─────────────────────────────────────────────┤
│ Capa 0 - Infraestructura                    │
└─────────────────────────────────────────────┘
```
# Explicación de la Arquitectura de Software

## 1. Explicación de las Capas de la Arquitectura

La plataforma implementa una **Arquitectura Híbrida** basada en un modelo de **seis capas**, donde cada nivel tiene responsabilidades específicas y una comunicación claramente definida. Esta organización facilita el mantenimiento, la escalabilidad y la evolución del sistema, permitiendo que cada componente pueda desarrollarse o reemplazarse sin afectar el funcionamiento global.

---

## Capa 5 – Presentación (Frontend)

La capa de presentación constituye el punto de interacción entre los usuarios y la plataforma. Su objetivo es ofrecer una experiencia intuitiva para la visualización de información geoespacial, resultados de análisis y reportes generados por inteligencia artificial.

### Responsabilidades

- Mostrar mapas interactivos.
- Visualizar indicadores ambientales.
- Presentar gráficos estadísticos.
- Consultar predicciones.
- Descargar reportes.
- Administrar autenticación y sesiones de usuario.

### Tecnologías

- React
- Leaflet
- Chart.js
- Plotly

### Entradas

- Datos provenientes de la API REST.
- Actualizaciones mediante WebSockets.

### Salidas

- Solicitudes HTTP.
- Eventos de interacción del usuario.

---

## Capa 4 – Backend API

Esta capa representa el núcleo de comunicación del sistema. Centraliza todas las solicitudes provenientes del frontend y coordina la interacción entre los distintos servicios y agentes inteligentes.

### Responsabilidades

- Exponer servicios REST.
- Gestionar autenticación.
- Administrar usuarios.
- Validar solicitudes.
- Publicar eventos.
- Orquestar procesos.
- Enviar actualizaciones en tiempo real.

### Tecnologías

- Node.js
- Express
- Socket.IO o WebSockets

### Entradas

- Solicitudes HTTP.
- Eventos de los agentes.

### Salidas

- Respuestas REST.
- Publicación de eventos.
- Comunicación con RabbitMQ.

---

## Capa 3 – Agentes de Inteligencia Artificial

Esta capa contiene los agentes autónomos responsables de ejecutar procesos especializados relacionados con visión computacional, aprendizaje automático y generación automática de conocimiento.

Cada agente posee una única responsabilidad y opera de manera independiente.

### Responsabilidades

- Procesar eventos.
- Ejecutar algoritmos especializados.
- Compartir resultados mediante el bus de eventos.
- Mantener independencia funcional.

### Tecnologías

- Python
- TensorFlow
- OpenCV
- RabbitMQ

### Beneficios

- Alta escalabilidad.
- Procesamiento distribuido.
- Bajo acoplamiento.
- Fácil incorporación de nuevos agentes.

---

## Capa 2 – Procesamiento Geoespacial

Implementa todos los algoritmos científicos necesarios para transformar las imágenes satelitales en información útil para el análisis ambiental.

### Responsabilidades

- Corrección de imágenes.
- Procesamiento raster.
- Filtrado de nubes.
- Cálculo de NDVI.
- Cálculo de NDWI.
- Operaciones morfológicas.
- Generación de productos intermedios.

### Tecnologías

- GDAL
- Rasterio
- OpenCV
- NumPy

---

## Capa 1 – Adquisición de Datos

Esta capa obtiene automáticamente las imágenes satelitales necesarias para el procesamiento.

### Responsabilidades

- Consulta de Google Earth Engine.
- Descarga automática.
- Filtrado temporal.
- Filtrado espacial.
- Exportación de imágenes.

### Tecnologías

- Google Earth Engine API
- Python

---

## Capa 0 – Infraestructura

Es la base tecnológica sobre la que funciona toda la solución.

Proporciona los recursos de ejecución, almacenamiento y despliegue.

### Responsabilidades

- Contenedores Docker.
- Redes.
- Persistencia.
- Balanceo.
- Infraestructura Cloud.
- Automatización del despliegue.

### Tecnologías

- Docker
- Docker Compose
- Azure
- GitHub Actions (opcional)

---

# 2. Sistema de Agentes Autogestionados

La plataforma implementa un sistema basado en **Agentes Inteligentes Autogestionados**, donde cada agente ejecuta una única responsabilidad de negocio y responde automáticamente a los eventos publicados en un bus de mensajería.

Este enfoque elimina las dependencias directas entre módulos y permite que el procesamiento ocurra de forma distribuida y asíncrona.

Cada agente:

- Se ejecuta como un proceso independiente.
- Escucha eventos específicos.
- Ejecuta una tarea especializada.
- Publica un nuevo evento cuando finaliza.
- No necesita conocer la existencia de otros agentes.

---

## Funcionamiento General

1. Se inicia una solicitud desde el frontend.
2. El Backend publica un evento inicial.
3. El GeospatialAgent descarga las imágenes.
4. El VisionAgent procesa la información.
5. El OracleAgent realiza las predicciones.
6. El ReportingAgent genera el reporte.
7. El Backend notifica al usuario.

Todo el flujo ocurre sin llamadas directas entre agentes.

---

## Beneficios del Modelo

- Alta escalabilidad.
- Procesamiento paralelo.
- Fácil mantenimiento.
- Tolerancia a fallos.
- Incorporación sencilla de nuevos agentes.
- Independencia tecnológica.
- Mejor aprovechamiento de recursos.

---

# 3. Explicación de los Agentes

## GeospatialAgent

Es el encargado de obtener la información satelital desde Google Earth Engine.

### Funciones

- Consultar colecciones satelitales.
- Filtrar por fechas.
- Filtrar por porcentaje de nubes.
- Descargar imágenes.
- Organizar metadatos.

### Evento emitido

```text
DATA_INGESTED
```

---

## VisionAgent

Realiza el procesamiento geoespacial y la extracción de características.

### Funciones

- Corrección de imágenes.
- Cálculo de NDVI.
- Cálculo de NDWI.
- Operaciones morfológicas.
- Generación de capas raster.
- Extracción de variables ambientales.

### Evento emitido

```text
ANALYSIS_COMPLETE
```

---

## OracleAgent

Responsable del entrenamiento y ejecución de modelos de inteligencia artificial.

### Funciones

- Entrenamiento de redes neuronales.
- Predicción de escenarios.
- Inferencias.
- Evaluación de precisión.
- Pronósticos ambientales.

### Tecnologías

- TensorFlow
- LSTM

### Evento emitido

```text
PREDICTION_COMPLETE
```

---

## ReportingAgent

Transforma los resultados técnicos en reportes comprensibles para investigadores y usuarios finales.

### Funciones

- Interpretación de resultados.
- Generación de narrativas.
- Elaboración de conclusiones.
- Construcción de reportes automáticos.

### Tecnologías

- Azure OpenAI
- Anthropic Claude

### Evento emitido

```text
REPORT_READY
```

---

# 4. Componentes de Infraestructura

La infraestructura está diseñada para ejecutarse completamente sobre Microsoft Azure utilizando contenedores Docker.

Cada componente cumple una función específica dentro del ecosistema de la plataforma.

---

## Azure Virtual Machine (GPU Series)

Servidor principal encargado de alojar los contenedores de la plataforma.

### Funciones

- Ejecutar Docker.
- Proveer aceleración mediante GPU.
- Entrenar modelos de IA.
- Ejecutar procesamiento geoespacial.

---

## Docker

Contenedor de ejecución de todos los servicios.

### Beneficios

- Reproducibilidad.
- Portabilidad.
- Escalabilidad.
- Aislamiento de servicios.

---

## Nginx Proxy

Puerta de entrada de la plataforma.

### Funciones

- HTTPS.
- Balanceador de carga.
- Reverse Proxy.
- Seguridad.
- Redirección de solicitudes.

---

## Node.js Container

Servicio principal del Backend.

### Funciones

- API REST.
- WebSockets.
- Autenticación.
- Orquestación.
- Comunicación con RabbitMQ.

---

## RabbitMQ

Sistema de mensajería utilizado por la arquitectura orientada a eventos.

### Funciones

- Distribución de eventos.
- Comunicación entre agentes.
- Procesamiento asíncrono.
- Gestión de colas.

---

## Python Workers

Conjunto de contenedores especializados para procesamiento intensivo.

### Ejecutan

- OpenCV.
- TensorFlow.
- Rasterio.
- GDAL.
- NumPy.

---

## Azure Blob Storage

Repositorio central para el almacenamiento de archivos.

### Contenido

- Imágenes Sentinel.
- Imágenes Landsat.
- GeoTIFF.
- Resultados de análisis.
- Reportes generados.

---

## Neo4j

Base de datos orientada a grafos.

### Utilización

- Relaciones entre cuencas.
- Redes hidrográficas.
- Estaciones meteorológicas.
- Dependencias espaciales.

---

## PostgreSQL + PostGIS

Base de datos relacional con soporte geoespacial.

### Utilización

- Información vectorial.
- Consultas espaciales.
- Geometrías.
- Capas GIS.

---

## Google Earth Engine

Servicio externo para la adquisición de imágenes satelitales.

### Funciones

- Acceso a Sentinel.
- Acceso a Landsat.
- Series históricas.
- Procesamiento inicial en la nube.

---

## Azure OpenAI Service

Servicio utilizado para la generación inteligente de reportes.

### Funciones

- Interpretación de resultados.
- Generación de lenguaje natural.
- Resúmenes ejecutivos.
- Explicaciones técnicas.

---

# Resumen General

La combinación de una arquitectura por capas con un sistema de agentes autogestionados permite construir una plataforma altamente modular, escalable y resiliente. Cada componente tiene una responsabilidad claramente definida, mientras que la comunicación basada en eventos reduce el acoplamiento entre módulos y facilita la incorporación de nuevas funcionalidades sin afectar el resto del sistema. Esta arquitectura está preparada para manejar grandes volúmenes de datos geoespaciales, integrar modelos avanzados de inteligencia artificial y desplegarse eficientemente sobre infraestructura en la nube mediante contenedores Docker y servicios administrados de Azure.