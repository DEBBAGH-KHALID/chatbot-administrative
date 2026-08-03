import os
from dotenv import load_dotenv
from google import genai

# Charger les variables du fichier .env (qui se trouve à la racine ou dans backend)
load_dotenv()

# Si la clé est sous le nom GEMINI_API_KEY ou GOOGLE_API_KEY
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    # Tu peux aussi coller ta clé directement entre guillemets ici pour tester rapidement :
    # api_key = "AIzaSy..."
    print("❌ Erreur : Aucune clé API trouvée. Vérifie ton fichier .env !")
    exit(1)

# Initialisation du nouveau client Google GenAI
client = genai.Client(api_key=api_key)

print("--- Modèles disponibles sur votre clé API ---")
try:
    for model in client.models.list():
        # Afficher les modèles supportant la génération de contenu
        print(f"- {model.name}")
except Exception as e:
    print(f"❌ Erreur lors de la récupération des modèles : {e}")