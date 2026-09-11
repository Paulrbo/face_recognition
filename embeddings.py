"""
╔══════════════════════════════════════════════════════════════════════╗
║                     BLOC 1 — GÉNÉRATION DES EMBEDDINGS              ║
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

from projects import csv_path

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def generer_embeddings(project_id: str, photos_dir: Path) -> int:
    """
    Génère les embeddings pour toutes les photos d'un projet.

    Args:
        project_id : identifiant du projet
        photos_dir : dossier contenant les photos téléchargées

    Returns:
        Nombre d'embeddings générés (après déduplication)
    """

    # ── Modèles ────────────────────────────────────────────────────────────────
    mtcnn = MTCNN(
        image_size=160,
        margin=20,
        min_face_size=40,
        keep_all=True,      # détecte TOUS les visages par photo
        device=DEVICE,
    )
    resnet = InceptionResnetV1(pretrained="vggface2").eval().to(DEVICE)

    # ⚙️  Si tu veux utiliser ton modèle fine-tuné, décommente :
    # resnet.load_state_dict(torch.load("../models/facenet_finetuned.pt", map_location=DEVICE))

    # ── Parcours des photos ────────────────────────────────────────────────────
    photos = list({
        p.resolve() for p in photos_dir.rglob("*")
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    })
    print(f"[BLOC 1] {len(photos)} photos trouvées pour '{project_id}'")

    records = []
    erreurs = []

    for photo_path in photos:
        try:
            img     = cv2.imread(str(photo_path))
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            faces, probs = mtcnn(img_rgb, return_prob=True)
            if faces is None:
                continue

            faces = faces.to(DEVICE)
            with torch.no_grad():
                embeddings = resnet(faces).cpu().numpy()

            for i, (embedding, prob) in enumerate(zip(embeddings, probs)):
                records.append({
                    # Chemin relatif depuis photos_dir (conserve les sous-dossiers)
                    "photo":      str(photo_path.relative_to(photos_dir)),
                    "visage_id":  i,
                    "confiance":  round(float(prob), 4),
                    **{f"e{j}": v for j, v in enumerate(embedding)},
                })

        except Exception as e:
            erreurs.append(str(photo_path.name))

    print(f"[BLOC 1] {len(records)} visages extraits — {len(erreurs)} erreurs")

    if not records:
        raise ValueError("Aucun visage détecté — vérifie le dossier de photos")

    # ── Déduplication + sauvegarde ─────────────────────────────────────────────
    df       = pd.DataFrame(records)
    df_clean = df.drop_duplicates(subset=["photo", "visage_id"])
    df_clean.to_csv(csv_path(project_id), index=False)

    print(f"[BLOC 1] ✅ {len(df_clean)} embeddings sauvegardés → {csv_path(project_id)}")
    return len(df_clean)
