# RNA Combeima — Red Neuronal Recurrente para el río Combeima (Tolima)

Módulo de **redes neuronales recurrentes (RNN)** para predicción multitemporal de
índices de vegetación (NDVI/EVI) en la cuenca del **río Combeima** (Ibagué, Tolima),
usando series satelitales **multisensor** extraídas de **Google Earth Engine (GEE)**.

Sigue la metodología CRISP-DM del plan `PLAN_PROYECTO_RED_NEURONAL_GEE.md` y el
proyecto Skyfusion Analytics. Enfocado en la Fase 4 (modelado) con configuración
reproducible de **múltiples experimentos**.

## Objetivo

Configurar y ejecutar una **matriz de pruebas** que verifique:

1. Que se **extraen series multitemporales reales** (múltiples fechas por píxel
   entre 2015-2024) del área del río Combeima vía GEE.
2. Que distintas **arquitecturas de RNA** (GRU, LSTM, BiGRU, GRU+Attention, TCN)
   se entrenan y comparan con la misma config de datos.
3. Comparación por **horizonte de predicción** (1, 4, 8 pasos ≈ 16 días, 2.5 meses, 5 meses).
4. División **espacio-temporal** (sin data leakage) para evitar que el modelo vea
   el mismo píxel en train y test.

## Estructura

```
rnn_combeima/
├── config/experiments.py      # Catálogo de arquitecturas, zonas, sensores, grids, lotes
├── gee/extractor.py           # Extracción multitemporal multisensor desde GEE
├── rnn/
│   ├── models.py              # 5 arquitecturas RNA (keras)
│   ├── preprocess.py          # Limpieza, features, ventaneo, split espacial
│   ├── train.py               # Motor de experimentos (entrena y evalúa lotes)
│   └── reporting.py           # Consolida resultados y ranking
├── scripts/via_completa.py    # CLI de todo el flujo
├── data/                      # raw / processed / splits
├── experiments/               # Resultados por corrida (summary.csv + modelos)
├── reports/                   # Reportes consolidados
└── requirements.txt
```

## Instalación

Requiere **Python 3.12/3.13** (TensorFlow aún no soporta 3.14). En Windows,
si hay varias versiones instaladas, usa `py -3.13` en los comandos del proyecto.

```bash
py -3.13 -m pip install -r requirements.txt
py -3.13 -m pip install earthengine-api       # para extracción real desde GEE
earthengine authenticate                       # una sola vez
```

## Uso

### 1. Autenticación GEE (una vez)

```bash
python scripts/via_completa.py --autenticar
```

### 2. Extracción multitemporal desde Combeima

```bash
# Extrae series MODIS 2015-2024 de la cuenca del Combeima (300 puntos muestreados)
python scripts/via_completa.py --extraer --sensores modis --n-puntos 300

# Verifica que la extracción fue multitemporal (fechas por píxel, rango, etc.)
python scripts/via_completa.py --verificar
```

La verificación reporta por cada sensor: filas, píxeles únicos, **fechas únicas**,
**rango temporal**, y **media de fechas por píxel** (debe ser >> 1 para confirmar
series multitemporales reales).

### 3. Entrenar un lote de experimentos

```bash
# Sin GEE autenticado usa datos sintéticos (señal estacional realista) para validar el pipeline
python scripts/via_completa.py --entrenar --lote smoke   --epochs 4
python scripts/via_completa.py --entrenar --lote basico  --epochs 8
python scripts/via_completa.py --entrenar --lote completo --epochs 15   # 36 exps
python scripts/via_completa.py --entrenar --lote todos    --epochs 20   # 120 exps

# Con datos reales extraídos de GEE
python scripts/via_completa.py --entrenar --lote basico --epochs 30 --reales
```

### 4. Reporte comparativo

```bash
python scripts/via_completa.py --reporte
```

Genera `reports/resumen_final.csv` con el ranking RMSE/R² de todos los experimentos.

## Configuración de experimentos (`config/experiments.py`)

| Concepto | Descripción |
|----------|-------------|
| `ARQUITECTURAS_RNN` | gru, lstm, bigru, gru_attention, tcn |
| `ZONAS` | `combeima` (bbox Tolima); extensible a más cuencas |
| `SENSORES` | modis (16d), sentinel2 (5d), landsat (16d) |
| `GRID_CONFIGS` | grid_pequeno / grid_medio / grid_amplio (unidades, dropout, lr, batch) |
| `HORIZONTES_PASOS` | 1, 4, 8 pasos de 16 días |
| `LOTES` | smoke (2), basico (10), completo (36), todos (120) |

Cada experimento tiene un **ID determinista** (`arq_h{horizonte}_{hash}`) y guarda
en `experiments/run_<fecha>__<lote>/<id>/`: `best.keras`, `history.csv`, `resultado.json`.

## Modelos (`rnn/models.py`)

Todas las arquitecturas usan la misma interfaz:

```
Input:  (batch, timesteps, features)   # 24 pasos ≈ 1 año
Output: (batch, horizonte)             # NDVI futuro
```

- **gru / lstm**: bloques apilados recurrentes con BatchNorm + Dropout.
- **bigru**: GRU bidireccional (captura contexto temporal en ambas direcciones).
- **gru_attention**: GRU + capa de atención sobre timesteps (mejor en las pruebas).
- **tcn**: convoluciones causales dilatadas (`padding="causal"`, dilations 1-8).

Loss: **Huber** (robusta a outliers satelitales). Optimizador: Adam con clipnorm=1.

## Preprocesamiento (`rnn/preprocess.py`)

1. `limpiar_series` — duplicados geoespaciales, nulos, valores negativos.
2. `normalizar_q_estacional` — winsorización por percentil 1-99 por mes.
3. `crear_features_temporales` — ciclicidad (mes/doy sin+cos), lags (1,2,4), media móvil 3.
4. Escalamiento `MinMaxScaler` por feature + target por separado.
5. `construir_secuencias_por_pixel` — ventanas deslizantes, retorna `pixel_ids`.
6. Split **por píxel** (`GroupShuffleSplit` sobre `pixel_ids`) → train/val/test sin leakage.

## Extracción GEE (`gee/extractor.py`)

- `inicializar_gee(proyecto)` — sesión GEE (cuenta Google + proyecto Cloud opcional).
- `construir_serie_sensor(...)` — serie temporal por sensor sobre la cuenca
  (`toBands()` + `sampleRegions`: una sola llamada de red por sensor).
- `verificar_extraccion(df, zona)` — **verificación multitemporal** (fechas/píxel, rango).
- QA y escala por sensor (según metadatos reales del catálogo):
  - MODIS: banda de calidad **`SummaryQA`** (no existe `QA_PIXEL` en MOD13A2);
    NDVI/EVI × **0.0001**.
  - Sentinel-2: banda `SCL` (2/4/5/6 válidas); SR × 0.0001; cobertura global
    solo desde **2017-01-01**.
  - Landsat 8 L2: banda `QA_PIXEL` (bit 6 claro); SR = DN×0.0000275 − 0.2.
- Para cuentas GEE creadas desde 2023 se requiere **proyecto Cloud** con Earth
  Engine API: completar `config/experiments.py → GEE_CONFIG['proyecto_id']`

### Diagnóstico de acceso y extracción (`gee/diagnostico.py`)

Verifica en orden: SDK → credenciales → `ee.Initialize` → asset roots/proyecto →
acceso a colecciones (size) → bandas reales → fechas → solape con el ROI.

```bash
python rnn_combeima/gee/diagnostico.py            # sin proyecto
python rnn_combeima/gee/diagnostico.py --proyecto tu-proyecto-gcp
```

Si falla en el paso 2/3, ejecuta una vez:

```bash
earthengine authenticate            # abre el navegador
earthengine set_project TU_PROYECTO # cuentas post-2023
python scripts/via_completa.py --autenticar --proyecto TU_PROYECTO
```

## Estado de validación (con datos sintéticos, 8 épocas)

| Arquitectura | RMSE | R² | SMAPE | Params |
|--------------|------|-----|-------|--------|
| **gru_attention** | **0.034** | **0.979** | 11.1% | 23.7k |
| bigru | 0.043 | 0.967 | 19.1% | 59.6k |
| lstm | 0.043 | 0.966 | 12.7% | 31.8k |
| gru | 0.045 | 0.962 | 11.7% | 23.7k |
| tcn | 0.114 | 0.763 | 27.5% | 87.5k |

> Resultados con datos sintéticos (validación de pipeline). Con datos reales GEE
> la métrica de referencia debe compararse contra baselines persistence/media estacional.

## Notas

- **TensorFlow** debe ejecutarse en Python 3.12/3.13 (no existe wheel para 3.14).
- Los lotes `completo`/`todos` requieren GPU o tiempo: `completo` = 36 exps,
  `todos` = 120 exps.
- El archivo `experiments/run_*/summary.csv` y `reports/resumen_final.csv` son los
  entregables comparativos clave.