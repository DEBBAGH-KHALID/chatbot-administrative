CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nom_complet VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table des conversations
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    conversation_id VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    reponse TEXT NOT NULL,
    images JSONB DEFAULT '[]'::jsonb,
    langue VARCHAR(10) DEFAULT 'fr',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    titre VARCHAR(255) NOT NULL,
    categorie VARCHAR(100),      
    contenu TEXT NOT NULL,       
    fichier_path VARCHAR(255),       
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
