"""
Script de génération d'embeddings depuis une galerie Pixieset publique.
Traite les photos en mémoire (sans les stocker sur disque).

Usage :
    conda activate off_recognition
    cd scripts
    python pixieset_embeddings.py

Produit : ../models/projets/dust-festival/embeddings.csv
"""

import io
import json
import time
import requests
import numpy as np
import pandas as pd
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from pathlib import Path
from PIL import Image

# ── Config ────────────────────────────────────────────────────────────────────
CUK       = "dustfestival"
CID       = "121586079"
PAGE_SIZE = 50                    # nb de photos par page (max Pixieset)
OUTPUT    = Path("../backend/models/projets/dust-festival/embeddings.csv")
DEVICE    = "cuda" if torch.cuda.is_available() else "cpu"

GALLERIES = [
    "thursdayatjfkoninckx",
    "fridayatjfkoninckx",
    "fridaycolorsatmariusbrst",
    "fridaybwatmariusbrst",
    "fridayatschottografie",
    "fridayatpitproduction",
    "fridayatpixelselements",
    "fridayatclemdeub",
    "fridayatludovicdonckerwolke",
    "fridayatantoinesedran",
    "saturdayatjfkoninckx",
    "saturdaycolorsatmariusbrst",
    "saturdaybwatmariusbrst",
    "saturdayatschottografie",
    "saturdayatclemdeub",
    "saturdayatpitproduction",
    "saturdayatmartintissot",
    "fridayatnaoph",
    "analogatmariusbrst",
    "saturdayatmdlms800",
]

# ── Modèles ───────────────────────────────────────────────────────────────────
print(f"Device : {DEVICE}")
mtcnn  = MTCNN(image_size=160, margin=20, min_face_size=40, keep_all=True, device=DEVICE)
resnet = InceptionResnetV1(pretrained="vggface2").eval().to(DEVICE)
print("✅ Modèles chargés")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://intocollective.pixieset.com/dustfestival/",
    "X-Requested-With": "XMLHttpRequest",
})


def fetch_gallery_urls(gallery_slug: str) -> list[dict]:
    """Récupère toutes les photos d'une galerie Pixieset via son API."""
    photos = []
    page   = 1

    while True:
        url = (
            f"https://intocollective.pixieset.com/client/loadphotos/"
            f"?cuk={CUK}&cid={CID}&gs={gallery_slug}&page={page}&size={PAGE_SIZE}"
        )
        resp = session.get(url, timeout=15)
        data = resp.json()

        if data["status"] != "success":
            break

        items = json.loads(data["content"])
        for item in items:
            photos.append({
                "name":        item["name"],
                "url_medium":  "https:" + item["pathMedium"],
                "url_large":   "https:" + item["pathLarge"],
                "gallery":     gallery_slug,
            })

        if data["isLastPage"]:
            break

        page += 1
        time.sleep(0.3)  # politesse

    return photos


def process_photo(photo: dict) -> list[dict]:
    """Télécharge une photo en mémoire, détecte les visages, retourne les embeddings."""
    try:
        resp = session.get(photo["url_medium"], timeout=15)
        img  = Image.open(io.BytesIO(resp.content)).convert("RGB")
        img_np = np.array(img)

        faces, probs = mtcnn(img_np, return_prob=True)
        if faces is None:
            return []

        faces = faces.to(DEVICE)
        with torch.no_grad():
            embeddings = resnet(faces).cpu().numpy()

        records = []
        for i, (embedding, prob) in enumerate(zip(embeddings, probs)):
            if prob < 0.90:
                continue
            records.append({
                "photo":      photo["name"],
                "url":        photo["url_large"],   # URL affichage dans la galerie web
                "gallery":    photo["gallery"],
                "visage_id":  i,
                "confiance":  round(float(prob), 4),
                **{f"e{j}": v for j, v in enumerate(embedding)},
            })
        return records

    except Exception as e:
        print(f"  ⚠️  Erreur sur {photo['name']} : {e}")
        return []


# ── Pipeline principal ────────────────────────────────────────────────────────
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

all_records = []
total_photos = 0

for gallery in GALLERIES:
    print(f"\n📁 Galerie : {gallery}")
    photos = fetch_gallery_urls(gallery)
    print(f"   {len(photos)} photos trouvées")
    total_photos += len(photos)

    for i, photo in enumerate(photos, 1):
        records = process_photo(photo)
        all_records.extend(records)
        if i % 10 == 0:
            print(f"   {i}/{len(photos)} traitées — {len(all_records)} visages extraits")

    time.sleep(1)  # pause entre galeries

print(f"\n✅ {total_photos} photos traitées — {len(all_records)} visages extraits")

# Déduplication + sauvegarde
df = pd.DataFrame(all_records)
df = df.drop_duplicates(subset=["photo", "visage_id"])
df.to_csv(OUTPUT, index=False)

print(f"💾 CSV sauvegardé : {OUTPUT}")
print(f"📊 Shape : {df.shape}")
