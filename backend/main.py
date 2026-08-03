import os
from pathlib import Path

# Chargement sécurisé des variables d'environnement
try:
    from dotenv import load_dotenv
    backend_path = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(dotenv_path=os.path.join(backend_path, ".env"))
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Import des routeurs
from backend.routers import chat, auth

app = FastAPI(title="Chatbot Administratif Marocain")

# Configuration des origines CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestionnaire d'exceptions globales
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erreur serveur : {str(exc)}"},
        headers={"Access-Control-Allow-Origin": "*"}
    )

# 🎯 Gestion des dossiers statiques (Images) avec résolution robuste pour Vercel
BASE_DIR = Path(__file__).resolve().parent.parent
images_dir = BASE_DIR / "data" / "images"

# Secours / Fallback spécifique au répertoire Serverless Vercel si besoin
if not images_dir.exists():
    images_dir = Path("/var/task/data/images")

print(f"--> IMAGES_DIR: {images_dir} (Existe: {images_dir.exists()})")

if images_dir.exists():
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

# Inclusion des routeurs
app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API Chatbot fonctionnelle !"}

@app.get("/health")
def health_check():
    return {"status": "ok"}