"""Configuration partagée du projet Workflow Data Science (Binôme 1 & Binôme 2)."""

from pathlib import Path

# Répertoire racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Chemins des données
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PDF_SOURCES_DIR = RAW_DATA_DIR / "pdf_sources"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CATALOGUES_CLIENTS_DIR = DATA_DIR / "catalogues_clients"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"

RAW_DATA_PATH = RAW_DATA_DIR / "appels_offres_raw.csv"
CLEAN_DATA_PATH = PROCESSED_DATA_DIR / "appels_offres_clean.csv"
VALIDATION_MATCHING_PATH = GROUND_TRUTH_DIR / "validation_matching.csv"

# Chemins des sorties (graphiques, modèles, notebooks)
FIGURES_DIR = BASE_DIR / "reports" / "figures"
MODELS_DIR = BASE_DIR / "models"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

# Reproductibilité (imposé pour Scikit-learn)
RANDOM_STATE = 42

# Cibles de collecte
TARGET_URL_MARCHES = "https://www.marchespublics.gov.ma"
MIN_ANNONCES = 150
MAX_ANNONCES = 300
REQUEST_DELAY_MIN = 2.0
REQUEST_DELAY_MAX = 5.0

# Catégories officielles attendues dans le contrat de données
CATEGORIES_VALIDES = ["Fournitures", "Services", "Travaux"]

# Stopwords métier administratifs à retirer en plus des stopwords français NLTK
STOPWORDS_METIER = [
    "relatif",
    "relative",
    "relatifs",
    "relatives",
    "objet",
    "appel",
    "offres",
    "offre",
    "marche",
    "marché",
    "lot",
    "unique",
    "portant",
    "travaux",
    "fourniture",
    "fournitures",
    "services",
    "prestation",
    "prestations",
    "mad",
    "dhs",
    "dh",
]

# Colonnes obligatoires du contrat d'interface (appels_offres_clean.csv)
COLONNES_CONTRAT = [
    "hash_ao",
    "reference",
    "acheteur",
    "ville",
    "categorie",
    "date_publication",
    "date_limite",
    "delai_reponse_jours",
    "estimation_mad",
    "caution_mad",
    "estimation_manquante",
    "objet_brut",
    "texte_propre",
]
