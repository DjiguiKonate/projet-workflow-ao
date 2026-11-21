"""Module de prétraitement NLP des textes d'appels d'offres (Étape 2 - Binôme 1).

Transforme la fusion `objet_brut + description_complete` en une colonne `texte_propre`
directement exploitable par le TfidfVectorizer du Binôme 2 :
- Conversion en minuscules et normalisation Unicode des accents
- Suppression des URLs, ponctuations, caractères spéciaux et chiffres isolés
- Filtrage des stopwords français (NLTK) + dictionnaire de mots vides administratifs
- Racinisation légère (SnowballStemmer français) pour réduire la sparsité TF-IDF
"""

from pathlib import Path
import re
import sys
import unicodedata

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import STOPWORDS_METIER

# Liste de secours des stopwords français courants si le corpus NLTK n'est pas téléchargé
STOPWORDS_FR_SECOURS = {
    "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du", "elle", "en",
    "et", "eux", "il", "ils", "je", "la", "le", "les", "leur", "lui", "ma",
    "mais", "me", "même", "mes", "moi", "mon", "ne", "nos", "notre", "nous",
    "on", "ou", "par", "pas", "pour", "qu", "que", "qui", "sa", "se", "ses",
    "son", "sur", "ta", "te", "tes", "toi", "ton", "tu", "un", "une", "vos",
    "votre", "vous", "c", "d", "j", "l", "à", "m", "n", "s", "t", "y", "été",
    "étée", "étées", "étés", "étant", "suis", "es", "est", "sommes", "êtes",
    "sont", "serai", "seras", "sera", "serons", "serez", "seront", "avais",
    "avait", "avions", "aviez", "avaient", "ai", "as", "a", "avons", "avez",
    "ont", "aurai", "auras", "aura", "aurons", "aurez", "auront", "faire",
}


def charger_stopwords_francais() -> set[str]:
    """Charge les stopwords français NLTK enrichis des stopwords métier administratifs."""
    try:
        from nltk.corpus import stopwords

        mots_nltk = set(stopwords.words("french"))
    except Exception:
        # Repli automatique hors ligne si le téléchargement NLTK n'a pas été effectué
        mots_nltk = set(STOPWORDS_FR_SECOURS)

    return mots_nltk.union(set(STOPWORDS_METIER))


def normaliser_accents(texte: str) -> str:
    """Normalise les caractères Unicode (NFC) tout en conservant les accents français."""
    return unicodedata.normalize("NFC", texte)


def nettoyer_texte(
    texte: object,
    stopwords_set: set[str] | None = None,
    appliquer_stemming: bool = False,
) -> str:
    """Nettoie un texte administratif en vue de sa vectorisation TF-IDF.

    Args:
        texte: Texte brut (objet + description).
        stopwords_set: Ensemble de mots vides à supprimer (chargé par défaut).
        appliquer_stemming: Si True, applique une racinisation légère SnowballStemmer.

    Returns:
        Chaîne nettoyée, en minuscules, sans caractères spéciaux ni mots vides.
    """
    if pd.isna(texte) or not str(texte).strip():
        return ""

    if stopwords_set is None:
        stopwords_set = charger_stopwords_francais()

    # 1. Minuscules et normalisation Unicode
    propre = normaliser_accents(str(texte).lower())

    # 2. Suppression des URLs et adresses e-mail
    propre = re.sub(r"https?://\S+|www\.\S+|\S+@\S+", " ", propre)

    # 3. Suppression des suites de chiffres non significatives et caractères spéciaux
    propre = re.sub(r"\b\d+\b", " ", propre)
    propre = re.sub(r"[^a-zàâäéèêëïîôöùûüç\s]", " ", propre)

    # 4. Suppression des stopwords (NLTK + métier) et des tokens de moins de 2 lettres
    tokens = [
        mot
        for mot in propre.split()
        if len(mot) > 2 and mot not in stopwords_set
    ]

    # 5. Racinisation optionnelle pour regrouper les variantes morphologiques
    if appliquer_stemming and tokens:
        try:
            from nltk.stem.snowball import FrenchStemmer

            stemmer = FrenchStemmer()
            tokens = [stemmer.stem(mot) for mot in tokens]
        except Exception:
            pass

    return " ".join(tokens)


def ajouter_colonne_texte_propre(
    df: pd.DataFrame,
    appliquer_stemming: bool = False,
) -> pd.DataFrame:
    """Fusionne `objet_brut` et `description_complete` et génère `texte_propre`.

    Args:
        df: DataFrame nettoyé sur le plan tabulaire.
        appliquer_stemming: Active ou non la racinisation française.

    Returns:
        DataFrame enrichi de la colonne `texte_propre`.
    """
    df_out = df.copy()
    stopwords_set = charger_stopwords_francais()

    objet = df_out.get("objet_brut", pd.Series("", index=df_out.index)).fillna("").astype(str)
    desc = df_out.get("description_complete", pd.Series("", index=df_out.index)).fillna("").astype(str)

    fusion = (objet + " " + desc).str.strip()
    df_out["texte_propre"] = fusion.apply(
        lambda txt: nettoyer_texte(
            txt,
            stopwords_set=stopwords_set,
            appliquer_stemming=appliquer_stemming,
        )
    )
    # Garantit qu'aucune ligne n'a un texte_propre vide
    df_out["texte_propre"] = df_out["texte_propre"].replace("", "marche public")
    return df_out
