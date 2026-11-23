import json
from pathlib import Path
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell("""# Implementación de Interpolación y Regresión Lineal bajo CRISP-DM
### Skyfusion Analytics · Cuenca del Río Combeima (Ibagué, Tolima)
**Curso:** Minería de Datos · UNIMINUTO Ibagué · 2026-2  
**Metodología:** CRISP-DM (Cross-Industry Standard Process for Data Mining)

---

```
┌────────────────────────────────────────────────────────┐
│                   FASES CRISP-DM                      │
├──────────────┬─────────────────────────────────────────┤
│ Fase 1       │ Comprensión del Negocio                 │
│ Fase 2       │ Comprensión de los Datos                │
│ Fase 3       │ Preparación de Datos (Interpolación)    │
│              │ • Análisis con Serie Completa           │
│              │ • Serie Reducida de MÁXIMO 15 DATOS     │
│ Fase 4       │ Modelado (Regresión Lineal Simple/Mult) │
│ Fase 5       │ Evaluación y Diagnóstico de Residuos    │
│ Fase 6       │ Despliegue y Acciones Multiagente       │
└──────────────┴─────────────────────────────────────────┘
```"""))

cells.append(nbf.v4.new_code_cell("""import os
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración visual
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
%matplotlib inline

# Importar herramientas especializadas de Skyfusion
sys.path.insert(0, str(Path('../skills/ml_tools').resolve()))
from spectral_interpolator import SpectralTemporalInterpolator
from crisp_linear_regression import CrispLinearRegressor
"""))

cells.append(nbf.v4.new_markdown_cell("""## Fase 1: Comprensión del Negocio (Business Understanding)
- **Problema:** En la cuenca alta del río Combeima, la presencia de nubosidad recurrente interrumpe las observaciones satelitales ópticas.
- **Requerimiento Operativo:** Desarrollar el análisis tanto en la serie multitemporal completa como en una **serie compacta de MÁXIMO 15 DATOS (Mes a Mes)** para visualizaciones y reportes ejecutivos.
- **Objetivo Técnico:**
  1. Reconstruir la continuidad de la señal espectral con técnicas de interpolación matemática.
  2. Ajustar modelos de regresión lineal para aislar la tasa de cambio multianual y las relaciones biofísicas entre índices."""))

cells.append(nbf.v4.new_markdown_cell("""## Fase 2: Comprensión de los Datos (Data Understanding)
Carga y exploración del dataset multitemporal GEE de la cuenca."""))

cells.append(nbf.v4.new_code_cell("""data_path = Path('../rnn_combeima/data/raw/series_multisensor_combeima.csv')
df = pd.read_csv(data_path)
df['fecha'] = pd.to_datetime(df['fecha'])
df = df.sort_values('fecha').reset_index(drop=True)

print(f"Total observaciones: {len(df)}")
print(f"Rango temporal: {df['fecha'].min().date()} a {df['fecha'].max().date()}")
display(df.describe().T)
"""))

cells.append(nbf.v4.new_markdown_cell("""## Fase 3: Preparación de los Datos (Data Preparation) — Interpolación

### 3.1 Serie Reducida de MÁXIMO 15 DATOS (Mes a Mes)
El enfoque **Mes a Mes** (15 meses continuos) captura fielmente el régimen bimodal de lluvias del Combeima (picos húmedos en abril-mayo y octubre-noviembre) y permite visualizar con total claridad la acción de la interpolación al enmascarar meses nublados."""))

cells.append(nbf.v4.new_code_cell("""interpolator = SpectralTemporalInterpolator(date_col='fecha')

# Agrupar a 15 meses continuos
df_15m = interpolator.resample_to_max_points(df, max_points=15, mode='mes_a_mes', numeric_cols=['NDVI', 'EVI'])
print(f"Serie de 15 datos generada: {len(df_15m)} registros")

# Simular 2 meses con pérdida por nubosidad (NaN)
df_15m_huecos = df_15m.copy()
huecos = [3, 10] # Meses simulados sin datos
df_15m_huecos.loc[huecos, 'NDVI'] = np.nan

# Interpolar con métodos Lineal y PCHIP
s_lineal_15 = interpolator.interpolate_series(df_15m_huecos['NDVI'], method='linear')
s_pchip_15 = interpolator.interpolate_series(df_15m_huecos['NDVI'], method='pchip')

tabla_15 = pd.DataFrame({
    'Mes': df_15m['fecha'].dt.strftime('%Y-%m'),
    'NDVI_Real': df_15m['NDVI'].round(4),
    'Con_Nubes_NaN': df_15m_huecos['NDVI'].round(4),
    'Interp_Lineal': s_lineal_15.round(4),
    'Interp_PCHIP': s_pchip_15.round(4)
})
display(tabla_15)

# Visualización gráfica de los 15 datos
plt.figure(figsize=(11, 4.5))
plt.plot(tabla_15['Mes'], tabla_15['NDVI_Real'], 'o--', color='#64748b', alpha=0.5, label='NDVI Real')
plt.plot(tabla_15['Mes'], s_lineal_15, 's-', color='#0284c7', lw=1.8, label='Interpolación Lineal')
plt.plot(tabla_15['Mes'], s_pchip_15, '^-', color='#10b981', lw=1.8, label='Interpolación PCHIP')
for h in huecos:
    plt.axvspan(h - 0.25, h + 0.25, color='#fbbf24', alpha=0.25, label='Mes Nublado (Imputado)' if h == huecos[0] else '')
plt.title('Demostración de Interpolación en Serie de 15 Meses (Combeima)')
plt.xticks(rotation=45)
plt.ylabel('NDVI')
plt.legend()
plt.tight_layout()
plt.show()
"""))

cells.append(nbf.v4.new_markdown_cell("""### 3.2 Evaluación Comparativa sobre la Serie Completa
Evaluación objetiva simulando un 20% de huecos artificiales en la serie histórica."""))

cells.append(nbf.v4.new_code_cell("""serie_media = df.groupby('fecha')[['NDVI', 'EVI']].mean().reset_index()
eval_interp = interpolator.evaluate_methods(serie_media['NDVI'], gap_percentage=0.20, gap_block_size=3)
display(eval_interp)

serie_interp = interpolator.interpolate_dataframe(serie_media, value_cols=['NDVI', 'EVI'], method='time')
"""))

cells.append(nbf.v4.new_markdown_cell("""## Fase 4: Modelado (Modeling) — Regresión Lineal

### 4.1 Regresión Lineal en Serie de 15 Meses
Modelado de la tendencia mes a mes en el periodo reciente."""))

cells.append(nbf.v4.new_code_cell("""df_15m['t_step'] = np.arange(len(df_15m))
reg_15 = CrispLinearRegressor(model_type='simple', scale_features=False)
reg_15.fit(df_15m[['t_step']], df_15m['NDVI'])

print("Pendiente mensual estimada:", reg_15.coefficients_['t_step'])
print("Intercepto:", reg_15.intercept_)

plt.figure(figsize=(10, 4))
plt.scatter(df_15m['t_step'], df_15m['NDVI'], color='#0284c7', label='Datos Mensuales (15 puntos)')
plt.plot(df_15m['t_step'], reg_15.predict(df_15m[['t_step']]), 'r--', label='Línea de Tendencia OLS')
plt.title('Regresión Lineal Simple sobre Serie Reducida de 15 Meses')
plt.xlabel('Paso Temporal (Mes)')
plt.ylabel('NDVI')
plt.legend()
plt.show()
"""))

cells.append(nbf.v4.new_markdown_cell("""### 4.2 Regresión Lineal Múltiple en Serie Completa"""))

cells.append(nbf.v4.new_code_cell("""serie_interp['dia_juliano'] = serie_interp['fecha'].dt.dayofyear
serie_interp['t_step'] = (serie_interp['fecha'] - serie_interp['fecha'].min()).dt.days
serie_interp['sen_estacional'] = np.sin(2 * np.pi * serie_interp['dia_juliano'] / 365.25)
serie_interp['cos_estacional'] = np.cos(2 * np.pi * serie_interp['dia_juliano'] / 365.25)

features = ['t_step', 'EVI', 'sen_estacional', 'cos_estacional']
X = serie_interp[features]
y = serie_interp['NDVI']

split_idx = int(len(serie_interp) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

reg_multiple = CrispLinearRegressor(model_type='multiple', scale_features=True)
reg_multiple.fit(X_train, y_train)
print('Coeficientes ajustados:', reg_multiple.coefficients_)
"""))

cells.append(nbf.v4.new_markdown_cell("""## Fase 5: Evaluación (Evaluation) y Diagnóstico de Residuos"""))

cells.append(nbf.v4.new_code_cell("""metricas_15 = reg_15.evaluate(df_15m[['t_step']], df_15m['NDVI'])
metricas_mult = reg_multiple.evaluate(X_test, y_test)

print("=== Evaluación Serie 15 Meses ===")
print(f"R²: {metricas_15['r2']} | RMSE: {metricas_15['rmse']}")

print("\\n=== Evaluación Serie Completa Múltiple ===")
print(f"R²: {metricas_mult['r2']} | RMSE: {metricas_mult['rmse']}")
print(f"Durbin-Watson: {metricas_mult['diagnostico_residuos']['durbin_watson']}")
"""))

cells.append(nbf.v4.new_markdown_cell("""## Fase 6: Despliegue (Deployment)
Integración con los agentes de Skyfusion Analytics (`OracleAgent` y `ReportingAgent`)."""))

cells.append(nbf.v4.new_code_cell("""despliegue_file = Path('../reports/crisp_dm/alerta_despliegue_skyfusion.json')
if despliegue_file.exists():
    with open(despliegue_file, 'r', encoding='utf-8') as f:
        alerta = json.load(f)
    print(json.dumps(alerta, indent=2))
"""))

nb.cells = cells
out_path = Path('notebooks/04_crisp_dm_interpolacion_regresion.ipynb')
with open(out_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print(f"✔ Notebook CRISP-DM actualizado exitosamente en: {out_path}")
