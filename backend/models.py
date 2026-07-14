from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str

class ReponseResponse(BaseModel):
    reponse: str
    sources: list[str] = []
    langue: str  # Ajouté pour indiquer la langue détectée au client (fr, ar, darija)