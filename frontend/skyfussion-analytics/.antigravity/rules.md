# Reglas del Workspace — Skyfussion Analytics

1. **Fuente única de verdad**: `PROJECT_SPEC.md` (y `/public/assets/aistudio/PROJECT_SPEC_451d4cdf.md`) gobierna los contratos de API, las definiciones de índices espectrales (`NDWI`, `NDVI`, `MNDWI`, `NDBI`, `EVI`), la morfología OpenCV (`1969–2023`) y la jerarquía de evidencia estadística.
2. **Regla de métricas honestas (Nivel A)**:
   - Nunca mostrar `R² = 0.66`.
   - Usar las métricas reproducibles verificadas: RNN real `gru_attention_h1` (`RMSE = 0.0712`, `R² = 0.0775`), árbol de decisión (`accuracy_test = 0.5676`, `macro-F1 = 0.5328` en artefacto / `0.66` en plan) y KNN (`macro-F1 = 0.5938`).
   - Todas las alertas mantienen operación asistida por humano.
3. **DEMO_MODE=true por defecto**: Mantener disponibles los datos reales históricos de la cuenca del Río Combeima (Ibagué, Tolima, `1969–2023`) para respuesta instantánea sin depender de descargas síncronas desde Google Earth Engine.
4. **Pipeline orientado a eventos**: Toda ejecución de análisis espacial o paramétrico registra explícitamente las 5 etapas: `AREA_DEFINED` → `DATA_INGESTED` → `ANALYSIS_COMPLETE` → `PREDICTION_COMPLETE` → `REPORT_READY`.
5. **Agente de Reportes Hidrológicos**: Las llamadas a Gemini (`@google/genai`) se ejecutan exclusivamente en el servidor con `GEMINI_API_KEY` y devuelven JSON estricto (`alert_level`, `headline`, `narrative`, `recommendations`).
6. **Estética Visual:**
   - Centro de control ambiental en modo oscuro: fondo `#0a1128`, paneles `#101a36`, acentos cian `#00bbf9` y verde neón `#00f5d4`, alerta preventiva `#ffd166` y emergencia `#ff3864`[cite: 1].
7. **Regla de Puertos y Variables:**
   - El frontend NUNCA debe tener URLs fijas a `localhost`; siempre debe leer `import.meta.env.VITE_API_URL || "http://localhost:8000"`.
   - El backend debe leer `PORT` desde el entorno (`0.0.0.0:$PORT`) y configurar `CORSMiddleware` leyendo `ALLOWED_ORIGINS`.  