"""Fichier 4 : Tests unitaires pour vérifier le bon fonctionnement du nettoyage."""

import numpy as np
import pandas as pd

from nettoyage import nettoyer_dataset, nettoyer_texte, parser_montant


def test_parser_montant():
    """Vérifie la conversion des montants textuels en nombres."""
    # Vérifier qu'un montant formaté avec espaces et virgule est bien converti
    assert parser_montant("125 000,00 DHS") == 125000.0
    # Vérifier qu'une mention textuelle non chiffrée renvoie NaN
    assert np.isnan(parser_montant("Non communiqué"))


def test_nettoyer_texte():
    """Vérifie que les mots vides, URLs et chiffres sont bien supprimés."""
    # Appeler la fonction de nettoyage sur une phrase exemple
    resultat = nettoyer_texte("Appel d'offres relatif à l'achat de serveurs https://ex.ma 2026!")
    # Vérifier que le mot-clé utile est conservé
    assert "serveurs" in resultat
    # Vérifier que le stopword administratif est supprimé
    assert "relatif" not in resultat
    # Vérifier que l'URL et l'année sont supprimées
    assert "http" not in resultat
    assert "2026" not in resultat


def test_nettoyer_dataset():
    """Vérifie la déduplication MD5 et la suppression des délais négatifs."""
    # Créer un petit DataFrame de test avec un doublon et un délai négatif
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
    # Exécuter le nettoyage complet
    df_clean = nettoyer_dataset(df_raw)
    # Vérifier qu'il ne reste qu'une seule ligne valide après déduplication et filtrage
    assert len(df_clean) == 1
    # Vérifier que le délai calculé est bien de 19 jours
    assert df_clean.loc[0, "delai_reponse_jours"] == 19
    # Vérifier que la ville a été normalisée
    assert df_clean.loc[0, "ville"] == "Agadir"
    # Vérifier que le texte nettoyé contient le mot-clé principal
    assert "ordinateurs" in df_clean.loc[0, "texte_propre"]
