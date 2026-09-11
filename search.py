"""
╔══════════════════════════════════════════════════════════════════════╗
║                     BLOC 2 — DÉTECTION / RECHERCHE                  ║
║                  (issu de detection_adv.ipynb)                       ║
║                                                                      ║
║  Entrée  : image PIL, project_id, seuil                             ║
║  Sortie  : liste de photos matchées avec leurs URLs                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import pandas as pd
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from pathlib import Path
from PIL import Image

from config import settings
from projects import csv_path, photos_dir, PROJECT_DIR

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ── Modèles chargés une seule fois au démarrage ───────────────────────────────
_mtcnn  = MTCNN(image_size=160, margin=20, min_face_size=40, device=DEVICE)
_resnet = InceptionResnetV1(pretrained="vggface2").eval().to(DEVICE)

# ⚙️  Si tu veux utiliser ton modèle fine-tuné, décommente :
# _resnet.load_state_dict(torch.load("models/facenet_finetuned.pt", map_location=DEVICE))

print(f"[BLOC 2] Modèles prêts sur {DEVICE}")

# ── Cache des embeddings par projet ───────────────────────────────────────────
_cache: dict[str, tuple[torch.Tensor, pd.DataFrame]] = {}


def _load_embeddings(project_id: str) -> tuple[torch.Tensor, pd.DataFrame]:
    """Charge et met en cache les embeddings d'un projet."""
    if project_id not in _cache:
        path = csv_path(project_id)
        if not path.exists():
            raise FileNotFoundError(f"CSV introuvable pour le projet '{project_id}'")

        df            = pd.read_csv(path)
        meta          = df[["photo", "visage_id", "confiance"]].reset_index(drop=True)
        emb_cols      = [c for c in df.columns if c.startswith("e")]
        embeddings_db = torch.tensor(df[emb_cols].values, dtype=torch.float32).to(DEVICE)

        _cache[project_id] = (embeddings_db, meta)
        print(f"[BLOC 2] {len(df)} embeddings chargés pour '{project_id}'")

    return _cache[project_id]


def _get_photo_url(project_id: str, filename: str) -> str:
    """
    Retourne l'URL d'une photo.
    DEV  → URL locale via le serveur de fichiers statiques FastAPI.
    PROD → URL Google Drive (à brancher plus tard).
    """
    if settings.DEV_MODE:
        for f in photos_dir(project_id).rglob(filename):
            rel = f.relative_to(PROJECT_DIR)
            return f"http://localhost:8000/photos/{rel.as_posix()}"
        return ""
    # TODO : retourner l'URL Google Drive en prod
    return ""


def rechercher(
    img: Image.Image,
    project_id: str,
    seuil: float = settings.SEUIL_DEFAULT,
) -> list[dict] | None:
    """
    Recherche les photos d'un projet où apparaît le visage du selfie.
    Adapté depuis trouver_photos() de detection_adv.ipynb.

    Returns:
        None  → aucun visage détecté dans le selfie
        []    → aucune correspondance (augmente le seuil)
        [...] → liste de photos matchées avec URLs
    """
    # PIL → numpy RGB (équivalent du cv2.cvtColor du notebook)
    img_rgb = np.array(img)

    # Détection du visage dans le selfie
    face = _mtcnn(img_rgb)
    if face is None:
        return None

    # Si plusieurs visages, prendre le plus grand (index 0)
    if face.dim() == 4:
        face = face[0].unsqueeze(0)
    else:
        face = face.unsqueeze(0)

    # Embedding du selfie
    with torch.no_grad():
        emb_ref = _resnet(face.to(DEVICE))  # shape (1, 512)

    # Comparaison cosine avec tous les embeddings du projet
    embeddings_db, meta = _load_embeddings(project_id)
    cos_sim   = torch.nn.functional.cosine_similarity(emb_ref, embeddings_db)
    distances = 1 - cos_sim

    matches_idx = (distances < seuil).nonzero(as_tuple=False).squeeze(1)
    if len(matches_idx) == 0:
        return []

    resultats             = meta.iloc[matches_idx.cpu().numpy()].copy()
    resultats["distance"] = distances[matches_idx].cpu().numpy()
    resultats             = resultats.sort_values("distance").reset_index(drop=True)

    # Une ligne par photo (meilleur match) + URL
    photos_uniques = (
        resultats.drop_duplicates("photo")
        .sort_values("distance")[["photo", "distance"]]
        .to_dict(orient="records")
    )
    for p in photos_uniques:
        p["url"] = _get_photo_url(project_id, p["photo"])

    print(f"[BLOC 2] {len(photos_uniques)} photos trouvées ({len(matches_idx)} visages matchés)")
    return photos_uniques


def invalider_cache(project_id: str):
    """Vide le cache d'un projet (à appeler après regénération des embeddings)."""
    _cache.pop(project_id, None)
