import os
import sys
import uuid
import json
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, Response, HTTPException, Depends
from psycopg2.extras import RealDictCursor
from backend.services.auth_service import get_current_user

# Sécurité pour les chemins d'importation au sein du backend
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_path = os.path.dirname(backend_path)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.database import get_connection
from backend.models import QuestionRequest, ReponseResponse
from backend.services.rag_service import (
    repondre_a_question, 
    transcrire_audio_gemini,
    sauvegarder_echange
)

router = APIRouter(prefix="/chat", tags=["chat"])


# 🗺️ MAPPING MULTI-SERVICES POUR LES IMAGES STATIQUES (FR, AR, DARIJA)
SERVICE_IMAGE_MAPPING = {
    "cnie": {
        "keywords": ["cnie", "carte nationale", "بطاقة الوطنية", "يلاكات", "cin", "لاكارت"],
        "folder": "data/images/cin"
    },
    "passeport": {
        "keywords": ["passeport", "جواز السفر", "باسبور"],
        "folder": "data/images/passeport"
    },
    "permis": {
        "keywords": ["permis", "رخصة السياقة", "بيرمي"],
        "folder": "data/images/permis"
    },
    "mariage": {
        "keywords": ["mariage", "acte de mariage", "عقد الزواج", "زواج"],
        "folder": "data/images/marriage"
    },
    "carte_bancaire": {
        "keywords": ["carte bancaire", "banque", "البطاقة البنكية", "كارت بنكير", "الكارت", "بانكير"],
        "folder": "data/images/la carte bancaire"
    }
}


def detecter_images_service(question: str) -> List[str]:
    """
    Scanne le dossier du service correspondant à la question 
    et renvoie la liste des chemins d'images à transmettre au frontend.
    """
    if not question:
        return []

    q_lower = question.lower()
    imgs = []

    for service_key, config in SERVICE_IMAGE_MAPPING.items():
        # Vérification si la question contient l'un des mots-clés du service
        if any(kw in q_lower for kw in config["keywords"]):
            folder_path = os.path.join(root_path, config["folder"])
            
            # Si le dossier existe, récupérer toutes les images qu'il contient
            if os.path.exists(folder_path):
                for fname in os.listdir(folder_path):
                    if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        # Chemin relatif conservé pour le serveur de fichiers statiques
                        rel_path = f"{config['folder']}/{fname}"
                        imgs.append(rel_path)
            break

    return imgs


# --- 1. CHAT TEXTUEL PRINCIPAL (AVEC MÉMOIRE & RAG) ---

@router.post("/", response_model=ReponseResponse)
def poser_question(request: QuestionRequest, current_user: dict = Depends(get_current_user)):
    try:
        resultat = repondre_a_question(
            question=request.question,
            conversation_id=request.conversation_id,
            langue=request.langue or "fr",
            user_id=current_user["id"]
        )
        
        # Récupération des images du RAG ou détection automatique si vides
        images = resultat.get("images", [])
        if not images:
            images = detecter_images_service(request.question)

        # Sécurisation des clés pour la validation Pydantic
        return ReponseResponse(
            reponse=resultat.get("reponse", ""),
            sources=resultat.get("sources", []),
            langue=resultat.get("langue", "fr"),
            images=images,
            conversation_id=resultat.get("conversation_id", request.conversation_id)
        )
        
    except Exception as e:
        print("ERREUR ROUTE /CHAT/ :", repr(e))
        raise HTTPException(status_code=500, detail=f"Erreur serveur lors du traitement : {str(e)}")


# --- 2. ENDPOINT VOCAL SPEECH-TO-SPEECH ---

@router.post("/vocal")
async def chat_vocal(
    audio: UploadFile = File(...), 
    conversation_id: str | None = Form(None),
    langue: str | None = Form("fr"),
    current_user: dict = Depends(get_current_user)
):
    try:
        audio_bytes = await audio.read()
        conversation_id = conversation_id or str(uuid.uuid4())
        mime_type = audio.content_type or "audio/mp3"

        # 1. Transcription de l'audio
        question_texte = transcrire_audio_gemini(audio_bytes, mime_type)
        if not question_texte:
            raise HTTPException(
                status_code=400, 
                detail="Impossible de lire ou transcrire le fichier audio."
            )

        # 2. Exécution du RAG
        resultat = repondre_a_question(
            question=question_texte,
            conversation_id=conversation_id,
            langue=langue or "fr",
            user_id=current_user["id"]
        )

        # Récupération des images du RAG ou détection automatique si vides
        images = resultat.get("images", [])
        if not images:
            images = detecter_images_service(question_texte)

        return {
            "conversation_id": conversation_id,
            "question_transcrite": question_texte,
            "reponse": resultat["reponse"],
            "sources": resultat["sources"],
            "langue": resultat.get("langue", langue),
            "images": images
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement vocal : {str(e)}")


# --- 3. LISTE DES CONVERSATIONS UTILISATEUR (POUR LA SIDEBAR) ---

@router.get("/mes-conversations")
def mes_conversations(current_user: dict = Depends(get_current_user)):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupère tous les échanges de l'utilisateur triés du plus ancien au plus récent
        cur.execute(
            """
            SELECT conversation_id, question, created_at 
            FROM conversations 
            WHERE user_id = %s 
            ORDER BY created_at ASC
            """,
            (current_user["id"],)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # Grouper par conversation_id en retenant la TOUTE PREMIÈRE question comme titre
        historique_dict = {}
        for r in rows:
            c_id = r["conversation_id"] if isinstance(r, dict) else r[0]
            question_text = r["question"] if isinstance(r, dict) else r[1]
            created_at = r["created_at"] if isinstance(r, dict) else r[2]

            if c_id not in historique_dict:
                historique_dict[c_id] = {
                    "conversation_id": c_id,
                    "titre": question_text[:35] + ("..." if len(question_text) > 35 else ""),
                    "created_at": created_at.isoformat() if created_at else None
                }
                
        # Conversion en liste et tri du plus récent au plus ancien
        liste_conversations = list(historique_dict.values())
        liste_conversations.sort(key=lambda x: x["created_at"] or "", reverse=True)
        
        return liste_conversations

    except Exception as e:
        print("ERREUR ROUTE /MES-CONVERSATIONS :", repr(e))
        return []


# --- 4. HISTORIQUE DÉTAILLÉ DE CONVERSATION ---

@router.get("/historique/{conversation_id}")
def get_historique_par_id(conversation_id: str, limit: int = 50, current_user: dict = Depends(get_current_user)):
    return obtenir_historique_db(conversation_id=conversation_id, limit=limit, user_id=current_user["id"])


@router.get("/historique")
def get_historique_global(conversation_id: str = None, limit: int = 50, current_user: dict = Depends(get_current_user)):
    return obtenir_historique_db(conversation_id=conversation_id, limit=limit, user_id=current_user["id"])


def obtenir_historique_db(conversation_id: str = None, limit: int = 50, user_id: str = None):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if conversation_id:
            cur.execute(
                """
                SELECT question, reponse, images, created_at 
                FROM conversations 
                WHERE conversation_id = %s AND user_id = %s
                ORDER BY created_at ASC 
                LIMIT %s
                """,
                (conversation_id, user_id, limit)
            )
        else:
            cur.execute(
                """
                SELECT question, reponse, images, created_at 
                FROM conversations 
                WHERE user_id = %s
                ORDER BY created_at DESC 
                LIMIT %s
                """,
                (user_id, limit)
            )
            
        resultats = cur.fetchall()
        cur.close()
        conn.close()
        
        historique_propre = []
        for r in resultats:
            imgs = r.get("images") if isinstance(r, dict) else r[2]
            if isinstance(imgs, str):
                try:
                    imgs = json.loads(imgs)
                except Exception:
                    imgs = []
            elif not imgs:
                imgs = []

            if isinstance(r, dict):
                historique_propre.append({
                    "question": r["question"],
                    "reponse": r["reponse"],
                    "images": imgs,
                    "created_at": r["created_at"].isoformat() if r.get("created_at") else None
                })
            else:
                historique_propre.append({
                    "question": r[0],
                    "reponse": r[1],
                    "images": imgs,
                    "created_at": r[3].isoformat() if r[3] else None
                })
        return historique_propre
        
    except Exception as e:
        print("ERREUR OBTENTION HISTORIQUE DB :", repr(e))
        return []