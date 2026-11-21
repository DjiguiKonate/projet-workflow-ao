"""Tests unitaires pour le module de nettoyage textuel NLP (text_cleaner.py)."""

import pandas as pd

from src.preprocessing.text_cleaner import ajouter_colonne_texte_propre, nettoyer_texte


def test_nettoyer_texte_supprime_urls_ponctuation_et_stopwords() -> None:
    """Vérifie la suppression des caractères spéciaux, URLs et mots vides métier."""
    texte_brut = (
        "Appel d'offres N° 12/2026 relatif à la fourniture de serveurs "
        "et ordinateurs! Voir https://www.marchespublics.gov.ma/ao12"
    )
    propre = nettoyer_texte(texte_brut)

    # Les URLs, chiffres isolés, ponctuations et stopwords métier doivent disparaître
    assert "http" not in propre
    assert "2026" not in propre
    assert "relatif" not in propre
    assert "offres" not in propre
    assert "!" not in propre

    # Les mots-clés métier utiles doivent être conservés en minuscules
    assert "serveurs" in propre
    assert "ordinateurs" in propre


def test_ajouter_colonne_texte_propre() -> None:
    """Vérifie la création de `texte_propre` à partir de `objet_brut` et `description_complete`."""
    df = pd.DataFrame(
        [
            {
                "objet_brut": "Travaux de réhabilitation voirie",
                "description_complete": "Réfection chaussée et éclairage public à Agadir.",
            }
        ]
    )
    df_out = ajouter_colonne_texte_propre(df)
    assert "texte_propre" in df_out.columns
    assert "voirie" in df_out.loc[0, "texte_propre"]
    assert "agadir" in df_out.loc[0, "texte_propre"]
