"""Fichier 1 : Collecte des appels d'offres (Web Scraping).

Notions utilisées (Cours Séance 3 & Séance 4) :
- requests.get() pour télécharger une page web
- BeautifulSoup pour analyser le code HTML
- time.sleep() pour respecter le serveur (bonnes pratiques)
- pandas.DataFrame et to_csv() pour stocker les données
"""

import os
import random
import time

from bs4 import BeautifulSoup
import pandas as pd
import requests


def extraire_annonces_html(html):
    """Extrait les informations des appels d'offres depuis une page HTML."""
    # Créer l'objet BeautifulSoup pour parcourir les balises HTML de la page
    soup = BeautifulSoup(html, "html.parser")
    # Créer une liste vide qui va contenir toutes les annonces trouvées
    annonces = []

    # Parcourir chaque ligne <tr> trouvée dans le tableau des résultats
    for ligne in soup.select("table tbody tr"):
        # Récupérer toutes les cellules <td> de la ligne et enlever les espaces inutiles
        cols = [c.get_text(" ", strip=True) for c in ligne.find_all("td")]
        # Vérifier qu'il y a au moins 7 colonnes pour éviter les lignes vides
        if len(cols) >= 7:
            # Ajouter un dictionnaire structuré avec les champs de l'annonce
            annonces.append(
                {
                    "reference": cols[0],
                    "objet_brut": cols[1],
                    "categorie": cols[2],
                    "acheteur": cols[3],
                    "ville": cols[4],
                    "date_publication": cols[5],
                    "date_limite": cols[6],
                    "estimation_mad": cols[7] if len(cols) > 7 else "",
                    "caution_mad": cols[8] if len(cols) > 8 else "",
                    "description_complete": cols[1],
                }
            )
    # Retourner la liste complète des annonces extraites de cette page
    return annonces


def collecter_appels_offres(max_pages=5, chemin_sortie="data/raw/appels_offres_raw.csv"):
    """Télécharge plusieurs pages du portail et sauvegarde les données brutes en CSV."""
    # Définir l'adresse web du portail des marchés publics
    base_url = "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons"
    # Définir un User-Agent pour se présenter comme un navigateur classique
    headers = {"User-Agent": "Mozilla/5.0"}
    # Créer une liste vide pour accumuler les annonces de toutes les pages
    toutes_annonces = []

    # Boucler sur les numéros de pages de 1 à max_pages
    for page_num in range(1, max_pages + 1):
        # Utiliser try/except pour éviter que le programme plante si le réseau échoue
        try:
            # Envoyer une requête HTTP GET avec un délai maximal de 20 secondes
            reponse = requests.get(f"{base_url}&page_num={page_num}", headers=headers, timeout=20)
            # Vérifier que le serveur a bien répondu (code 200 OK)
            reponse.raise_for_status()
            # Extraire les annonces de la page HTML téléchargée
            annonces_page = extraire_annonces_html(reponse.text)
            # Arrêter la boucle s'il n'y a plus aucune annonce sur la page
            if not annonces_page:
                break
            # Ajouter les annonces de cette page à la liste globale
            toutes_annonces.extend(annonces_page)
            # Afficher la progression dans le terminal
            print(f"Page {page_num} : {len(annonces_page)} annonces récupérées.")
            # Faire une pause aléatoire entre 2 et 5 secondes (bonne pratique du cours)
            time.sleep(random.uniform(2.0, 5.0))
        except Exception as erreur:
            # Afficher le message d'erreur sans bloquer le reste du script
            print(f"Erreur sur la page {page_num} : {erreur}")
            # Sortir de la boucle en cas d'erreur réseau
            break

    # Convertir la liste de dictionnaires en tableau Pandas (DataFrame)
    df = pd.DataFrame(toutes_annonces)
    # Vérifier que le tableau n'est pas vide avant de sauvegarder
    if not df.empty:
        # Créer le dossier parent s'il n'existe pas encore
        os.makedirs(os.path.dirname(chemin_sortie), exist_ok=True)
        # Sauvegarder le DataFrame au format CSV compatible Excel et Pandas
        df.to_csv(chemin_sortie, index=False, encoding="utf-8-sig")
        # Confirmer la sauvegarde à l'utilisateur
        print(f"Fichier brut sauvegardé : {chemin_sortie} ({len(df)} lignes)")
    # Retourner le DataFrame collecté
    return df


if __name__ == "__main__":
    # Lancer la collecte quand on exécute directement python scraper.py
    collecter_appels_offres()
