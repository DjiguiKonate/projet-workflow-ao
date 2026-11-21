"""Module d'exploration statistique et visuelle des données — EDA (Étape 3 - Binôme 1).

Produit les tableaux d'audit de qualité sous Pandas et les 5+ visualisations
commentées avec Matplotlib et Seaborn (enregistrées en PNG 300 DPI dans reports/figures/).
"""

from collections import Counter
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import FIGURES_DIR

# Style global homogène pour tous les graphiques du rapport
sns.set_theme(style="whitegrid", palette="Set2")


def audit_qualite(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calcule le taux de valeurs manquantes (%) et les statistiques descriptives.

    Args:
        df: DataFrame nettoyé.

    Returns:
        Tuple (tableau_valeurs_manquantes, statistiques_descriptives).
    """
    manquants = pd.DataFrame(
        {
            "valeurs_manquantes": df.isna().sum(),
            "pourcentage_manquant (%)": (df.isna().mean() * 100).round(2),
            "type_colonne": df.dtypes.astype(str),
        }
    )
    stats_desc = df.describe(include="all").T
    return manquants, stats_desc


def detecter_outliers_iqr(serie: pd.Series) -> dict[str, float]:
    """Identifie les valeurs extrêmes selon la méthode de l'écart interquartile (IQR).

    Args:
        serie: Série numérique Pandas (ex. estimation_mad).

    Returns:
        Dictionnaire contenant Q1, Q3, IQR, borne supérieure et nombre d'outliers.
    """
    valeurs = serie.dropna()
    q1 = float(valeurs.quantile(0.25))
    q3 = float(valeurs.quantile(0.75))
    iqr = q3 - q1
    borne_sup = q3 + 1.5 * iqr
    nb_outliers = int((valeurs > borne_sup).sum())
    return {
        "Q1": round(q1, 2),
        "Q3": round(q3, 2),
        "IQR": round(iqr, 2),
        "borne_sup_iqr": round(borne_sup, 2),
        "nb_outliers": nb_outliers,
    }


def plot_distributions_budgets(
    df: pd.DataFrame,
    output_dir: Path = FIGURES_DIR,
) -> Path:
    """Graphique 1 : Distributions (histogramme + KDE en échelle log) et boxplots des montants."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Histogramme + KDE de estimation_mad (échelle log10 pour isoler les très gros marchés)
    est = df["estimation_mad"].dropna()
    est_pos = est[est > 0]
    sns.histplot(np.log10(est_pos), kde=True, ax=axes[0, 0], color="#2b5c8f")
    axes[0, 0].set_title("Distribution de l'estimation budgétaire (échelle log10)")
    axes[0, 0].set_xlabel("log10(Estimation en MAD)")
    axes[0, 0].set_ylabel("Nombre d'offres")

    # Boxplot estimation_mad
    sns.boxplot(x=est_pos, ax=axes[0, 1], color="#4c9f70")
    axes[0, 1].set_xscale("log")
    axes[0, 1].set_title("Boîte à moustaches de l'estimation (détection des outliers)")
    axes[0, 1].set_xlabel("Estimation budgétaire (MAD, échelle log)")

    # Histogramme + KDE de caution_mad
    caut = df["caution_mad"].dropna()
    caut_pos = caut[caut > 0]
    sns.histplot(np.log10(caut_pos), kde=True, ax=axes[1, 0], color="#d97724")
    axes[1, 0].set_title("Distribution de la caution provisoire (échelle log10)")
    axes[1, 0].set_xlabel("log10(Caution en MAD)")
    axes[1, 0].set_ylabel("Nombre d'offres")

    # Boxplot caution_mad
    sns.boxplot(x=caut_pos, ax=axes[1, 1], color="#c94c4c")
    axes[1, 1].set_xscale("log")
    axes[1, 1].set_title("Boîte à moustaches de la caution provisoire")
    axes[1, 1].set_xlabel("Caution provisoire (MAD, échelle log)")

    plt.tight_layout()
    chemin = output_dir / "01_distributions_budgets_outliers.png"
    fig.savefig(chemin, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin


def plot_repartition_categories_villes(
    df: pd.DataFrame,
    output_dir: Path = FIGURES_DIR,
) -> Path:
    """Graphique 2 : Barres horizontales par catégorie et par top 10 villes/acheteurs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Volume par catégorie
    cat_counts = df["categorie"].value_counts()
    sns.barplot(x=cat_counts.values, y=cat_counts.index, ax=axes[0], palette="viridis")
    axes[0].set_title("Volume d'appels d'offres par catégorie")
    axes[0].set_xlabel("Nombre d'offres")
    axes[0].set_ylabel("Catégorie")

    # Volume par ville (Top 10)
    ville_counts = df["ville"].value_counts().head(10)
    sns.barplot(x=ville_counts.values, y=ville_counts.index, ax=axes[1], palette="crest")
    axes[1].set_title("Top 10 des villes par volume d'offres")
    axes[1].set_xlabel("Nombre d'offres")
    axes[1].set_ylabel("Ville / Région")

    # Top 10 acheteurs publics
    acheteur_counts = df["acheteur"].value_counts().head(10)
    sns.barplot(x=acheteur_counts.values, y=acheteur_counts.index, ax=axes[2], palette="magma")
    axes[2].set_title("Top 10 des acheteurs publics")
    axes[2].set_xlabel("Nombre d'offres")
    axes[2].set_ylabel("Organisme acheteur")

    plt.tight_layout()
    chemin = output_dir / "02_repartition_categories_villes_acheteurs.png"
    fig.savefig(chemin, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin


def plot_tendances_temporelles_et_delais(
    df: pd.DataFrame,
    output_dir: Path = FIGURES_DIR,
) -> Path:
    """Graphique 3 : Évolution temporelle des publications et délais de réponse par catégorie."""
    output_dir.mkdir(parents=True, exist_ok=True)
    df_tmp = df.copy()
    df_tmp["date_publication"] = pd.to_datetime(df_tmp["date_publication"], errors="coerce")
    df_tmp["mois_pub"] = df_tmp["date_publication"].dt.to_period("M").astype(str)

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # Évolution temporelle mensuelle
    serie_temps = df_tmp.groupby("mois_pub").size().reset_index(name="nb_offres")
    sns.lineplot(data=serie_temps, x="mois_pub", y="nb_offres", marker="o", ax=axes[0], color="#1f77b4")
    axes[0].set_title("Évolution temporelle des publications d'appels d'offres")
    axes[0].set_xlabel("Mois de publication")
    axes[0].set_ylabel("Nombre d'offres")
    axes[0].tick_params(axis="x", rotation=45)

    # Délai de réponse par catégorie
    sns.boxplot(data=df_tmp, x="categorie", y="delai_reponse_jours", ax=axes[1], palette="Set2")
    axes[1].set_title("Délai de réponse par catégorie")
    axes[1].set_xlabel("Catégorie")
    axes[1].set_ylabel("Délai de réponse (jours)")

    plt.tight_layout()
    chemin = output_dir / "03_tendances_temporelles_delais.png"
    fig.savefig(chemin, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin


def plot_heatmap_correlations(
    df: pd.DataFrame,
    output_dir: Path = FIGURES_DIR,
) -> Path:
    """Graphique 4 : Matrice de corrélation Seaborn (estimation, caution, délai, longueur texte)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    df_num = pd.DataFrame(
        {
            "Estimation (MAD)": df["estimation_mad"],
            "Caution (MAD)": df["caution_mad"],
            "Délai (jours)": df["delai_reponse_jours"],
            "Longueur texte (car.)": df["texte_propre"].astype(str).str.len(),
        }
    )
    corr = df_num.corr(numeric_only=True)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, square=True, ax=ax)
    ax.set_title("Matrice de corrélation des variables numériques")

    plt.tight_layout()
    chemin = output_dir / "04_heatmap_correlations.png"
    fig.savefig(chemin, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin


def plot_top_mots_cles(
    df: pd.DataFrame,
    top_n: int = 20,
    output_dir: Path = FIGURES_DIR,
) -> Path:
    """Graphique 5 : Top 20 des termes les plus fréquents après nettoyage NLP."""
    output_dir.mkdir(parents=True, exist_ok=True)
    compteur: Counter[str] = Counter()
    for texte in df["texte_propre"].dropna().astype(str):
        compteur.update(texte.split())

    top_termes = compteur.most_common(top_n)
    mots, freqs = zip(*top_termes) if top_termes else ([], [])

    fig, ax = plt.subplots(figsize=(10, 7))
    sns.barplot(x=list(freqs), y=list(mots), ax=ax, palette="viridis")
    ax.set_title(f"Top {top_n} des mots-clés les plus fréquents (après suppression des stopwords)")
    ax.set_xlabel("Nombre d'occurrences")
    ax.set_ylabel("Terme nettoyé")

    plt.tight_layout()
    chemin = output_dir / "05_top_20_mots_cles.png"
    fig.savefig(chemin, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return chemin


def generer_toutes_figures_eda(df: pd.DataFrame, output_dir: Path = FIGURES_DIR) -> list[Path]:
    """Génère et enregistre l'ensemble des 5 figures analytiques de l'EDA."""
    return [
        plot_distributions_budgets(df, output_dir),
        plot_repartition_categories_villes(df, output_dir),
        plot_tendances_temporelles_et_delais(df, output_dir),
        plot_heatmap_correlations(df, output_dir),
        plot_top_mots_cles(df, top_n=20, output_dir=output_dir),
    ]
