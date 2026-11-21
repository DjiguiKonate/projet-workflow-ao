"""Fichier unique de tests unitaires pour le Binôme 1 (pytest)."""

import numpy as np
import pandas as pd

from src.nettoyage import charger_stopwords, nettoyer_dataset, nettoyer_texte, parser_montant


def test_parser_montant() -> None:
    assert parser_montant("125 000,00 DHS") == 125000.0
    assert np.isnan(parser_montant("Non communiqué"))


def test_nettoyer_texte() -> None:
    sw = charger_stopwords()
    res = nettoyer_texte("Appel d'offres relatif à l'achat de serveurs https://ex.ma 2026!", sw)
    assert "serveurs" in res
    assert "relatif" not in res
    assert "http" not in res
    assert "2026" not in res


def test_nettoyer_dataset_dedoublonne_et_filtre() -> None:
    df_raw = pd.DataFrame([
        {
            "reference": "AO-01",
            "acheteur": "CHU Agadir",
            "ville": "AGADIR",
            "categorie": "Fournitures",
            "date_publication": "2026-10-01",
            "date_limite": "2026-10-20",
            "estimation_mad": "250 000,00 DHS",
            "caution_mad": "5 000,00 DHS",
            "objet_brut": "Achat ordinateurs portables",
            "description_complete": "Matériel informatique",
        },
        # Doublon exact
        {
            "reference": "AO-01",
            "acheteur": "CHU Agadir",
            "ville": "Agadir",
            "categorie": "Fournitures",
            "date_publication": "2026-10-01",
            "date_limite": "2026-10-20",
            "estimation_mad": "250 000,00 DHS",
            "caution_mad": "5 000,00 DHS",
            "objet_brut": "Achat ordinateurs portables",
            "description_complete": "Matériel informatique",
        },
        # Délai négatif (doit être retiré)
        {
            "reference": "AO-02",
            "acheteur": "Commune Rabat",
            "ville": "Rabat",
            "categorie": "Services",
            "date_publication": "2026-10-15",
            "date_limite": "2026-10-10",
            "estimation_mad": "100 000 DHS",
            "caution_mad": "2 000 DHS",
            "objet_brut": "Nettoyage locaux",
            "description_complete": "",
        },
    ])
    df_clean = nettoyer_dataset(df_raw)
    assert len(df_clean) == 1
    assert df_clean.loc[0, "delai_reponse_jours"] == 19
    assert df_clean.loc[0, "ville"] == "Agadir"
    assert "ordinateurs" in df_clean.loc[0, "texte_propre"]
