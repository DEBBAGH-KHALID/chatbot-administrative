import os
import sys
from fastapi import APIRouter
from backend.database import get_connection

# Sécurité pour les chemins d'importation au sein du backend
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from models import QuestionRequest, ReponseResponse
from services.rag_service import repondre_a_question
from services.history_service import sauvegarder_conversation

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ReponseResponse)
def poser_question(request: QuestionRequest):
    # 1. Obtenir le résultat du pipeline RAG complet
    resultat = repondre_a_question(request.question)
    
    # 2. Sauvegarder l'échange dans l'historique
    sauvegarder_conversation(
        question=request.question,
        reponse=resultat["reponse"],
        langue=resultat["langue"]
    )
    
    return ReponseResponse(**resultat)

@router.get("/historique")
def get_historique(limit: int = 20):
    """
     Permet de consulter les derniers échanges formatés proprement.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT question, reponse, langue, created_at 
            FROM conversations 
            ORDER BY created_at DESC 
            LIMIT %s
            """,
            (limit,)
        )
        resultats = cur.fetchall()
        cur.close()
        conn.close()
        
        # Formatage des données pour renvoyer un JSON dictionnaire agréable à lire
        historique_propre = []
        for r in resultats:
            if isinstance(r, dict):
                historique_propre.append(r)
            else:
                historique_propre.append({
                    "question": r[0],
                    "reponse": r[1],
                    "langue": r[2],
                    "created_at": r[3].isoformat() if r[3] else None
                })
        return historique_propre
        
    except Exception as e:
        return {"error": f"Impossible de récupérer l'historique : {e}"}