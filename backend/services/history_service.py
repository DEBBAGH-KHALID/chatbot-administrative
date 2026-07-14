import os
import sys
from backend.database import get_connection

# Sécurité pour les imports
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

def sauvegarder_conversation(question: str, reponse: str, langue: str):
 
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO conversations (question, reponse, langue)
            VALUES (%s, %s, %s)
            """,
            (question, reponse, langue)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(" Échange sauvegardé avec succès dans l'historique.")
    except Exception as e:
        print(f"erreur SAUVEGARDE historique : {e}")