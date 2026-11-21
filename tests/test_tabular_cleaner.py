"""Tests unitaires pour le module de nettoyage tabulaire (tabular_cleaner.py)."""

import pandas as pd
import numpy as np

from src.preprocessing.tabular_cleaner import (
    calculer_hash_ao,
    nettoyer_donnees_tabulaires,
    parser_montant_mad,
    standardiser_ville,
)


def test_parser_montant_mad() -> None:
    """Vérifie la conversion de montants textuels en float64 positif."""
    assert parser_montant_mad("125 000,00 DHS") == 125000.0
    assert parser_montant_mad("45000.50 MAD") == 45000.50
    assert np.isnan(parser_montant_mad("Non communiqué"))
    assert np.isnan(parser_montant_mad(-100))


def test_standardiser_ville() -> None:
    """Vérifie la normalisation des noms de villes/préfectures."""
    assert standardiser_ville("AGADIR") == "Agadir"
    assert standardiser_ville("Agadir Ida-Outanane") == "Agadir"
    assert standardiser_ville("grand casablanca") == "Casablanca"
    assert standardiser_ville("") == "Non précisé"


def test_deduplication_et_delai() -> None:
    """Vérifie la déduplication MD5 et le filtrage des délais négatifs."""
    df_raw = pd.DataFrame(
        [
            {
                "reference": "AO-01/2026",
                "acheteur": "CHU Souss Massa",
                "ville": "AGADIR",
                "categorie": "Fournitures",
                "date_publication": "2026-10-01",
                "date_limite": "2026-10-20",
                "estimation_mad": "250 000,00 DHS",
                "caution_mad": "5 000,00 DHS",
                "objet_brut": "Achat de matériel informatique",
            },
            # Doublon exact
            {
                "reference": "AO-01/2026",
                "acheteur": "CHU Souss Massa",
                "ville": "Agadir",
                "categorie": "Fournitures",
                "date_publication": "2026-10-01",
                "date_limite": "2026-10-20",
                "estimation_mad": "250 000,00 DHS",
                "caution_mad": "5 000,00 DHS",
                "objet_brut": "Achat de matériel informatique",
            },
            # Délai négatif aberrant (doit être supprimé)
            {
                "reference": "AO-02/2026",
                "acheteur": "Commune Rabat",
                "ville": "Rabat",
                "categorie": "Services",
                "date_publication": "2026-10-15",
                "date_limite": "2026-10-10",
                "estimation_mad": "100 000 DHS",
                "caution_mad": "2 000 DHS",
                "objet_brut": "Nettoyage des locaux",
            },
        ]
    )

    df_clean = nettoyer_donnees_tabulaires(df_raw)
    assert len(df_clean) == 1
    assert df_clean.loc[0, "delai_reponse_jours"] == 19
    assert df_clean.loc[0, "ville"] == "Agadir"
    assert df_clean.loc[0, "estimation_manquante"] == False  # noqa: E712
    assert df_clean.loc[0, "hash_ao"] == calculer_hash_ao("AO-01/2026", "CHU Souss Massa", "2026-10-01")
