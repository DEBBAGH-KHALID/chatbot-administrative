import os
import sys
from langdetect import detect, DetectorFactory

# Sécurité pour les imports
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

DetectorFactory.seed = 0  # Garantit des résultats reproductibles

# Mots fréquents en darija écrite en caractères latins 
MOTS_DARIJA = [
    "wach", "bghit", "3afak", "chno", "kifach", "fin", "wa9t",
    "mennin", "kayn", "makaynch", "bzaf", "daba", "chokran", "chhal", "db"
]

def detecter_langue(texte: str) -> str:
    texte_lower = texte.lower()
    
  
    # Si le texte contient au moins un des mots-clés typiques du dialecte marocain
    if any(mot in texte_lower for mot in MOTS_DARIJA):
        return "darija"
        
    # 2. Détection classique pour l'arabe (lettres arabes) ou le français
    try:
        langue_detectee = detect(texte)
    except Exception:
        return "fr"  # Fallback par défaut si le texte est vide ou indétectable
        
    if langue_detectee == "ar":
        return "ar"
    elif langue_detectee == "fr":
        return "fr"
    else:
        return "fr"  # Fallback pour le reste (ex: anglais détecté par erreur)