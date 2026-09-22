"""BLOC 2 — DÉTECTION / RECHERCHE (issu de detection_adv.ipynb)"""

import numpy as np
import pandas as pd
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image

from config import settings
from projects import csv_path, photos_dir

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_mtcnn  = MTCNN(image_size=160, margin=20, min_face_size=40, device=DEVICE)
_resnet = InceptionResnetV1(pretrained="vggface2").eval().to(DEVICE)
print(f"[BLOC 2] Modèles prêts sur {DEVICE}")

_cache: dict[str, tuple[torch.Tensor, pd.DataFrame]] = {}


def _load_embeddings(project_id: str) -> tuple[torch.Tensor, pd.DataFrame]:
    if project_id not in _cache:
        path = csv_path(project_id)
        if not path.exists():
            raise FileNotFoundError(f"CSV introuvable pour '{project_id}'")
        df        = pd.read_csv(path)
        meta_cols = ["photo", "visage_id", "confiance"]
        if "url" in df.columns:
            meta_cols.append("url")
        meta          = df[meta_cols].reset_index(drop=True)
        emb_cols      = [c for c in df.columns if c.startswith("e")]
        embeddings_db = torch.tensor(df[emb_cols].values, dtype=torch.float32).to(DEVICE)
        _cache[project_id] = (embeddings_db, meta)
        print(f"[BLOC 2] {len(df)} embeddings chargés pour '{project_id}'")
    return _cache[project_id]


def _get_photo_url(project_id: str, filename: str, csv_url: str = "") -> str:
    if csv_url:
        return csv_url  # URL externe (Pixieset, Drive...)
    return f"/projects/{project_id}/photos/{filename}"  # fallback local


def rechercher(img: Image.Image, project_id: str, seuil: float = settings.SEUIL_DEFAULT) -> list[dict] | None:
    img_rgb = np.array(img)

    face = _mtcnn(img_rgb)
    if face is None:
        return None

    if face.dim() == 4:
        face = face[0].unsqueeze(0)
    else:
        face = face.unsqueeze(0)

    with torch.no_grad():
        emb_ref = _resnet(face.to(DEVICE))

    embeddings_db, meta = _load_embeddings(project_id)
    cos_sim   = torch.nn.functional.cosine_similarity(emb_ref, embeddings_db)
    distances = 1 - cos_sim

    matches_idx = (distances < seuil).nonzero(as_tuple=False).squeeze(1)
    if len(matches_idx) == 0:
        return []

    resultats             = meta.iloc[matches_idx.cpu().numpy()].copy()
    resultats["distance"] = distances[matches_idx].cpu().numpy()
    resultats             = resultats.sort_values("distance").reset_index(drop=True)

    cols = ["photo", "distance"]
    if "url" in resultats.columns:
        cols.append("url")

    photos_uniques = (
        resultats.drop_duplicates("photo")
        .sort_values("distance")[cols]
        .to_dict(orient="records")
    )

    for p in photos_uniques:
        csv_url = p.pop("url", "")
        p["url"] = _get_photo_url(project_id, p["photo"], csv_url)

    print(f"[BLOC 2] {len(photos_uniques)} photos trouvées")
    return photos_uniques


def invalider_cache(project_id: str):
    _cache.pop(project_id, None)
