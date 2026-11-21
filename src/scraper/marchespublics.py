"""Collecteur d'appels d'offres et bons de commande sur marchespublics.gov.ma.

Combine BeautifulSoup (vu en Séance 4 du cours) pour l'analyse HTML et Playwright
pour le rendu dynamique des pages du portail des marchés publics.
"""

from pathlib import Path
import sys
from typing import Any

from bs4 import BeautifulSoup
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import (
    RAW_DATA_PATH,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    TARGET_URL_MARCHES,
)
from src.scraper.base_scraper import BaseScraper


class MarchesPublicsScraper(BaseScraper):
    """Collecteur spécialisé pour le portail marocain des marchés publics."""

    def __init__(
        self,
        base_url: str = TARGET_URL_MARCHES,
        delay_min: float = REQUEST_DELAY_MIN,
        delay_max: float = REQUEST_DELAY_MAX,
    ) -> None:
        """Initialise le collecteur avec l'URL officielle et les délais de courtoisie."""
        super().__init__(base_url=base_url, delay_min=delay_min, delay_max=delay_max)

    def parse_listing_html(self, html: str) -> list[dict[str, Any]]:
        """Extrait les champs structurés depuis le code HTML d'une page de résultats.

        Args:
            html: Code HTML de la page listant les appels d'offres.

        Returns:
            Liste de dictionnaires représentant chaque annonce extraite.
        """
        soup = BeautifulSoup(html, "html.parser")
        annonces: list[dict[str, Any]] = []

        # Parcours des lignes/blocs d'annonces du tableau de résultats
        lignes = soup.select("table tbody tr, div.avis-item")
        for bloc in lignes:
            try:
                reference = self._extract_text(bloc, [".ref", "td:nth-of-type(1)"])
                objet_brut = self._extract_text(bloc, [".objet", "td:nth-of-type(2)"])
                categorie = self._extract_text(bloc, [".categorie", "td:nth-of-type(3)"])
                acheteur = self._extract_text(bloc, [".acheteur", "td:nth-of-type(4)"])
                ville = self._extract_text(bloc, [".ville", "td:nth-of-type(5)"])
                date_publication = self._extract_text(bloc, [".date-pub", "td:nth-of-type(6)"])
                date_limite = self._extract_text(bloc, [".date-limite", "td:nth-of-type(7)"])
                estimation_mad = self._extract_text(bloc, [".estimation", "td:nth-of-type(8)"])
                caution_mad = self._extract_text(bloc, [".caution", "td:nth-of-type(9)"])
                description_complete = self._extract_text(bloc, [".description", ".details"])

                if reference or objet_brut:
                    annonces.append(
                        {
                            "reference": reference,
                            "objet_brut": objet_brut,
                            "categorie": categorie,
                            "acheteur": acheteur,
                            "ville": ville,
                            "date_publication": date_publication,
                            "date_limite": date_limite,
                            "estimation_mad": estimation_mad,
                            "caution_mad": caution_mad,
                            "description_complete": description_complete or objet_brut,
                        }
                    )
            except Exception as err:
                self.logger.warning("Erreur de parsing sur un bloc d'annonce : %s", err)

        return annonces

    @staticmethod
    def _extract_text(bloc: Any, selectors: list[str]) -> str:
        """Retourne le premier texte non vide trouvé parmi une liste de sélecteurs CSS."""
        for sel in selectors:
            element = bloc.select_one(sel)
            if element:
                return element.get_text(" ", strip=True)
        return ""

    def collect(self, max_items: int = 200) -> pd.DataFrame:
        """Collecte jusqu'à `max_items` annonces via Playwright puis sauvegarde en CSV.

        Args:
            max_items: Nombre cible d'annonces à collecter (150 à 300 recommandé).

        Returns:
            DataFrame Pandas des annonces brutes collectées.
        """
        toutes_annonces: list[dict[str, Any]] = []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.logger.error("Playwright n'est pas installé. Exécutez `playwright install chromium`.")
            return pd.DataFrame()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                search_url = f"{self.base_url}/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons"
                self.logger.info("Ouverture du portail : %s", search_url)
                page.goto(search_url, timeout=45000)

                page_num = 1
                while len(toutes_annonces) < max_items:
                    self.logger.info("Extraction de la page %d...", page_num)
                    html = page.content()
                    batch = self.parse_listing_html(html)
                    if not batch:
                        self.logger.info("Aucune nouvelle annonce trouvée sur la page %d.", page_num)
                        break

                    toutes_annonces.extend(batch)
                    self.pause_courtoisie()

                    # Passage à la page suivante si le bouton existe
                    next_btn = page.locator("a.next, button.next, a[title*='Suivant']")
                    if next_btn.count() == 0:
                        break
                    next_btn.first.click()
                    page.wait_for_load_state("networkidle", timeout=20000)
                    page_num += 1

                browser.close()
        except Exception as err:
            self.logger.error("Erreur lors du scraping Playwright : %s", err)

        df = pd.DataFrame(toutes_annonces[:max_items])
        if not df.empty:
            self.save_raw(df, RAW_DATA_PATH)
        return df

    def save_raw(self, df: pd.DataFrame, output_path: Path = RAW_DATA_PATH) -> Path:
        """Sauvegarde immédiate des données brutes au format CSV UTF-8-SIG pour Pandas/Excel.

        Args:
            df: DataFrame brut à sauvegarder.
            output_path: Chemin de destination.

        Returns:
            Chemin du fichier sauvegardé.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        self.logger.info("Données brutes sauvegardées (%d lignes) -> %s", len(df), output_path)
        return output_path
