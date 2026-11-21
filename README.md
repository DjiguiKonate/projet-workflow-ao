# Projet Workflow Data Science (Binôme 1)

Structure simple basée uniquement sur les notions vues en cours :

- `source/` :
  - `scraper.py` : collecte des annonces avec `requests`, `BeautifulSoup` et `pandas`
  - `nettoyage.py` : nettoyage tabulaire et textuel avec `pandas`, `numpy` et `re`
  - `visualisation.py` : statistiques `pandas` et graphiques `matplotlib` / `seaborn`
- `tests/` :
  - `test_binome1.py` : tests unitaires (`pytest`)
- `notebook/` :
  - `01_collecte_pretraitement_eda.ipynb` : notebook Jupyter appelant les 3 scripts
- `requirements.txt` : bibliothèques du cours à installer avec `pip install -r requirements.txt`
