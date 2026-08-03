# backend/scripts/insert_images.py
import os
import sys

backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_path = os.path.dirname(backend_path)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from backend.database import get_connection

def inserer_images_en_base(dossier_images: str):
    if not os.path.exists(dossier_images):
        print(f"Erreur : Le dossier '{dossier_images}' n'existe pas.")
        return

    conn = get_connection()
    cur = conn.cursor()
    
    compteur = 0
    for root, dirs, fichiers in os.walk(dossier_images):
        for fichier in fichiers:
            if fichier.lower().endswith((".png", ".jpg", ".jpeg")):
                
                # 📍 1. Calcul du chemin relatif (ex: 'cin/exemple.png' au lieu de 'exemple.png')
                chemin_relatif = os.path.relpath(os.path.join(root, fichier), dossier_images)
                chemin_relatif = chemin_relatif.replace("\\", "/") # Harmonisation pour les URLs Web

                # 📍 2. Extraction intelligente du service (dossier parent OU nom de fichier)
                nom_dossier_parent = os.path.basename(root).lower()
                
                if nom_dossier_parent in ["cin", "cnie", "passeport", "passport"]:
                    service = "cin" if nom_dossier_parent in ["cin", "cnie"] else "passeport"
                elif "_p" in fichier:
                    service = fichier.split("_p")[0].lower()
                else:
                    service = os.path.splitext(fichier)[0].lower()
                
                try:
                    cur.execute(
                        """
                        INSERT INTO images (fichier, service, categorie, description)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (fichier) DO UPDATE 
                        SET service = EXCLUDED.service
                        """,
                        (chemin_relatif, service, "non_categorise", f"Illustration {service}")
                    )
                    compteur += 1
                except Exception as e:
                    print(f"Impossible d'insérer l'image {chemin_relatif} : {e}")
                    conn.rollback()

    conn.commit()
    cur.close()
    conn.close()
    print(f"Importation réussie ! {compteur} images traitées avec leurs sous-dossiers.")

if __name__ == "__main__":
    dossier_script = os.path.dirname(os.path.abspath(__file__))
    racine_projet = os.path.dirname(os.path.dirname(dossier_script))
    chemin_images = os.path.join(racine_projet, "data", "images")
    
    print(f"Recherche récursive des images dans : {chemin_images}")
    inserer_images_en_base(chemin_images)