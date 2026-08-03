import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from backend.main import app
except Exception as e:

    print(f"Erreur lors de l'importation de backend.main: {e}")
    raise e