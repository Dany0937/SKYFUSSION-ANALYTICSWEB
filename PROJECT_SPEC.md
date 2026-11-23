# PROJECT_SPEC.md — Skyfussion Analytics

> **Contexto maestro del proyecto** · Cuenca del río Combeima (Ibagué, Tolima)  
> **Fecha de consolidación:** 2026-11-22  
> **Marco metodológico:** CRISP-DM  
> **Uso:** fuente única de contexto para `frontend/`, `backend/`, `docs/` y despliegue (Vercel / Render).  
> **Nota de procedencia:** las cifras se extrajeron de los artefactos del repositorio y del material de estudio referido (NotebookLM). No se accedió a NotebookLM directamente en esta sesión; toda afirmación numérica está respaldada por una ruta de archivo local.
> **Contrato de API:** sección [§12](#12-contrato-json-único-frontend--backend).

---

## 0. Regla de oro: jerarquía de evidencia

Ante cifras contradictorias, **manda el artefacto reproducible**. Esta decisión fue acordada explícitamente.

| Nivel | Tipo de fuente | Ejemplos | Uso en este documento |
|---|---|---|---|
| **A** | Artefactos generados por código, con semilla/CSV/JSON | `sesion7/resultados/metricas_finales.json`, `sesion8/resultados/torneo_modelos_gee.csv`, `rnn_combeima/reports/resumen_final.csv`, `reports/crisp_dm/metricas_regresion.json` | **Fuente de verdad** |
| **B** | Planes, presentaciones y notas de sesión | `PLAN_ARBOL.md`, `PLAN_SESIONES_8_9_SKYFUSION.md` | Se citan y se marcan como **no reproducibles** cuando difieren de A |
| **C** | Documentación de arquitectura y criterios de diseño | `docs/src/content/docs/**`, `ARQUITECTURA_AZURE.md`, `PROJECT_STRUCTURE.md` | Definen **objetivos y contratos**, no resultados medidos |

### Conflicto crítico de métricas base

| Cita del usuario / plan | Interpretación correcta | Valor en artefacto (nivel A) |
|---|---|---|
| `$R^2 = 0.66$` | **No existe como R² en ningún artefacto.** Corresponde a macro-F1 de validación cruzada `0.6606` y a accuracy reportado `0.6674` (clasificación, nivel B). | `accuracy_test = 0.5676`, `macro_f1_test = 0.5328` (`sesion7/resultados/metricas_finales.json`) |
| `RMSE = 0.07` | Redondeo de `RMSE = 0.0712`, pero **viene con `R² = 0.0775`**, no con 0.66. | `rnn_combeima/reports/resumen_final.csv`, fila `gru_attention_h1_3d7b5aec`, `fuente = REALES (GEE)` |
| `0.073` de `PLAN_ARBOL.md:26` | Brecha CV→test del árbol, **no es RMSE**. | — |
| `R² = 0.979 / RMSE = 0.034` | Validación de pipeline con **datos sintéticos**. | `rnn_combeima/README.md:167-178` y corridas `run_20260907_*` |
| KNN `accuracy 0.7443 / macro-F1 0.7301` | Cifra de los planes (nivel B). | `accuracy_test = 0.6216`, `macro_f1_test = 0.5938` (`torneo_modelos_gee.csv`, KNN k=5 escalado) |

> **Regla de redacción obligatoria para el frontend, los reportes y la documentación:** nunca escribir «R² = 0.66». Escribir «macro-F1 ≈ 0.66 (plan) / 0.53 (artefacto)» o «R² = 0.078 (RNN real)», según corresponda. El ejemplo de `forecast` en el [contrato JSON (§12)](#12-contrato-json-único-frontend--backend) usa `rmse: 0.0712` y `r2: 0.0775` conforme a esta regla.

---

## 1. Contexto de negocio y marco CRISP-DM

La cuenca del río Combeima aporta ~80 % del agua potable de Ibagué y es vulnerable a avenidas torrenciales, deslizamientos, pérdida de cobertura vegetal y expansión urbana. Skyfussion Analytics es una plataforma de monitoreo hidroclimático y detección de cambios de cobertura que integra teledetección, minería de datos, modelos recurrentes y una arquitectura multiagente orientada a eventos.

| Fase CRISP-DM | Aplicación en el proyecto | Evidencia |
|---|---|---|
| 1. Entendimiento del negocio | Alertar sobre desabastecimiento, erosión y presión antrópica. Criterio declarado: macro-F1 > 0.65 y R² > 0.70 | `docs/analisis_arquitectura_skyfusion_crisp_dm.md:73-79` |
| 2. Entendimiento de los datos | Sentinel-2, MODIS, WorldCover 2021; nubosidad en abril-mayo y octubre-noviembre | ídem, `:81-85` |
| 3. Preparación | Interpolación lineal/tiempo/spline cúbico/PCHIP; split estratificado congelado semilla 42 (1.443 / 481); `StandardScaler` solo en train | ídem, `:87-90` |
| 4. Modelado | Árbol depth 5 entropy, GaussianNB, KNN, K-Means/jerárquico, regresión OLS/Ridge, RNN (GRU/LSTM/BiGRU/GRU+Attention/TCN) | ídem, `:92-100`, `rnn_combeima/rnn/models.py` |
| 5. Evaluación | Accuracy, macro-F1, balanced accuracy, RMSE, R², MAE, SMAPE, Shapiro-Wilk, Durbin-Watson, silueta | ídem, `:102-105` |
| 6. Despliegue | Scripts reproducibles, notebooks, presentaciones HTML y agentes Python | ídem, `:107-111` |

**Objetivos de minería de datos:** (i) clasificación explicable de 7 clases de cobertura; (ii) clustering espectral para alertas segmentadas; (iii) regresión/predicción multitemporal de NDVI y caudal.

---

## 2. Fuentes de datos

| Dataset | Contenido | Uso | Fuente |
|---|---|---|---|
| `sesion7/datasets/sentinel2_combeima_clases.csv` | 1.924 filas · 7 clases · 118 tiles (~1 km) · 6 bandas (B2, B3, B4, B8, B11, B12) + NDVI, NDWI, NDBI, B8/B4 ratio, temporada lluviosa | Clasificación y reglas de negocio | `PLAN_ARBOL.md:7` |
| Split congelado | 1.443 train / 481 test, estratificado, semilla 42, índices disjuntos; `tile_id` guardado | Todas las comparaciones | `sesion7/resultados/metricas_split.json` |
| `rnn_combeima/data/raw/series_multisensor_combeima.csv` | 4.016 observaciones · 40 píxeles · 226 fechas MODIS (2015-2024) | Series temporales RNN | `PLAN_PROYECTO_RED_NEURONAL_GEE.md:8` |
| `reports/crisp_dm/tabla_interpolacion_15_puntos.csv` | 15 meses continuos mes a mes | Interpolación y regresión de tendencia | `reports/crisp_dm/` |
| Escenas satelitales | Sentinel-2 MSI (10/20 m, 5 días), Landsat 8/9 (30 m, 16 días), MODIS MOD13A2 (1 km, 16 días), WorldCover 2021 (10 m) | Adquisición vía GEE | `docs/analisis_arquitectura_skyfusion_crisp_dm.md:14`, `PLAN_PROYECTO_RED_NEURONAL_GEE.md:576` |

**Control de fuga:** el split de clasificación es por índices disjuntos; el split de RNN es **espacio-temporal** (el mismo píxel no aparece en train y test) y los scalers se ajustan solo con train (`PLAN_PROYECTO_RED_NEURONAL_GEE.md:10-11`). La validación espacial por bloques del árbol quedó diferida; la sensibilidad del split se probó en 12 escenarios (macro-F1 entre 0.6395 y 0.7010, `PLAN_ARBOL.md:27`).

---

## 3. Índices espectrales (NDWI / NDVI)

Implementación canónica: `agents/python/vision_agent/processors/indices.py` (también `skills/vision_tools/river_morphology.py`).

| Índice | Fórmula | Bandas | Rangos / interpretación |
|---|---|---|---|
| **NDVI** | `(NIR − Red) / (NIR + Red + 1e-10)` | B8, B4 | < 0.1 suelo desnudo · 0.1–0.3 vegetación escasa · 0.3–0.6 moderada · ≥ 0.6 densa |
| **NDWI** | `(Green − NIR) / (Green + NIR + 1e-10)` | B3, B8 | < −0.3 suelo seco · −0.3–0 humedad baja · 0–0.3 humedad moderada · ≥ 0.3 cuerpo de agua |
| **MNDWI** | `(Green − SWIR1) / (Green + SWIR1 + 1e-10)` | B3, B11 | Alternativa para agua en zonas urbanas |
| **NDBI** | `(SWIR1 − NIR) / (SWIR1 + NIR + 1e-10)` | B11, B8 | Zonas urbanas / suelo desnudo |
| **EVI** | `2.5 · (NIR − Red) / (NIR + 6·Red − 7.5·Blue + 1 + 1e-10)` | B8, B4, B2 | Corrige saturación y influencia atmosférica |

Todos se recortan a `[-1, 1]`; el parámetro `scale=True` los convierte a `uint8` mediante `((x + 1) * 127.5)`.

**Reglas de negocio derivadas del árbol** (`PLAN_ARBOL.md:20-24`, nivel B):

- `agua`: NDWI > −0.32 **y** B11 ≤ 1480.75 **y** B8 ≤ 1190.25 → pureza 100 %, 67 muestras de test.
- `urbano`: NDWI > −0.32 **y** B11 > 1480.75 **y** B8 ≤ 2672.50 **y** NDBI > 0.13 **y** B11 ≤ 3301 → pureza 92,2 %.
- `suelo_desnudo` y `bosque` también tienen hoja propia; las reglas son **asociaciones, no causalidad**.

> Nota técnica: el umbral `NDWI > −0.32` del árbol es una condición débil; la separación real la hacen las bandas B11/B8. No debe confundirse con el criterio de interpretación `NDWI > 0.3` para «cuerpo de agua».

---

## 4. Análisis morfológico con OpenCV

Dos implementaciones complementarias:

1. **`agents/python/vision_agent/processors/morphology.py`** — primitivas: `opening`/`closing` (kernel elíptico 5×5), `dilation`/`erosion` (3×3), `skeletonize` (kernel cruz 3×3) y `filter_by_area` (`connectedComponentsWithStats`, `connectivity=8`, mínimo 100 px).
2. **`skills/vision_tools/river_morphology.py`** — pipeline completo `RiverMorphologyAnalyzer`:

| Paso | Operación | Parámetros |
|---|---|---|
| 1 | NDWI = (Green − NIR)/(Green + NIR) | recorte `[-1,1]`, denominador protegido con `1e-10` |
| 2 | Umbralización y limpieza | `ndwi_threshold = 0.0`, `MORPH_OPEN` + `MORPH_CLOSE`, kernel `5×5`, 1 iteración |
| 3 | Bordes | `GaussianBlur 5×5` → `Canny(50, 150)` |
| 4 | Línea central | skeletonization iterativa (erosión/dilatación/sustracción) |
| 5 | Perfil de anchos | recorrido por fila/columna desde cada píxel del esqueleto → media, std, min, max en píxeles |
| 6 | Comparación entre épocas | `erosión = M1 ∩ ¬M2`, `deposición = ¬M1 ∩ M2`; change de ancho y cobertura |
| 7 | Interpretación | ±5 % de cobertura hídrica → alerta/recuperación/estabilidad; erosión > 1.5× deposición → incisión; deposición > 1.5× erosión → sedimentación |

Periodo de análisis: **1969–2023**. Salidas: `MorphologicalAnalysisResult` y `MorphologicalComparison`, serializables vía `generate_report()`.

---

## 5. Eventos del sistema

Existen **dos familias de nombres** que deben conservarse por compatibilidad y unificarse en el contrato del backend FastAPI:

### 5.1 Familia de adquisición (UPPER_SNAKE)

| Evento | Productor | Significado | Payload clave |
|---|---|---|---|
| `IMAGENES_HISTORICAS_LISTAS` | GeospatialAgent / `skills/geo_tools` | Imágenes disponibles | `dateRange`, `collectionsUsed`, `imageCount`, `cloudFilterApplied`, `basin` |
| `IMAGEN_INDIVIDUAL_PROCESADA` | GeospatialAgent | Escena procesada | `imageId`, `collection`, `cloudCover` |
| `GEOSPATIAL_AGENT_ERROR` | GeospatialAgent | Fallo de adquisición | `errorType`, `message`, `context`, `traceback` |

Esquemas validables en `shared/events/schemas.js` (`validateEvent`); backends soportados: `local` (archivos `.jsonl` en `data/events/`), `redis` y `rabbitmq` (`shared/events/README.md:59-63`).

### 5.2 Familia de pipeline (lower:colon)

| Evento | Origen → Destino | Definición |
|---|---|---|
| `analysis:requested` | Backend → GeospatialAgent | Solicitud de análisis |
| `data:ingested` | GeospatialAgent → VisionAgent | Datos satelitales listos |
| `analysis:completed` | VisionAgent → OracleAgent | Índices y segmentación listos |
| `prediction:completed` | OracleAgent → ReportingAgent | Predicción con nivel de alerta |
| `report:ready` | ReportingAgent → Backend | Reporte generado |

Contrato en `docs/src/content/docs/04-engineering-standards/03-agent-protocol.md:45-49` y `services/backend-node/src/services/eventBus.js`. El orquestador Node actual mantiene `Map<requestId, PipelineState>` con timeouts y reintentos (`.opencode/plans/integration-plan.md:67-73`).

**Mapeo de resultados a agentes** (`docs/analisis_arquitectura_skyfusion_crisp_dm.md:117-125`): reglas del árbol → VisionAgent/OracleAgent/ReportingAgent; K-Means Z2 (94,5 % agua) → monitoreo de espejo hídrico; Z1 (50,1 % suelo desnudo + 34,1 % urbano) → alerta de erosión; Z0 → salud vegetal.

---

## 6. Estado real de los modelos

### 6.1 Clasificación de cobertura (fuente de verdad: nivel A)

| Modelo | Accuracy train | Accuracy test | Macro-F1 test | Fuente |
|---|---:|---:|---:|---|
| Árbol depth 5, entropy | 0.6736 | **0.5676** | **0.5328** | `sesion7/resultados/metricas_finales.json` |
| GaussianNB | — | 0.5177 | 0.4375 | `sesion8/resultados/torneo_modelos_gee.csv` |
| KNN k=5 escalado (11 features) | 0.7152 | **0.6216** | **0.5938** | ídem |
| KNN k=5 sin escalar (solo índices) | 0.7235 | 0.6341 | 0.5934 | ídem |

Referencias de los planes (nivel B, **no reproducibles con los artefactos actuales**): árbol `0.6674 / 0.6595 / 0.6574`, CV macro-F1 `0.6606`, baseline mayoría `0.1559`, KNN k=5 escalado `0.7443 / 0.7301` (`PLAN_ARBOL.md:10-14`, `PLAN_SESIONES_8_9_SKYFUSION.md:100-103`).

**Lectura:** el mejor clasificador *estadísticamente* es KNN; el árbol se conserva como **modelo de comunicación** porque entrega reglas auditables para los comités de gestión del riesgo.

### 6.2 Regresión / serie temporal de NDVI

| Experimento | Datos | RMSE | R² | SMAPE | MAE | Observación |
|---|---|---:|---:|---:|---:|---|
| `gru_attention_h1_3d7b5aec`, h=1, 8 épocas, 24.329 params | **GEE real** | **0.0712** | **0.0775** | **6,61 %** | 0.0492 | Mejor baseline real; falta baseline persistence/media estacional |
| `gru_attention_h1_ad77193c`, h=1, 8 épocas | GEE real | 0.0875 | −0.3965 | 10,01 % | 0.0742 | Segundo real |
| `gru_attention_h1_ad77193c`, h=1, 8 épocas | Sintético | 0.0341 | 0.9789 | 11,12 % | 0.0267 | **Solo validación de pipeline** |
| `tcn_h1_0dd7f44a`, h=1, 8 épocas | Sintético | 0.1143 | 0.7625 | 27,48 % | 0.0963 | Peor arquitectura sintética |

Fuente: `rnn_combeima/reports/resumen_final.csv`. El `PLAN_PROYECTO_RED_NEURONAL_GEE.md:12` confirma el baseline real `RMSE 0.0712 / R² 0.0775`.

### 6.3 Regresión lineal CRISP-DM

| Modelo | n | RMSE | MAE | R² | R² ajustado | Shapiro p | Durbin-Watson |
|---|---:|---:|---:|---:|---:|---:|---:|
| Serie 15 meses (tendencia) | 15 | 0.0260 | 0.0212 | 0.0205 | −0.0548 | 0.176 (normal) | 1.403 (**autocorrelación**) |
| Serie completa (4 features) | 46 | 0.0366 | 0.0273 | 0.0356 | −0.0585 | 0.00081 (**no normal**) | 2.327 (sin autocorrelación) |

Fuente: `reports/crisp_dm/metricas_regresion.json`. Pendiente mensual NDVI `β₁ = 0.00087` (`reports/crisp_dm/alerta_despliegue_skyfusion.json`). Aunque tiene el **menor RMSE absoluto**, su R² ajustado es negativo: no explica la varianza y no debe usarse como pronóstico productivo.

### 6.4 Clustering

K-Means con k=3, seleccionado por inercia/silueta; jerárquico `ward` sobre 60 píxeles (`docs/analisis_arquitectura_skyfusion_crisp_dm.md:97-99`). Perfiles (`sesion9/resultados/perfil_clusters_combeima.csv`):

| Zona | Píxeles | Composición dominante |
|---|---:|---|
| Z0 · Vegetación mixta | 1.113 | cultivo 32,4 %, pastizal 32,2 %, bosque 24,3 % |
| Z1 · Suelo urbano-desnudo (riesgo) | 501 | suelo desnudo 50,1 %, urbano 34,1 % |
| Z2 · Cuerpos de agua | 310 | agua 94,5 % |

---

## 7. Decisión técnica: ¿cuál es el mejor margen de error?

**Respuesta corta:** no existe una sola cifra válida. `RMSE`, `R²`, `SMAPE` y `macro-F1` miden cosas distintas y **no son comparables entre tareas ni entre escalas**.

1. **Por escala:** un RMSE de 0.026 (CRISP-DM, serie de 15 meses) parece «mejor» que 0.0712 (RNN), pero el primero es una regresión lineal de baja varianza y el segundo es un pronóstico multitemporal. Sin **NRMSE** (`RMSE / σ_y`) no se puede comparar.
2. **Por poder explicativo:** el CRISP-DM tiene el error absoluto más bajo, pero `R² ≈ 0.02–0.04` y ajustado negativo; es un modelo con **error pequeño y señal casi nula**. La RNN real tiene `R² = 0.0775`: explica apenas 7,8 % de la varianza. **Ninguno cumple el objetivo R² > 0.70 / > 0.80**.
3. **Por honestidad:** `R² = 0.979` es sintético; `0.66` es macro-F1/accuracy de clasificación; `0.073` es una brecha CV. Ninguno es un «margen de error».
4. **Por tarea:** en clasificación, KNN gana en macro-F1 (`0.5938` artefacto / `0.7301` plan); en regresión, el candidato real es `gru_attention`, **condicionado** a compararlo contra persistence y media estacional.
5. **Por inferencia:** el reporte debe dar un **intervalo**, no un punto. La arquitectura LSTM-CNN ya prevé una cabeza de incertidumbre (`README.md:1293-1307`), pero no hay evidencia de que esté calibrada.

**Conclusión para el producto:** el «mejor margen de error» defendible es el del **modelo que simultáneamente reduzca NRMSE, supere al baseline naive y mantenga residuos sanos**. Hoy esa comparación está **pendiente**; por lo tanto, el estado oficial es *«baseline prometedor, no apto para decisión automática»*. Las alertas deben seguir siendo **asistidas por humano**.

---

## 8. Criterios de aceptación estadística propuestos

| Métrica | Umbral propuesto | Justificación |
|---|---|---|
| R² (test, datos reales) | ≥ 0.70 (CRISP-DM) / ≥ 0.80 (docs de éxito) | Objetivos declarados; hoy incumplidos |
| NRMSE = RMSE / σ_y | ≤ 0.10 | Hace comparable el error entre series y sensores |
| SMAPE | ≤ 10 % | El mejor real ya está en 6,61 % |
| MAE | ≤ 0.10 | Objetivo documentado para LSTM-CNN |
| Baseline | Superar persistence **y** media estacional | Requerido por `rnn_combeima/README.md:177-178` |
| Durbin-Watson | 1.5 – 2.5 | La serie de 15 meses tiene 1.403 |
| Shapiro-Wilk | p > 0.05 o usar errores robustos | La serie completa tiene p = 0.00081 |
| IC 95 % (bootstrap por bloque espacial/temporal) | ancho ≤ ±0.05 en NDVI | Cuantifica el margen de error real |
| Macro-F1 / balanced accuracy | ≥ 0.65 / ≥ 0.60 | Objetivo de clasificación, con intervalo |
| Precisión de alertas | > 85 % | `docs/.../04-success-metrics.md:16` |

**Protocolo de validación obligatorio antes de subir un modelo a Render:** split espacio-temporal congelado → scalers solo en train → métricas punto + intervalo → diagnóstico de residuos → comparación con baselines → registro de hash del dataset, semilla, commit y versiones.

---

## 9. Arquitectura destino y despliegue

```
skyfussion-analytics/            # raíz de la copia de trabajo
├── frontend/                    # React + Vite + Tailwind + Leaflet + Chart.js → Vercel
│   ├── src/{components,lib}/
│   ├── index.html · package.json · vite.config.ts · tailwind.config.js · tsconfig.json
│   └── vercel.json
├── backend/                     # Python FastAPI + OpenCV + inferencia + Gemini → Render
│   ├── app/{main.py,api/v1,core,schemas,services}/
│   ├── agents/                                        # desde agents/python/
│   ├── skills/                                        # desde skills/
│   ├── rnn_combeima/                                  # experimentos y reportes RNN
│   ├── data/ · notebooks/ · reports/ · scripts/ · tests/ · shared/
│   ├── archive/{sesion7,sesion8,sesion9}/             # evidencia histórica
│   ├── legacy/backend-node/                           # Node/Express anterior, sin borrar
│   ├── docs/                                          # planes y arquitectura originales
│   └── requirements.txt · Dockerfile · render.yaml · .env.example
├── docs/                        # Astro/Starlight — intacto
├── README.md
└── PROJECT_SPEC.md
```

**Mapa de rutas citadas en este documento** (las secciones 1-8 usan las rutas originales
por trazabilidad; después de la reorganización están así):

| Ruta citada | Ruta actual en la copia |
|---|---|
| `sesion7/`, `sesion8/`, `sesion9/` | `backend/archive/sesion7/`, `.../sesion8/`, `.../sesion9/` |
| `rnn_combeima/` | `backend/rnn_combeima/` |
| `reports/`, `data/`, `notebooks/`, `scripts/`, `tests/` | `backend/reports/`, `backend/data/`, … |
| `agents/python/`, `skills/`, `shared/events/` | `backend/agents/`, `backend/skills/`, `backend/shared/events/` |
| `PLAN_*.md`, `ARQUITECTURA_AZURE.md`, `PROJECT_STRUCTURE.md` | `backend/docs/` |
| `services/backend-node/` | `backend/legacy/backend-node/` |
| `docs/` (Astro/Starlight) | `docs/` (sin cambios) |

**Proveedor de LLM:** Gemini API se añade como **proveedor preferido** del `ReportingAgent`; se conservan OpenAI/Ollama como fallback (`agents/python/reporting_agent/agent.py` ya es multi-provider). La clave debe inyectarse por variable de entorno (`GEMINI_API_KEY`), nunca versionada.

**Contratos que el frontend consume del backend:** el contrato productivo y único es `POST /api/v1/analyze`, definido en el [§12](#12-contrato-json-único-frontend--backend) (`metrics`, `forecast`, `report`). Los endpoints `GET /api/v1/demo/metrics` (`ndvi`, `ndwi`, `flow_rate`, `alert_level`) y `GET /api/v1/series/demo` son de demostración y no deben ampliarse. El backend publica además los eventos `prediction:completed` y `report:ready` para actualizar la UI. Objetivos de calidad: disponibilidad > 99,5 %, latencia < 200 ms, procesamiento de escena < 5 min, reporte < 30 s (`docs/.../04-success-metrics.md:18-25`).

---

## 10. Reproducibilidad y trazabilidad

```bash
# Árbol explicable (semana 7)
py -3.13 "sesion7/codigo/arbol_gee_skyfusion.py" --extraer-gee

# RNN: extracción → verificación → entrenamiento → ranking
python rnn_combeima/scripts/via_completa.py --extraer --sensores modis --n-puntos 300
python rnn_combeima/scripts/via_completa.py --verificar
python rnn_combeima/scripts/via_completa.py --entrenar --lote basico --epochs 30 --reales
python rnn_combeima/scripts/via_completa.py --reporte
```

Dos corridas consecutivas del árbol producen hashes idénticos en métricas, reglas, baseline y split. `sesion7/resultados/resumen_ejecucion.json` registra hash SHA-256 del CSV, comando, commit, versiones, procedencia GEE y bloqueos. Requisitos de entorno: Python 3.12/3.13 (TensorFlow no tiene wheel para 3.14), TensorFlow 2.20, OpenCV 4.9+, earthengine-api, Node.js 20 (legacy).

---

## 11. Riesgos y pendientes

| # | Riesgo / pendiente | Acción |
|---|---|---|
| 1 | Cifras de planes no coinciden con artefactos | Publicar solo cifras nivel A; corregir `README.md`, presentaciones y docs |
| 2 | R² real 0.0775 muy por debajo del objetivo | Calcular baselines persistence/media estacional y ampliar épocas/horizontes |
| 3 | Sin IC 95 % calibrada | Implementar bootstrap por bloque y verificar la cabeza de incertidumbre |
| 4 | CRISP-DM con autocorrelación y no normalidad | Usar errores robustos / modelos con términos autorregresivos |
| 5 | Dos familias de eventos sin unificación | **Resuelto en el [§12](#12-contrato-json-único-frontend--backend)**: contrato único `POST /api/v1/analyze` y mapeo de eventos; los aliases de compatibilidad se conservan en `shared/events/` |
| 6 | Umbral NDWI del árbol (−0.32) vs interpretación (>0.3) | Documentar que son criterios distintos en el pipeline de segmentación |
| 7 | Archivos sensibles en el repo (`services/backend-node/.env`, `config/gee-private-key.json`) | Mover a secretos de Render; no copiar a frontend ni versionar |
| 8 | La validación espacial por bloques del árbol está diferida | Ejecutar en la siguiente iteración antes de usar reglas en alertas automáticas |

---

## 12. Contrato JSON único (frontend ↔ backend)

> **Fuente de verdad de la interfaz.** Esta sección es el único lugar donde se define el shape de `POST /api/v1/analyze`. Frontend y backend deben derivar sus tipos de aquí; cualquier divergencia se corrige primero en este documento. Los endpoints `/demo/*` son de demostración (§9) y no forman parte de este contrato.

### 12.1 Request

```http
POST /api/v1/analyze
Content-Type: application/json
```

```json
{
  "area_name": "Río Combeima",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [[-75.53, 4.21], [-75.52, 4.21], [-75.52, 4.20], [-75.53, 4.21]]
    ]
  },
  "years": [1969, 2023]
}
```

| Campo | Tipo | Restricción | Justificación |
|---|---|---|---|
| `area_name` | `string` | 1–120 caracteres, UTF-8, sin espacios sobrantes al inicio/fin | Acepta tildes («Río»); se reutiliza en `report.narrative`. |
| `geometry` | GeoJSON Geometry | Solo `Polygon` o `MultiPolygon`; CRS WGS84 (EPSG:4326); posiciones `[lon, lat]`; anillos cerrados (primera = última posición) y ≥ 4 posiciones por anillo; `Feature`/`FeatureCollection` → `422` | El pipeline de morfología (§4) necesita un área recortable. |
| `years` | `integer[2]` | Exactamente 2 enteros, `1969 ≤ years[0] < years[1] ≤ 2023`, ascendentes y sin duplicados | §4 fija el periodo 1969–2023 y la comparación es entre dos épocas. |

### 12.2 Response

La forma canónica incluye el envelope usado por el resto de la API (§9, `frontend/src/lib/api.ts`): el objeto de negocio descrito en el contrato es el contenido de `data`.

```json
{
  "success": true,
  "data": {
    "metrics": {
      "ndwi_mean": 0.12,
      "ndvi_mean": 0.58,
      "channel_width_change_pct": -8.4
    },
    "forecast": {
      "dates": ["2024-01-01", "2024-02-01"],
      "caudal_m3s": [41.2, 39.8],
      "rmse": 0.0712,
      "r2": 0.0775
    },
    "report": {
      "alert_level": "watch",
      "narrative": "Texto generado por ReportingAgent…",
      "recommendations": ["Verificar sensores aguas arriba"]
    }
  }
}
```

| Campo | Tipo / rango | Convención congelada |
|---|---|---|
| `metrics.ndwi_mean` | `float` en `[-1, 1]`, 4 decimales | Media espacial de NDWI sobre `geometry` (§3). |
| `metrics.ndvi_mean` | `float` en `[-1, 1]`, 4 decimales | Media espacial de NDVI sobre `geometry` (§3). |
| `metrics.channel_width_change_pct` | `float` con signo, 2 decimales | `(ancho_final − ancho_inicial) / ancho_inicial × 100`. Negativo = estrechamiento; positivo = ensanchamiento (§4). |
| `forecast.dates` | `string[]`, `YYYY-MM-DD` | Únicas y ascendentes; mismo largo que `caudal_m3s`. |
| `forecast.caudal_m3s` | `float[]` ≥ 0, 2 decimales | Unidad m³/s; alineado índice a índice con `dates`. |
| `forecast.rmse` | `float` ≥ 0, 4 decimales | Unidad NDVI (no m³/s). Valor de ejemplo: baseline real `gru_attention_h1_3d7b5aec` (§6.2). |
| `forecast.r2` | `float` ≤ 1, **puede ser negativo**, 4 decimales | No aplicar `ge = 0`: el spec ya registra `−0.3965` y `−0.0585` (§6.2, §6.3). Valor de ejemplo: `0.0775` de la RNN real (§6.2, §0). |
| `report.alert_level` | enum `normal` \| `watch` \| `alert` \| `critical` | Etiquetas es-CO: Normal / Vigilancia / Alerta / Emergencia. Hereda la jerarquía verde/amarillo/naranja/rojo del backend legacy. |
| `report.narrative` | `string` no vacío | Generado por `ReportingAgent` (Gemini preferido, §9). |
| `report.recommendations` | `string[]` (puede ser `[]`) | Acciones priorizadas, en español. |

**Invariantes obligatorias**

- `forecast.dates.length === forecast.caudal_m3s.length` y ambas > 0.
- `r2` y `rmse` describen el modelo de `forecast`, no la clasificación de cobertura; nunca reemplazar `r2` por macro-F1 ni por accuracy (§0).
- `alert_level` es asistido por humano: el producto no toma decisiones automáticas mientras `r2` real esté por debajo del objetivo (§7).

### 12.3 Errores y versionado

Los errores **no** usan el envelope; conservan el formato de `HTTPException` de FastAPI:

```json
{ "detail": "years debe contener exactamente dos años ascendentes entre 1969 y 2023" }
```

| Código | Significado |
|---|---|
| `400` | Semántica inválida: anillo GeoJSON abierto, `years` descendente o fuera de rango. |
| `422` | Forma inválida: tipo de campo, rango numérico, enum desconocido o `geometry.type` no soportado. |
| `501` | Contrato declarado pero pipeline aún no cableado (estado actual de la fase de implementación). |
| `503` | GEE o proveedor de LLM no disponible. |
| `500` | Error interno no previsto. |

- La versión del contrato es el prefijo `/api/v1`.
- Se permiten campos nuevos **opcionales** dentro de v1. Renombrar, quitar o cambiar el tipo de un campo existente exige publicar `/api/v2`.

### 12.4 Correspondencia con los eventos del pipeline

El cuerpo de la petición y cada bloque de la respuesta corresponden a una etapa (§5), sin alterar los nombres de eventos por compatibilidad:

| Elemento del contrato | Evento | Productor |
|---|---|---|
| Request `POST /api/v1/analyze` | `analysis:requested` | Backend → GeospatialAgent |
| `data.metrics` | `analysis:completed` | VisionAgent → OracleAgent |
| `data.forecast` | `prediction:completed` | OracleAgent → ReportingAgent |
| `data.report` | `report:ready` | ReportingAgent → Backend |

Los aliases de la familia UPPER_SNAKE (`IMAGENES_HISTORICAS_LISTAS`, `IMAGEN_INDIVIDUAL_PROCESADA`, `GEOSPATIAL_AGENT_ERROR`) se conservan en `shared/events/` y no cambian este contrato HTTP.
