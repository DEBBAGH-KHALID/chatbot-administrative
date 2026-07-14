
from google import genai
from google.genai import types
from dotenv import load_dotenv


# Initialisation du client natif Gemini
client = genai.Client()
MODEL_NAME = "gemini-2.5-flash"

# Dictionnaire de prompts systèmes selon la langue détectée
PROMPTS_PAR_LANGUE = {
    "fr": """Tu es un assistant administratif marocain. Réponds en FRANÇAIS UNIQUEMENT.
Règles importantes :
- Réponds UNIQUEMENT à partir des informations fournies dans le contexte ci-dessous.
- Si l'information n'est pas dans le contexte, dis-le clairement et invite à contacter l'administration compétente.
- Ne jamais inventer de pièces, tarifs, délais ou conditions.
- Sois clair, structuré (utilise des listes à puces si nécessaire) et concis.""",

    "ar": """أنت مساعد إداري مغربي. أجب باللغة العربية فقط.
قواعد مهمة:
- أجب فقط بناءً على المعلومات المتوفرة في السياق أسفله.
- إذا لم تكن المعلومة متوفرة، وضّح ذلك بصراحة وانصح بالتواصل مع الإدارة المعنية.
- لا تخترع أي وثائق أو شروط أو آجال غير موجودة في السياق.
- كن واضحًا ومنظمًا ومختصرًا.""",

    "darija": """Nta assistant idari maghribi. Jaweb b darija b horouf latine (Arabizi) (kifma katb l'utilisateur).
Qwanine mouhima:
- Jaweb ghir b les infos li kaynin f context li lteht.
- Ila l'information machi mawjouda, goul had chi b sarraha o goul l'utilisateur ychouf l'idara lma3eniya.
- Ma tkhtare3ch des documents wla des délais wla des conditions wla des tarifs li machi f context.
- Kon wadeh omekhetasser."""
}

def generer_reponse(question: str, contexte: str, langue: str = "fr") -> str:
    """
    Génère une réponse avec Gemini 2.5 Flash en injectant le prompt système
    adapté à la langue détectée.
    """
    try:
        # Récupération du prompt correspondant ou repli sur le français
        system_instruction = PROMPTS_PAR_LANGUE.get(langue, PROMPTS_PAR_LANGUE["fr"])
        
        # Construction du message utilisateur contenant le contexte et la question
        prompt_utilisateur = f"Contexte :\n{contexte}\n\nQuestion : {question}\nRéponse :"
        
        # Appel à Gemini avec la config système dédiée à la langue
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt_utilisateur,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2  # Reste bas pour éviter les hallucinations
            )
        )
       
        return response.text
    except Exception as e:
        print(f" ERREUR DANS LLM_SERVICE : {e}")
        return "Désolé, une erreur technique est survenue lors de la génération de la réponse.عذرًا، حدث خطأ تقني أثناء إنشاء الإجابة"