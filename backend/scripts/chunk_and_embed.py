import json
import os
import sys
# Déterminer la racine du projet (deux niveaux au-dessus de ce script)
chemin_script = os.path.dirname(os.path.abspath(__file__))
racine_projet = os.path.abspath(os.path.join(chemin_script, "..", ".."))

# Ajouter la racine au système de recherche de Python
if racine_projet not in sys.path:
    sys.path.append(racine_projet)

from google import genai
from google.genai import types
from dotenv import load_dotenv
from backend.database import get_connection

# 1. Charger la clé API Gemini depuis le fichier .env
load_dotenv()

# 2. Initialiser le client Gemini
client = genai.Client()
EMBEDDING_MODEL = "gemini-embedding-2"  # 768 dimensions

def inserer_dans_postgres(all_chunks):
    """Prend la liste des chunks, génère les embeddings avec Gemini et les stocke en BDD"""
    conn = get_connection()
    cur = conn.cursor()
    
    print(f"Début de l'insertion de {len(all_chunks)} chunks...")
    
    for i, chunk in enumerate(all_chunks):
        contenu = chunk["contenu"]
        service = chunk["service"]
        categorie = chunk["categorie"]
        
        try:
            # Appel mis à jour avec la syntaxe exacte du nouveau SDK
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=contenu,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            
            # Extraction propre du vecteur selon la structure de la réponse du SDK
            vecteur = response.embeddings[0].values
            # Insertion dans PostgreSQL (table modifiée en 768 dimensions au Jour 10/11)
            cur.execute(
                """
                INSERT INTO documents (contenu, service, categorie, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (contenu, service, categorie, vecteur)
            )
            
            # Commit régulier ou affichage pour suivre l'avancement
            if (i + 1) % 5 == 0 or (i + 1) == len(all_chunks):
                conn.commit()
                print(f"  {i + 1}/{len(all_chunks)} chunks insérés avec succès.")
                
        except Exception as e:
            print(f"Erreur lors du traitement du chunk {i}: {e}")
            conn.rollback()

    cur.close()
    conn.close()
    print("Félicitations ! Base de données vectorielle initialisée.")

def charger_et_traiter():
    # Déterminer l'emplacement de ce script (backend/scripts)
    chemin_script = os.path.dirname(os.path.abspath(__file__))
    
    # REMONTER DE 2 NIVEAUX pour sortir de 'scripts' et de 'backend'
    racine_projet = os.path.abspath(os.path.join(chemin_script, "..", ".."))
    
    # Pointer directement vers data/chun.json à la racine
    chemin_chunks = os.path.join(racine_projet, "data", "processed", "chunks_db.json")
    
    print(f"Recherche du fichier à l'adresse : {chemin_chunks}")
    
    if not os.path.exists(chemin_chunks):
        print(f"Erreur : Le fichier {chemin_chunks} n'existe pas.")
        return
        
    with open(chemin_chunks, "r", encoding="utf-8") as f:
        all_chunks = json.load(f)
        
    inserer_dans_postgres(all_chunks)

if __name__ == "__main__":
    charger_et_traiter()