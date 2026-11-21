"""Module d'extraction de texte depuis les pièces jointes PDF (Avis / CPS).

Utilise PyMuPDF (fitz) pour extraire rapidement le texte natif des documents PDF,
avec une détection des pages scannées (moins de 50 caractères extractibles).
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Path, min_chars_per_page: int = 50) -> str:
    """Extrait le texte brut d'un fichier PDF avec PyMuPDF.

    Si une page contient moins de `min_chars_per_page` caractères, elle est
    signalée dans les logs comme potentiellement scannée (nécessitant un OCR).

    Args:
        pdf_path: Chemin local vers le fichier PDF à lire.
        min_chars_per_page: Seuil minimal de caractères pour considérer une page
            comme contenant du texte natif exploitable.

    Returns:
        Texte complet extrait du PDF, ou chaîne vide en cas d'erreur.
    """
    if not pdf_path.exists():
        logger.warning("Fichier PDF introuvable : %s", pdf_path)
        return ""

    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF (fitz) n'est pas installé dans l'environnement.")
        return ""

    pages_texte: list[str] = []

    try:
        # Ouverture sécurisée du document PDF
        with fitz.open(pdf_path) as document:
            logger.info("Lecture du PDF %s (%d pages)", pdf_path.name, len(document))
            for num_page, page in enumerate(document, start=1):
                texte_page = page.get_text("text").strip()
                if len(texte_page) < min_chars_per_page:
                    logger.info(
                        "Page %d/%d de %s contient peu de texte (%d car.) : document possiblement scanné.",
                        num_page,
                        len(document),
                        pdf_path.name,
                        len(texte_page),
                    )
                if texte_page:
                    pages_texte.append(texte_page)
    except Exception as err:
        logger.error("Erreur lors de la lecture du PDF %s : %s", pdf_path, err)
        return ""

    return "\n".join(pages_texte)


def download_and_extract_pdf(
    pdf_url: str,
    dest_dir: Path,
    filename: Optional[str] = None,
) -> str:
    """Télécharge un PDF depuis une URL puis en extrait le texte.

    Args:
        pdf_url: Lien direct vers le document PDF.
        dest_dir: Dossier local où enregistrer la copie du PDF.
        filename: Nom de fichier souhaité (facultatif).

    Returns:
        Texte extrait du PDF, ou chaîne vide si le téléchargement échoue.
    """
    import requests

    dest_dir.mkdir(parents=True, exist_ok=True)
    nom_fichier = filename or pdf_url.split("/")[-1] or "document.pdf"
    if not nom_fichier.lower().endswith(".pdf"):
        nom_fichier += ".pdf"
    chemin_local = dest_dir / nom_fichier

    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        chemin_local.write_bytes(response.content)
        logger.info("PDF téléchargé : %s", chemin_local)
        return extract_text_from_pdf(chemin_local)
    except Exception as err:
        logger.warning("Impossible de télécharger le PDF %s : %s", pdf_url, err)
        return ""
