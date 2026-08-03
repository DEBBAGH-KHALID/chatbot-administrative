import os

# Gestion sécurisée de dotenv
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

# Configuration CORS
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

# Gestion des fichiers statiques (Images)
images_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "images")
if os.path.exists(images_dir):
    app.mount("/images", StaticFiles(directory=images_dir), name="images")

# Inclusions des routeurs
app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API Chatbot fonctionnelle !"}

@app.get("/health")
def health_check():
    return {"status": "ok"}