import os
import time
from google import genai
from google.genai import types
from backend.prompts import PROMPTS_PAR_LANGUE

# Initialisation du client (récupère automatiquement GEMINI_API_KEY depuis le .env)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Liste des modèles à essayer dans l'ordre de priorité
MODELS_TO_TRY = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-3.5-flash"
]

def generer_reponse(question: str, contexte: str, langue: str = "fr", historique: str = "") -> str:
    # 1. Récupération des consignes système selon la langue sélectionnée
    system_instruction = PROMPTS_PAR_LANGUE.get(langue, PROMPTS_PAR_LANGUE["fr"])

    # 2. Construction du prompt utilisateur (séparé du système)
    user_prompt = f"""HISTORIQUE DE LA CONVERSATION :
{historique if historique else "(Début de discussion)"}

CONTEXTE EXTRAIT DES DOCUMENTS OFFICIELS :
{contexte if contexte else "L'utilisateur demande des informations administratives ou un visuel."}

QUESTION DE L'UTILISATEUR :
{question}"""

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.2
    )

    # 3. Boucle de génération avec fallback
    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=config
            )

            if response.text and response.text.strip():
                return response.text.strip()

        except Exception as e:
            error_msg = repr(e)
            print(f"Échec du modèle {model_name} : {error_msg[:120]}...")
            
            
            # on fait une petite pause de 1 seconde puis on passe au modèle suivant.
            if "429" in error_msg or "503" in error_msg:
                time.sleep(1)
                continue
            else:
                continue

    # 4. Message de secours si tous les quotas/modèles ont échoué en même temps
    return "L'assistant est très sollicité actuellement. Veuillez patienter une vingtaine de secondes avant de poser votre prochaine question."