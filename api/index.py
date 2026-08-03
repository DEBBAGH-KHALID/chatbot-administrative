import sys
import os

# Ajouter la racine du projet et le dossier backend au path Python
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Importer l'objet app de backend.main
from backend.main import app

# Exposer 'app' pour le runtime Serverless de Vercel
app = app