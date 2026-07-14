import os
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Découpe tous les fichiers JSON en petits morceaux
def decouper_tous_les_json(dossier_structured, dossier_processed):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["\n\n", "\n", "•", " ", ""]
    )

    all_chunks = []

    for fichier in os.listdir(dossier_structured):
        if not fichier.endswith(".json"):
            continue

        chemin_json = os.path.join(dossier_structured, fichier)

        with open(chemin_json, "r", encoding="utf-8") as f:
            donnees = json.load(f)

        service = donnees["service"]
        texte = donnees.get("texte_brut", "")
        
        # Si ton JSON a des sections, ou si tu veux définir une catégorie par défaut
        categorie = donnees.get("categorie", "Général")

        # Récupérer les images si elles existent
        images = donnees.get("images", [])

        # Découpage du texte en morceaux de ~600 caractères
        chunks = splitter.split_text(texte)

        for index, chunk in enumerate(chunks):
            all_chunks.append({
                "service": service,
                "categorie": categorie,  # Ajouté pour correspondre à ta table PostgreSQL
                "chunk_index": index,
                "contenu": chunk.strip(),
                "images": images
            })

        print(f"{service} : {len(chunks)} chunks créés.")

    os.makedirs(dossier_processed, exist_ok=True)

    chemin_sortie = os.path.join(dossier_processed, "chunks_db.json")

    with open(chemin_sortie, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"{len(all_chunks)} chunks enregistrés dans : {chemin_sortie}")


if __name__ == "__main__":
    # Récupération propre des chemins absolus
    CHEMIN_SCRIPT = os.path.dirname(os.path.abspath(__file__))
    
    # Remonte de 2 niveaux pour atteindre la racine du projet
    RACINE_PROJET = os.path.abspath(os.path.join(CHEMIN_SCRIPT, "..", ".."))

    DOSSIER_STRUCTURED = os.path.join(RACINE_PROJET, "data", "structured")
    DOSSIER_PROCESSED = os.path.join(RACINE_PROJET, "data", "processed")

    decouper_tous_les_json(DOSSIER_STRUCTURED, DOSSIER_PROCESSED)