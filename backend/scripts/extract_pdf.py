import os
import fitz
from langchain_community.document_loaders import PyPDFLoader


# Extraire le texte d'un fichier PDF
def extraire_texte_pdf(chemin_pdf: str) -> str:

    loader = PyPDFLoader(chemin_pdf)

    pages = loader.load()

    texte = "\n\n".join(
        page.page_content
        for page in pages
    )

    return texte


# Extraire toutes les images d'un PDF
def extraire_images_pdf(chemin_pdf: str, dossier_images: str):

    doc = fitz.open(chemin_pdf)

    images = []

    for numero_page in range(len(doc)):

        page = doc.load_page(numero_page)

        liste_images = page.get_images(full=True)

        for index, img in enumerate(liste_images):

            xref = img[0]

            image = doc.extract_image(xref)

            image_bytes = image["image"]

            extension = image["ext"]

            nom_image = f"page_{numero_page + 1}_{index}.{extension}"

            chemin_image = os.path.join(
                dossier_images,
                nom_image
            )

            with open(chemin_image, "wb") as fichier:
                fichier.write(image_bytes)

            images.append(chemin_image)

    doc.close()

    return images


# Parcourir tous les services
def traiter_tous_les_pdf(
    dossier_raw,
    dossier_sortie,
    dossier_images
):

    os.makedirs(dossier_sortie, exist_ok=True)
    os.makedirs(dossier_images, exist_ok=True)

    for service in os.listdir(dossier_raw):

        chemin_service = os.path.join(
            dossier_raw,
            service
        )

        if not os.path.isdir(chemin_service):
            continue

        texte_service = ""

        dossier_images_service = os.path.join(
            dossier_images,
            service
        )

        os.makedirs(
            dossier_images_service,
            exist_ok=True
        )

        images_service = []

        for fichier in os.listdir(chemin_service):

            if not fichier.lower().endswith(".pdf"):
                continue

            chemin_pdf = os.path.join(
                chemin_service,
                fichier
            )

            print(f"Lecture : {chemin_pdf}")

            texte = extraire_texte_pdf(
                chemin_pdf
            )

            texte_service += texte + "\n\n"

            images = extraire_images_pdf(
                chemin_pdf,
                dossier_images_service
            )

            images_service.extend(images)

        chemin_txt = os.path.join(
            dossier_sortie,
            f"{service}.txt"
        )

        with open(
            chemin_txt,
            "w",
            encoding="utf-8"
        ) as fichier:

            fichier.write(texte_service)

        print(f"Texte enregistré : {chemin_txt}")

        print(
            f"{len(images_service)} image(s) enregistrée(s) pour le service {service}"
        )


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

    DOSSIER_RAW = os.path.join(
        RACINE_PROJET,
        "data",
        "raw"
    )

    DOSSIER_SORTIE = os.path.join(
        RACINE_PROJET,
        "data",
        "extracted"
    )

    DOSSIER_IMAGES = os.path.join(
        RACINE_PROJET,
        "data",
        "images"
    )

    traiter_tous_les_pdf(
        DOSSIER_RAW,
        DOSSIER_SORTIE,
        DOSSIER_IMAGES
    )