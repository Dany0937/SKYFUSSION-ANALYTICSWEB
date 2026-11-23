"""
Segmentación No Supervisada de la Cuenca del Combeima - Sesión 9 (SkyFusion)
============================================================================
Aplica técnicas de agrupamiento no supervisado:
1. K-Means con barrido de k=2..8 sobre las 6 bandas espectrales Sentinel-2 (B2, B3, B4, B8, B11, B12).
2. Curvas de Codo (inercia) y Coeficiente de Silueta.
3. Selección operativa de k=3 (Z0 Vegetación mixta, Z1 Suelo urbano-desnudo, Z2 Cuerpos de agua).
4. Perfilamiento espectral y distribución de clases WorldCover para caracterización de zonas.
5. Clustering Jerárquico Aglomerativo (Ward) sobre muestra de 60 píxeles con dendrograma.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.cluster.hierarchy import dendrogram, linkage

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / "sesion7" / "datasets" / "sentinel2_combeima_clases.csv"

    if not data_path.exists():
        raise FileNotFoundError(f"Falta dataset: {data_path}")

    df = pd.read_csv(data_path)
    bandas = ["B2", "B3", "B4", "B8", "B11", "B12"]
    X_bandas = df[bandas].values

    # Estandarización obligatoria para clustering
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_bandas)

    # 1. Barrido de k=2..8
    metricas_k = []
    for k in range(2, 9):
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(X_scaled)
        inercia = round(km.inertia_, 1)
        sil = round(silhouette_score(X_scaled, labels), 3)
        metricas_k.append({
            "k": k,
            "inercia": inercia,
            "silueta": sil
        })

    df_k = pd.DataFrame(metricas_k)
    out_k = base_dir / "sesion9" / "resultados" / "inercia_silueta_combeima.csv"
    df_k.to_csv(out_k, index=False)
    print("=" * 60)
    print("MÉTRICAS DE CLUSTERING K-MEANS (k=2..8):")
    print("=" * 60)
    print(df_k.to_string(index=False))

    # 2. Modelo Final k=3
    km_final = KMeans(n_clusters=3, n_init=10, random_state=42)
    df["cluster"] = km_final.fit_predict(X_scaled)

    # Nombres operativos de zonas
    # Identificar cluster de agua (el que tiene menor B8 promedio)
    cluster_b8 = df.groupby("cluster")["B8"].mean()
    c_agua = cluster_b8.idxmin()
    # Identificar cluster urbano/suelo (el que tiene mayor B11 promedio)
    cluster_b11 = df.groupby("cluster")["B11"].mean()
    c_urbano = cluster_b11.idxmax()
    # El restante es vegetacion
    c_veg = list(set([0, 1, 2]) - set([c_agua, c_urbano]))[0]

    cluster_nombres = {
        c_veg: "Z0 · Vegetación mixta",
        c_urbano: "Z1 · Suelo urbano-desnudo (riesgo)",
        c_agua: "Z2 · Cuerpos de agua"
    }
    df["zona_nombre"] = df["cluster"].map(cluster_nombres)

    # Perfiles espectrales
    perfil_espectral = df.groupby("zona_nombre")[bandas].mean().round(1)
    conteo_pixeles = df.groupby("zona_nombre")["tile_id"].count().rename("num_pixeles")
    perfil_completo = pd.concat([conteo_pixeles, perfil_espectral], axis=1)

    # Distribución WorldCover
    distribucion_wc = (df.groupby("zona_nombre")["clase"].value_counts(normalize=True) * 100).round(1).unstack(fill_value=0)

    resumen_perfiles = pd.concat([perfil_completo, distribucion_wc], axis=1)
    out_perfiles = base_dir / "sesion9" / "resultados" / "perfil_clusters_combeima.csv"
    resumen_perfiles.to_csv(out_perfiles)
    print("\n" + "=" * 80)
    print("PERFILES OPERACIONALES POR ZONA (k=3):")
    print("=" * 80)
    print(resumen_perfiles.to_string())

    # 3. Clustering Jerárquico Aglomerativo (Ward) sobre muestra de 60 píxeles
    np.random.seed(42)
    # Seleccionar muestra estratificada de 60 píxeles
    sample_indices = df.groupby("zona_nombre", group_keys=False).apply(lambda s: s.sample(min(len(s), 20), random_state=42)).index
    sample_X = X_scaled[sample_indices]
    sample_labels = df.loc[sample_indices, "zona_nombre"].values

    Z = linkage(sample_X, method="ward")

    plt.figure(figsize=(12, 6), dpi=150)
    plt.title("Dendrograma de Agrupamiento Jerárquico (Ward) — Muestra 60 Píxeles Cuenca Combeima", fontsize=12, fontweight="bold")
    plt.xlabel("Índice de muestra (coloreado por zona espectral)")
    plt.ylabel("Distancia de Fusión (Ward)")
    dendrogram(
        Z,
        labels=[s[:2] for s in sample_labels],
        leaf_rotation=90,
        leaf_font_size=9,
        color_threshold=6.5
    )
    plt.axhline(y=6.5, color='crimson', linestyle='--', linewidth=1.5, label='Corte sugerido (k=3 macrogrupos)')
    plt.legend(loc='upper right')
    plt.tight_layout()

    out_dendro = base_dir / "sesion9" / "datasets" / "dendrograma_combeima_muestra60.png"
    plt.savefig(out_dendro)
    plt.close()
    print(f"\nDendrograma guardado exitosamente en: {out_dendro}")

if __name__ == "__main__":
    main()
