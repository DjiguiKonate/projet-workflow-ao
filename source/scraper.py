"""Fichier 1 : Collecte des appels d'offres (Web Scraping).

Notions utilisées (Cours Séance 3 & Séance 4) :
- requests.Session() pour conserver la session et paginer via formulaire POST
- BeautifulSoup pour analyser le code HTML
- re (expressions régulières) pour extraire chaque champ d'une annonce
- time.sleep() pour respecter le serveur (bonnes pratiques)
- pandas.DataFrame et to_csv() pour stocker les données
"""

import os
import random
import re
import time

from bs4 import BeautifulSoup
import pandas as pd
import requests


def extraire_champ(texte, motif):
    """Extrait un texte entre deux repères grâce à une expression régulière."""
    # Chercher le motif dans le texte (sans tenir compte des majuscules/retours à la ligne)
    match = re.search(motif, texte, flags=re.IGNORECASE | re.DOTALL)
    # Retourner le texte capturé sans espaces inutiles, ou une chaîne vide si absent
    return match.group(1).strip(" |:") if match else ""


def extraire_etat_formulaire(html):
    """Récupère tous les champs <input> et <select> nécessaires au formulaire PRADO."""
    # Analyser la page HTML avec BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    # Créer un dictionnaire pour stocker les champs du formulaire
    donnees = {}
    # Parcourir tous les champs <input> cachés ou texte
    for champ in soup.find_all("input"):
        nom = champ.get("name")
        if nom and champ.get("type") in ("hidden", "text", None):
            donnees[nom] = champ.get("value", "")
    # Retourner le dictionnaire des champs du formulaire
    return donnees


def extraire_annonces_html(html):
    """Extrait les informations des appels d'offres depuis les blocs <div> de la page."""
    # Créer l'objet BeautifulSoup pour parcourir les balises HTML de la page
    soup = BeautifulSoup(html, "html.parser")
    # Créer une liste vide qui va contenir toutes les annonces trouvées
    annonces = []
    # Créer un ensemble pour éviter de lire deux fois la même référence sur une page
    refs_vues = set()

    # Parcourir tous les blocs <div> de la page
    for bloc in soup.find_all("div"):
        # Remplacer les retours à la ligne / espaces multiples par un seul espace
        texte = re.sub(r"\s+", " ", bloc.get_text(" | ", strip=True))
        # Vérifier que ce bloc contient bien une annonce complète
        if "Référence :" not in texte or "Objet :" not in texte or "Acheteur public :" not in texte:
            continue
        # Ignorer les grands conteneurs qui englobent plusieurs annonces
        if len(texte) > 2000 or texte.count("Référence :") > 1:
            continue

        # Extraire la référence officielle de l'appel d'offres
        reference = extraire_champ(texte, r"Référence\s*:\s*\|\s*([^|]+)")
        # Ignorer le bloc si la référence est vide ou déjà extraite
        if not reference or reference in refs_vues:
            continue
        # Mémoriser cette référence pour ne pas la dupliquer
        refs_vues.add(reference)

        # Extraire l'objet détaillé de l'annonce
        objet_brut = extraire_champ(texte, r"Objet\s*:\s*\|\s*(.+?)\s*\|\s*(?:Détail|Acheteur public)")
        # Extraire le nom de l'organisme acheteur
        acheteur = extraire_champ(texte, r"Acheteur public\s*:\s*\|\s*([^|]+)")
        # Extraire l'estimation budgétaire TTC en DH si elle est affichée
        estimation_mad = extraire_champ(texte, r"Estimation[^:]*:\s*\|\s*([0-9\s,\.]+)")
        # Extraire la caution provisoire en DH si elle est affichée
        caution_mad = extraire_champ(texte, r"Caution provisoire[^:]*:\s*\|\s*([0-9\s,\.]+)")
        # Extraire la ville / lieu d'exécution si présent, sinon "Maroc"
        ville = extraire_champ(texte, r"Lieu d'exécution\s*:\s*\|\s*([^|]+)") or "Maroc"

        # Définir la date de publication du jour et extraire ou estimer la date limite
        date_publication = pd.Timestamp.today().strftime("%Y-%m-%d")
        date_limite = extraire_champ(texte, r"(\d{2}/\d{2}/\d{4})")
        if not date_limite:
            date_limite = (pd.Timestamp.today() + pd.Timedelta(days=21)).strftime("%Y-%m-%d")

        # Ajouter l'annonce structurée dans la liste
        annonces.append(
            {
                "reference": reference,
                "objet_brut": objet_brut,
                "categorie": objet_brut,
                "acheteur": acheteur,
                "ville": ville,
                "date_publication": date_publication,
                "date_limite": date_limite,
                "estimation_mad": estimation_mad,
                "caution_mad": caution_mad,
                "description_complete": objet_brut,
            }
        )

    # Retourner la liste complète des annonces extraites de cette page
    return annonces


def collecter_appels_offres(max_pages=5, chemin_sortie="data/raw/appels_offres_raw.csv"):
    """Télécharge plusieurs pages (50 résultats/page) et sauvegarde en CSV."""
    # Définir l'URL des consultations en cours du portail des marchés publics
    url = "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&EnCours&searchAnnCons"
    # Ouvrir une session HTTP pour conserver les cookies de navigation
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    # Créer une liste vide pour accumuler les annonces de toutes les pages
    toutes_annonces = []

    try:
        # 1. Charger la page initiale en GET
        reponse = session.get(url, timeout=20)
        reponse.raise_for_status()
        # Passer l'affichage à 50 résultats par page via un envoi POST
        donnees = extraire_etat_formulaire(reponse.text)
        donnees["PRADO_POSTBACK_TARGET"] = "ctl0$CONTENU_PAGE$resultSearch$listePageSizeTop"
        donnees["ctl0$CONTENU_PAGE$resultSearch$listePageSizeTop"] = "50"
        donnees["ctl0$CONTENU_PAGE$resultSearch$listePageSizeBottom"] = "50"
        reponse = session.post(url, data=donnees, timeout=20)
        reponse.raise_for_status()

        # 2. Parcourir les pages de 1 à max_pages
        for page_num in range(1, max_pages + 1):
            # Extraire les annonces de la page courante
            annonces_page = extraire_annonces_html(reponse.text)
            if not annonces_page:
                break
            # Ajouter les annonces à la liste globale
            toutes_annonces.extend(annonces_page)
            print(f"Page {page_num} : {len(annonces_page)} annonces récupérées.")
            # Arrêter si on a atteint le nombre de pages demandé
            if page_num == max_pages:
                break
            # Pause de courtoisie (2 à 5 s) pour respecter le serveur
            time.sleep(random.uniform(2.0, 5.0))
            # Préparer le POST pour passer à la page suivante via numPageTop
            donnees = extraire_etat_formulaire(reponse.text)
            donnees["PRADO_POSTBACK_TARGET"] = "ctl0$CONTENU_PAGE$resultSearch$numPageTop"
            donnees["ctl0$CONTENU_PAGE$resultSearch$listePageSizeTop"] = "50"
            donnees["ctl0$CONTENU_PAGE$resultSearch$listePageSizeBottom"] = "50"
            donnees["ctl0$CONTENU_PAGE$resultSearch$numPageTop"] = str(page_num + 1)
            donnees["ctl0$CONTENU_PAGE$resultSearch$numPageBottom"] = str(page_num + 1)
            reponse = session.post(url, data=donnees, timeout=20)
            reponse.raise_for_status()
    except Exception as erreur:
        # Afficher le message d'erreur sans bloquer le reste du script
        print(f"Erreur lors de la collecte : {erreur}")

    # Convertir la liste de dictionnaires en tableau Pandas (DataFrame)
    df = pd.DataFrame(toutes_annonces)
    # Sauvegarder le fichier brut s'il contient des données
    if not df.empty:
        os.makedirs(os.path.dirname(chemin_sortie), exist_ok=True)
        df.to_csv(chemin_sortie, index=False, encoding="utf-8-sig")
        print(f"Fichier brut sauvegardé : {chemin_sortie} ({len(df)} lignes)")
    # Retourner le DataFrame collecté
    return df


if __name__ == "__main__":
    # Lancer la collecte (5 pages x ~45-50 annonces = ~200+ annonces)
    collecter_appels_offres()
