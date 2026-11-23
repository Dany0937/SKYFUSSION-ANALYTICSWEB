# Plan de temas de las presentaciones · Sesiones 8 y 9 aplicadas a SkyFusion

> Curso: Minería de Datos · UNIMINUTO Ibagué · 2026-2  
> Proyecto de contexto: **Skyfusion Analytics** — cuenca del río Combeima (Sentinel-2 + WorldCover 2021)  
> Estado: **plan de contenidos**. Las presentaciones actuales (`sesion8/presentacion.html` y `sesion9/presentacion.html`) y sus scripts siguen usando el caso genérico *TelecomUNO*; este plan las adapta a todo el trabajo ya realizado.

---

## 1. Propósito y diagnóstico de la brecha

| Aspecto | Lo que ya se hizo | Lo que hay que alinear |
|---|---|---|
| Sesión 7 | Árbol explicable sobre GEE (`arbol_gee_skyfusion.py`): 1.924 filas, 7 clases, 11 features, split congelado 1.443/481, accuracy 0.6674, macro-F1 0.6595 | Es el punto de partida obligatorio de la sesión 8 (existe `handoff_sesion8.md`) |
| Sesión 8 | Presentación y script con árbol/NB/KNN sobre TelecomUNO | Retomar el **split congelado de GEE** y competir contra el árbol de la sesión 7 |
| Sesión 9 | Presentación y script de K-means sobre TelecomUNO | Segmentar **píxeles/tiles de la cuenca** y nombrar zonas ambientales accionables |
| Proyecto integrador | EDA GEE (sesión 5), pitch del escalado (sesión 4), plan de red neuronal | Dejar claro que NB/KNN/K-means son **complementos/baselines**, no reemplazo de la red neuronal final |

**Reglas de oro que atraviesan ambas sesiones**

1. Mismo dataset, mismo orden de features y mismo split (`metricas_split.json`), semilla 42.
2. Dividir antes de cualquier `fit`; escalar dentro de `Pipeline` o con `fit` solo sobre train.
3. Reportar accuracy **y** macro-F1/balanced accuracy: hay 7 clases y desbalance.
4. Toda conclusión se traduce a una acción de Skyfusion (alerta hídrica, expansión urbana, erosión, conservación) vía `VisionAgent → OracleAgent → ReportingAgent`.

---

## 2. Mapa de sustitución TelecomUNO → SkyFusion (para reescribir las diapositivas)

| Elemento | Versión actual (genérica) | Versión SkyFusion |
|---|---|---|
| Dominio | Retención de clientes de telecomunicaciones | Monitoreo ambiental de la cuenca del Combeima |
| Unidad observada | Cliente | Píxel/parcela Sentinel-2 (~1 km, `tile_id`) |
| Target | `fuga` (Sí/No) | `clase` WorldCover: agua, arbustal, bosque, cultivo, pastizal, suelo_desnudo, urbano |
| Features | edad, facturación, quejas… | B2, B3, B4, B8, B11, B12, NDVI, NDWI, NDBI, B8_B4_ratio, temporada_lluviosa |
| Métrica de referencia | accuracy 0.820 | accuracy 0.6674 / macro-F1 0.6595 (árbol depth 5, entropy) |
| Decisión de negocio | Campaña de retención | Alerta temprana hídrica, expansión urbana, riesgo de erosión |
| Ejemplo probabilístico | Prueba médica | "Dado NDWI alto y B11 bajo, ¿es agua?" |
| Ejemplo KNN | Clientes parecidos | Píxeles espectralmente vecinos ("gemelos de cobertura") |
| Clustering | Segmentos de clientes | Zonas espectrales: cuerpo de agua / suelo urbano-desnudo / vegetación |
| Modelo final del proyecto | — | Red neuronal del `PLAN_PROYECTO_RED_NEURONAL_GEE.md` (los modelos de hoy son baselines) |

---

## 3. Sesión 8 — Clasificación II: Naive Bayes y K-Vecinos en SkyFusion

**Duración:** 120 min · **Instrumento:** taller práctico · **Unidad:** 2  
**Resultado de aprendizaje:** construir y comparar modelos de minería de datos seleccionando el más adecuado para el problema de negocio.

### 3.1 Objetivos adaptados

1. Aplicar el teorema de Bayes con conteos simples a un ejemplo de cobertura (NDWI → agua).
2. Entrenar `GaussianNB` y `KNeighborsClassifier` sobre el **mismo split congelado** de la sesión 7.
3. Justificar el escalado con evidencia del propio dataset (índices -1..1 frente a bandas 0-10.000).
4. Comparar árbol, NB y KNN en accuracy, macro-F1, balanced accuracy y tiempo; recomendar un modelo para las alertas de Skyfusion.

### 3.2 Agenda

| Tiempo | Bloque |
|---|---|
| 00:00 – 00:05 | Repaso del árbol GEE y del handoff; reto: "¿quién supera macro-F1 0.6595?" |
| 00:05 – 00:25 | Teoría I: Bayes con conteos + Naive Bayes (GaussianNB) |
| 00:25 – 00:40 | Teoría II: KNN, distancia euclidiana entre píxeles, efecto de k, escalado |
| 00:40 – 00:45 | Pausa activa |
| 00:45 – 01:05 | Demo guiada: torneo de 3 modelos sobre el split de GEE |
| 01:05 – 01:40 | Taller: torneo propio y recomendación técnica |
| 01:40 – 01:50 | Socialización de veredictos |
| 01:50 – 02:00 | Evaluación formativa, trabajo independiente y anticipo de clustering |

### 3.3 Guion diapositiva a diapositiva (22 diapositivas, mismo formato que la actual)

| # | Tema | Punto clave adaptado a SkyFusion | Evidencia / recurso |
|---|---|---|---|
| 1 | Portada | "Probabilidades y vecindarios: dos rivales para el árbol de la cuenca" | Badges: 2 h, Unidad 2, taller |
| 2 | Gancho | Filtros de spam (NB) y búsqueda de vecinos, trasladado a detección de cobertura; pregunta: ¿qué gana un modelo que no explica sus reglas? | Analogía + cifra 99,9% spam |
| 3 | Objetivos | Los 4 objetivos adaptados (arriba) | RA de la Unidad 2 |
| 4 | Agenda | Tabla de 120 min | — |
| 5 | Conexión sesión 7 | Árbol depth 5, entropy: 1.443 train / 481 test, accuracy 0.6674, macro-F1 0.6595, baseline mayoría 0.1559 | `metricas_finales.json`, `handoff_sesion8.md` |
| 6 | Teorema de Bayes contando personas | Ejemplo médico 9/59≈15% **y** traslado: P(agua \| NDWI alto) combina evidencia con prior de clase | Tabla 1.000 personas |
| 7 | De Bayes a Naive Bayes | Supuesto de independencia: "NDVI no cambia la probabilidad de NDWI dado agua"; falso, útil | GaussianNB / MultinomialNB |
| 8 | Cuándo brilla NB | Texto, bases pequeñas, línea base rápida; límites: probabilidades mal calibradas, doble conteo de bandas correlacionadas | — |
| 9 | KNN: dime con quién andas | El modelo guarda los 1.924 píxeles; un píxel nuevo vota con sus k vecinos espectrales | Analogía "gemelos de cobertura" |
| 10 | Distancia euclidiana a mano | Ejemplo con dos bandas: píxel nuevo B3=900, B8=2.900 frente a 3 candidatos; calcular distancias y votar k=3 | Tabla de cálculos |
| 11 | Efecto de k | **Cifras reales SkyFusion**: k=1 acc 0.7484 (train 1.000), k=5 0.7443, k=11 0.7360, k=31 0.7193, k=101 0.6445 | Resultados del script con split congelado |
| 12 | ¿Por qué escalar? | Bandas 0-10.000 e índices -1..1; con todas las variables la brecha es pequeña (0.7401 → 0.7443), pero con solo índices KNN pasa de **0.6258 a 0.6528** | Contraste: "el escalado importa según la mezcla de escalas"; regla de oro sesión 4 |
| 13 | Código 1: tablero compartido | Cargar `sentinel2_combeima_clases.csv`, reconstruir 11 features con el mismo orden, leer `metricas_split.json`, `X.loc[indices_train]` | Fragmento de código |
| 14 | Código 2: el torneo | Árbol depth 5 entropy, GaussianNB, Pipeline(StandardScaler+KNN k=5); imprimir train/test, macro-F1 y tiempo | **Salida verificada** (tabla abajo) |
| 15 | Tabla comparativa | Árbol = explicable para reportes a entidades; NB = línea base veloz; KNN = mejor precisión local, costoso en predicción | Criterios: interpretabilidad, escalado, fronteras |
| 16 | Vida real | Clasificación de cobertura en GEE, filtros de spam y recomendación; Skyfusion usa el árbol para narrar y la red neuronal para predecir | Casos reales |
| 17 | Ejercicio: torneo de cobertura | 5 pasos: tablero → 3 modelos → k=1/11/51 → veredicto de 8 líneas → defensa de 90 s | Dataset del equipo |
| 18 | Criterios y auxilios | Misma partición, Pipeline sin fuga, train **y** test, veredicto con ≥2 criterios; pista `set_params` para variar k | Errores frecuentes |
| 19 | Instrumento: taller | Tabla 40% / exploración k 20% / veredicto 40% + escala de logro | Rúbrica |
| 20 | Errores comunes | Confiar probabilidades de NB, mezclar escalas, k par, medir solo `fit()` y no `predict()` | Tips |
| 21 | Trabajo independiente | Lectura Han-Kamber-Pei; probar `weights="distance"`; consolidar cuaderno `modelos_v1` con árbol+NB+KNN para el Avance 2 | Anticipo: se apagan las etiquetas |
| 22 | Cierre | NB 0.5800, árbol 0.6674, KNN 0.7443 en accuracy; la decisión final la definen explicabilidad y costo operativo | Próxima sesión: clustering |

### 3.4 Marcador real para la diapositiva 14 (calculado con el split congelado)

| Modelo | Accuracy train | Accuracy test | Macro-F1 test | Balanced accuracy |
|---|---:|---:|---:|---:|
| Árbol depth 5 · entropy (sesión 7) | 0.7401 | 0.6674 | 0.6595 | 0.6574 |
| GaussianNB | 0.6057 | 0.5800 | 0.5588 | 0.5882 |
| KNN k=5 sin escalar (11 features) | 0.8254 | 0.7401 | 0.7264 | 0.7349 |
| KNN k=5 escalado (11 features) | 0.8267 | **0.7443** | **0.7301** | 0.7333 |
| KNN k=5 sin escalar (solo índices) | — | 0.6258 | 0.5979 | — |
| KNN k=5 escalado (solo índices) | — | 0.6528 | 0.6266 | — |

**Lectura para sustentar:** NB es el más rápido pero el más débil (las bandas están correlacionadas y no son gaussianas puras). KNN gana en precisión, pero es "perezoso": guarda toda la historia y paga en predicción. El árbol pierde en accuracy, sin embargo es el único que entrega reglas auditables para los reportes de Skyfusion; por eso se mantiene como modelo de comunicación y la red neuronal como modelo final.

### 3.5 Esqueleto de código de la demo (adaptar `sesion8/codigo/comparacion_modelos.py`)

```python
import json
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier

base = Path(__file__).resolve().parents[2]
split = json.loads((base / "sesion7/resultados/metricas_split.json").read_text(encoding="utf-8"))
df = pd.read_csv(base / "sesion7/datasets/sentinel2_combeima_clases.csv")
# ... reconstruir NDVI/NDWI/NDBI/B8_B4_ratio y temporada_lluviosa (ídem sesión 7)
X, y = df[split["features_orden"]].astype(float), df["clase"].astype(str)
X_train, X_test = X.loc[split["indices_train"]], X.loc[split["indices_test"]]
y_train, y_test = y.loc[split["indices_train"]], y.loc[split["indices_test"]]

modelos = {
    "Árbol d5 entropía": DecisionTreeClassifier(max_depth=5, criterion="entropy", random_state=42),
    "Naive Bayes": GaussianNB(),
    "KNN k=5": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5)),
}
```

---

## 4. Sesión 9 — Clustering: K-means y jerárquico en SkyFusion

**Duración:** 120 min · **Instrumento:** ejercicios en clase · **Unidad:** 2  
**Resultado de aprendizaje:** descubrir estructura sin etiquetas y defender una segmentación útil para la cuenca.

### 4.1 Objetivos adaptados

1. Diferenciar supervisado (clasificar cobertura con WorldCover) y no supervisado (encontrar zonas spectrales sin la etiqueta).
2. Trazar K-means paso a paso y elegir k con codo (inercia) + silueta + operatividad de alertas.
3. Ejecutar la segmentación de los píxeles de Combeima con `StandardScaler` + `KMeans` y perfilar cada zona con `groupby().mean()` y distribución de clases.
4. Nombrar comercialmente/operativamente cada zona y leer un dendrograma (`ward`) como evidencia complementaria.

### 4.2 Agenda

| Tiempo | Bloque |
|---|---|
| 00:00 – 00:05 | Repaso del torneo (KNN 0.7443) y pregunta: ¿y si no existiera la columna `clase`? |
| 00:05 – 00:25 | Teoría I: supervisado vs no supervisado, casos de uso ambientales, K-means paso a paso |
| 00:25 – 00:35 | Teoría II: codo e inercia, coeficiente de silueta |
| 00:35 – 00:40 | Pausa activa |
| 00:40 – 01:00 | Demo: segmentación de la cuenca y perfilamiento |
| 01:00 – 01:10 | Clustering jerárquico: dendrograma sobre 60 píxeles |
| 01:10 – 01:45 | Ejercicio: segmentar, nombrar zonas y diseñar alertas |
| 01:45 – 01:50 | Socialización y aplicación del instrumento |
| 01:50 – 02:00 | Trabajo independiente, anticipo de asociación y cierre |

### 4.3 Guion diapositiva a diapositiva (24 diapositivas, mismo formato que la actual)

| # | Tema | Punto clave adaptado a SkyFusion | Evidencia / recurso |
|---|---|---|---|
| 1 | Portada | "Aprendizaje no supervisado: descubrir las zonas naturales de la cuenca" | 2 h, Unidad 2, ejercicios |
| 2 | Gancho | Retención del 5% → utilidades 25-95% (Bain) trasladado a alertas: una sola alerta no sirve para agua, urbano y vegetación | 1 mensaje, 3 audiencias |
| 3 | Objetivos | Los 4 objetivos adaptados (arriba) | RA Unidad 2 |
| 4 | Agenda | Tabla de 120 min | — |
| 5 | Conexión sesión 8 | Hoy alguien pone la etiqueta `clase`; mañana no: la pregunta es "¿qué zonas existen aunque WorldCover no las nombre?" | Comparación supervisado / no supervisado |
| 6 | Supervisado vs no supervisado | Tabla: X e y vs solo X; accuracy/macro-F1 vs inercia/silueta; el cluster puede ser feature de la red neuronal | Idea Avance 2 |
| 7 | Casos de uso | Segmentación de cuencas, agrupación de sensores IoT, anomalías en series temporales, compresión de imágenes | 4 tarjetas |
| 8 | K-means paso a paso | Farolas sobre la cuenca: sembrar (k-means++), asignar, recalcular, iterar; inercia y `n_init=10` | Analogía + `figura_sobreajuste.png` como contraste |
| 9 | Método del codo | **Inercia real**: k=1 11.544, k=2 5.976, k=3 4.143, k=4 2.820, k=5 2.378, k=8 1.661; codo suave entre 2 y 4 | Tabla calculada |
| 10 | Silueta | **Silueta real**: k=2 0.463, k=3 0.440, k=4 0.439, k=5 0.425, k=6 0.349, k=8 0.332. Máximo en k=2, k=3 es la opción operativa | Gráfica sugerida |
| 11 | Código 1: escalar y buscar k | `V = ["B2","B3","B4","B8","B11","B12"]`, `StandardScaler`, `KMeans(n_init=10, random_state=42)`, `silhouette_score` | Salida verificada |
| 12 | Código 2: modelo final y perfiles | k=3 → 1.113 / 501 / 310 píxeles; `groupby("cluster")[V].mean()` + distribución de `clase` | Tabla de perfiles (abajo) |
| 13 | Nombrar las zonas | **Cuerpo de agua** (94,5% agua), **suelo urbano-desnudo en riesgo** (50,1% suelo_desnudo + 34,1% urbano), **vegetación productiva** ( bosque/cultivo/pastizal ~73% ) | Cada zona con alerta Skyfusion |
| 14 | Jerárquico: concepto | Aglomerativo con `ward`: cada píxel es su grupo; fusiones progresivas; cortar el dendrograma define zonas sin fijar k | Dendrograma conceptual |
| 15 | Código 3: dendrograma | Muestra de 60 píxeles, `linkage(..., method="ward")`; primeras fusiones 0,12-0,27, última fusión 17,62; corte ~6-7 apoya 2-3 macrogrupos | `dendrograma_muestra60.png` (nuevo, adaptado) |
| 16 | K-means vs jerárquico | K-means escala a 1.924+ píxeles y produce la asignación final; jerárquico es determinista y explora la estructura en muestra | Tabla comparativa |
| 17 | Limitaciones | Formas esféricas, sensibilidad a escala y outliers, k es decisión humana; en cuencas hay autocorrelación espacial | Aviso para sesión 11 |
| 18 | Vida real | Operadores y agencias: features → segmentar → nombrar → campaña/alerta → medir por zona y re-entrenar | Secuencia de 5 etapas |
| 19 | Ejercicio: alerta segmentada | 5 pasos: escalar 6 bandas, calcular codo/silueta k=2..6, justificar k, perfilar y nombrar, dendrograma de muestra | Equipos de proyecto |
| 20 | Criterios y auxilios | Escalar antes, perfiles con distribución de clases, nombres accionables, justificación con cifras; evitar IDs/coordenadas en X | Errores frecuentes |
| 21 | Instrumento: ejercicios | Tabla 30% / 30% / 30% / 10% + escala de logro | Rúbrica |
| 22 | Trabajo independiente | Lectura Han-Kamber-Pei; agregar 2 variables (NDVI, NDWI); consolidar Avance 2 parte 1 (torneo + segmentación) | Anticipo: Apriori |
| 23 | Errores comunes | Clusterizar coordenadas, contar historias sin evidencia, olvidar que centroides están estandarizados, usar `clase` dentro de X | Tips |
| 24 | Cierre | Tres zonas naturales; el segmento puede convertirse en feature del modelo supervisado y de la red neuronal | Próxima: reglas de asociación |

### 4.4 Perfil real de la segmentación (k=3, variables B2-B12 escaladas)

| Zona (nombre propuesto) | Píxeles | B2 | B3 | B4 | B8 | B11 | B12 | Composición WorldCover |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Z0 · Vegetación mixta | 1.113 | 692 | 893 | 746 | 2.898 | 2.114 | 1.280 | bosque 24,3% · cultivo 24,5% · pastizal 24,1% · arbustal 11,1% |
| Z1 · Suelo urbano-desnudo (riesgo) | 501 | 1.839 | 2.103 | 2.222 | 2.929 | 3.273 | 2.755 | suelo_desnudo 50,1% · urbano 34,1% |
| Z2 · Cuerpos de agua | 310 | 785 | 1.019 | 707 | 574 | 443 | 275 | agua 94,5% |

**Alertas derivadas:** Z2 → alerta hídrica y caudal; Z1 → inspección de expansión urbana/erosión (`VisionAgent → ReportingAgent`); Z0 → seguimiento de estrés hídrico y conservación. La columna `clase` se usa **solo para perfilar**, nunca dentro de X.

### 4.5 Esqueleto de código de la demo (adaptar `sesion9/codigo/kmeans_segmentacion.py`)

```python
V = ["B2", "B3", "B4", "B8", "B11", "B12"]
X = StandardScaler().fit_transform(df[V])      # fit sobre X de comportamiento espectral

for k in range(2, 9):
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    etiquetas = km.fit_predict(X)
    print(k, round(km.inertia_), round(silhouette_score(X, etiquetas), 3))

df["cluster"] = KMeans(n_clusters=3, n_init=10, random_state=42).fit_predict(X)
perfil = df.groupby("cluster")[V].mean().round(0)
distribucion = df.groupby("cluster")["clase"].value_counts(normalize=True).unstack()
```

---

## 5. Artefactos a reutilizar y artefactos nuevos

**Reutilizar (sin modificar)**

- `sesion7/resultados/metricas_split.json`, `test_indices.csv`, `features_modelado.json`, `metricas_finales.json`, `handoff_sesion8.md`, `hallazgos_semana7.md`, `reglas_negocio.md`, `matriz_confusion_normalizada.png`, `importancia_variables.csv`.
- `sesion7/datasets/sentinel2_combeima_clases.csv` (1.924 filas modelables, GEE).
- `PITCH_SCALAMIENTO_RED_NEURONAL.md` y `PLAN_PROYECTO_RED_NEURONAL_GEE.md` para el hilo conductor del escalado y del modelo final.

**Generar al adaptar las presentaciones**

- `sesion8/resultados/torneo_modelos_gee.csv` (accuracy/macro-F1/tiempo por modelo y por k).
- `sesion8/resultados/comparacion_modelos_gee.py` (versión GEE del script actual).
- `sesion9/datasets/dendrograma_combeima_muestra60.png` (reemplaza al de TelecomUNO).
- `sesion9/resultados/perfil_clusters_combeima.csv` e `inercia_silueta_combeima.csv`.
- Cuaderno `modelos_v1` del equipo: árbol + NB + KNN + segmentación, listo para el Avance 2.

---

## 6. Riesgos y mensajes de cautela que deben aparecer en ambas presentaciones

1. **Autocorrelación espacial:** el split es aleatorio; 100 tiles distintos en test pueden inflar métricas. La validación por bloques es la sesión 11.
2. **Etiqueta derivada:** WorldCover 2021 no es verdad terreno; requiere fotointerpretación/campo.
3. **Asociación ≠ causalidad:** reglas del árbol y centroides describen patrones, no mecanismos.
4. **Escalado con matices:** en SkyFusion las seis bandas ya comparten rango (0-10.000), por lo que escalar KNN cambia poco; al mezclar índices (-1..1) con bandas, la diferencia es medible (0.6258 → 0.6528). En K-means el escalado es obligatorio.
5. **k no es un hallazgo:** se negocia entre codo, silueta y capacidad operativa de alertas.
6. **Jerarquía sobre muestra:** el dendrograma es exploratorio (60 píxeles), no la asignación final de la cuenca.

---

## 7. Orden de implementación sugerido

1. Aprobar este plan de temas.
2. Reescribir `sesion8/presentacion.html` y `sesion9/presentacion.html` manteniendo la numeración y el estilo de `assets/estilo.css` (22 y 24 diapositivas).
3. Adaptar los scripts `comparacion_modelos.py` y `kmeans_segmentacion.py` al dataset GEE y guardar sus salidas en `resultados/`.
4. Verificar que todas las cifras mostradas coincidan con las tablas de este documento.
5. Actualizar los README de sesión y el hilo del Avance 2.

> Nota metodológica: las cifras de las secciones 3.4 y 4.4 se calcularon ejecutando los modelos sobre el dataset real `sentinel2_combeima_clases.csv` con el split congelado de `metricas_split.json` (semilla 42, estratificado, 1.443/481), reproduciendo primero el árbol de la sesión 7 (accuracy 0.6674, macro-F1 0.6595) como control de validez.
