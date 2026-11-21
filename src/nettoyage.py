"""Étape 2 (Binôme 1) : Nettoyage tabulaire et textuel (NLP) avec Pandas et re/NLTK.

Transforme data/raw/appels_offres_raw.csv en data/processed/appels_offres_clean.csv
en respectant le contrat d'interface avec le Binôme 2.
"""

import hashlib
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import CLEAN_DATA_PATH, COLONNES_CONTRAT, RAW_DATA_PATH, STOPWORDS_METIER
from src.utils.validate_contract import valider_contrat_donnees

# Stopwords français de secours si NLTK n'est pas téléchargé hors ligne
STOPWORDS_BASE = {
    "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du", "en", "et",
    "il", "la", "le", "les", "leur", "mais", "ne", "nos", "notre", "nous",
    "ou", "par", "pas", "pour", "que", "qui", "sa", "se", "ses", "son", "sur",
    "un", "une", "vos", "votre", "vous", "est", "sont", "été", "être", "avoir",
}


def charger_stopwords() -> set[str]:
    """Charge les stopwords français NLTK + mots vides administratifs."""
    try:
        from nltk.corpus import stopwords
        mots = set(stopwords.words("french"))
    except Exception:
        mots = set(STOPWORDS_BASE)
    return mots.union(STOPWORDS_METIER)


def parser_montant(valeur: object) -> float:
    """Convertit un texte comme '125 000,00 DHS' en nombre float64 ou NaN."""
    if pd.isna(valeur):
        return np.nan
    texte = re.sub(r"(?i)(dhs?|mad|dirhams?|\s)", "", str(valeur)).replace(",", ".")
    texte = re.sub(r"[^0-9.\-]", "", texte)
    try:
        val = float(texte)
        return val if val >= 0 else np.nan
    except ValueError:
        return np.nan


def nettoyer_texte(texte: object, stopwords_set: set[str]) -> str:
    """Met en minuscules, retire URLs/chiffres/ponctuation et filtre les stopwords."""
    if pd.isna(texte):
        return ""
    propre = re.sub(r"https?://\S+|\b\d+\b", " ", str(texte).lower())
    propre = re.sub(r"[^a-zàâäéèêëïîôöùûüç\s]", " ", propre)
    mots = [m for m in propre.split() if len(m) > 2 and m not in stopwords_set]
    return " ".join(mots)


def nettoyer_dataset(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Applique tout le nettoyage (doublons MD5, dates, montants, villes, texte NLP)."""
    df = df_raw.copy()

    # 1. Nettoyage simple des chaînes et standardisation des villes/catégories
    for col in ["reference", "acheteur", "objet_brut", "ville"]:
        df[col] = df.get(col, "").fillna("").astype(str).str.strip()
    df["ville"] = df["ville"].replace("", "Non précisé").str.title()

    def _cat(c: object) -> str:
        s = str(c).lower()
        if "fourniture" in s or "equipement" in s:
            return "Fournitures"
        if "travaux" in s or "btp" in s:
            return "Travaux"
        return "Services"

    df["categorie"] = df.get("categorie", "Services").apply(_cat).astype("category")

    # 2. Dates (ISO ou JJ/MM/AAAA) et calcul du délai de réponse
    for col in ["date_publication", "date_limite"]:
        d_iso = pd.to_datetime(df[col], format="%Y-%m-%d", errors="coerce")
        d_fr = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
        df[col] = d_iso.fillna(d_fr)
    df = df.dropna(subset=["date_publication", "date_limite"]).copy()
    df["delai_reponse_jours"] = (df["date_limite"] - df["date_publication"]).dt.days
    df = df[df["delai_reponse_jours"] >= 0].copy()

    # 3. Montants en MAD et indicateur de valeur manquante
    df["estimation_mad"] = df["estimation_mad"].apply(parser_montant).astype("float64")
    df["caution_mad"] = df["caution_mad"].apply(parser_montant).astype("float64")
    df["estimation_manquante"] = df["estimation_mad"].isna()

    # 4. Empreinte MD5 et suppression des doublons exacts
    df["hash_ao"] = df.apply(
        lambda r: hashlib.md5(
            f"{r['reference'].lower()}|{r['acheteur'].lower()}|{r['date_publication']:%Y-%m-%d}".encode()
        ).hexdigest(),
        axis=1,
    )
    df = df.drop_duplicates(subset=["hash_ao"]).reset_index(drop=True)
    df["date_publication"] = df["date_publication"].dt.strftime("%Y-%m-%d")
    df["date_limite"] = df["date_limite"].dt.strftime("%Y-%m-%d")

    # 5. Nettoyage NLP pour créer texte_propre
    sw = charger_stopwords()
    fusion = df["objet_brut"] + " " + df.get("description_complete", "").fillna("").astype(str)
    df["texte_propre"] = fusion.apply(lambda t: nettoyer_texte(t, sw)).replace("", "marche public")

    return df[COLONNES_CONTRAT]


if __name__ == "__main__":
    df_clean = nettoyer_dataset(pd.read_csv(RAW_DATA_PATH))
    CLEAN_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(CLEAN_DATA_PATH, index=False, encoding="utf-8-sig")
    valider_contrat_donnees(CLEAN_DATA_PATH)
