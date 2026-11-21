"""Étape 3 (Binôme 1) : Exploration statistique et visualisations (Matplotlib & Seaborn).

Génère les tableaux d'audit Pandas et 5 graphiques enregistrés dans reports/figures/.
"""

from collections import Counter
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import CLEAN_DATA_PATH, FIGURES_DIR

sns.set_theme(style="whitegrid")


def resume_statistique(df: pd.DataFrame) -> None:
    """Affiche le taux de valeurs manquantes (%) et les statistiques descriptives."""
    print("=== Valeurs manquantes (%) ===")
    print((df.isna().mean() * 100).round(2))
    print("\n=== Statistiques descriptives ===")
    print(df.describe().round(2))


def generer_graphiques(df: pd.DataFrame, output_dir: Path = FIGURES_DIR) -> list[Path]:
    """Génère et sauvegarde les 5 graphiques EDA demandés (PNG 300 DPI)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fichiers = []

    # 1. Distribution & Outliers des budgets (échelle log)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    est = df["estimation_mad"].dropna()
    est = est[est > 0]
    sns.histplot(np.log10(est), kde=True, ax=axes[0], color="#2b5c8f")
    axes[0].set_title("Distribution des estimations (log10)")
    axes[0].set_xlabel("log10(Estimation en MAD)")
    sns.boxplot(x=est, ax=axes[1], color="#4c9f70")
    axes[1].set_xscale("log")
    axes[1].set_title("Boxplot des estimations (détection outliers)")
    axes[1].set_xlabel("Estimation (MAD, échelle log)")
    p1 = output_dir / "01_budgets_outliers.png"
    fig.savefig(p1, dpi=300, bbox_inches="tight")
    plt.close(fig)
    fichiers.append(p1)

    # 2. Répartition par catégorie et Top 10 villes
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    cat = df["categorie"].value_counts()
    sns.barplot(x=cat.values, y=cat.index, ax=axes[0])
    axes[0].set_title("Offres par catégorie")
    axes[0].set_xlabel("Nombre d'offres")
    villes = df["ville"].value_counts().head(10)
    sns.barplot(x=villes.values, y=villes.index, ax=axes[1])
    axes[1].set_title("Top 10 des villes")
    axes[1].set_xlabel("Nombre d'offres")
    p2 = output_dir / "02_categories_villes.png"
    fig.savefig(p2, dpi=300, bbox_inches="tight")
    plt.close(fig)
    fichiers.append(p2)

    # 3. Tendances temporelles et délais de réponse
    df_t = df.copy()
    df_t["mois"] = pd.to_datetime(df_t["date_publication"]).dt.to_period("M").astype(str)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    sns.lineplot(data=df_t.groupby("mois").size().reset_index(name="nb"), x="mois", y="nb", marker="o", ax=axes[0])
    axes[0].set_title("Évolution mensuelle des publications")
    axes[0].tick_params(axis="x", rotation=45)
    sns.boxplot(data=df_t, x="categorie", y="delai_reponse_jours", ax=axes[1])
    axes[1].set_title("Délais de réponse (jours) par catégorie")
    p3 = output_dir / "03_tendances_delais.png"
    fig.savefig(p3, dpi=300, bbox_inches="tight")
    plt.close(fig)
    fichiers.append(p3)

    # 4. Matrice de corrélation Seaborn
    num = pd.DataFrame({
        "Estimation": df["estimation_mad"],
        "Caution": df["caution_mad"],
        "Délai (j)": df["delai_reponse_jours"],
        "Longueur texte": df["texte_propre"].astype(str).str.len(),
    })
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(num.corr(), annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title("Corrélations des variables numériques")
    p4 = output_dir / "04_correlations.png"
    fig.savefig(p4, dpi=300, bbox_inches="tight")
    plt.close(fig)
    fichiers.append(p4)

    # 5. Top 20 des mots-clés après nettoyage NLP
    compteur = Counter()
    for txt in df["texte_propre"].dropna():
        compteur.update(str(txt).split())
    mots, freqs = zip(*compteur.most_common(20)) if compteur else ([], [])
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.barplot(x=list(freqs), y=list(mots), ax=ax)
    ax.set_title("Top 20 des mots-clés après suppression des stopwords")
    ax.set_xlabel("Occurrences")
    p5 = output_dir / "05_top_mots_cles.png"
    fig.savefig(p5, dpi=300, bbox_inches="tight")
    plt.close(fig)
    fichiers.append(p5)

    return fichiers


if __name__ == "__main__":
    df_clean = pd.read_csv(CLEAN_DATA_PATH)
    resume_statistique(df_clean)
    generer_graphiques(df_clean)
