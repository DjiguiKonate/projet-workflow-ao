"""Module de nettoyage tabulaire des appels d'offres (Étape 2 - Binôme 1).

Opérations réalisées :
1. Calcul de l'empreinte unique MD5 (hash_ao) et déduplication exacte
2. Normalisation des chaînes (reference, acheteur, ville, categorie)
3. Conversion des dates au format datetime64 et calcul de delai_reponse_jours
4. Conversion des montants textuels (ex. "125 000,00 DHS") en float64
5. Gestion des valeurs manquantes (estimation_manquante) et suppression des anomalies
"""

import hashlib
import logging
import re
from typing import Optional
import unicodedata

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Dictionnaire de standardisation des principales villes et préfectures marocaines
CORRESPONDANCE_VILLES: dict[str, str] = {
    "agadir": "Agadir",
    "agadir ida outanane": "Agadir",
    "casablanca": "Casablanca",
    "grand casablanca": "Casablanca",
    "rabat": "Rabat",
    "sale": "Salé",
    "marrakech": "Marrakech",
    "tanger": "Tanger",
    "tanger assilah": "Tanger",
    "fes": "Fès",
    "meknes": "Meknès",
    "oujda": "Oujda",
    "kenitra": "Kénitra",
    "tetouan": "Tétouan",
    "laayoune": "Laâyoune",
    "settat": "Settat",
    "beni mellal": "Béni Mellal",
}

# Mapping vers les 3 catégories officielles du contrat de données
CORRESPONDANCE_CATEGORIES: dict[str, str] = {
    "fourniture": "Fournitures",
    "fournitures": "Fournitures",
    "equipement": "Fournitures",
    "service": "Services",
    "services": "Services",
    "prestation": "Services",
    "etude": "Services",
    "travaux": "Travaux",
    "btp": "Travaux",
    "amenagement": "Travaux",
}


def calculer_hash_ao(reference: str, acheteur: str, date_publication: str) -> str:
    """Calcule une empreinte MD5 unique à partir de la référence, de l'acheteur et de la date.

    Garantit l'idempotence et la déduplication exacte lors des collectes répétées.

    Args:
        reference: Référence officielle de l'appel d'offres.
        acheteur: Nom de l'organisme acheteur.
        date_publication: Date de publication sous forme de chaîne.

    Returns:
        Empreinte hexadécimale MD5 sur 32 caractères.
    """
    cle = f"{str(reference).strip().lower()}|{str(acheteur).strip().lower()}|{str(date_publication).strip()}"
    return hashlib.md5(cle.encode("utf-8")).hexdigest()


def parser_montant_mad(valeur: object) -> float:
    """Convertit un montant textuel (ex. '125 000,00 DHS') en float64 positif ou NaN.

    Args:
        valeur: Valeur brute issue du scraping (chaîne, nombre ou NaN).

    Returns:
        Montant numérique en MAD, ou np.nan si absent ou non convertible.
    """
    if pd.isna(valeur):
        return np.nan

    if isinstance(valeur, (int, float)):
        return float(valeur) if float(valeur) >= 0 else np.nan

    texte = str(valeur).strip()
    if not texte or texte.lower() in {"nan", "none", "nc", "non communiqué", "-"}:
        return np.nan

    # Suppression des devises et espaces insécables, puis normalisation de la virgule décimale
    texte = re.sub(r"(?i)(dhs?|mad|dirhams?)", "", texte)
    texte = texte.replace("\xa0", "").replace(" ", "").replace(",", ".")
    texte = re.sub(r"[^0-9.\-]", "", texte)

    try:
        montant = float(texte)
        return montant if montant >= 0 else np.nan
    except ValueError:
        return np.nan


def standardiser_ville(ville: object) -> str:
    """Uniformise les noms de villes/régions (ex. 'AGADIR', 'Agadir Ida-Outanane' -> 'Agadir').

    Args:
        ville: Nom brut de la ville ou région.

    Returns:
        Nom standardisé de la ville, ou 'Non précisé' si manquant.
    """
    if pd.isna(ville) or not str(ville).strip():
        return "Non précisé"

    texte = str(ville).strip()
    # Suppression des accents et tirets pour faciliter la recherche dans le dictionnaire
    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", texte.lower()) if unicodedata.category(c) != "Mn"
    )
    cle = re.sub(r"[-_/]+", " ", sans_accent)
    cle = re.sub(r"\s+", " ", cle).strip()

    for motif, ville_propre in CORRESPONDANCE_VILLES.items():
        if motif in cle:
            return ville_propre

    return re.sub(r"\s+", " ", texte).title()


def standardiser_categorie(categorie: object) -> str:
    """Rattache chaque catégorie brute à l'une des 3 classes : Fournitures, Services, Travaux."""
    if pd.isna(categorie) or not str(categorie).strip():
        return "Services"

    sans_accent = "".join(
        c
        for c in unicodedata.normalize("NFD", str(categorie).lower())
        if unicodedata.category(c) != "Mn"
    )
    for motif, cat_propre in CORRESPONDANCE_CATEGORIES.items():
        if motif in sans_accent:
            return cat_propre
    return "Services"


def nettoyer_donnees_tabulaires(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Applique l'ensemble du pipeline de nettoyage tabulaire sur le DataFrame brut.

    Args:
        df_raw: DataFrame brut issu de la collecte.

    Returns:
        DataFrame nettoyé, dédupliqué et typé conformément au contrat d'interface.
    """
    df = df_raw.copy()
    nb_initial = len(df)
    logger.info("Début du nettoyage tabulaire sur %d lignes.", nb_initial)

    # 1. Nettoyage des chaînes de base (suppression des espaces superflus)
    for col in ["reference", "acheteur", "objet_brut"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

    # 2. Standardisation des villes et des catégories
    df["ville"] = df.get("ville", pd.Series("", index=df.index)).apply(standardiser_ville)
    df["categorie"] = (
        df.get("categorie", pd.Series("Services", index=df.index))
        .apply(standardiser_categorie)
        .astype("category")
    )

    # 3. Conversion des dates (ISO YYYY-MM-DD en priorité, sinon format français JJ/MM/AAAA)
    for col_date in ["date_publication", "date_limite"]:
        s_iso = pd.to_datetime(df[col_date], format="%Y-%m-%d", errors="coerce")
        s_fr = pd.to_datetime(df[col_date], dayfirst=True, errors="coerce")
        df[col_date] = s_iso.fillna(s_fr)
    df = df.dropna(subset=["date_publication", "date_limite"]).copy()
    df["delai_reponse_jours"] = (df["date_limite"] - df["date_publication"]).dt.days

    # Suppression des délais aberrants négatifs
    df = df[df["delai_reponse_jours"] >= 0].copy()

    # 4. Conversion des montants (MAD) et indicateur de valeur manquante
    df["estimation_mad"] = df["estimation_mad"].apply(parser_montant_mad).astype("float64")
    df["caution_mad"] = df["caution_mad"].apply(parser_montant_mad).astype("float64")
    df["estimation_manquante"] = df["estimation_mad"].isna()

    # 5. Calcul du hash_ao (MD5) et suppression des doublons exacts
    df["hash_ao"] = df.apply(
        lambda row: calculer_hash_ao(
            row["reference"],
            row["acheteur"],
            row["date_publication"].strftime("%Y-%m-%d"),
        ),
        axis=1,
    )
    df = df.drop_duplicates(subset=["hash_ao"], keep="first").reset_index(drop=True)

    # Formatage ISO YYYY-MM-DD des dates pour l'export CSV propre
    df["date_publication"] = df["date_publication"].dt.strftime("%Y-%m-%d")
    df["date_limite"] = df["date_limite"].dt.strftime("%Y-%m-%d")

    logger.info(
        "Nettoyage tabulaire terminé : %d -> %d lignes uniques conservées.",
        nb_initial,
        len(df),
    )
    return df
