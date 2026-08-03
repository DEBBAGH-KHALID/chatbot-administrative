import os
from dotenv import load_dotenv

# 1. Charger le fichier .env immédiatement (vu qu'on lance depuis la racine, il cherche dans backend/.env)
backend_path = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(backend_path, ".env"))
from fastapi import FastAPI
from backend.routers import chat, auth
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Chatbot Administratif Marocain")
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En développement, autorise toutes les origines (ex: http://localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],  # Autorise POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)
app.mount("/images", StaticFiles(directory="data/images"), name="images")
app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}