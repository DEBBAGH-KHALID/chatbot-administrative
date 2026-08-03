from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str
    conversation_id: str | None = None  # None = nouvelle conversation
    langue: str | None = "fr"
class TexteAudioRequest(BaseModel):
    """
    Modèle de requête pour convertir un texte en audio (TTS).
    """
    texte: str
    langue: str 

class ReponseResponse(BaseModel):
    reponse: str
    sources: list[str] = []
    langue: str  # Ajouté pour indiquer la langue détectée au client (fr, ar, darija)
    images: list[str] = []  # Ajouté pour inclure les images pertinentes
    conversation_id: str | None = None  # 👈 AJOUTE CETTE LIGNE