"""Unsupervised segmentation of countries by debt profile.

Finds natural groupings using K-means (k chosen via silhouette score) and
compares against agglomerative (hierarchical) clustering, then projects the
feature space to 2D with PCA for visualization.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

FEATURES = [
    "debt_pct_gni", "debt_pct_gdp", "debt_service_pct_exports",
    "debt_service_pct_debt", "reserves_to_debt", "short_term_share",
    "public_ppg_share", "private_png_share", "multilateral_share",
    "debt_per_capita_usd", "gdp_per_capita_usd",
]


def prepare_matrix(df):
    X = df[FEATURES].copy()
    X = SimpleImputer(strategy="median").fit_transform(X)
    X = StandardScaler().fit_transform(X)
    return X


def choose_k(X, k_range=range(2, 8)):
    results = []
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        sil = silhouette_score(X, km.labels_)
        results.append({"k": k, "inertia": km.inertia_, "silhouette": sil})
    return pd.DataFrame(results)


def main():
    df = pd.read_csv("data/country_features.csv")
    X = prepare_matrix(df)

    k_scan = choose_k(X)
    best_k = int(k_scan.loc[k_scan["silhouette"].idxmax(), "k"])
    print("k-scan:\n", k_scan.to_string(index=False))
    print(f"Chosen k (max silhouette) = {best_k}")

    kmeans = KMeans(n_clusters=best_k, n_init=10, random_state=42).fit(X)
    hier = AgglomerativeClustering(n_clusters=best_k).fit(X)

    df["kmeans_cluster"] = kmeans.labels_
    df["hierarchical_cluster"] = hier.labels_
    agreement = (pd.crosstab(df["kmeans_cluster"], df["hierarchical_cluster"])
                 .max(axis=1).sum() / len(df))
    print(f"K-means vs hierarchical label agreement (best matching): {agreement:.1%}")

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X)
    df["pca_1"], df["pca_2"] = coords[:, 0], coords[:, 1]
    explained = pca.explained_variance_ratio_

    profile = df.groupby("kmeans_cluster")[FEATURES].median().round(2)
    print("\nCluster profiles (median feature values):\n", profile.to_string())

    df.to_csv("data/country_clusters.csv", index=False)

    # -- Elbow / silhouette plot --
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(k_scan["k"], k_scan["inertia"], "o-")
    axes[0].set_xlabel("k"); axes[0].set_ylabel("Inertia"); axes[0].set_title("Elbow")
    axes[1].plot(k_scan["k"], k_scan["silhouette"], "o-", color="darkorange")
    axes[1].axvline(best_k, color="gray", linestyle="--", alpha=0.6)
    axes[1].set_xlabel("k"); axes[1].set_ylabel("Silhouette score"); axes[1].set_title("Silhouette")
    fig.tight_layout()
    fig.savefig("models/figures/cluster_k_selection.png", dpi=150)

    # -- PCA scatter --
    fig2, ax2 = plt.subplots(figsize=(7, 6))
    scatter = ax2.scatter(df["pca_1"], df["pca_2"], c=df["kmeans_cluster"],
                           cmap="tab10", s=40, alpha=0.85)
    for _, row in df.nlargest(8, "total_debt_usd").iterrows():
        ax2.annotate(row["country_name"], (row["pca_1"], row["pca_2"]), fontsize=8)
    ax2.set_xlabel(f"PC1 ({explained[0]:.0%} var)")
    ax2.set_ylabel(f"PC2 ({explained[1]:.0%} var)")
    ax2.set_title(f"Country debt profiles -- PCA projection, k={best_k} clusters")
    legend1 = ax2.legend(*scatter.legend_elements(), title="cluster", loc="best")
    ax2.add_artist(legend1)
    fig2.tight_layout()
    fig2.savefig("models/figures/pca_clusters.png", dpi=150)

    with open("models/clustering_metrics.json", "w") as f:
        json.dump({
            "features": FEATURES,
            "k_scan": k_scan.to_dict(orient="records"),
            "chosen_k": best_k,
            "kmeans_hierarchical_agreement": round(agreement, 3),
            "pca_explained_variance": explained.round(3).tolist(),
            "cluster_profiles": json.loads(profile.to_json(orient="index")),
            "cluster_sizes": df["kmeans_cluster"].value_counts().sort_index().to_dict(),
        }, f, indent=2)

    print("\nSaved data/country_clusters.csv, models/clustering_metrics.json, "
          "models/figures/cluster_k_selection.png, models/figures/pca_clusters.png")


if __name__ == "__main__":
    main()
