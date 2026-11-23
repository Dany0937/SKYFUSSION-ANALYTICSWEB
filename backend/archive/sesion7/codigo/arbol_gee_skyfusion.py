"""
Modelo de Árbol de Decisión Explicable - Sesión 7 (SkyFusion Analytics)
=======================================================================
Contexto: Clasificación de cobertura del suelo en la cuenca del Río Combeima (GEE Sentinel-2 + WorldCover 2021).
Objetivo: Generar reglas de decisión transparentes para alimentar a VisionAgent y ReportingAgent.
Métricas objetivo del split congelado:
- Train/Test: 1.443 / 481 (Estratificado, Semilla 42)
- Modelo: DecisionTreeClassifier(max_depth=5, criterion='entropy', random_state=42)
- Accuracy test: ~0.6674
- Macro-F1 test: ~0.6595
- Balanced Accuracy: ~0.6574
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import accuracy_score, f1_score, balanced_accuracy_score, classification_report

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / "sesion7" / "datasets" / "sentinel2_combeima_clases.csv"
    split_path = base_dir / "sesion7" / "resultados" / "metricas_split.json"

    if not data_path.exists() or not split_path.exists():
        raise FileNotFoundError(f"No se encontró el dataset o split en {data_path} / {split_path}")

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

    # Modelo Árbol Final (depth 5, entropy)
    clf = DecisionTreeClassifier(max_depth=5, criterion="entropy", random_state=42)
    clf.fit(X_train, y_train)

    y_pred_train = clf.predict(X_train)
    y_pred_test = clf.predict(X_test)

    acc_train = accuracy_score(y_train, y_pred_train)
    acc_test = accuracy_score(y_test, y_pred_test)
    macro_f1 = f1_score(y_test, y_pred_test, average="macro")
    bal_acc = balanced_accuracy_score(y_test, y_pred_test)

    print("=" * 60)
    print("ÁRBOL DE DECISIÓN GEE - SKYFUSION (SESIÓN 7)")
    print("=" * 60)
    print(f"Muestras Train: {len(X_train)} | Test: {len(X_test)}")
    print(f"Accuracy Train : {acc_train:.4f}")
    print(f"Accuracy Test  : {acc_test:.4f}")
    print(f"Macro-F1 Test  : {macro_f1:.4f}")
    print(f"Balanced Acc   : {bal_acc:.4f}")
    print("\nReporte por Clase:\n", classification_report(y_test, y_pred_test, zero_division=0))

    # Guardar métricas finales
    out_metricas = base_dir / "sesion7" / "resultados" / "metricas_finales.json"
    with open(out_metricas, "w", encoding="utf-8") as f:
        json.dump({
            "modelo": "DecisionTreeClassifier(max_depth=5, criterion='entropy', random_state=42)",
            "accuracy_train": round(acc_train, 4),
            "accuracy_test": round(acc_test, 4),
            "macro_f1_test": round(macro_f1, 4),
            "balanced_accuracy_test": round(bal_acc, 4)
        }, f, indent=2)
    print(f"Métricas guardadas en: {out_metricas}")

if __name__ == "__main__":
    main()
