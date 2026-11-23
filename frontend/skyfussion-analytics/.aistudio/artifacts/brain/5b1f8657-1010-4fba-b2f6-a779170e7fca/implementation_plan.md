# Skyfussion Analytics — Integración Leaflet, Chart.js, GeoJSON/KML y Pipeline de Eventos

Actualización integral de la consola web **Skyfussion Analytics** para incorporar cartografía interactiva real con **Leaflet**, carga y digitalización de polígonos (**GeoJSON / KML / Coordenadas manuales**), gráficas temporales **1969–2023** con **Chart.js**, trazabilidad en vivo del **pipeline de 5 etapas** y cumplimiento estricto de las métricas reproducibles (Nivel A) de `PROJECT_SPEC.md`.

---

### User Review & Critical Decisions

> [!IMPORTANT]
> Decisiones confirmadas durante la segunda ronda de aclaración:

- **Capacidades Integradas en Consola (Confirmado)**:
  1. **Mapa Interactivo Leaflet**: Mapa real con capas base (Satelital Esri / Topográfico OpenStreetMap), dibujo de polígonos sobre la cuenca del Río Combeima, entrada manual de coordenadas `[lon, lat]` y carga de archivos `.geojson` y `.kml`.
  2. **Gráficas Chart.js (1969–2023)**: Serie temporal histórica y pronóstico del Río Combeima (`NDWI`, `NDVI`, caudal en $\text{m}^3/\text{s}$ y evolución del ancho de cauce) con bandas de referencia.
  3. **Rastreador del Pipeline de Eventos (5 Etapas)**: Indicador de ejecución paso a paso (`AREA_DEFINED` → `DATA_INGESTED` → `ANALYSIS_COMPLETE` → `PREDICTION_COMPLETE` → `REPORT_READY`) sincronizado con el análisis de cada polígono y el endpoint `POST /api/v1/analyze`.
  4. **Visor Espectral Sentinel-2 / OpenCV Conservado como Modo Alterno**: El usuario puede alternar dentro del visor entre **Mapa Geográfico (Leaflet)** y **Visor Espectral Sentinel-2 / OpenCV** sin perder las herramientas de inspección morfológica 1969–2023.
- **Convención de Métricas Estadísticas (Confirmado)**: Se aplica estrictamente `PROJECT_SPEC.md` (Nivel A): `macro-F1 ≈ 0.66 (plan) / 0.53 (artefacto)`, `RMSE = 0.0712` y `R² = 0.0775` (RNN real `gru_attention_h1`, alerta asistida por humano). Nunca se mostrará `R² = 0.66`.
- **Reglas del Workspace**: Creación del archivo `.antigravity/rules.md` con `PROJECT_SPEC.md` como fuente de verdad y `DEMO_MODE=true` habilitado por defecto para respuesta instantánea con datos reales históricos del Río Combeima.

---

### 1. Overview & Core Concept

- **Qué entrega**: Evoluciona la consola hacia un entorno GIS completo donde cualquier usuario (alcaldía, autoridad ambiental o analista) puede delimitar un polígono real sobre el Río Combeima (dibujando en Leaflet, pegando coordenadas o subiendo un archivo `.geojson` / `.kml`), disparar el pipeline analítico de 5 etapas, inspeccionar la evolución histórica 1969–2023 en Chart.js y obtener el dictamen JSON estructurado del Agente Hidrológico.
- **Contrato unificado**: El servidor Express expondrá `POST /api/v1/analyze` alineado al contrato de `PROJECT_SPEC.md` §12 (`area_name`, `geometry`, `years`), manteniendo `POST /api/report` para evaluaciones paramétricas directas desde los deslizadores.

---

### 2. User Experience & Visual Design

- **Flujo GIS + Pipeline en la Consola**:
  1. **Delimitación del Área de Estudio (Panel Izquierdo / Herramienta de Mapa)**:
     - Pestañas compactas para elegir cuenca base o ingresar área personalizada: **Presets**, **Dibujar / Coordenadas** (entrada manual de vértices `[lon, lat]` o dibujo clic-a-clic sobre Leaflet) y **Archivo (.geojson / .kml)** con validación geométrica inmediata (verificando anillos cerrados y rango de coordenadas WGS84).
  2. **Visor Dual Geoespacial (Centro)**:
     - Conmutador superior limpio entre **Mapa Leaflet (GIS)** y **Visor Espectral (Sentinel-2 / OpenCV)**.
     - En **Mapa Leaflet**: tiles satelitales/topográficos reales, polígono activo de la cuenca del Río Combeima (`[-75.257, 4.433]` – `[-75.142, 4.529]`), marcadores de estaciones (*Estación Poblado*, *Bocatoma Ibagué*, *Cabecera Nevado*), herramienta de dibujo interactivo de polígonos por clic y ajuste automático de zoom (`fitBounds`) al cargar `.geojson` o `.kml`.
  3. **Banda de Pipeline Orientado a Eventos (5 Etapas)**:
     - Barra horizontal técnica sobre la bandeja de análisis mostrando el progreso real de cada evento (`AREA_DEFINED` → `DATA_INGESTED` → `ANALYSIS_COMPLETE` → `PREDICTION_COMPLETE` → `REPORT_READY`) con marcas de tiempo en `JetBrains Mono` y estado explícito sin puntos pulsantes decorativos.
  4. **Panel de Gráficas Temporales Chart.js (Debajo de la Consola / Pestaña Series 1969–2023)**:
     - Dos gráficas interactivas responsivas en Chart.js adaptadas automáticamente a **Orbital Oscuro** y **Oceánico Claro**:
       - *Evolución Multitemporal NDWI / NDVI y Ancho de Cauce (1969–2023)* con anotación de tendencia.
       - *Caudal Histórico y Pronóstico ($\text{m}^3/\text{s}$)* con métricas honestas Nivel A (`RMSE: 0.0712 · R²: 0.0775 · macro-F1: 0.53 artefacto / 0.66 plan`).

---

### 3. Key Product Decisions & Trade-Offs

- **Leaflet + Parser propio de KML/GeoJSON sin dependencias frágiles de plugins**:
  - *Enfoque elegido*: Instalar `leaflet`, `@types/leaflet` y `chart.js` en una única operación de dependencias. Implementar dibujo interactivo de polígonos nativo con eventos de mapa Leaflet y un parser seguro `DOMParser` para `.kml` (`<Polygon>` / `<LineString>` / `<Point>`) y `JSON.parse` validado para `.geojson`.
  - *Por qué*: Evita conflictos de compatibilidad entre plugins antiguos (`leaflet-draw`) y React 19 / Vite 8, garantizando cero errores en consola y soporte completo para `.geojson` y `.kml`.
- **Conservación del Visor Sentinel-2 / OpenCV junto a Leaflet**:
  - *Enfoque elegido*: Ofrecer un conmutador `Leaflet GIS | Sentinel-2 OpenCV` dentro del visor central.
  - *Por qué*: Responde al pedido explícito de mapa real Leaflet con dibujo/archivos mientras preserva las ortofotografías satelitales generadas, los transectos OpenCV y la cortina 1969–2023.
- **Cálculo geométrico determinista + Gemini en `/api/v1/analyze`**:
  - *Enfoque elegido*: Al enviar una geometría GeoJSON a `POST /api/v1/analyze`, el servidor calcula área (hectáreas), centroide, índice de compacidad y ajusta las métricas hidrológicas y la serie `1969–2023` del Río Combeima para invocar a `@google/genai` (`gemini-4-hydrogen`) y devolver el dictamen estructurado + los 5 eventos de ejecución.

---

### 4. Technical Architecture & Data Strategy

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                  Consola Skyfussion Analytics (React + Vite)             │
│                                                                          │
│  ┌─────────────────────┐  ┌────────────────────────────────────────────┐ │
│  │ Entrada Geoespacial │  │ Visor Central Dual                         │ │
│  │ - Presets Combeima  │  │ [Leaflet GIS] <──> [Sentinel-2 OpenCV]     │ │
│  │ - Dibujo / Coords   │  │ - Polígonos, Estaciones, FitBounds         │ │
│  │ - Carga GeoJSON/KML │  │ - Dibujo interactivo por vértices          │ │
│  │ - Sliders Técnicos  │  └────────────────────────────────────────────┘ │
│  └──────────┬──────────┘                                                 │
│             │                                                            │
│  ┌──────────▼──────────────────────────────────────────────────────────┐ │
│  │ Rastreador Pipeline 5 Etapas                                        │ │
│  │ AREA_DEFINED ─▶ DATA_INGESTED ─▶ ANALYSIS ─▶ PREDICTION ─▶ REPORT   │ │
│  └──────────┬──────────────────────────────────────────────────────────┘ │
│             │                                                            │
│  ┌──────────▼─────────────────────────┐ ┌──────────────────────────────┐ │
│  │ Gráficas Chart.js (1969–2023)      │ │ Dictamen Ejecutivo IA        │ │
│  │ - Serie NDWI / NDVI / Cauce        │ │ - JSON Estricto + Narrativa  │ │
│  │ - Caudal y Métricas Nivel A        │ │ - Acciones para Alcaldías    │ │
│  └────────────────────────────────────┘ └──────────────────────────────┘ │
└───────────────────────────────────────┬──────────────────────────────────┘
                                        │ POST /api/v1/analyze
                                        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│              Servidor Express (Puerto 3000) + @google/genai              │
│  - Validación GeoJSON Polygon/MultiPolygon y rango años (1969–2023)      │
│  - Cálculo geodésico de área/centroide + serie histórica Combeima        │
│  - Generación de reporte JSON estructurado vía gemini-4-hydrogen         │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Dependencias a instalar**: `leaflet`, `@types/leaflet`, `chart.js`.
- **Artefactos de reglas**: `.antigravity/rules.md` especificando `PROJECT_SPEC.md` como fuente de verdad y `DEMO_MODE=true`.
