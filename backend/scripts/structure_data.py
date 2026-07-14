
import re
import json
import os


# Nettoie le texte extrait des PDF
def nettoyer_texte(texte: str) -> str:

    texte = re.sub(r"\n{3,}", "\n\n", texte)
    texte = re.sub(r" {2,}", " ", texte)

    return texte.strip()


# Découpe le texte en différentes sections
def decouper_en_sections(texte: str) -> dict:

    sections = {
        "pieces_requises": "",
        "conditions": "",
        "etapes": "",
        "delais": "",
        "autre": ""
    }

    patterns = {
        "pieces_requises": r"(pièces? (nécessaires|requises?|à fournir))(.*?)(?=(conditions?|étapes?|délai|$))",
        "conditions": r"(conditions?)(.*?)(?=(étapes?|délai|pièces?|$))",
        "etapes": r"(étapes?|procédure)(.*?)(?=(délai|conditions?|pièces?|$))",
        "delais": r"(délai)(.*?)(?=(conditions?|étapes?|pièces?|$))",
    }

    for cle, pattern in patterns.items():

        match = re.search(
            pattern,
            texte,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            sections[cle] = nettoyer_texte(match.group(0))

    return sections


# Récupère toutes les images d'un service
def recuperer_images_service(dossier_images, nom_service):

    images = []

    dossier_service = os.path.join(
        dossier_images,
        nom_service
    )

    if os.path.exists(dossier_service):

        for fichier in sorted(os.listdir(dossier_service)):

            if fichier.lower().endswith(
                (".png", ".jpg", ".jpeg", ".bmp", ".webp")
            ):

                images.append(
                    os.path.join(
                        dossier_service,
                        fichier
                    )
                )

    return images


# Traite un fichier texte
def traiter_fichier(
    chemin_txt,
    nom_service,
    dossier_images
):

    with open(
        chemin_txt,
        "r",
        encoding="utf-8"
    ) as f:

        texte = f.read()

    texte = nettoyer_texte(texte)

    sections = decouper_en_sections(texte)

    images = recuperer_images_service(
        dossier_images,
        nom_service
    )

    return {

        "service": nom_service,

        "sections": sections,

        "texte_brut": texte,

        "images": images

    }


if __name__ == "__main__":

    CHEMIN_SCRIPT = os.path.dirname(
        os.path.abspath(__file__)
    )

    RACINE_PROJET = os.path.abspath(
        os.path.join(
            CHEMIN_SCRIPT,
            "..",
            ".."
        )
    )

    dossier_extracted = os.path.join(
        RACINE_PROJET,
        "data",
        "extracted"
    )

    dossier_structured = os.path.join(
        RACINE_PROJET,
        "data",
        "structured"
    )

    dossier_images = os.path.join(
        RACINE_PROJET,
        "data",
        "images"
    )

    os.makedirs(
        dossier_structured,
        exist_ok=True
    )

    if not os.path.exists(dossier_extracted):

        print(
            f"Dossier introuvable : {dossier_extracted}"
        )

    else:

        print(
            f"Lecture des fichiers depuis : {dossier_extracted}"
        )

        for fichier in os.listdir(dossier_extracted):

            if not fichier.endswith(".txt"):
                continue

            nom_service = fichier.replace(
                ".txt",
                ""
            )

            chemin = os.path.join(
                dossier_extracted,
                fichier
            )

            resultat = traiter_fichier(
                chemin,
                nom_service,
                dossier_images
            )

            chemin_sortie = os.path.join(
                dossier_structured,
                f"{nom_service}.json"
            )

            with open(
                chemin_sortie,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    resultat,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            print(
                f"Structuration terminée : {chemin_sortie}"
            )

