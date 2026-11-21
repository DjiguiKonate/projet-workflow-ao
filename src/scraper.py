"""Étape 1 (Binôme 1) : Collecte des appels d'offres depuis marchespublics.gov.ma.

Utilise Playwright (navigation) + BeautifulSoup (extraction HTML vue en cours)
et enregistre le résultat brut dans data/raw/appels_offres_raw.csv.
"""

from pathlib import Path
import random
import sys
import time

from bs4 import BeautifulSoup
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import RAW_DATA_PATH, TARGET_URL_MARCHES


def extraire_annonces_html(html: str) -> list[dict]:
    """Extrait les champs principaux d'une page HTML avec BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    annonces = []

    for ligne in soup.select("table tbody tr, div.avis-item"):
        cols = [c.get_text(" ", strip=True) for c in ligne.find_all("td")]
        if len(cols) >= 7:
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
    return annonces


def collecter_appels_offres(max_items: int = 200) -> pd.DataFrame:
    """Collecte jusqu'à `max_items` annonces et les sauvegarde en CSV pour Pandas."""
    from playwright.sync_api import sync_playwright

    toutes_annonces = []
    url = f"{TARGET_URL_MARCHES}/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=45000)

            while len(toutes_annonces) < max_items:
                batch = extraire_annonces_html(page.content())
                if not batch:
                    break
                toutes_annonces.extend(batch)
                print(f"Annonces collectées : {len(toutes_annonces)}")

                # Pause de courtoisie (2 à 5 s) pour respecter le serveur
                time.sleep(random.uniform(2.0, 5.0))

                suivant = page.locator("a.next, button.next, a[title*='Suivant']")
                if suivant.count() == 0:
                    break
                suivant.first.click()
                page.wait_for_load_state("networkidle", timeout=20000)

            browser.close()
    except Exception as err:
        print(f"Erreur lors du scraping : {err}")

    df = pd.DataFrame(toutes_annonces[:max_items])
    if not df.empty:
        RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(RAW_DATA_PATH, index=False, encoding="utf-8-sig")
        print(f"Sauvegardé ({len(df)} lignes) -> {RAW_DATA_PATH}")
    return df


if __name__ == "__main__":
    collecter_appels_offres(max_items=200)
