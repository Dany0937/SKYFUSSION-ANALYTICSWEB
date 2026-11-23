Ejecutado: Semana 7 con datos reales de GEE
El pipeline corre completo de principio a fin con Sentinel-2 + WorldCover 2021 desde Earth Engine, sin respaldo sintético.
Script: sesion7/codigo/arbol_gee_skyfusion.py (el arbol_fuga.py de TelecomUNO quedó intacto).
Evidencia: sesion7/resultados/ y sesion7/README_SEMANA7.md.
Resultados de la corrida final
Métrica	Valor
Dataset real GEE	1,924 filas · 7 clases · 118 tiles (~1 km)
Split congelado	1,443 train / 481 test (estratificado, semilla 42, índices disjuntos)
Selección por CV 5-fold	max_depth=5, entropy (test no participó)
Macro-F1 CV (config. final)	0.6606
Accuracy test	0.6674
Macro-F1 test	0.6595
Balanced accuracy	0.6574
Baseline mayoría	0.1559 (suelo_desnudo)
Los tres árboles entregados
Uso	Artefacto	Tamaño real
Comunicación (depth 3)	arbol_gee_depth3.png	depth 3, 8 hojas
Modelo final	arbol_gee_final_depth5.png	depth 5, 29 hojas
Diagnóstico de sobreajuste	arbol_gee_sin_limite.png	depth 14, 254 hojas
Reglas priorizadas por negocio (reglas_negocio.md, 7 del árbol final + 7 del depth 3):
- agua: NDWI > -0.32 Y B11 <= 1480.75 Y B8 <= 1190.25 → pureza 100 %, 67 test, precisión 100 %.
- urbano: NDWI > -0.32 Y B11 > 1480.75 Y B8 <= 2672.50 Y NDBI > 0.13 Y B11 <= 3301 → pureza 92.2 %, 40 test, precisión 90 %.
- suelo_desnudo y bosque también tienen hoja propia; las 4 clases prioritarias quedan cubiertas y mapeadas a VisionAgent, OracleAgent y ReportingAgent.
- Cada regla reporta soporte train/test, cobertura de la clase y pureza; se declara explícitamente que son asociaciones, no causalidad.
Honestidad del modelo
- El árbol sin límite llega a accuracy train 1.0 con brecha CV 0.314; el final la reduce a 0.073 en test.
- Sensibilidad del split en 12 escenarios: macro-F1 entre 0.6395 y 0.7010; el valor del split congelado cae dentro del rango.
- tile_id queda guardado en metricas_split.json y test_indices.csv; la validación espacial por bloques se difiere a la sesión 11.
- Checklist: 8/8 PASS (sin PASS (pipeline), porque los datos son reales).
Reproducibilidad
py -3.13 "sesion7\codigo\arbol_gee_skyfusion.py" --extraer-gee
- Dos corridas consecutivas producen hashes idénticos en métricas, reglas, baseline y split.
- El resumen_ejecucion.json guarda hash SHA-256 del CSV, comando, commit, versiones, procedencia GEE y bloqueos.
- También validé --sin-figuras: termina en OK con 7/8 ítems (el de figuras queda N/A).
Observaciones
- No pude inspeccionar visualmente los PNG (el modelo no acepta imágenes); verifiqué dimensiones y que se regeneran: depth 3 = 3,179×2,498 px, final = 4,350×3,378 px, sin límite = 4,366×3,818 px.
- No dupliqué nada en Skyfusion-Analytics: la fuente de verdad quedó en el repo del curso, como se decidió.
- sesion7/ sigue sin commit (solo hay archivos nuevos sin rastrear); no hice commit sin pedirlo.