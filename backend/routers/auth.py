from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from backend.database import get_connection
from backend.services.auth_service import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    nom_complet: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(user_data: UserRegister):
    conn = get_connection()
    cur = conn.cursor()
    
    # 1. Vérifier si l'utilisateur existe
    cur.execute("SELECT id FROM users WHERE email = %s", (user_data.email,))
    user_existant = cur.fetchone()
    if user_existant:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")
    
    # 2. Insérer le nouvel utilisateur
    hashed_pwd = hash_password(user_data.password)
    cur.execute(
        "INSERT INTO users (email, hashed_password, nom_complet) VALUES (%s, %s, %s) RETURNING id",
        (user_data.email, hashed_pwd, user_data.nom_complet)
    )
    row = cur.fetchone()
    
    # Gestion souple Tuple vs Dictionnaire
    new_id = row["id"] if isinstance(row, dict) else row[0]
    
    conn.commit()
    cur.close()
    conn.close()
    
    token = create_access_token({"sub": str(new_id)})
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": {"id": str(new_id), "email": user_data.email, "nom_complet": user_data.nom_complet}
    }

@router.post("/login")
def login(credentials: UserLogin):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, hashed_password, nom_complet FROM users WHERE email = %s", (credentials.email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect.")
    
    # Récupération selon le type du curseur
    user_id = row["id"] if isinstance(row, dict) else row[0]
    hashed_pwd = row["hashed_password"] if isinstance(row, dict) else row[1]
    nom_complet = row["nom_complet"] if isinstance(row, dict) else row[2]

    if not verify_password(credentials.password, hashed_pwd):
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect.")
    
    token = create_access_token({"sub": str(user_id)})
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": {"id": str(user_id), "email": credentials.email, "nom_complet": nom_complet}
    }

@router.get("/me")
def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user