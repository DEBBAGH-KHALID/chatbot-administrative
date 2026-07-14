
from google import genai
from google.genai import types

from backend.database import get_connection
from backend.services.llm_service import generer_reponse
from backend.services.language_service import detecter_langue


client = genai.Client()
EMBEDDING_MODEL = "gemini-embedding-2"

# Seuil pour la distance cosinus (<=>) (C'est un seuil de pertinence.)
SEUIL_DISTANCE_MAX = 0.55

#Centralisation des réponses par défaut
MESSAGES_ABSENCE_INFO = {
    "fr": "Je ne dispose pas d'information fiable sur ce sujet. Merci de contacter l'administration compétente.",
    "ar": "لا أتوفر على معلومات موثوقة حول هذا الموضوع. يرجى التواصل مع الإدارة المعنية.",
    "darija": "Ma 3andich l'information sahiha 3la had sujet. 3afak tawasel m3a l'idara lma3niya."
}

def rechercher_chunks_pertinents(question: str, top_k: int = 6) -> list[dict]:
 try:
    # 1. Génération de l'embedding
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )

    vecteur_question = response.embeddings[0].values
    vecteur_string = f"[{','.join(map(str, vecteur_question))}]"

    # 2. Connexion PostgreSQL
    conn = get_connection()
    cur = conn.cursor()
    
    # Recherche vectorielle
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

def repondre_a_question(question: str) -> dict:
    # Détection de la langue en premier
    langue = detecter_langue(question)
    
    chunks = rechercher_chunks_pertinents(question, top_k=6)
    
    # Cas 1 : La BDD n'a rien renvoyé
    if not chunks:
        return {"reponse": MESSAGES_ABSENCE_INFO[langue], "sources": [], "langue": langue}

    # Filtrage selon le seuil cosinus
    chunks_filtreres = [c for c in chunks if c["distance"] < SEUIL_DISTANCE_MAX]
    
    # Cas 2 : Les morceaux trouvés sont hors-sujet
    if not chunks_filtreres:
        return {"reponse": MESSAGES_ABSENCE_INFO[langue], "sources": [], "langue": langue}

    # Cas 3 : Tout est bon -> Génération multilingue avec Gemini
    contexte = "\n\n".join([c["contenu"] for c in chunks_filtreres])
    
    reponse = generer_reponse(question, contexte, langue)
    
    sources = list(set([f"{c['service']} - {c['categorie']}" for c in chunks_filtreres]))

    return {"reponse": reponse, "sources": sources, "langue": langue}