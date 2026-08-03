import os
import sys
import re
from langdetect import detect, DetectorFactory

# Sécurité pour les imports
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

DetectorFactory.seed = 0  # Garantit des résultats reproductibles

# Mots fréquents en Darija écrite en caractères latins (Arabizi)
MOTS_DARIJA_LATIN = [
    "wach", "bghit", "3afak", "chno", "kifach", "fin", "wa9t",
    "mennin", "kayn", "makaynch", "bzaf", "daba", "chokran", "chhal", "db", "ngad", "ngaduh"
]

def contient_caracteres_arabes(texte: str) -> bool:
    """Vérifie si le texte contient de l'alphabet arabe."""
    return bool(re.search(r'[\u0600-\u06FF]', texte))

def detecter_langue(texte: str) -> str:
    texte_lower = texte.lower()
    
    # 1. Si le texte contient des lettres arabes -> Darija (en écriture arabe)
    if contient_caracteres_arabes(texte):
        return "darija"

    # 2. Si le texte contient des mots-clés en Darija latine (Arabizi)
    if any(mot in texte_lower for mot in MOTS_DARIJA_LATIN):
        return "darija"
        
    # 3. Détection pour le Français (ou fallback)
    try:
        langue_detectee = detect(texte)
        if langue_detectee == "fr":
            return "fr"
    except Exception:
        return "fr"
        
    return "fr"