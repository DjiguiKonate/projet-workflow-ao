"""Validation du contrat d'interface entre le Binôme 1 et le Binôme 2."""

import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import CATEGORIES_VALIDES, CLEAN_DATA_PATH, COLONNES_CONTRAT


def valider_contrat_donnees(chemin_csv: Path = CLEAN_DATA_PATH) -> bool:
    """Vérifie que le fichier nettoyé respecte le contrat d'interface Binôme 1 -> Binôme 2.

    Args:
        chemin_csv: Chemin vers le fichier CSV nettoyé.

    Returns:
        True si toutes les règles du contrat sont respectées.

    Raises:
        ValueError: Si une colonne manque ou si une règle de validation échoue.
    """
    if not chemin_csv.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin_csv}")

    df = pd.read_csv(chemin_csv)

    # 1. Présence exacte des colonnes requises
    colonnes_manquantes = [c for c in COLONNES_CONTRAT if c not in df.columns]
    if colonnes_manquantes:
        raise ValueError(f"Colonnes manquantes dans le contrat : {colonnes_manquantes}")

    # 2. Unicité et non-nullité de hash_ao
    if df["hash_ao"].isna().any():
        raise ValueError("La colonne 'hash_ao' contient des valeurs nulles.")
    if df["hash_ao"].duplicated().any():
        raise ValueError("La colonne 'hash_ao' contient des doublons.")

    # 3. Catégories valides
    categories_trouvees = set(df["categorie"].dropna().unique())
    invalides = categories_trouvees - set(CATEGORIES_VALIDES)
    if invalides:
        raise ValueError(f"Catégories invalides détectées : {invalides}")

    # 4. Délais de réponse positifs ou nuls
    if (df["delai_reponse_jours"].dropna() < 0).any():
        raise ValueError("Des délais de réponse négatifs ont été détectés.")

    # 5. Montants positifs (hors NaN)
    for col in ["estimation_mad", "caution_mad"]:
        if (df[col].dropna() < 0).any():
            raise ValueError(f"Des valeurs négatives ont été détectées dans '{col}'.")

    # 6. Texte propre non vide
    if df["texte_propre"].isna().any() or (df["texte_propre"].astype(str).str.strip() == "").any():
        raise ValueError("La colonne 'texte_propre' contient des valeurs vides.")

    print(f"Contrat de données validé avec succès ({len(df)} lignes).")
    return True


if __name__ == "__main__":
    valider_contrat_donnees()
