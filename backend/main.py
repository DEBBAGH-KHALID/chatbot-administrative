import os

# Gestion sécurisée de dotenv (évite le crash si la lib n'est pas installée)
try:
    from dotenv import load_dotenv
    backend_path = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(dotenv_path=os.path.join(backend_path, ".env"))
except Exception:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Chatbot Administratif Marocain")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestion du dossier StaticFiles
images_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "images")
if os.path.exists(images_dir):
    app.mount("/images", StaticFiles(directory=images_dir), name="images")

# Imports sécurisés des routeurs
try:
    from backend.routers import chat, auth
except ImportError:
    from routers import chat, auth

app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API Chatbot fonctionnelle !"}

@app.get("/health")
def health_check():
    return {"status": "ok"}