# Plan del Proyecto: Red Neuronal con Datos de Google Earth Engine

> **Metodología:** CRISP-DM (Sesiones 1-3) aplicada al modelado de una red neuronal
> **Fuente de datos principal:** Google Earth Engine (GEE)
> **Enfoque:** Integración completa desde la obtención de datos satelitales hasta el despliegue del modelo

---

## Fase 0 — Entendimiento del Negocio

### 0.1 Definición del Problema

| Elemento | Descripción |
|----------|-------------|
| **Contexto** | Utilizar imágenes y datos geoespaciales de GEE para entrenar una red neuronal que resuelva un problema de clasificación, predicción o detección de patrones ambientales/geográficos |
| **Pregunta de negocio** | Ejemplo: *¿Se puede predecir la cobertura forestal o detectar cambios en el uso del suelo a partir de composiciones satelitales multitemporales?* |
| **Objetivo analítico** | Entrenar una red neuronal (CNN, RNN o MLP) que clasifique píxeles/zonas según una variable de interés ambiental |
| **Métrica de éxito** | Exactitud (accuracy), F1-score, mIoU según el caso; referencia a un baseline convencional |

### 0.2 Alcance del Proyecto

```
┌─────────────────────────────────────────────────────────────────┐
│                    FASES CRISP-DM APLICADAS                    │
├─────────────┬───────────────────────────────────────────────────┤
│ Fase 0      │ Entendimiento del negocio (este documento)       │
│ Fase 1      │ Obtención de datos desde GEE (Sesión 2)         │
│ Fase 2      │ Limpieza y preprocesamiento (Sesión 3)          │
│ Fase 3      │ Transformación y preparación para la red neuronal│
│ Fase 4      │ Modelado: diseño y entrenamiento de la red       │
│ Fase 5      │ Evaluación y comparación con baselines           │
│ Fase 6      │ Despliegue y documentación                       │
└─────────────┴───────────────────────────────────────────────────┘
```

---

## Fase 1 — Obtención de Datos desde Google Earth Engine (Sesión 2)

### 1.1 Configuración del Entorno

```bash
# Instalación de dependencias
pip install earthengine-api pandas numpy matplotlib
pip install tensorflow keras scikit-learn
pip install rasterio geopandas shapely

# Autenticación de GEE (una sola vez)
earthengine authenticate
```

### 1.2 Conexión con GEE y Definición de la Región de Interés

```python
import ee
ee.Initialize()

# Definir geometría de estudio (ejemplo: departamento del Tolima)
region_roi = ee.Geometry.Rectangle([-75.8, 3.2, -74.7, 5.2])

# Definir rango temporal
fecha_inicio = '2023-01-01'
fecha_fin = '2023-12-31'
```

### 1.3 Selección de Colecciones de Imágenes

```python
# Sentinel-2 (bandas ópticas: B1-B12, NDVI, NDWI)
sentinel2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(region_roi)
    .filterDate(fecha_inicio, fecha_fin)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    .select(['B2', 'B3', 'B4', 'B8', 'B8A', 'B11', 'B12']))

# Landsat 8/9 (alternativa con mayor cobertura temporal)
landsat = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
    .filterBounds(region_roi)
    .filterDate(fecha_inicio, fecha_fin)
    .select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']))

# MODIS (para series de tiempo de NDVI a resolución diaria)
modis = (ee.ImageCollection('MODIS/061/MOD13A2')
    .filterBounds(region_roi)
    .filterDate(fecha_inicio, fecha_fin)
    .select(['NDVI', 'EVI', 'QA_PIXEL']))
```

### 1.4 Extracción de Datos Tabulares para la Red Neuronal

```python
# Opción A: Muestreo de píxeles → tabla CSV (para MLP/clásica)
def extraer_muestreo_pixeles(image, region, n_muestras=10000):
    """Extrae valores de píxeles como puntos muestreados"""
    puntos = image.sample(
        region=region,
        scale=30,           # resolución en metros
        numPixels=n_muestras,
        seed=42,
        geometries=True
    )
    return puntos

# Opción B: Exportar patches de imágenes (para CNN)
def crear_patches(image, region, patch_size=64):
    """Recorta parches de imagen para CNN"""
    patches = image.sampleRectangle(
        region=region,
        defaultValue=0
    )
    return patches

# Exportar a Google Drive o Earth Engine Asset
task = ee.batch.Export.table.toDrive(
    collection=muestras,
    description='muestras_sentinel2_tolima',
    fileNamePrefix='sentinel2_tolima',
    folder='GEE_Proyecto',
    fileFormat='CSV'
)
task.start()
```

### 1.5 Estructura del Dataset Resultante

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `longitude` | float | Coordenada X del píxel | -75.234 |
| `latitude` | float | Coordenada Y del píxel | 4.123 |
| `B2` | int16 | Blue (Sentinel-2) | 1245 |
| `B3` | int16 | Green | 1180 |
| `B4` | int16 | Red | 1050 |
| `B8` | int16 | NIR | 2890 |
| `B11` | int16 | SWIR1 | 1650 |
| `NDVI` | float | Índice de vegetación | 0.72 |
| `clase` | int | Variable objetivo (0-5) | 1 |

---

## Fase 2 — Limpieza y Preprocesamiento (Sesión 3)

### 2.1 Diagnóstico Inicial

```python
import pandas as pd
import numpy as np

# Cargar datos extraídos de GEE
df = pd.read_csv('sentinel2_tolima.csv')

# === Las tres preguntas del diagnóstico (Sesión 3) ===

# 1. ¿Cuánto falta?
print("Nulos por columna:")
print(df.isna().sum()[lambda s: s > 0])

# 2. ¿Qué está repetido?
print(f"\nFilas duplicadas: {df.duplicated().sum()}")

# 3. ¿Qué se sale de rango?
print("\nEstadísticas descriptivas:")
print(df.describe().round(2))
```

### 2.2 Problemas Comunes con Datos de GEE

| Problema | Origen | Solución |
|----------|--------|----------|
| **Nulos en bandas** | Nubes, sombras, ausencia de cobertura | Imputar con mediana del píxel temporal o eliminar si MCAR |
| **Valores fuera de rango** | Errores de calibración, saturación del sensor | Clips a rango válido (0-10000 para Sentinel-2 L2A) |
| **Duplicados geoespaciales** | Solapamiento de órbitas | `drop_duplicates(subset=['longitude','latitude'], keep='last')` |
| **Coordenadas NaN** | Píxeles en bordes de geometría | Eliminar filas sin geometría válida |
| **Desbalanceo de clases** | Clases minoritarias (agua, humedal) | SMOTE, class_weight, o submuestreo |

### 2.3 Pipeline de Limpieza para Datos GEE

```python
def limpiar_datos_gee(df):
    """Pipeline de limpieza adaptado a datos satelitales"""
    df = df.copy()
    
    # PASO 1: Eliminar duplicados geoespaciales
    df = df.drop_duplicates(
        subset=['longitude', 'latitude'], 
        keep='last'
    ).reset_index(drop=True)
    
    # PASO 2: Filtrar valores imposibles de bandas
    bandas = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
    for b in bandas:
        df.loc[df[b] < 0, b] = df[b].median()
        df.loc[df[b] > 10000, b] = df[b].median()
    
    # PASO 3: Imputar nulos
    for col in df.columns:
        if df[col].isna().sum() > 0:
            if df[col].dtype in ['float64', 'int64']:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0])
    
    # PASO 4: Eliminar coordenadas inválidas
    df = df.dropna(subset=['longitude', 'latitude'])
    
    print(f"Filas finales: {len(df)}, Nulos: {df.isna().sum().sum()}")
    return df

df_limpio = limpiar_datos_gee(df)
```

---

## Fase 3 — Transformación y Preparación para la Red Neuronal

### 3.1 Ingeniería de Características

```python
# === Índices espectrales (variables derivadas) ===

# NDVI: Normalized Difference Vegetation Index
df_limpio['NDVI'] = (df_limpio['B8'] - df_limpio['B4']) / (df_limpio['B8'] + df_limpio['B4'] + 1e-10)

# NDWI: Normalized Difference Water Index
df_limpio['NDWI'] = (df_limpio['B3'] - df_limpio['B8']) / (df_limpio['B3'] + df_limpio['B8'] + 1e-10)

# NDBI: Normalized Difference Built-up Index
df_limpio['NDBI'] = (df_limpio['B11'] - df_limpio['B8']) / (df_limpio['B11'] + df_limpio['B8'] + 1e-10)

# Razón de bandas
df_limpio['B8_B4_ratio'] = df_limpio['B8'] / (df_limpio['B4'] + 1e-10)
```

### 3.2 Codificación y Escalamiento

```python
from sklearn.preprocessing import StandardScaler, LabelEncoder

# Escalar bandas espectrales (estandarización z-score)
scaler = StandardScaler()
bandas_entrada = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'NDVI', 'NDWI', 'NDBI']
df_limpio[bandas_entrada] = scaler.fit_transform(df_limpio[bandas_entrada])

# Codificar variable objetivo
le = LabelEncoder()
df_limpio['clase_encoded'] = le.fit_transform(df_limpio['clase'])
n_clases = len(le.classes_)

print(f"Clases: {dict(zip(le.classes_, range(n_clases)))}")
```

### 3.3 División del Dataset

```python
from sklearn.model_selection import train_test_split

X = df_limpio[bandas_entrada].values
y = df_limpio['clase_encoded'].values

# División: 70% entrenamiento, 15% validación, 15% prueba
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
)

print(f"Entrenamiento: {X_train.shape[0]} muestras")
print(f"Validación:    {X_val.shape[0]} muestras")
print(f"Prueba:        {X_test.shape[0]} muestras")
```

---

## Fase 4 — Modelado: Red Neuronal

### 4.1 Arquitectura del Modelo (MLP para datos tabulares)

```python
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

def crear_modelo_mlp(n_entradas, n_clases):
    """Red neuronal para clasificación de píxeles satelitales"""
    modelo = keras.Sequential([
        # Capa de entrada
        layers.Input(shape=(n_entradas,)),
        
        # Capas ocultas con regularización
        layers.Dense(128, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        
        layers.Dense(64, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        
        layers.Dense(32, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        
        # Capa de salida
        layers.Dense(n_clases, activation='softmax')
    ])
    
    modelo.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return modelo

modelo = crear_modelo_mlp(X_train.shape[1], n_clases)
modelo.summary()
```

### 4.2 Entrenamiento con Callbacks

```python
callbacks = [
    keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=15,
        restore_best_weights=True
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=1e-6
    ),
    keras.callbacks.ModelCheckpoint(
        'mejor_modelo.keras',
        monitor='val_accuracy',
        save_best_only=True
    )
]

historial = modelo.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=150,
    batch_size=32,
    callbacks=callbacks,
    verbose=1
)
```

### 4.3 Variantes de Red Neuronal según Tipo de Dato GEE

| Tipo de Dato GEE | Arquitectura Recomendada | Uso |
|-------------------|--------------------------|-----|
| **Píxeles individuales** (tabular) | MLP (Dense layers) | Clasificación de cobertura del suelo |
| **Parches de imagen** (2D) | CNN (Conv2D + MaxPool) | Detección de patrones espaciales |
| **Series de tiempo** (MODIS diario) | LSTM / GRU / Temporal CNN | Predicción de NDVI, sequías |
| **Píxel + vecindario** (3D) | U-Net, ResNet | Segmentación semántica |
| **Multiespectral multitemporal** | CNN + LSTM (híbrida) | Cambio de uso del suelo en el tiempo |

---

## Fase 5 — Evaluación

### 5.1 Métricas del Modelo

```python
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Predicciones sobre conjunto de prueba
y_pred = modelo.predict(X_test).argmax(axis=1)

# Reporte de clasificación
print(classification_report(
    y_test, y_pred, 
    target_names=[str(c) for c in le.classes_]
))

# Matriz de confusión
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=le.classes_,
            yticklabels=le.classes_)
plt.title('Matriz de Confusión - Red Neuronal vs Datos GEE')
plt.ylabel('Real')
plt.xlabel('Predicho')
plt.savefig('matriz_confusion.png', dpi=150, bbox_inches='tight')
plt.show()
```

### 5.2 Comparación con Baselines

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

baselines = {
    'Random Forest': RandomForestClassifier(n_estimators=200, random_state=42),
    'SVM': SVC(kernel='rbf', random_state=42)
}

resultados = {}
for nombre, clf in baselines.items():
    clf.fit(X_train, y_train)
    acc = clf.score(X_test, y_test)
    resultados[nombre] = acc
    print(f"{nombre}: {acc:.4f}")

resultados['Red Neuronal'] = modelo.evaluate(X_test, y_test, verbose=0)[1]
print(f"Red Neuronal: {resultados['Red Neuronal']:.4f}")
```

### 5.3 Curvas de Aprendizaje

```python
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Loss
axes[0].plot(historial.history['loss'], label='Entrenamiento')
axes[0].plot(historial.history['val_loss'], label='Validación')
axes[0].set_title('Pérdida por Época')
axes[0].set_xlabel('Época')
axes[0].set_ylabel('Loss')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Accuracy
axes[1].plot(historial.history['accuracy'], label='Entrenamiento')
axes[1].plot(historial.history['val_accuracy'], label='Validación')
axes[1].set_title('Exactitud por Época')
axes[1].set_xlabel('Época')
axes[1].set_ylabel('Accuracy')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('curvas_aprendizaje.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

## Fase 6 — Despliegue y Documentación

### 6.1 Exportar Modelo Entrenado

```python
# Guardar modelo completo
modelo.save('modelo_gee_clasificacion.keras')

# Guardar preprocesadores
import joblib
joblib.dump(scaler, 'scaler_gee.pkl')
joblib.dump(le, 'label_encoder_gee.pkl')

# Script de predicción para nuevos datos de GEE
def predecir_nueva_imagen(ruta_csv):
    """Carga datos de GEE y predice con el modelo entrenado"""
    df_nuevo = pd.read_csv(ruta_csv)
    scaler = joblib.load('scaler_gee.pkl')
    modelo = keras.models.load_model('modelo_gee_clasificacion.keras')
    
    X_nuevo = scaler.transform(df_nuevo[bandas_entrada].values)
    predicciones = modelo.predict(X_nuevo).argmax(axis=1)
    clases_predichas = le.inverse_transform(predicciones)
    
    df_nuevo['clase_predicha'] = clases_predichas
    return df_nuevo
```

### 6.2 Visualización de Resultados en GEE

```python
# Exportar predicciones como Asset de GEE para visualización geográfica
def predecir_en_mapa(modelo, imagen_satelital, region):
    """Aplica el modelo a toda la imagen y genera mapa de clasificación"""
    # Extraer todas las bandas como arrays
    bandas = imagen_satelital.select(bandas_entrada)
    
    # Muestrear para predecir (o aplicar pixel-wise)
    puntos = bandas.sample(region=region, scale=30, numPixels=50000)
    
    # Predecir
    features_list = puntos.getInfo()['features']
    # ... (procesamiento y reconstrucción como imagen GEE)
    
    return imagen_clasificada
```

### 6.3 Documentación del Proyecto

```markdown
## Estructura de Entrega Final

proyecto_gee_red_neuronal/
├── datos/
│   ├── raw/                    # Datos crudos descargados de GEE
│   ├── processed/              # Datos limpios y transformados
│   └── splits/                 # train.csv, val.csv, test.csv
├── notebooks/
│   ├── 01_extraccion_gee.ipynb       # Conexión con GEE y extracción
│   ├── 02_limpieza.ipynb             # Pipeline de limpieza
│   ├── 03_eda.ipynb                  # Exploración de datos
│   ├── 04_modelado.ipynb             # Red neuronal
│   ├── 05_evaluacion.ipynb           # Métricas y comparaciones
│   └── 06_visualizacion_gee.ipynb    # Resultados en mapa
├── modelos/
│   ├── modelo_gee.keras              # Modelo entrenado
│   ├── scaler_gee.pkl                # Escalador
│   └── label_encoder_gee.pkl         # Codificador de clases
├── scripts/
│   ├── extraccion_gee.py             # Módulo de extracción
│   ├── limpieza.py                   # Pipeline de limpieza
│   └── prediccion.py                 # Inferencia
├── reportes/
│   ├── matriz_confusion.png
│   ├── curvas_aprendizaje.png
│   └── mapa_clasificacion.png
├── requirements.txt
└── README.md
```

---

## Cronograma Integrado (Sesiones 1-3 + Proyecto)

| Semana | Sesión del Curso | Actividad del Proyecto | Entregable |
|--------|------------------|------------------------|------------|
| 1 | **Sesión 1** — Introducción | Definir problema de negocio, explorar dataset inicial de GEE | Acta del proyecto + pregunta de negocio |
| 2 | **Sesión 2** — Fuentes y Tipos | Conectar con GEE, extraer colecciones, exportar CSV | Datos crudos en Drive + notebook de extracción |
| 3 | **Sesión 3** — Limpieza | Diagnosticar y limpiar datos satelitales | `datos_limpio_propio.csv` + informe de limpieza |
| 4 | Sesión 4 — Transformación | Escalar, codificar índices espectrales, dividir dataset | Dataset listo para modelado |
| 5 | Sesión 5 — EDA | Análisis exploratorio completo de bandas y clases | Visualizaciones y hallazgos |
| 6 | Sesión 6 — Prep. avanzada | Selección de features, PCA si aplica | Dataset optimizado |
| 7-8 | Sesiones 7-8 — Clasificación | Entrenar y ajustar red neuronal MLP/CNN | Modelo entrenado + métricas |
| 9 | Sesión 9 — Clustering | Comparar con K-Means como baseline no supervisado | Análisis comparativo |
| 10 | Sesión 10 — Asociación | Reglas de asociación entre bandas y clases | Reglas extraídas |
| 11 | Sesión 11 — Validación | Validación cruzada, ajuste de hiperparámetros | Modelo optimizado |
| 12-13 | Sesiones 12-13 — Eval. y series | Evaluar en conjunto de prueba, series temporales | Resultados finales |
| 14 | Sesión 14 — Texto/NLP | Documentar hallazgos en reporte técnico | Borrador del informe |
| 15 | Sesión 15 — Prep. presentación | Preparar sustentación y visualizaciones finales | Presentación |
| 16 | Sesión 16 — Entrega final | Sustentación y entrega completa | Proyecto final |

---

## Recursos Necesarios

### Herramientas
- **Google Earth Engine** (cuenta gratuita: earthengine.google.com)
- **Google Colab** o **Jupyter Notebook** local
- **Python 3.9+** con TensorFlow/Keras, scikit-learn, pandas, numpy, matplotlib
- **geemap** (para visualización interactiva de GEE en Colab)

### Datos Disponibles en GEE
| Colección | Resolución | Bandas Útiles | Ideal Para |
|-----------|------------|----------------|------------|
| `COPERNICUS/S2_SR_HARMONIZED` | 10m | B2-B12 | Clasificación de cobertura |
| `LANDSAT/LC08/C02/T1_L2` | 30m | SR_B2-SR_B7 | Análisis regional |
| `MODIS/061/MOD13A2` | 1km | NDVI, EVI | Series de tiempo |
| `LANDSAT/LC08/C02/T1_L2` | 30m | ST_B10 | Temperatura superficial |
| `COPERNICUS/S2_SR_HARMONIZED` | 10m | SCL | Máscara de nubes |

### Documentación de Referencia
- [GEE Python API](https://developers.google.com/earth-engine/guides/python_install)
- [GEE Dataset Catalog](https://developers.google.com/earth-engine/datasets)
- Han, Kamber & Pei — *Data Mining: Concepts and Techniques*, Cap. 1 y 2
- TensorFlow Tutorials: [image classification](https://www.tensorflow.org/tutorials/images/classification)

---

## Criterios de Evaluación del Proyecto

| Criterio | Peso | Nivel Esperado |
|----------|------|----------------|
| **Funcionalidad del pipeline** | 30% | Extracción → limpieza → modelado ejecutan sin errores |
| **Calidad del modelo** | 25% | Accuracy > baseline + justificación de métricas elegidas |
| **Justificación técnica** | 20% | Cada decisión defendida con conceptos de las sesiones (MCAR/MAR, IQR, CRISP-DM) |
| **Documentación y reproducibilidad** | 15% | Código comentado, rutas relativas, requisitos declarados |
| **Presentación y comunicación** | 10% | Resultados visuales claros en mapa GEE, explicación no técnica |

---

> **Nota:** Este plan se mapea directamente con las sesiones 1-16 del curso de Minería de Datos.
> Las sesiones 1-3 establecen las bases (conceptos, fuentes, limpieza) que se aplican
> íntegramente en la obtención y preparación de los datos de GEE antes del modelado.
