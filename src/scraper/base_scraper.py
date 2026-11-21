"""Module de base pour la collecte de données web (Scraping).

Fournit une interface abstraite et des utilitaires communs :
- Journalisation horodatée (logging)
- Pauses de courtoisie aléatoires (rate limiting de 2 à 5 secondes)
- Gestion défensive des erreurs réseau et mécanisme de réessai (retry)
"""

from abc import ABC, abstractmethod
import logging
import random
import time
from typing import Optional

import pandas as pd
import requests

# Configuration du logger pour tracer chaque étape de la collecte
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class BaseScraper(ABC):
    """Classe abstraite définissant le contrat de tout collecteur d'appels d'offres."""

    def __init__(
        self,
        base_url: str,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        max_retries: int = 3,
    ) -> None:
        """Initialise le collecteur avec ses paramètres de courtoisie et de résilience.

        Args:
            base_url: URL racine du portail cible.
            delay_min: Temps d'attente minimum (en secondes) entre deux requêtes.
            delay_max: Temps d'attente maximum (en secondes) entre deux requêtes.
            max_retries: Nombre maximal de tentatives en cas d'erreur réseau.
        """
        self.base_url = base_url
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.max_retries = max_retries
        self.logger = logging.getLogger(self.__class__.__name__)

        # En-têtes HTTP standards pour simuler un navigateur classique (bonnes pratiques du cours)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9",
        }

    def pause_courtoisie(self) -> None:
        """Observe une pause aléatoire entre delay_min et delay_max secondes.

        Permet de respecter la charge du serveur cible (rate limiting).
        """
        duree = random.uniform(self.delay_min, self.delay_max)
        self.logger.debug("Pause de courtoisie : %.2f secondes", duree)
        time.sleep(duree)

    def fetch_html(self, url: str, timeout: int = 20) -> Optional[str]:
        """Télécharge le contenu HTML d'une page avec gestion des erreurs et réessais.

        Args:
            url: Adresse web complète de la page à récupérer.
            timeout: Délai d'expiration de la requête en secondes.

        Returns:
            Le code HTML brut sous forme de chaîne, ou None en cas d'échec définitif.
        """
        for tentative in range(1, self.max_retries + 1):
            try:
                self.logger.info("Requête HTTP (%d/%d) : %s", tentative, self.max_retries, url)
                response = requests.get(url, headers=self.headers, timeout=timeout)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or "utf-8"
                return response.text
            except requests.RequestException as err:
                self.logger.warning(
                    "Échec de la tentative %d/%d pour %s : %s",
                    tentative,
                    self.max_retries,
                    url,
                    err,
                )
                if tentative < self.max_retries:
                    self.pause_courtoisie()

        self.logger.error("Abandon après %d tentatives pour %s", self.max_retries, url)
        return None

    @abstractmethod
    def collect(self, max_items: int = 200) -> pd.DataFrame:
        """Collecte les annonces et retourne un DataFrame Pandas structuré.

        Args:
            max_items: Nombre maximal d'annonces à collecter.

        Returns:
            DataFrame contenant les données brutes collectées.
        """
