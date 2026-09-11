"""
╔══════════════════════════════════════════════════════════════════════╗
║                     BLOC 1 — GÉNÉRATION DES EMBEDDINGS              ║
║                  (issu de pretraitement_adv.ipynb)                   ║
║                                                                      ║
║  Entrée  : project_id (str), photos_dir (Path)                      ║
║  Sortie  : nombre d'embeddings générés (int)                        ║
║  Produit : models/projets/<project_id>/embeddings.csv               ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import cv2
import numpy as np
import pandas as pd
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from pathlib import Path

from config import settings
from projects import csv_path

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMG_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def generer_embeddings(project_id: str, photos_dir: Path) -> int:
    """
    Génère les embeddings pour toutes les photos d'un projet.
    Adapté depuis pretraitement_adv.ipynb.
    """

    # ── Chargement des modèles ─────────────────────────────────────────────────
    mtcnn = MTCNN(
        image_size=160,
        margin=20,
        min_face_size=40,
        keep_all=True,
        device=DEVICE,
    )
    resnet = InceptionResnetV1(pretrained="vggface2").eval().to(DEVICE)

    # ⚙️  Si tu veux utiliser ton modèle fine-tuné, décommente :
    # resnet.load_state_dict(torch.load("models/facenet_finetuned.pt", map_location=DEVICE))

    # ── Récupère toutes les photos sans doublons ───────────────────────────────
    photos = list({
        p.resolve() for p in photos_dir.rglob("*")
        if p.suffix.lower() in IMG_EXTENSIONS
    })
    print(f"[BLOC 1] {len(photos)} photos trouvées pour le projet '{project_id}'")

    # ── Traitement photo par photo ─────────────────────────────────────────────
    records = []
    erreurs = []

    for photo_path in photos:
        try:
            # Chargement (identique au notebook)
            img = cv2.imread(str(photo_path))
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Détection des visages
            faces, probs = mtcnn(img_rgb, return_prob=True)
            if faces is None:
                continue

            # Extraction des embeddings
            faces = faces.to(DEVICE)
            with torch.no_grad():
                embeddings = resnet(faces).cpu().numpy()

            # Sauvegarde de chaque visage détecté
            for i, (embedding, prob) in enumerate(zip(embeddings, probs)):
                records.append({
                    "photo": photo_path.name,
                    "visage_id": i,
                    "confiance": round(float(prob), 4),
                    **{f"e{j}": v for j, v in enumerate(embedding)},
                })

        except Exception as e:
            erreurs.append({"photo": photo_path.name, "erreur": str(e)})

    print(f"[BLOC 1] {len(records)} visages extraits — {len(erreurs)} erreurs")

    if not records:
        raise ValueError("Aucun visage détecté dans les photos — vérifie le dossier Drive")

    # ── Sauvegarde + déduplication ─────────────────────────────────────────────
    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["photo", "visage_id"])
    df.to_csv(csv_path(project_id), index=False)

    print(f"[BLOC 1] ✅ {len(df)} embeddings sauvegardés")
    return len(df)
