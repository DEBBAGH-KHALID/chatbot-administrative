# "Chatbot Administratif Marocain" #

# Base de données
- PostgreSQL + pgvector (via Docker)
- Table `documents` : ID, contenu, service, categorie, embedding (768 dim), created_at 
- Table `conversations ` : ID, question, reponse, langue, created_at 

# Pipeline de données
PDF -> extraction texte -> structuration JSON -> chunking -> embeddings -> PostgreSQL
├── 📁 data
│   ├── 📁 extracted
│   │   ├── 📄 cin.txt
│   │   └── 📄 passeport.txt
│   ├── 📁 images
│   │   ├── 📁 cin
│   │   │   ├── 🖼️ page_3_0.jpeg
│   │   │   ├── 🖼️ page_4_0.jpeg
│   │   │   └── 🖼️ page_6_0.jpeg
│   │   └── 📁 passeport
│   ├── 📁 processed
│   │   └── ⚙️ chunks_db.json
│   ├── 📁 raw
│   │   ├── 📁 cin
│   │   │   └── 📕 CNIE.pdf
│   │   └── 📁 passeport
│   │       └── 📕 passeport.pdf
│   └── 📁 structured
│       ├── ⚙️ cin.json
│       └── ⚙️ passeport.json


# Pipeline RAG complet
Question -> détection langue -> recherche vectorielle -> filtrage par seuil -> génération LLM -> réponse + sources

# API
- `GET /health` : vérification du serveur
- `POST /chat/` : poser une question, reçoit réponse + sources + langue détectée
- `GET /chat/historique` : consulter les dernières conversations

# Comment lancer le projet #
## lancer docker compose : docker-compose up -d
## la base de donnee : psql -U admin -d chatbot_admin -f sql/init.sql
## creation di fichier .env dans backend contient les infos : 
- DB_HOST
- DB_PORT
- DB_NAME
- DB_USER
- DB_PASSWORD
- DATABASE_URL=postgresql://DB_USER:DB_PASSWORD@DB_HOST:DB_PORT/DB_NAME
- GEMINI_API_KEY= ******************

1. `Préparation des données`
2. `Placer les PDF dans `data/raw/`.`
3. `Extraire le texte `: python backend/scripts/extract_pdf.py
4. `Structurer les données` : python backend/scripts/structure_data.py
5. `Créer les chunks` : python backend/scripts/chunk_data.py
6. `Initialiser la base vectorielle` : python backend/scripts/chunk_and_embed.py
7. `lancer app `: uvicorn backend.main:app --reload