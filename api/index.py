import sys
import os

# Ajouter la racine et le dossier backend au path Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app