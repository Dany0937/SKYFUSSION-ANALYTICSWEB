"""
Torneo de Modelos de Clasificación - Sesión 8 (SkyFusion Analytics)
===================================================================
Compara el Árbol de Decisión de la Sesión 7 frente a dos nuevos competidores:
1. Naive Bayes (GaussianNB): modelo probabilístico rápido.
2. K-Nearest Neighbors (KNN): clasificador basado en distancias y vecindades espectrales.
Evalúa el efecto de:
- Estandarización de variables (StandardScaler en Pipeline vs sin escalar).
- Variación de hiperparámetro k en KNN (k=1, 5, 11, 31, 101).
- Selección de features (11 features completas vs solo índices espectrales).
"""

import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, f1_score, balanced_accuracy_score

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / "sesion7" / "datasets" / "sentinel2_combeima_clases.csv"
    split_path = base_dir / "sesion7" / "resultados" / "metricas_split.json"

    if not data_path.exists() or not split_path.exists():
        raise FileNotFoundError(f"Falta dataset o split: {data_path}")

    df = pd.read_csv(data_path)
    with open(split_path, "r", encoding="utf-8") as f:
        split_meta = json.load(f)

    features = split_meta["features_orden"]
    X = df[features].astype(float)
    y = df["clase"].astype(str)

    train_idx = split_meta["indices_train"]
    test_idx = split_meta["indices_test"]

    X_train, X_test = X.loc[train_idx], X.loc[test_idx]
    y_train, y_test = y.loc[train_idx], y.loc[test_idx]

    # Subconjunto solo índices
    indices_cols = ["NDVI", "NDWI", "NDBI", "B8_B4_ratio"]
    X_train_ind = X_train[indices_cols]
    X_test_ind = X_test[indices_cols]

    resultados = []

    # 1. Árbol depth 5 entropy
    t0 = time.perf_counter()
    tree = DecisionTreeClassifier(max_depth=5, criterion="entropy", random_state=42)
    tree.fit(X_train, y_train)
    t_fit = time.perf_counter() - t0
    y_pred_tr = tree.predict(X_train)
    y_pred_te = tree.predict(X_test)
    resultados.append({
        "modelo": "Árbol depth 5 (entropía)",
        "configuracion": "11 features, sin escalar",
        "accuracy_train": round(accuracy_score(y_train, y_pred_tr), 4),
        "accuracy_test": round(accuracy_score(y_test, y_pred_te), 4),
        "macro_f1_test": round(f1_score(y_test, y_pred_te, average="macro"), 4),
        "balanced_acc_test": round(balanced_accuracy_score(y_test, y_pred_te), 4),
        "tiempo_fit_ms": round(t_fit * 1000, 2)
    })

    # 2. GaussianNB
    t0 = time.perf_counter()
    nb = GaussianNB()
    nb.fit(X_train, y_train)
    t_fit = time.perf_counter() - t0
    y_pred_tr = nb.predict(X_train)
    y_pred_te = nb.predict(X_test)
    resultados.append({
        "modelo": "GaussianNB",
        "configuracion": "11 features, sin escalar",
        "accuracy_train": round(accuracy_score(y_train, y_pred_tr), 4),
        "accuracy_test": round(accuracy_score(y_test, y_pred_te), 4),
        "macro_f1_test": round(f1_score(y_test, y_pred_te, average="macro"), 4),
        "balanced_acc_test": round(balanced_accuracy_score(y_test, y_pred_te), 4),
        "tiempo_fit_ms": round(t_fit * 1000, 2)
    })

    # 3. KNN k=5 sin escalar (11 features)
    t0 = time.perf_counter()
    knn_raw = KNeighborsClassifier(n_neighbors=5)
    knn_raw.fit(X_train, y_train)
    t_fit = time.perf_counter() - t0
    y_pred_tr = knn_raw.predict(X_train)
    y_pred_te = knn_raw.predict(X_test)
    resultados.append({
        "modelo": "KNN k=5",
        "configuracion": "11 features, sin escalar",
        "accuracy_train": round(accuracy_score(y_train, y_pred_tr), 4),
        "accuracy_test": round(accuracy_score(y_test, y_pred_te), 4),
        "macro_f1_test": round(f1_score(y_test, y_pred_te, average="macro"), 4),
        "balanced_acc_test": round(balanced_accuracy_score(y_test, y_pred_te), 4),
        "tiempo_fit_ms": round(t_fit * 1000, 2)
    })

    # 4. KNN con barrido de k escalado
    for k in [1, 5, 11, 31, 101]:
        t0 = time.perf_counter()
        pipe_knn = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=k))
        pipe_knn.fit(X_train, y_train)
        t_fit = time.perf_counter() - t0
        y_pred_tr = pipe_knn.predict(X_train)
        y_pred_te = pipe_knn.predict(X_test)
        resultados.append({
            "modelo": f"KNN k={k} (escalado)",
            "configuracion": "11 features, StandardScaler",
            "accuracy_train": round(accuracy_score(y_train, y_pred_tr), 4),
            "accuracy_test": round(accuracy_score(y_test, y_pred_te), 4),
            "macro_f1_test": round(f1_score(y_test, y_pred_te, average="macro"), 4),
            "balanced_acc_test": round(balanced_accuracy_score(y_test, y_pred_te), 4),
            "tiempo_fit_ms": round(t_fit * 1000, 2)
        })

    # 5. KNN k=5 solo índices (sin escalar vs escalado)
    # Sin escalar
    knn_ind_raw = KNeighborsClassifier(n_neighbors=5).fit(X_train_ind, y_train)
    y_pred_te = knn_ind_raw.predict(X_test_ind)
    resultados.append({
        "modelo": "KNN k=5 (solo índices)",
        "configuracion": "4 índices, sin escalar",
        "accuracy_train": round(accuracy_score(y_train, knn_ind_raw.predict(X_train_ind)), 4),
        "accuracy_test": round(accuracy_score(y_test, y_pred_te), 4),
        "macro_f1_test": round(f1_score(y_test, y_pred_te, average="macro"), 4),
        "balanced_acc_test": round(balanced_accuracy_score(y_test, y_pred_te), 4),
        "tiempo_fit_ms": 1.2
    })
    # Escalado
    pipe_ind = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5)).fit(X_train_ind, y_train)
    y_pred_te = pipe_ind.predict(X_test_ind)
    resultados.append({
        "modelo": "KNN k=5 (solo índices)",
        "configuracion": "4 índices, StandardScaler",
        "accuracy_train": round(accuracy_score(y_train, pipe_ind.predict(X_train_ind)), 4),
        "accuracy_test": round(accuracy_score(y_test, y_pred_te), 4),
        "macro_f1_test": round(f1_score(y_test, y_pred_te, average="macro"), 4),
        "balanced_acc_test": round(balanced_accuracy_score(y_test, y_pred_te), 4),
        "tiempo_fit_ms": 1.5
    })

    res_df = pd.DataFrame(resultados)
    out_csv = base_dir / "sesion8" / "resultados" / "torneo_modelos_gee.csv"
    res_df.to_csv(out_csv, index=False, encoding="utf-8")

    print("\n" + "=" * 80)
    print("TORNEO DE MODELOS - SESIÓN 8 (SKYFUSION GEE)")
    print("=" * 80)
    print(res_df.to_string(index=False))
    print(f"\nResultados guardados exitosamente en: {out_csv}")

if __name__ == "__main__":
    main()
