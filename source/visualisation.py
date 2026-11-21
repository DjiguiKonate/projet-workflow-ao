"""Fichier 3 : Exploration statistique et visualisations (EDA).

Notions utilisées (Cours Séance 6) :
- df.isna(), df.describe() pour l'audit statistique sous Pandas
- Matplotlib (plt.subplots, savefig, close) et Seaborn (histplot, boxplot, barplot, lineplot, heatmap)
"""

from collections import Counter
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Appliquer un thème visuel propre à tous les graphiques Seaborn
sns.set_theme(style="whitegrid")


def resume_statistique(df):
    """Affiche le pourcentage de valeurs manquantes et les statistiques descriptives."""
    # Afficher le titre de la section valeurs manquantes
    print("=== Valeurs manquantes (%) ===")
    # Calculer la moyenne des valeurs nulles par colonne et multiplier par 100
    print((df.isna().mean() * 100).round(2))
    # Afficher le titre de la section statistiques descriptives
    print("\n=== Statistiques descriptives ===")
    # Afficher moyenne, écart-type, min, quartiles et max avec df.describe()
    print(df.describe().round(2))


def generer_graphiques(df, dossier_sortie="reports/figures"):
    """Génère et sauvegarde les 5 graphiques d'exploration dans reports/figures/."""
    # Créer le dossier de destination des images s'il n'existe pas
    os.makedirs(dossier_sortie, exist_ok=True)
    # Créer une liste pour stocker les chemins des images générées
    fichiers = []

    # --- Graphique 1 : Distribution et valeurs extrêmes des budgets ---
    # Créer une figure avec 2 graphiques côte à côte
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    # Garder uniquement les estimations positives et non nulles
    est = df["estimation_mad"].dropna()
    est = est[est > 0]
    # Tracer l'histogramme avec courbe KDE en échelle logarithmique (log10)
    sns.histplot(np.log10(est), kde=True, ax=axes[0], color="#2b5c8f")
    # Ajouter le titre et les noms d'axes
    axes[0].set_title("Distribution des estimations (échelle log10)")
    axes[0].set_xlabel("log10(Estimation en MAD)")
    # Tracer la boîte à moustaches (boxplot) pour visualiser les outliers
    sns.boxplot(x=est, ax=axes[1], color="#4c9f70")
    # Passer l'axe X en échelle logarithmique
    axes[1].set_xscale("log")
    axes[1].set_title("Boxplot des estimations (valeurs extrêmes)")
    axes[1].set_xlabel("Estimation (MAD)")
    # Définir le chemin du fichier image
    p1 = os.path.join(dossier_sortie, "01_budgets_outliers.png")
    # Sauvegarder la figure en haute résolution (300 DPI)
    fig.savefig(p1, dpi=300, bbox_inches="tight")
    # Fermer la figure pour libérer la mémoire
    plt.close(fig)
    # Ajouter le chemin à la liste
    fichiers.append(p1)

    # --- Graphique 2 : Répartition par catégorie et Top 10 des villes ---
    # Créer une figure avec 2 sous-graphiques
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    # Compter le nombre d'offres par catégorie
    cat = df["categorie"].value_counts()
    # Tracer un diagramme en barres horizontales pour les catégories
    sns.barplot(x=cat.values, y=cat.index, ax=axes[0])
    axes[0].set_title("Volume d'offres par catégorie")
    axes[0].set_xlabel("Nombre d'offres")
    # Compter les 10 villes ayant le plus d'offres
    villes = df["ville"].value_counts().head(10)
    # Tracer un diagramme en barres horizontales pour les villes
    sns.barplot(x=villes.values, y=villes.index, ax=axes[1])
    axes[1].set_title("Top 10 des villes")
    axes[1].set_xlabel("Nombre d'offres")
    p2 = os.path.join(dossier_sortie, "02_categories_villes.png")
    fig.savefig(p2, dpi=300, bbox_inches="tight")
    plt.close(fig)
    fichiers.append(p2)

    # --- Graphique 3 : Tendances temporelles et délais par catégorie ---
    # Copier le DataFrame pour ajouter une colonne mois temporaire
    df_t = df.copy()
    # Extraire l'année et le mois de publication
    df_t["mois"] = pd.to_datetime(df_t["date_publication"]).dt.to_period("M").astype(str)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    # Compter les offres par mois et tracer la courbe d'évolution (lineplot)
    serie_mois = df_t.groupby("mois").size().reset_index(name="nb")
    sns.lineplot(data=serie_mois, x="mois", y="nb", marker="o", ax=axes[0])
    axes[0].set_title("Évolution mensuelle des publications")
    axes[0].tick_params(axis="x", rotation=45)
    # Tracer le boxplot des délais de réponse selon la catégorie
    sns.boxplot(data=df_t, x="categorie", y="delai_reponse_jours", ax=axes[1])
    axes[1].set_title("Délais de réponse (jours) par catégorie")
    p3 = os.path.join(dossier_sortie, "03_tendances_delais.png")
    fig.savefig(p3, dpi=300, bbox_inches="tight")
    plt.close(fig)
    fichiers.append(p3)

    # --- Graphique 4 : Matrice de corrélation (Heatmap Seaborn) ---
    # Construire un DataFrame uniquement avec les variables numériques
    num = pd.DataFrame({
        "Estimation": df["estimation_mad"],
        "Caution": df["caution_mad"],
        "Délai (j)": df["delai_reponse_jours"],
        "Longueur texte": df["texte_propre"].astype(str).str.len(),
    })
    fig, ax = plt.subplots(figsize=(6, 5))
    # Tracer la heatmap de corrélation avec les valeurs affichées (annot=True)
    sns.heatmap(num.corr(), annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title("Corrélations entre variables numériques")
    p4 = os.path.join(dossier_sortie, "04_correlations.png")
    fig.savefig(p4, dpi=300, bbox_inches="tight")
    plt.close(fig)
    fichiers.append(p4)

    # --- Graphique 5 : Top 20 des mots-clés après nettoyage ---
    # Initialiser un compteur de mots
    compteur = Counter()
    # Parcourir chaque texte propre et compter la fréquence de chaque mot
    for txt in df["texte_propre"].dropna():
        compteur.update(str(txt).split())
    # Extraire les 20 mots les plus fréquents et leurs effectifs
    mots, freqs = zip(*compteur.most_common(20)) if compteur else ([], [])
    fig, ax = plt.subplots(figsize=(9, 6))
    # Tracer le graphique en barres horizontales des mots-clés
    sns.barplot(x=list(freqs), y=list(mots), ax=ax)
    ax.set_title("Top 20 des mots-clés après nettoyage")
    ax.set_xlabel("Nombre d'occurrences")
    p5 = os.path.join(dossier_sortie, "05_top_mots_cles.png")
    fig.savefig(p5, dpi=300, bbox_inches="tight")
    plt.close(fig)
    fichiers.append(p5)

    # Retourner la liste des 5 chemins d'images créées
    return fichiers


if __name__ == "__main__":
    # Charger le dataset nettoyé produit à l'étape 2
    df_clean = pd.read_csv("data/processed/appels_offres_clean.csv")
    # Afficher le résumé statistique dans le terminal
    resume_statistique(df_clean)
    # Générer les 5 graphiques dans reports/figures/
    generer_graphiques(df_clean)
