"""Fichier 2 : Prétraitement et nettoyage des données (Tabulaire + Texte).

Notions utilisées (Cours Séance 2, Séance 3 & Séance 5) :
- Pandas (DataFrame, to_datetime, drop_duplicates, dropna, isna, to_csv)
- NumPy (np.nan)
- Méthodes de chaînes (.lower(), .strip(), .split(), .title()) et expressions régulières (re)
"""

import hashlib
import os
import re

import numpy as np
import pandas as pd

# Ensemble des mots vides (stopwords) français et administratifs à retirer des textes
STOPWORDS_FR = {
    "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du", "en", "et",
    "il", "la", "le", "les", "leur", "mais", "ne", "nos", "notre", "nous",
    "ou", "par", "pas", "pour", "que", "qui", "sa", "se", "ses", "son", "sur",
    "un", "une", "vos", "votre", "vous", "est", "sont", "été", "être", "avoir",
    "relatif", "relative", "objet", "appel", "offres", "offre", "marche",
    "marché", "lot", "unique", "portant", "mad", "dhs", "dh",
}


def parser_montant(valeur):
    """Convertit un texte comme '125 000,00 DHS' en nombre flottant (float) ou NaN."""
    # Retourner NaN si la valeur est déjà manquante
    if pd.isna(valeur):
        return np.nan
    # Supprimer les mots de devise et les espaces, puis remplacer la virgule par un point
    texte = re.sub(r"(?i)(dhs?|mad|dirhams?|\s)", "", str(valeur)).replace(",", ".")
    # Garder uniquement les chiffres, le point et le signe moins
    texte = re.sub(r"[^0-9.\-]", "", texte)
    # Tenter de convertir la chaîne nettoyée en nombre décimal (float)
    try:
        nombre = float(texte)
        # Retourner le nombre s'il est positif, sinon NaN (valeur aberrante)
        return nombre if nombre >= 0 else np.nan
    except ValueError:
        # Retourner NaN si la conversion échoue
        return np.nan


def nettoyer_texte(texte):
    """Nettoie un texte en vue de l'analyse NLP (minuscules, sans ponctuation ni stopwords)."""
    # Retourner une chaîne vide si le texte est manquant
    if pd.isna(texte):
        return ""
    # Passer tout le texte en minuscules et supprimer les URLs et nombres isolés
    propre = re.sub(r"https?://\S+|\b\d+\b", " ", str(texte).lower())
    # Remplacer tous les caractères spéciaux et ponctuations par des espaces
    propre = re.sub(r"[^a-zàâäéèêëïîôöùûüç\s]", " ", propre)
    # Découper en mots et garder ceux de plus de 2 lettres qui ne sont pas des stopwords
    mots = [m for m in propre.split() if len(m) > 2 and m not in STOPWORDS_FR]
    # Reconstruire une phrase propre avec des espaces simples
    return " ".join(mots)


def standardiser_categorie(categorie):
    """Rattache la catégorie brute à l'une des 3 classes : Fournitures, Services, Travaux."""
    # Convertir la valeur en minuscules pour faciliter la comparaison
    texte = str(categorie).lower()
    # Détecter si l'annonce concerne des fournitures ou équipements
    if "fourniture" in texte or "equipement" in texte:
        return "Fournitures"
    # Détecter si l'annonce concerne des travaux ou du BTP
    if "travaux" in texte or "btp" in texte:
        return "Travaux"
    # Par défaut, classer dans Services
    return "Services"


def nettoyer_dataset(df_raw):
    """Applique tout le nettoyage tabulaire et textuel sur le DataFrame brut."""
    # Faire une copie pour ne pas modifier le DataFrame original
    df = df_raw.copy()

    # Nettoyer les colonnes texte de base (remplacer les vides et enlever les espaces en trop)
    for col in ["reference", "acheteur", "objet_brut", "ville"]:
        df[col] = df.get(col, "").fillna("").astype(str).str.strip()
    # Uniformiser la casse des noms de villes (ex: "AGADIR" -> "Agadir")
    df["ville"] = df["ville"].replace("", "Non précisé").str.title()
    # Standardiser les catégories et convertir la colonne en type category
    df["categorie"] = df.get("categorie", "Services").apply(standardiser_categorie).astype("category")

    # Convertir les colonnes de dates au format datetime (ISO ou JJ/MM/AAAA)
    for col in ["date_publication", "date_limite"]:
        d_iso = pd.to_datetime(df[col], format="%Y-%m-%d", errors="coerce")
        d_fr = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
        df[col] = d_iso.fillna(d_fr)
    # Supprimer les lignes dont les dates sont invalides ou manquantes
    df = df.dropna(subset=["date_publication", "date_limite"]).copy()
    # Calculer le délai de réponse en nombre de jours
    df["delai_reponse_jours"] = (df["date_limite"] - df["date_publication"]).dt.days
    # Supprimer les délais négatifs (erreurs de saisie)
    df = df[df["delai_reponse_jours"] >= 0].copy()

    # Convertir les montants textuels en nombres décimaux (float64)
    df["estimation_mad"] = df["estimation_mad"].apply(parser_montant).astype("float64")
    df["caution_mad"] = df["caution_mad"].apply(parser_montant).astype("float64")
    # Créer une colonne booléenne indiquant si l'estimation est manquante
    df["estimation_manquante"] = df["estimation_mad"].isna()

    # Calculer une empreinte unique MD5 par annonce pour repérer les doublons exacts
    df["hash_ao"] = df.apply(
        lambda r: hashlib.md5(
            f"{r['reference'].lower()}|{r['acheteur'].lower()}|{r['date_publication']:%Y-%m-%d}".encode()
        ).hexdigest(),
        axis=1,
    )
    # Supprimer les doublons en gardant la première occurrence
    df = df.drop_duplicates(subset=["hash_ao"]).reset_index(drop=True)
    # Formater les dates en texte ISO YYYY-MM-DD pour l'export CSV
    df["date_publication"] = df["date_publication"].dt.strftime("%Y-%m-%d")
    df["date_limite"] = df["date_limite"].dt.strftime("%Y-%m-%d")

    # Fusionner l'objet et la description puis nettoyer le texte pour le Machine Learning
    fusion = df["objet_brut"] + " " + df.get("description_complete", "").fillna("").astype(str)
    df["texte_propre"] = fusion.apply(nettoyer_texte).replace("", "marche public")

    # Définir l'ordre exact des colonnes attendues par le Binôme 2
    colonnes = [
        "hash_ao", "reference", "acheteur", "ville", "categorie",
        "date_publication", "date_limite", "delai_reponse_jours",
        "estimation_mad", "caution_mad", "estimation_manquante",
        "objet_brut", "texte_propre",
    ]
    # Retourner le DataFrame propre avec les colonnes ordonnées
    return df[colonnes]


if __name__ == "__main__":
    # Lire le fichier brut collecté à l'étape 1
    df_brut = pd.read_csv("data/raw/appels_offres_raw.csv")
    # Appliquer la fonction de nettoyage complet
    df_propre = nettoyer_dataset(df_brut)
    # Créer le dossier de sortie si besoin
    os.makedirs("data/processed", exist_ok=True)
    # Sauvegarder le fichier propre pour le Binôme 2
    df_propre.to_csv("data/processed/appels_offres_clean.csv", index=False, encoding="utf-8-sig")
    # Afficher un résumé dans le terminal
    print(f"Nettoyage terminé : {len(df_propre)} annonces propres sauvegardées.")
