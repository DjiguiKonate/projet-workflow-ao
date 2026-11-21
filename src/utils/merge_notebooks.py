"""Script utilitaire pour fusionner les notebooks du Binôme 1 et du Binôme 2 sans conflit Git."""

from pathlib import Path
import nbformat

BASE_DIR = Path(__file__).resolve().parent.parent.parent
NOTEBOOKS_DIR = BASE_DIR / "notebooks"


def fusionner_notebooks(
    part1_path: Path = NOTEBOOKS_DIR / "01_collecte_pretraitement_eda.ipynb",
    part2_path: Path = NOTEBOOKS_DIR / "02_modelisation_matching.ipynb",
    output_path: Path = NOTEBOOKS_DIR / "workflow_data_science.ipynb",
) -> Path:
    """Fusionne les deux notebooks de travail en un seul notebook final.

    Args:
        part1_path: Notebook du Binôme 1 (Sections 1 à 3).
        part2_path: Notebook du Binôme 2 (Sections 4 et 5).
        output_path: Notebook final fusionné pour le rendu.

    Returns:
        Chemin du notebook final généré.
    """
    nb1 = nbformat.read(part1_path, as_version=4)
    nb2 = nbformat.read(part2_path, as_version=4)

    nb_final = nbformat.v4.new_notebook()
    nb_final.metadata = nb1.metadata
    nb_final.cells = nb1.cells + nb2.cells

    output_path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb_final, output_path)
    print(f"Notebook fusionné avec succès : {output_path} ({len(nb_final.cells)} cellules)")
    return output_path


if __name__ == "__main__":
    fusionner_notebooks()
