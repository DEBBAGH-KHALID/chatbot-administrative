import os
import sys
import uuid
import json
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from google import genai
from google.genai import types

from backend.database import get_connection
from backend.services.llm_service import generer_reponse
from backend.services.language_service import detecter_langue

client = genai.Client()

# Modèle et configuration des Embeddings
EMBEDDING_MODEL = "gemini-embedding-2"
SEUIL_DISTANCE_MAX = 0.38  # Seuil strict pour ne garder que les chunks locaux pertinents

# Messages de repli mis à jour avec les nouveaux services
MESSAGES_ABSENCE_INFO = {
    "fr": "Je suis un assistant spécialisé dans les démarches de la CNIE, du Passeport, du Mariage, du Permis de conduire et de la Carte bancaire.",
    "ar": "أنا مساعد متخصص في المساطر الخاصة بالبطاقة الوطنية، جواز السفر، عقد الزواج، رخصة السياقة، والبطاقة البنكية.",
    "darija": "Ana mou3awin moukhtass f les procédures dial La Carte Nationale (CNIE), Le Passeport, L'Acte de Mariage (Zawaj), Le Permis w La Carte Bancaire."
}


# --- 1. FONCTIONS DE GESTION DE L'HISTORIQUE ---

def recuperer_historique(conversation_id: str, limit: int = 6) -> list[dict]:
    if not conversation_id:
        return []
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT question, reponse 
            FROM conversations 
            WHERE conversation_id = %s 
            ORDER BY created_at ASC 
            LIMIT %s
            """,
            (conversation_id, limit)
        )
        resultats = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in resultats]
    except Exception as e:
        print("ERREUR RECUPERATION HISTORIQUE :", repr(e))
        return []


def sauvegarder_echange(
    conversation_id: str, 
    question: str, 
    reponse: str, 
    user_id: str | None = None, 
    langue: str | None = None,
    images: list | None = None
):
    try:
        images_liste = images if images is not None else []
        conn = get_connection()
        cur = conn.cursor()
        images_json = json.dumps(images_liste)

        cur.execute(
            """
            INSERT INTO conversations (conversation_id, user_id, question, reponse, images)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (conversation_id, user_id, question, reponse, images_json)
        )
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print("ERREUR SAUVEGARDE HISTORIQUE :", repr(e))


# --- 2. FONCTIONS DE RECHERCHE LOCALE (BDD) ---

def embed_texte_query(texte: str) -> list[float]:
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texte,
        config=types.EmbedContentConfig(
            output_dimensionality=768,
            task_type="RETRIEVAL_QUERY"
        )
    )
    vecteur = np.array(response.embeddings[0].values)
    norme = np.linalg.norm(vecteur)
    if norme > 0:
        vecteur = vecteur / norme
    return vecteur.tolist()


def rechercher_chunks_pertinents(question: str, top_k: int = 4) -> list[dict]:
    try:
        vecteur_question = embed_texte_query(question)
        vecteur_string = f"[{','.join(map(str, vecteur_question))}]"

        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(
            """
            SELECT contenu,
                   service,
                   categorie,
                   embedding <=> %s::vector AS distance
            FROM documents
            ORDER BY distance
            LIMIT %s
            """,
            (vecteur_string, top_k)
        )

        resultats = cur.fetchall()
        cur.close()
        conn.close()

        if not resultats:
            return []

        chunks_pertinents = []
        for r in resultats:
            chunks_pertinents.append({
                "contenu": r["contenu"],
                "service": r["service"],
                "categorie": r["categorie"],
                "distance": float(r["distance"])
            })

        return chunks_pertinents

    except Exception as e:
        print("ERREUR RECHERCHE CHUNKS :", repr(e))
        return []


def rechercher_images_pertinentes(service: str, categorie: str = None) -> list[dict]:
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if categorie:
            cur.execute(
                "SELECT fichier, service, description FROM images WHERE service = %s AND categorie = %s",
                (service, categorie)
            )
        else:
            cur.execute(
                "SELECT fichier, service, description FROM images WHERE service = %s",
                (service,)
            )

        resultats = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in resultats]
    except Exception as e:
        print("ERREUR RECHERCHE IMAGES :", repr(e))
        return []


# --- 3. FONCTION PRINCIPALE RAG ---

def repondre_a_question(
    question: str, 
    conversation_id: str | None = None, 
    langue: str | None = None, 
    user_id: str | None = None
) -> dict:
    
    conversation_id = conversation_id or str(uuid.uuid4())
    langue_finale = langue or detecter_langue(question) or "fr"

    # 1. Historique de discussion
    historique_db = recuperer_historique(conversation_id)
    fil_conversation = ""
    for h in historique_db:
        fil_conversation += f"Utilisateur : {h['question']}\nAssistant : {h['reponse']}\n\n"

    # 2. Recherche BDD locale (PGVector)
    chunks = rechercher_chunks_pertinents(question, top_k=4)
    chunks_filtres = [c for c in chunks if c["distance"] < SEUIL_DISTANCE_MAX]

    contexte = "\n\n".join([c["contenu"] for c in chunks_filtres]) if chunks_filtres else ""

    # 3. Récupération des images intelligente (Sans images parasites)
    images_trouvees = []
    q_lower = question.lower()

    # Mots-clés indiquant une VRAIE demande ou besoin visuel
    mots_cles_demande_image = [
        "image", "exemple", "photo", "kifach", "voir", "specimen", 
        "شكل", "صورة", "نموذج", "وريني", "شوف", "فرجينا"
    ]
    demande_visuelle = any(m in q_lower for m in mots_cles_demande_image)

    # Détection explicite du service ciblé par l'utilisateur
    service_explicite = None
    if any(m in q_lower for m in ["mariage", "zawaj", "zowaj", "الزواج", "عقد الزواج", "3doul", "l3odoul"]):
        service_explicite = "mariage"
    elif any(p in q_lower for p in ["permis", "permi", "narsa", "siga", "رخصة السياقة", "البيرمي"]):
        service_explicite = "permis"
    elif any(b in q_lower for b in ["carte bancaire", "banque", "bank", "guichet", "rib", "البطاقة البنكية", "البنك"]):
        service_explicite = "carte_bancaire"
    elif any(p in q_lower for p in ["passeport", "passport", "جواز السفر", "الباسبور"]):
        service_explicite = "passeport"
    elif any(c in q_lower for c in ["carte nationale", "cnie", "cin", "lakart", "البطاقة الوطنية"]):
        service_explicite = "cin"

    services_a_chercher = set()

    # Si le service est explicite, on cherche uniquement les images de CE service
    if service_explicite:
        services_a_chercher.add(service_explicite)
    elif demande_visuelle:
        # Seulement s'il y a une demande visuelle ET pas de service explicite, on parcourt les chunks BDD
        for chunk in chunks_filtres:
            if chunk.get("service"):
                services_a_chercher.add(chunk.get("service"))

    # Filtrage par catégorie
    categorie_cible = None
    if any(p in q_lower for p in ["photo", "photographie", "visage", "صورة"]):
        categorie_cible = "photo_identite"
    elif any(c in q_lower for c in ["carte", "kifach", "exemple", "specimen", "شكل"]):
        categorie_cible = "specimen_carte"

    # Récupération effective des images
    # RÈGLE : On n'affiche d'image que si la demande est visuelle OU si la catégorie/service l'exige
    if demande_visuelle or service_explicite in ["cin", "passeport"]:
        for srv in services_a_chercher:
            if categorie_cible:
                imgs = rechercher_images_pertinentes(service=srv, categorie=categorie_cible)
                if not imgs:
                    imgs = rechercher_images_pertinentes(service=srv)
            else:
                imgs = rechercher_images_pertinentes(service=srv)

            for img in imgs:
                url_image = f"http://localhost:8000/images/{img['fichier']}"
                if url_image not in images_trouvees:
                    images_trouvees.append(url_image)

    # 4. Génération de la réponse via Gemini
    reponse = generer_reponse(
        question=question, 
        contexte=contexte, 
        langue=langue_finale,
        historique=fil_conversation
    )

    # 5. Sauvegarde et retour du payload
    sauvegarder_echange(
        conversation_id=conversation_id, 
        question=question, 
        reponse=reponse, 
        user_id=user_id, 
        langue=langue_finale,
        images=images_trouvees
    )

    return {
        "reponse": reponse, 
        "sources": [], 
        "langue": langue_finale, 
        "images": images_trouvees, 
        "conversation_id": conversation_id
    }
# --- 4. TRAITEMENT AUDIO MULTIMODAL (AVEC FALLBACK MULTI-MODÈLES) ---

import tempfile
from groq import Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcrire_audio_gemini(audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
    try:
        # Création d'un fichier temporaire pour l'audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name

        # Transcription instantanée via Groq Whisper (Gratuit)
        with open(temp_audio_path, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
                file=(temp_audio_path, file.read()),
                model="whisper-large-v3",
                language="ar"  # Ou "fr" / détection automatique
            )

        os.remove(temp_audio_path)
        return transcription.text.strip()

    except Exception as e:
        print("ERREUR TRANSCRIPTION GROQ :", repr(e))
        return ""