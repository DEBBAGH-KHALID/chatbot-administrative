import os

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

# Imports des routeurs
from backend.routers import chat, auth

app = FastAPI(title="Chatbot Administratif Marocain")

# Configuration CORS globale
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#  CAPTURE D'ERREUR POUR DEBUGGING
@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    error_trace = traceback.format_exc()
    print("CRASH SERVEUR :", error_trace)  # S'affichera instantanément dans Vercel Logs
    return JSONResponse(
        status_code=500,
        content={
            "error_type": type(exc).__name__,
            "message": str(exc),
            "traceback": error_trace.splitlines()[-3:]  # Les 3 dernières lignes du crash
        },
        headers={"Access-Control-Allow-Origin": "*"}

# Intercepteur d'erreurs globales : Force le renvoi des headers CORS même en cas de crash
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erreur serveur interne : {str(exc)}"},
        headers={"Access-Control-Allow-Origin": "*"}
    )

# Fast-path pour les requêtes de vérification OPTIONS (CORS preflight)
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return JSONResponse(
        content="OK",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Gestion du dossier des images
images_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "images")
if os.path.exists(images_dir):
    app.mount("/images", StaticFiles(directory=images_dir), name="images")

app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API Chatbot fonctionnelle !"}

@app.get("/health")
def health_check():
    return {"status": "ok"}