# Projet Workflow Data Science — Analyse & Matching B2B des Appels d'Offres

Ce dépôt est structuré pour permettre aux **deux binômes de travailler en parallèle** sans conflits et de fusionner leurs travaux en une seule commande à la fin.

## Organisation du travail en parallèle

| Rôle | Modules Python | Notebook de travail | Branche Git |
| :--- | :--- | :--- | :--- |
| **Binôme 1** (Collecte, Nettoyage, EDA) | `src/scraper/`, `src/preprocessing/`, `src/eda/`, `tests/test_tabular_cleaner.py`, `tests/test_text_cleaner.py` | `notebooks/01_collecte_pretraitement_eda.ipynb` | `feature/collecte-eda` |
| **Binôme 2** (ML, Matching B2B, Évaluation) | `src/models/`, `src/matching/`, `tests/test_pipelines.py`, `tests/test_recommender.py` | `notebooks/02_modelisation_matching.ipynb` | `feature/modelisation-matching` |
| **Commun** | `config/settings.py`, `src/utils/` | `notebooks/workflow_data_science.ipynb` (généré) | `main` |

## Contrat d'interface entre Binôme 1 et Binôme 2

Le point de jonction unique est le fichier `data/processed/appels_offres_clean.csv`.
Pour vérifier qu'il respecte toutes les colonnes et règles de typage :
```bash
python src/utils/validate_contract.py
```

## Fusion finale des Notebooks (Jour 4)

Pour éviter les conflits Git sur les fichiers `.ipynb`, chacun travaille sur son propre notebook (`01_...` et `02_...`). À la fin, exécuter :
```bash
python src/utils/merge_notebooks.py
```
Cela génère `notebooks/workflow_data_science.ipynb` prêt pour le `Restart & Run All` et le rendu.
