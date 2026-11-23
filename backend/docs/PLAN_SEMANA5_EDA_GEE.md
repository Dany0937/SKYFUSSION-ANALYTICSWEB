# Plan Técnico Semana 5 — EDA para Datos Satelitales GEE
## Proyecto: Red Neuronal con Google Earth Engine (SkyFussion)

> **Fase CRISP-DM:** Entendimiento de los Datos (EDA)
> **Sesión del curso:** Sesión 5 — Análisis Exploratorio de Datos
> **Entrada:** Dataset limpio y transformado de Sesión 4 (datos_procesados.csv)
> **Salida:** Notebook EDA completo + visualizaciones + hallazgos documentados\n> **Estado:** **COMPLETADO (16 entregables generados en reports/eda/ y notebooks/)**

---

## 1. Objetivos Técnicos de la Semana

| Objetivo | Descripción | Entregable |
|----------|-------------|------------|
| OBJ-1 | Cargar y validar dataset procesado (post-Sesión 4) | Check de integridad: shape, tipos, nulos, rangos |
| OBJ-2 | EDA Univariado: distribución de bandas espectrales e índices | Histogramas, boxplots, estadísticos por banda/índice |
| OBJ-3 | EDA Bivariado: relaciones banda-banda, banda-clase, índice-clase | Scatter matrix, heatmap correlaciones, boxplots por clase |
| OBJ-4 | EDA Geoespacial: visualización espacial de muestras y clases | Mapa de distribución muestras, mapa de clases predichas (baseline) |
| OBJ-5 | Detección de problemas: multicolinealidad, desbalanceo, outliers espaciales | Informe de hallazgos + recomendaciones para modelado |
| OBJ-6 | Documentar todo en notebook reproducible | notebooks/03_eda.ipynb

---

## 2. Estructura del Notebook EDA (notebooks/03_eda.ipynb)

### 2.1 Secciones del Notebook

1. Carga y Validación Inicial
2. Análisis Univariado — Bandas Espectrales
3. Análisis Univariado — Índices Derivados
4. Análisis Univariado — Variable Objetivo (clase)
5. Análisis Bivariado — Correlaciones
6. Análisis Bivariado — Features vs Clase
7. Análisis Multivariado
8. Análisis Geoespacial (Único GEE)
9. Hallazgos y Recomendaciones
10. Exportación para Modelado

---

## 3. Tareas Técnicas Detalladas (9 tareas con código completo)

### Tarea 5.1 — Configuración y Carga de Datos (30 min)
### Tarea 5.2 — EDA Univariado: Bandas Espectrales (60 min)
### Tarea 5.3 — EDA Univariado: Variable Objetivo (30 min)
### Tarea 5.4 — EDA Bivariado: Matriz de Correlaciones (45 min)
### Tarea 5.5 — EDA Bivariado: Features vs Clase (60 min)
### Tarea 5.6 — EDA Multivariado: PCA/UMAP (45 min)
### Tarea 5.7 — EDA Geoespacial (45 min)
### Tarea 5.8 — Hallazgos y Recomendaciones (30 min)
### Tarea 5.9 — Exportación y Verificación Final (15 min)

---

## 4. Entregables (16 archivos)

- notebooks/03_eda.ipynb
- 14 figuras PNG en reportes/
- reportes/hallazgos_eda.csv
- datos/processed/features_modelado.json

---

## 5. Checklist de Calidad (9 criterios)

Verificar: notebook ejecutable, 14+ figuras, hallazgos CSV, features JSON, estratificación, convenciones, rutas relativas, random_state=42, informe escrito.

## 6. Riesgos y Mitigaciones (6 riesgos identificados)

---

## 7. Referencias a Sesión 5 del Curso

Mapeo de conceptos: Histograma→Bandas, Boxplot→Outliers nubes, Barras→Clases, Heatmap→Multicolinealidad, Pairplot→PCA, Informe EDA→Avance 1.
