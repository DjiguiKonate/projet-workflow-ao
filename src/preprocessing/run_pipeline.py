"""Script principal de prétraitement (Étape 2 - Binôme 1).

Lit `data/raw/appels_offres_raw.csv`, applique le nettoyage tabulaire puis NLP,
enregistre `data/processed/appels_offres_clean.csv` et vérifie le contrat d'interface.
"""

from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import CLEAN_DATA_PATH, COLONNES_CONTRAT, RAW_DATA_PATH
from src.preprocessing.tabular_cleaner import nettoyer_donnees_tabulaires
from src.preprocessing.text_cleaner import ajouter_colonne_texte_propre
from src.utils.validate_contract import valider_contrat_donnees


def executer_pretraitement(
    raw_path: Path = RAW_DATA_PATH,
    clean_path: Path = CLEAN_DATA_PATH,
) -> pd.DataFrame:
    """Exécute la chaîne complète de nettoyage et valide le fichier produit."""
    df_raw = pd.read_csv(raw_path)
    df_tab = nettoyer_donnees_tabulaires(df_raw)
    df_clean = ajouter_colonne_texte_propre(df_tab)

    # Réorganisation des colonnes selon l'ordre exact du contrat d'interface
    df_export = df_clean[COLONNES_CONTRAT].copy()
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    df_export.to_csv(clean_path, index=False, encoding="utf-8-sig")

    valider_contrat_donnees(clean_path)
    return df_export


if __name__ == "__main__":
    executer_pretraitement()
