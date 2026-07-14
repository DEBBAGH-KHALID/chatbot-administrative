CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    contenu TEXT NOT NULL,
    service VARCHAR(50) NOT NULL,
    categorie VARCHAR(50),
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    question TEXT,
    reponse TEXT,
    langue VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);
