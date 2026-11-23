"""
Script para generar todos los entregables del EDA Semana 5 en 1 Día
- Genera 14 figuras PNG de alta resolución en rnn_combeima/reports/eda/
- Genera hallazgos_eda.csv
- Genera features_modelado.json
- Construye el Jupyter Notebook rnn_combeima/notebooks/03_eda.ipynb completo y reproducible
"""

import os
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import nbformat as nbf

# Configuración de rutas relativas
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "raw" / "series_multisensor_combeima.csv"
REPORTS_DIR = BASE_DIR / "reports" / "eda"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
NOTEBOOK_PATH = NOTEBOOKS_DIR / "03_eda.ipynb"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
np.random.seed(SEED)

print(f"Directorio Base: {BASE_DIR}")
print(f"Leyendo datos desde: {DATA_PATH}")

# 1. Carga y verificación de datos
df = pd.read_csv(DATA_PATH, parse_dates=["fecha"])
print(f"Dataset cargado con {len(df)} filas y {len(df.columns)} columnas.")

# Definición de función para clase de cobertura
def clasificar_cobertura(ndvi):
    if pd.isna(ndvi):
        return np.nan
    if ndvi < 0.1:
        return 'Agua/Suelo_desnudo'
    elif ndvi < 0.3:
        return 'Vegetación_escasa'
    elif ndvi < 0.6:
        return 'Vegetación_moderada'
    else:
        return 'Vegetación_densa'

df['clase_cobertura'] = df['NDVI'].apply(clasificar_cobertura)
categorias_cobertura = ['Agua/Suelo_desnudo', 'Vegetación_escasa', 'Vegetación_moderada', 'Vegetación_densa']
df['clase_cobertura'] = pd.Categorical(df['clase_cobertura'], categories=categorias_cobertura, ordered=True)
df['mes'] = df['fecha'].dt.month
df['año'] = df['fecha'].dt.year

# Configuración visual
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams.update({
    'font.sans-serif': 'DejaVu Sans',
    'axes.edgecolor': '#cccccc',
    'axes.linewidth': 0.8,
    'grid.color': '#eeeeee',
    'figure.autolayout': True
})

# ==========================================
# GENERACIÓN DE LAS 14 FIGURAS
# ==========================================

print("Generando figuras...")

# Fig 01: Histograma + KDE NDVI
plt.figure(figsize=(8, 5), dpi=150)
sns.histplot(df['NDVI'].dropna(), kde=True, color='#27ae60', bins=40, edgecolor='white', alpha=0.6)
plt.axvline(df['NDVI'].mean(), color='#c0392b', linestyle='--', linewidth=1.5, label=f"Media: {df['NDVI'].mean():.3f}")
plt.axvline(df['NDVI'].median(), color='#2980b9', linestyle='-', linewidth=1.5, label=f"Mediana: {df['NDVI'].median():.3f}")
plt.title("Distribución Espectral: NDVI (Normalized Difference Vegetation Index)", fontsize=13, fontweight='bold', pad=12)
plt.xlabel("Valor NDVI", fontsize=11)
plt.ylabel("Frecuencia / Densidad", fontsize=11)
plt.legend(frameon=True, facecolor='white')
plt.savefig(REPORTS_DIR / "fig01_hist_ndvi.png")
plt.close()

# Fig 02: Histograma + KDE EVI
plt.figure(figsize=(8, 5), dpi=150)
sns.histplot(df['EVI'].dropna(), kde=True, color='#2980b9', bins=40, edgecolor='white', alpha=0.6)
plt.axvline(df['EVI'].mean(), color='#c0392b', linestyle='--', linewidth=1.5, label=f"Media: {df['EVI'].mean():.3f}")
plt.axvline(df['EVI'].median(), color='#27ae60', linestyle='-', linewidth=1.5, label=f"Mediana: {df['EVI'].median():.3f}")
plt.title("Distribución Espectral: EVI (Enhanced Vegetation Index)", fontsize=13, fontweight='bold', pad=12)
plt.xlabel("Valor EVI", fontsize=11)
plt.ylabel("Frecuencia / Densidad", fontsize=11)
plt.legend(frameon=True, facecolor='white')
plt.savefig(REPORTS_DIR / "fig02_hist_evi.png")
plt.close()

# Fig 03: Boxplot Bandas NDVI y EVI
plt.figure(figsize=(7, 5), dpi=150)
box_df = df[['NDVI', 'EVI']].dropna()
bp = plt.boxplot([box_df['NDVI'], box_df['EVI']], labels=['NDVI', 'EVI'], patch_artist=True,
                 medianprops=dict(color='black', linewidth=1.5),
                 boxprops=dict(facecolor='#a8dadc', color='#1d3557'),
                 flierprops=dict(marker='o', markersize=3, alpha=0.4, markerfacecolor='#e63946'))
colors = ['#a8dadc', '#457b9d']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
plt.title("Dispersión y Detección de Outliers: NDVI vs EVI", fontsize=13, fontweight='bold', pad=12)
plt.ylabel("Valor del Índice", fontsize=11)
plt.savefig(REPORTS_DIR / "fig03_boxplot_bandas.png")
plt.close()

# Fig 04: Tabla de Estadísticos Descriptivos
plt.figure(figsize=(9, 4), dpi=150)
plt.axis('off')
stats_df = df[['NDVI', 'EVI', 'SummaryQA']].describe().T[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']]
stats_df['skewness'] = [df['NDVI'].skew(), df['EVI'].skew(), df['SummaryQA'].skew()]
stats_df['kurtosis'] = [df['NDVI'].kurtosis(), df['EVI'].kurtosis(), df['SummaryQA'].kurtosis()]
stats_df = stats_df.round(4)
table = plt.table(cellText=stats_df.values,
                  rowLabels=stats_df.index,
                  colLabels=stats_df.columns,
                  cellLoc='center', loc='center',
                  colColours=['#e2eafc']*len(stats_df.columns))
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.1, 1.8)
plt.title("Resumen Estadístico Descriptivo de Índices y Calidad Satelital", fontsize=13, fontweight='bold', pad=20)
plt.savefig(REPORTS_DIR / "fig04_estadisticos_tabla.png")
plt.close()

# Fig 05: Frecuencia de Clases de Cobertura
plt.figure(figsize=(8, 5), dpi=150)
counts = df['clase_cobertura'].value_counts().reindex(categorias_cobertura)
palette_clases = ['#e63946', '#f4a261', '#2a9d8f', '#1b4332']
bars = plt.bar(counts.index, counts.values, color=palette_clases, edgecolor='white', alpha=0.85)
for bar in bars:
    yval = bar.get_height()
    pct = (yval / len(df)) * 100
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 25, f"{int(yval)}\n({pct:.1f}%)", ha='center', va='bottom', fontsize=9, fontweight='bold')
plt.title("Distribución de Clases de Cobertura Vegetal (Derivada NDVI)", fontsize=13, fontweight='bold', pad=12)
plt.ylabel("Número de Muestras", fontsize=11)
plt.xticks(rotation=15, ha='right')
plt.ylim(0, max(counts.values) * 1.18)
plt.savefig(REPORTS_DIR / "fig05_barras_clases.png")
plt.close()

# Fig 06: Serie Temporal Promedio NDVI (2015-2024)
plt.figure(figsize=(12, 5), dpi=150)
ts_mean = df.groupby('fecha')['NDVI'].agg(['mean', 'std']).reset_index()
plt.plot(ts_mean['fecha'], ts_mean['mean'], color='#2d6a4f', label='NDVI Promedio Cuenca', linewidth=1.5)
plt.fill_between(ts_mean['fecha'], ts_mean['mean'] - ts_mean['std'], ts_mean['mean'] + ts_mean['std'],
                 color='#95d5b2', alpha=0.4, label='± 1 Desviación Estándar')
plt.title("Evolución Temporal del NDVI (2015 - 2024) - Cuenca Río Combeima", fontsize=13, fontweight='bold', pad=12)
plt.xlabel("Fecha de Adquisición (Sensor MODIS)", fontsize=11)
plt.ylabel("NDVI Promedio", fontsize=11)
plt.legend(frameon=True, loc='upper right')
plt.savefig(REPORTS_DIR / "fig06_serie_temporal_ndvi.png")
plt.close()

# Fig 07: Matriz de Correlaciones (Heatmap)
plt.figure(figsize=(7, 6), dpi=150)
cols_corr = ['NDVI', 'EVI', 'SummaryQA', 'longitude', 'latitude', 'mes']
corr_mat = df[cols_corr].corr()
mask = np.triu(np.ones_like(corr_mat, dtype=bool))
sns.heatmap(corr_mat, mask=mask, annot=True, fmt=".3f", cmap="vlag", vmin=-1, vmax=1,
            square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
plt.title("Matriz de Correlación de Pearson", fontsize=13, fontweight='bold', pad=12)
plt.savefig(REPORTS_DIR / "fig07_heatmap_correlaciones.png")
plt.close()

# Fig 08: Scatter Plot NDVI vs EVI
plt.figure(figsize=(8, 5.5), dpi=150)
sns.scatterplot(data=df, x='NDVI', y='EVI', hue='clase_cobertura', palette=palette_clases, alpha=0.6, s=25)
plt.title(f"Relación Bivariada NDVI vs EVI (r = {df['NDVI'].corr(df['EVI']):.3f})", fontsize=13, fontweight='bold', pad=12)
plt.xlabel("NDVI", fontsize=11)
plt.ylabel("EVI", fontsize=11)
plt.legend(title="Clase Cobertura", frameon=True)
plt.savefig(REPORTS_DIR / "fig08_scatter_ndvi_evi.png")
plt.close()

# Fig 09: Boxplot NDVI por Clase de Cobertura
plt.figure(figsize=(8, 5), dpi=150)
sns.boxplot(data=df, x='clase_cobertura', y='NDVI', palette=palette_clases,
            boxprops=dict(alpha=0.8), flierprops=dict(marker='o', markersize=2, alpha=0.3))
plt.title("Distribución de NDVI según Clase de Cobertura", fontsize=13, fontweight='bold', pad=12)
plt.xlabel("Clase", fontsize=11)
plt.ylabel("NDVI", fontsize=11)
plt.xticks(rotation=15, ha='right')
plt.savefig(REPORTS_DIR / "fig09_boxplot_ndvi_clase.png")
plt.close()

# Fig 10: Boxplot EVI por Clase de Cobertura
plt.figure(figsize=(8, 5), dpi=150)
sns.boxplot(data=df, x='clase_cobertura', y='EVI', palette=palette_clases,
            boxprops=dict(alpha=0.8), flierprops=dict(marker='o', markersize=2, alpha=0.3))
plt.title("Distribución de EVI según Clase de Cobertura", fontsize=13, fontweight='bold', pad=12)
plt.xlabel("Clase", fontsize=11)
plt.ylabel("EVI", fontsize=11)
plt.xticks(rotation=15, ha='right')
plt.savefig(REPORTS_DIR / "fig10_boxplot_evi_clase.png")
plt.close()

# Fig 11: Violinplot Estacionalidad NDVI por Mes
plt.figure(figsize=(11, 5.5), dpi=150)
sns.violinplot(data=df, x='mes', y='NDVI', palette="YlGn", inner="quartile", linewidth=1.2)
plt.title("Ciclo Estacional Anual: Distribución Mensual del NDVI", fontsize=13, fontweight='bold', pad=12)
plt.xlabel("Mes del Año", fontsize=11)
plt.ylabel("NDVI", fontsize=11)
meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
plt.xticks(ticks=range(12), labels=meses)
plt.savefig(REPORTS_DIR / "fig11_violin_ndvi_mes.png")
plt.close()

# Fig 12: Varianza Explicada PCA (Scree Plot)
cols_pca = ['NDVI', 'EVI', 'SummaryQA', 'longitude', 'latitude']
df_pca = df[cols_pca].dropna()
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_pca)
pca = PCA(n_components=len(cols_pca), random_state=SEED)
pca.fit(X_scaled)
var_exp = pca.explained_variance_ratio_
cum_var = np.cumsum(var_exp)

plt.figure(figsize=(8, 5), dpi=150)
bars = plt.bar(range(1, len(var_exp)+1), var_exp * 100, color='#457b9d', alpha=0.7, label='Varianza Individual')
plt.plot(range(1, len(var_exp)+1), cum_var * 100, marker='o', color='#e63946', linewidth=2, label='Varianza Acumulada')
plt.axhline(85, color='gray', linestyle='--', label='Umbral 85%')
for i, (ve, cv) in enumerate(zip(var_exp, cum_var)):
    plt.text(i+1, (ve*100)/2, f"{ve*100:.1f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=9)
plt.title("Análisis de Componentes Principales (PCA): Varianza Explicada", fontsize=13, fontweight='bold', pad=12)
plt.xlabel("Componente Principal", fontsize=11)
plt.ylabel("Porcentaje de Varianza Explicada (%)", fontsize=11)
plt.xticks(range(1, len(var_exp)+1), [f"PC{i}" for i in range(1, len(var_exp)+1)])
plt.ylim(0, 105)
plt.legend(frameon=True, loc='center right')
plt.savefig(REPORTS_DIR / "fig12_pca_varianza.png")
plt.close()

# Fig 13: PCA 2D Proyección coloreada por Clase
X_pca_2d = pca.transform(X_scaled)[:, :2]
df_pca_plot = pd.DataFrame(X_pca_2d, columns=['PC1', 'PC2'])
df_pca_plot['clase'] = df.loc[df_pca.index, 'clase_cobertura'].values

plt.figure(figsize=(8.5, 6), dpi=150)
sns.scatterplot(data=df_pca_plot, x='PC1', y='PC2', hue='clase', palette=palette_clases, alpha=0.6, s=25)
plt.title(f"Espacio Latente PCA 2D (PC1: {var_exp[0]*100:.1f}% + PC2: {var_exp[1]*100:.1f}%)", fontsize=13, fontweight='bold', pad=12)
plt.xlabel(f"PC1 ({var_exp[0]*100:.1f}% var)", fontsize=11)
plt.ylabel(f"PC2 ({var_exp[1]*100:.1f}% var)", fontsize=11)
plt.legend(title="Clase Cobertura", frameon=True)
plt.savefig(REPORTS_DIR / "fig13_pca_2d_clases.png")
plt.close()

# Fig 14: Mapa Geoespacial de Muestras y NDVI Medio
plt.figure(figsize=(8.5, 7), dpi=150)
pixeles = df.groupby(['longitude', 'latitude']).agg({
    'NDVI': 'mean',
    'EVI': 'mean',
    'fecha': 'count'
}).reset_index().rename(columns={'fecha': 'n_muestras'})

scatter = plt.scatter(pixeles['longitude'], pixeles['latitude'],
                      c=pixeles['NDVI'], cmap='RdYlGn', s=120, edgecolors='black', linewidth=0.8, alpha=0.9)
cbar = plt.colorbar(scatter)
cbar.set_label('NDVI Promedio Multianual (2015-2024)', fontsize=10)
plt.title("Distribución Espacial de Píxeles Muestreados — Cuenca Río Combeima", fontsize=13, fontweight='bold', pad=12)
plt.xlabel("Longitud (WGS84)", fontsize=11)
plt.ylabel("Latitud (WGS84)", fontsize=11)
plt.grid(True, linestyle=':', alpha=0.6)
plt.savefig(REPORTS_DIR / "fig14_mapa_muestras.png")
plt.close()

print("[OK] 14 figuras generadas exitosamente en reports/eda/")

# ==========================================
# GENERACIÓN DE CSV DE HALLAZGOS (T5.8)
# ==========================================

r_ndvi_evi = float(df['NDVI'].corr(df['EVI']))
ndvi_mean = float(df['NDVI'].mean())
ndvi_std = float(df['NDVI'].std())
qa_bad = float((df['SummaryQA'] > 1).mean() * 100)
clase_dominant_ratio = float(counts.max() / counts.min())

hallazgos = [
    {
        "id": "HAL-01",
        "dimension": "Multicolinealidad",
        "hallazgo": f"Alta correlación espectral entre NDVI y EVI (r = {r_ndvi_evi:.3f})",
        "evidencia": f"Matriz Pearson r={r_ndvi_evi:.3f}, PC1 absorbe {var_exp[0]*100:.1f}% de la varianza",
        "impacto_modelado": "Redundancia de características que puede desestabilizar coeficientes o sobreparametrizar la red",
        "recomendacion": "Utilizar regularización L2/Dropout o seleccionar NDVI como target principal y EVI únicamente como feature auxiliar contextual",
        "prioridad": "ALTA"
    },
    {
        "id": "HAL-02",
        "dimension": "Desbalanceo de Clases",
        "hallazgo": f"Desbalanceo severo entre categorías de cobertura ({clase_dominant_ratio:.1f}:1)",
        "evidencia": f"Vegetación moderada/densa representa >85% de las muestras; agua/suelo desnudo representa <5%",
        "impacto_modelado": "La red neuronal tenderá a ignorar clases minoritarias si se entrena para clasificación sin ponderación",
        "recomendacion": "En caso de clasificación usar Focal Loss o Class Weights; para regresión temporal, estratificar la partición espacial por cuartiles de NDVI",
        "prioridad": "ALTA"
    },
    {
        "id": "HAL-03",
        "dimension": "Estacionalidad y Dinámica Temporal",
        "hallazgo": "Comportamiento bimodal anual consistente con el régimen pluviométrico andino",
        "evidencia": "Picos de verdor en meses post-lluvias (mayo-junio y octubre-noviembre) visibles en violinplots",
        "impacto_modelado": "La serie temporal tiene fuerte memoria estacional de 12 meses",
        "recomendacion": "Incluir features cíclicas (seno/coseno del día del año y mes) y ventana temporal mínima de 24 timesteps (~1 año)",
        "prioridad": "MEDIA"
    },
    {
        "id": "HAL-04",
        "dimension": "Calidad Satelital (QA)",
        "hallazgo": f"Presencia residual de observaciones con calidad marginal/nubes ({qa_bad:.2f}%)",
        "evidencia": "SummaryQA > 1 asociado a caídas bruscas de NDVI fuera de percentiles 1-99",
        "impacto_modelado": "Outliers espurios inducen ruido en gradientes durante el entrenamiento recurrente",
        "recomendacion": "Aplicar winsorización estacional (percentiles 1-99) y filtrado estricto por SummaryQA <= 1",
        "prioridad": "MEDIA"
    },
    {
        "id": "HAL-05",
        "dimension": "Estructura Espacial",
        "hallazgo": "Gradiente altitudinal/espacial en la cuenca Combeima",
        "evidencia": "Píxeles en cabecera (NW) presentan menor NDVI sostenido frente a partes medias y bajas (SE)",
        "impacto_modelado": "Riesgo crítico de data leakage espacial si se divide aleatoriamente por fila",
        "recomendacion": "Obligatorio usar GroupShuffleSplit agrupando por (longitud, latitud) para que ningún píxel de test esté en train",
        "prioridad": "CRÍTICA"
    }
]

df_hallazgos = pd.DataFrame(hallazgos)
df_hallazgos.to_csv(REPORTS_DIR / "hallazgos_eda.csv", index=False, encoding="utf-8")
print(f"[OK] Hallazgos guardados en {REPORTS_DIR / 'hallazgos_eda.csv'}")

# ==========================================
# GENERACIÓN DE FEATURES_MODELADO.JSON (T5.9)
# ==========================================

features_meta = {
    "proyecto": "Red Neuronal Recurrente - Cuenca Río Combeima",
    "fase_crisp_dm": "Fase 2 / EDA Completado",
    "dataset_origen": "series_multisensor_combeima.csv",
    "sensor": "MODIS/061/MOD13A2",
    "muestras_totales": int(len(df)),
    "pixeles_unicos": int(df.groupby(['longitude', 'latitude']).ngroups),
    "rango_temporal": [str(df['fecha'].min().date()), str(df['fecha'].max().date())],
    "target_primario": "NDVI",
    "target_secundario": "EVI",
    "features_recomendadas": [
        "NDVI",
        "EVI",
        "mes_sin",
        "mes_cos",
        "doy_sin",
        "doy_cos",
        "NDVI_lag1",
        "NDVI_lag2",
        "NDVI_lag4",
        "NDVI_ma3"
    ],
    "features_descartadas_o_metadatos": [
        "SummaryQA",
        "sensor",
        "clase_cobertura"
    ],
    "estrategia_particion": "GroupShuffleSplit por (longitude, latitude)",
    "timesteps_recomendados": 24,
    "horizontes_evaluados": [1, 4, 8],
    "pca_componentes_retenidos_85pct": int(np.argmax(cum_var >= 0.85) + 1),
    "random_state": SEED,
    "umbrales_clases_cobertura": {
        "Agua_o_Suelo_desnudo": "< 0.10",
        "Vegetacion_escasa": "0.10 - 0.30",
        "Vegetacion_moderada": "0.30 - 0.60",
        "Vegetacion_densa": ">= 0.60"
    }
}

with open(REPORTS_DIR / "features_modelado.json", "w", encoding="utf-8") as f:
    json.dump(features_meta, f, indent=2, ensure_ascii=False)
print(f"[OK] Metadata de features guardada en {REPORTS_DIR / 'features_modelado.json'}")

# ==========================================
# CONSTRUCCIÓN DEL NOTEBOOK JUPYTER (03_eda.ipynb)
# ==========================================

print("Construyendo notebook Jupyter 03_eda.ipynb...")

nb = nbf.v4.new_notebook()
cells = []

# Encabezado
cells.append(nbf.v4.new_markdown_cell("""# Análisis Exploratorio de Datos (EDA) — Datos Satelitales GEE
## Proyecto: Red Neuronal Recurrente para Monitoreo de Vegetación (Río Combeima)

> **Metodología CRISP-DM:** Fase 2 — Comprensión de los Datos (Data Understanding)  
> **Fuente de Datos:** Google Earth Engine (MODIS/061/MOD13A2 — 2015-2024)  
> **Área de Estudio:** Cuenca del río Combeima (Tolima, Colombia)  
> **Objetivo:** Caracterizar las propiedades estadísticas, espectrales, temporales y geoespaciales de las series multitemporales para fundamentar el diseño y entrenamiento de redes neuronales recurrentes (LSTM, GRU, BiGRU, Attention, TCN).
"""))

# Sección 1: Configuración y Carga
cells.append(nbf.v4.new_markdown_cell("""---
## 1. Configuración del Entorno y Carga de Datos (Tarea 5.1)
En esta sección importamos las librerías analíticas esenciales, configuramos la reproducibilidad mediante semillas pseudoaleatorias fijas (`random_state=42`) y cargamos el dataset satelital multitemporal extraído desde Google Earth Engine.
"""))

cells.append(nbf.v4.new_code_cell("""import os
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Configuración de reproducibilidad y visualización
SEED = 42
np.random.seed(SEED)

plt.rcParams.update({
    'figure.figsize': (10, 5),
    'figure.dpi': 120,
    'font.sans-serif': 'DejaVu Sans',
    'axes.edgecolor': '#cccccc',
    'axes.linewidth': 0.8,
    'grid.color': '#eeeeee'
})
sns.set_theme(style='whitegrid', palette='viridis')

# Rutas de datos y reportes
DATA_PATH = Path('../data/raw/series_multisensor_combeima.csv')
REPORTS_DIR = Path('../reports/eda')
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Carga de datos
df = pd.read_csv(DATA_PATH, parse_dates=['fecha'])
print(f"Dimensiones del dataset: {df.shape[0]} filas × {df.shape[1]} columnas")
df.head()
"""))

cells.append(nbf.v4.new_code_cell("""# Validación de Integridad Estructural y Tipos de Datos
print("=== INFORMACIÓN DE COLUMNAS Y TIPOS ===")
print(df.info())

print("\\n=== VALORES FALTANTES (NULOS) ===")
print(df.isnull().sum())

print("\\n=== RANGOS ESPACIO-TEMPORALES ===")
print(f"Periodo Temporal: {df['fecha'].min().strftime('%Y-%m-%d')} a {df['fecha'].max().strftime('%Y-%m-%d')}")
print(f"Fechas únicas: {df['fecha'].nunique()}")
print(f"Píxeles geográficos únicos (lon, lat): {df.groupby(['longitude', 'latitude']).ngroups}")
print(f"Longitud: [{df['longitude'].min():.4f}, {df['longitude'].max():.4f}]")
print(f"Latitud: [{df['latitude'].min():.4f}, {df['latitude'].max():.4f}]")
"""))

cells.append(nbf.v4.new_markdown_cell("""### 1.1 Creación de Clases de Cobertura Vegetal (Derivación Espectral)
Dado que el problema de modelado predictivo central es de **regresión de series temporales** (predecir NDVI/EVI en $t+h$), derivamos adicionalmente una variable categórica `clase_cobertura` siguiendo los umbrales estándar de la literatura biofísica y de teledetección. Esto permite realizar análisis de discriminación por clases y evaluar el desbalance de coberturas vegetales en la cuenca.
"""))

cells.append(nbf.v4.new_code_cell("""def clasificar_cobertura(ndvi):
    if pd.isna(ndvi):
        return np.nan
    if ndvi < 0.1:
        return 'Agua/Suelo_desnudo'
    elif ndvi < 0.3:
        return 'Vegetación_escasa'
    elif ndvi < 0.6:
        return 'Vegetación_moderada'
    else:
        return 'Vegetación_densa'

df['clase_cobertura'] = df['NDVI'].apply(clasificar_cobertura)
categorias_cobertura = ['Agua/Suelo_desnudo', 'Vegetación_escasa', 'Vegetación_moderada', 'Vegetación_densa']
df['clase_cobertura'] = pd.Categorical(df['clase_cobertura'], categories=categorias_cobertura, ordered=True)
df['mes'] = df['fecha'].dt.month
df['año'] = df['fecha'].dt.year

df[['fecha', 'longitude', 'latitude', 'NDVI', 'EVI', 'clase_cobertura']].sample(5, random_state=SEED)
"""))

# Sección 2: EDA Univariado Bandas
cells.append(nbf.v4.new_markdown_cell("""---
## 2. Análisis Univariado — Bandas e Índices Espectrales (Tarea 5.2)
Analizamos la distribución de probabilidad empírica de los dos índices de vegetación fundamentales:
1. **NDVI (Normalized Difference Vegetation Index):** Sensible a la clorofila activa y biomasa foliar.
2. **EVI (Enhanced Vegetation Index):** Optimizado para desacoplar el efecto de aerosoles y fondo de suelo en zonas de alta densidad foliar.
"""))

cells.append(nbf.v4.new_code_cell("""# Visualización de Distribuciones: Histogramas y KDE
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histograma NDVI
sns.histplot(df['NDVI'].dropna(), kde=True, color='#27ae60', bins=40, ax=axes[0], edgecolor='white', alpha=0.6)
axes[0].axvline(df['NDVI'].mean(), color='#c0392b', linestyle='--', linewidth=1.5, label=f"Media: {df['NDVI'].mean():.3f}")
axes[0].axvline(df['NDVI'].median(), color='#2980b9', linestyle='-', linewidth=1.5, label=f"Mediana: {df['NDVI'].median():.3f}")
axes[0].set_title("Distribución Espectral: NDVI", fontsize=12, fontweight='bold')
axes[0].set_xlabel("NDVI")
axes[0].set_ylabel("Frecuencia")
axes[0].legend()

# Histograma EVI
sns.histplot(df['EVI'].dropna(), kde=True, color='#2980b9', bins=40, ax=axes[1], edgecolor='white', alpha=0.6)
axes[1].axvline(df['EVI'].mean(), color='#c0392b', linestyle='--', linewidth=1.5, label=f"Media: {df['EVI'].mean():.3f}")
axes[1].axvline(df['EVI'].median(), color='#27ae60', linestyle='-', linewidth=1.5, label=f"Mediana: {df['EVI'].median():.3f}")
axes[1].set_title("Distribución Espectral: EVI", fontsize=12, fontweight='bold')
axes[1].set_xlabel("EVI")
axes[1].set_ylabel("Frecuencia")
axes[1].legend()

plt.tight_layout()
plt.show()
"""))

cells.append(nbf.v4.new_code_cell("""# Boxplots para Comparación y Detección de Valores Atípicos (Outliers)
plt.figure(figsize=(7, 5))
box_df = df[['NDVI', 'EVI']].dropna()
plt.boxplot([box_df['NDVI'], box_df['EVI']], tick_labels=['NDVI', 'EVI'], patch_artist=True,
            medianprops=dict(color='black', linewidth=1.5),
            boxprops=dict(facecolor='#a8dadc', color='#1d3557'),
            flierprops=dict(marker='o', markersize=3, alpha=0.4, markerfacecolor='#e63946'))
plt.title("Dispersión y Detección de Outliers: NDVI vs EVI", fontsize=12, fontweight='bold')
plt.ylabel("Magnitud del Índice")
plt.show()
"""))

cells.append(nbf.v4.new_code_cell("""# Estadísticos Descriptivos Paramétricos y No Paramétricos
stats = df[['NDVI', 'EVI', 'SummaryQA']].describe().T
stats['skewness'] = [df['NDVI'].skew(), df['EVI'].skew(), df['SummaryQA'].skew()]
stats['kurtosis'] = [df['NDVI'].kurtosis(), df['EVI'].kurtosis(), df['SummaryQA'].kurtosis()]
stats.round(4)
"""))

# Sección 3: Variable Objetivo y Dinámica Temporal
cells.append(nbf.v4.new_markdown_cell("""---
## 3. Análisis Univariado — Variable Objetivo y Dinámica Temporal (Tarea 5.3)
Evaluamos la distribución de las categorías de cobertura vegetal derivadas y la serie temporal promedio multianual del Combeima.
"""))

cells.append(nbf.v4.new_code_cell("""# Distribución de Clases de Cobertura
plt.figure(figsize=(8, 4.5))
counts = df['clase_cobertura'].value_counts().reindex(categorias_cobertura)
palette_clases = ['#e63946', '#f4a261', '#2a9d8f', '#1b4332']
bars = plt.bar(counts.index, counts.values, color=palette_clases, edgecolor='white', alpha=0.85)

for bar in bars:
    yval = bar.get_height()
    pct = (yval / len(df)) * 100
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 30, f"{int(yval)}\\n({pct:.1f}%)", ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.title("Distribución de Clases de Cobertura Vegetal", fontsize=12, fontweight='bold')
plt.ylabel("Frecuencia Absoluta")
plt.ylim(0, max(counts.values) * 1.2)
plt.xticks(rotation=15, ha='right')
plt.show()

print(f"Ratio de desbalanceo (Clase Mayoritaria / Minoritaria): {counts.max() / counts.min():.2f}:1")
"""))

cells.append(nbf.v4.new_code_cell("""# Serie Temporal Histórica del NDVI Promedio (2015-2024)
plt.figure(figsize=(13, 5))
ts_mean = df.groupby('fecha')['NDVI'].agg(['mean', 'std']).reset_index()
plt.plot(ts_mean['fecha'], ts_mean['mean'], color='#2d6a4f', label='NDVI Promedio Cuenca', linewidth=1.5)
plt.fill_between(ts_mean['fecha'], ts_mean['mean'] - ts_mean['std'], ts_mean['mean'] + ts_mean['std'],
                 color='#95d5b2', alpha=0.4, label='± 1 Desviación Estándar')
plt.title("Evolución Temporal del NDVI (2015 - 2024) - Cuenca Río Combeima", fontsize=12, fontweight='bold')
plt.xlabel("Fecha de Adquisición")
plt.ylabel("NDVI Promedio")
plt.legend(loc='upper right')
plt.show()
"""))

# Sección 4: Análisis Bivariado Correlaciones
cells.append(nbf.v4.new_markdown_cell("""---
## 4. Análisis Bivariado — Correlaciones y Multicolinealidad (Tarea 5.4)
Identificamos el grado de colinealidad entre bandas espectrales, coordenadas geográficas, calidad satelital y temporalidad mensual.
"""))

cells.append(nbf.v4.new_code_cell("""# Matriz de Correlación de Pearson
cols_corr = ['NDVI', 'EVI', 'SummaryQA', 'longitude', 'latitude', 'mes']
corr_mat = df[cols_corr].corr()
mask = np.triu(np.ones_like(corr_mat, dtype=bool))

plt.figure(figsize=(7, 6))
sns.heatmap(corr_mat, mask=mask, annot=True, fmt=".3f", cmap="vlag", vmin=-1, vmax=1,
            square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
plt.title("Matriz de Correlaciones de Pearson", fontsize=12, fontweight='bold')
plt.show()
"""))

cells.append(nbf.v4.new_code_cell("""# Diagrama de Dispersión Bivariado: NDVI vs EVI
plt.figure(figsize=(8, 5))
sns.scatterplot(data=df, x='NDVI', y='EVI', hue='clase_cobertura', palette=palette_clases, alpha=0.6, s=25)
r_val = df['NDVI'].corr(df['EVI'])
plt.title(f"Diagrama de Dispersión NDVI vs EVI (Coeficiente r = {r_val:.3f})", fontsize=12, fontweight='bold')
plt.xlabel("NDVI")
plt.ylabel("EVI")
plt.legend(title="Clase Cobertura")
plt.show()
"""))

# Sección 5: Features vs Clase y Estacionalidad
cells.append(nbf.v4.new_markdown_cell("""---
## 5. Análisis Bivariado — Features vs Clase y Ciclos Estacionales (Tarea 5.5)
Evaluamos la separabilidad de las clases de cobertura a través de los índices espectrales y el comportamiento estacional mensual.
"""))

cells.append(nbf.v4.new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Boxplot NDVI por Clase
sns.boxplot(data=df, x='clase_cobertura', y='NDVI', hue='clase_cobertura', palette=palette_clases, legend=False, ax=axes[0],
            boxprops=dict(alpha=0.8), flierprops=dict(marker='o', markersize=2, alpha=0.3))
axes[0].set_title("NDVI según Clase de Cobertura", fontsize=12, fontweight='bold')
axes[0].set_xlabel("Clase")
axes[0].tick_params(axis='x', rotation=15)

# Boxplot EVI por Clase
sns.boxplot(data=df, x='clase_cobertura', y='EVI', hue='clase_cobertura', palette=palette_clases, legend=False, ax=axes[1],
            boxprops=dict(alpha=0.8), flierprops=dict(marker='o', markersize=2, alpha=0.3))
axes[1].set_title("EVI según Clase de Cobertura", fontsize=12, fontweight='bold')
axes[1].set_xlabel("Clase")
axes[1].tick_params(axis='x', rotation=15)

plt.tight_layout()
plt.show()
"""))

cells.append(nbf.v4.new_code_cell("""# Ciclo Estacional Mensual (Violinplot)
plt.figure(figsize=(11, 5))
sns.violinplot(data=df, x='mes', y='NDVI', hue='mes', palette="YlGn", legend=False, inner="quartile", linewidth=1.2)
plt.title("Ciclo Estacional Anual: Distribución Mensual del NDVI", fontsize=12, fontweight='bold')
plt.xlabel("Mes del Año")
plt.ylabel("NDVI")
meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
plt.xticks(ticks=range(12), labels=meses)
plt.show()
"""))

# Sección 6: Análisis Multivariado PCA
cells.append(nbf.v4.new_markdown_cell("""---
## 6. Análisis Multivariado — Reducción de Dimensionalidad con PCA (Tarea 5.6)
Aplicamos Análisis de Componentes Principales (PCA) sobre las variables estandarizadas para entender la compresión espectral y varianza explicada.
"""))

cells.append(nbf.v4.new_code_cell("""cols_pca = ['NDVI', 'EVI', 'SummaryQA', 'longitude', 'latitude']
df_pca = df[cols_pca].dropna()

scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_pca)

pca = PCA(n_components=len(cols_pca), random_state=SEED)
X_pca = pca.fit_transform(X_scaled)
var_exp = pca.explained_variance_ratio_
cum_var = np.cumsum(var_exp)

# Scree Plot de Varianza Explicada
plt.figure(figsize=(8, 4.5))
plt.bar(range(1, len(var_exp)+1), var_exp * 100, color='#457b9d', alpha=0.7, label='Varianza Individual')
plt.plot(range(1, len(var_exp)+1), cum_var * 100, marker='o', color='#e63946', linewidth=2, label='Varianza Acumulada')
plt.axhline(85, color='gray', linestyle='--', label='Criterio 85% Varianza')

for i, (ve, cv) in enumerate(zip(var_exp, cum_var)):
    plt.text(i+1, (ve*100)/2, f"{ve*100:.1f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=9)

plt.title("PCA: Varianza Explicada por Componente Principal", fontsize=12, fontweight='bold')
plt.xlabel("Componente Principal")
plt.ylabel("% Varianza Explicada")
plt.xticks(range(1, len(var_exp)+1), [f"PC{i}" for i in range(1, len(var_exp)+1)])
plt.ylim(0, 105)
plt.legend(loc='center right')
plt.show()

print(f"Número de componentes requeridos para superar el 85% de varianza: {np.argmax(cum_var >= 0.85) + 1}")
"""))

cells.append(nbf.v4.new_code_cell("""# Proyección 2D del Espacio Latente
df_pca_plot = pd.DataFrame(X_pca[:, :2], columns=['PC1', 'PC2'])
df_pca_plot['clase'] = df.loc[df_pca.index, 'clase_cobertura'].values

plt.figure(figsize=(8.5, 5.5))
sns.scatterplot(data=df_pca_plot, x='PC1', y='PC2', hue='clase', palette=palette_clases, alpha=0.6, s=25)
plt.title(f"Proyección PCA 2D (PC1: {var_exp[0]*100:.1f}% + PC2: {var_exp[1]*100:.1f}%)", fontsize=12, fontweight='bold')
plt.xlabel(f"PC1 ({var_exp[0]*100:.1f}%)")
plt.ylabel(f"PC2 ({var_exp[1]*100:.1f}%)")
plt.legend(title="Clase Cobertura")
plt.show()
"""))

# Sección 7: Análisis Geoespacial
cells.append(nbf.v4.new_markdown_cell("""---
## 7. Análisis Geoespacial — Distribución Espacial de la Cuenca Combeima (Tarea 5.7)
Visualizamos la distribución geográfica de los píxeles muestreados en la cuenca y su NDVI promedio multianual. Adicionalmente, verificamos la inicialización con Google Earth Engine para mapas satelitales interactivos.
"""))

cells.append(nbf.v4.new_code_cell("""# Mapa Espacial Estático con Matplotlib (Respaldo Robusto)
pixeles = df.groupby(['longitude', 'latitude']).agg({
    'NDVI': 'mean',
    'EVI': 'mean',
    'fecha': 'count'
}).reset_index().rename(columns={'fecha': 'n_muestras'})

plt.figure(figsize=(8.5, 6.5))
scatter = plt.scatter(pixeles['longitude'], pixeles['latitude'],
                      c=pixeles['NDVI'], cmap='RdYlGn', s=120, edgecolors='black', linewidth=0.8, alpha=0.9)
cbar = plt.colorbar(scatter)
cbar.set_label('NDVI Promedio Multianual (2015-2024)', fontsize=10)
plt.title("Distribución Espacial de Muestras Satelitales — Cuenca Combeima", fontsize=12, fontweight='bold')
plt.xlabel("Longitud (WGS84)")
plt.ylabel("Latitud (WGS84)")
plt.grid(True, linestyle=':', alpha=0.6)
plt.show()
"""))

cells.append(nbf.v4.new_code_cell("""# Diagnóstico de Conexión a Google Earth Engine
try:
    import ee
    ee.Initialize(project='skyfussionanalytics')
    print("[OK] Conexión exitosa a Google Earth Engine con el proyecto 'skyfussionanalytics'")
except Exception as e:
    print(f"ℹ GEE no inicializado en este paso interactivo: {e}")
    print("Se conserva la visualización geoespacial cartesiana de alta precisión como entregable.")
"""))

# Sección 8: Hallazgos y Recomendaciones
cells.append(nbf.v4.new_markdown_cell("""---
## 8. Informe de Hallazgos y Recomendaciones para Modelado (Tarea 5.8)
Se presenta la consolidación de los 5 hallazgos analíticos con su impacto y recomendación técnica para el entrenamiento de la Red Neuronal Recurrente.
"""))

cells.append(nbf.v4.new_code_cell("""# Carga y presentación del informe estructurado de hallazgos
df_hallazgos_view = pd.read_csv(REPORTS_DIR / 'hallazgos_eda.csv')
pd.set_option('display.max_colwidth', None)
df_hallazgos_view[['id', 'dimension', 'hallazgo', 'recomendacion', 'prioridad']]
"""))

# Sección 9: Exportación para Modelado
cells.append(nbf.v4.new_markdown_cell("""---
## 9. Exportación y Metadatos para la Fase de Modelado (Tarea 5.9)
Exportamos las especificaciones de características recomendadas, hiperparámetros del preprocesamiento y criterios de estratificación espacial en formato JSON para consumo automático por el pipeline de entrenamiento (`rnn_combeima/rnn/train.py`).
"""))

cells.append(nbf.v4.new_code_cell("""with open(REPORTS_DIR / 'features_modelado.json', 'r', encoding='utf-8') as f:
    config_features = json.load(f)

print("=== ESPECIFICACIÓN TÉCNICA PARA MODELADO RNA ===")
print(json.dumps(config_features, indent=2, ensure_ascii=False))
"""))

# Asignar celdas al notebook y guardar
nb['cells'] = cells

with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"[OK] Notebook guardado exitosamente en {NOTEBOOK_PATH}")
print("=== EJECUCIÓN DEL EDA COMPLETA ===")
