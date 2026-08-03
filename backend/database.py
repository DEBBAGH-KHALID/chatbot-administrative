import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

# Recherche le fichier .env dans le dossier backend/
CURRENT_DIR = Path(__file__).resolve().parent  # Dossier backend/
ENV_PATH = CURRENT_DIR / ".env"

# Charge explicitement backend/.env
load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    # Sécurité pour diagnostiquer immédiatement si le .env n'est pas lu
    if not DATABASE_URL:
        raise ValueError(
            f"Erreur : Impossible de lire DATABASE_URL.\n"
            f"Vérifie que le fichier .env existe bien à l'emplacement : {ENV_PATH}"
        )
    
    return psycopg2.connect(DATABASE_URL)

def test_connection():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print("Connexion réussie :", version)
        cur.close()
        conn.close()
    except Exception as e:
        print("Erreur de connexion :", e)

if __name__ == "__main__":
    test_connection()
