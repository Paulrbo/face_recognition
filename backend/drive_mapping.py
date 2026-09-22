"""
Génère un mapping {nom_fichier → file_id_drive} en scannant
récursivement un dossier Google Drive public.
Sauvegardé dans models/projets/<project_id>/drive_mapping.json.
"""

import json
import re
from pathlib import Path

from googleapiclient.discovery import build

from config import settings
from projects import PROJECT_DIR


def _extract_folder_id(drive_url: str) -> str:
    """Extrait l'ID du dossier depuis une URL Google Drive."""
    match = re.search(r"/folders/([a-zA-Z0-9_-]+)", drive_url)
    if not match:
        raise ValueError(f"URL Drive invalide : {drive_url}")
    return match.group(1)


def _lister_fichiers(service, folder_id: str) -> list[dict]:
    """Liste récursivement tous les fichiers d'un dossier Drive public."""
    resultats = []
    query     = f"'{folder_id}' in parents and trashed = false"
    page_token = None

    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
        ).execute()

        for item in response.get("files", []):
            if item["mimeType"] == "application/vnd.google-apps.folder":
                # Récursion dans les sous-dossiers photographes
                resultats.extend(_lister_fichiers(service, item["id"]))
            else:
                resultats.append({"name": item["name"], "id": item["id"]})

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return resultats


def generer_mapping_drive(project_id: str, drive_url: str) -> dict:
    """
    Scanne le dossier Drive et sauvegarde le mapping nom → file_id.

    Args:
        project_id : identifiant du projet
        drive_url  : URL publique du dossier Drive

    Returns:
        dict {nom_fichier: file_id}
    """
    service   = build("drive", "v3", developerKey=settings.GOOGLE_API_KEY)
    folder_id = _extract_folder_id(drive_url)

    print(f"[Drive] Scan du dossier {folder_id}...")
    fichiers = _lister_fichiers(service, folder_id)

    # En cas de doublons (même nom, dossiers différents), garde le dernier
    mapping = {f["name"]: f["id"] for f in fichiers}

    output = PROJECT_DIR / project_id / "drive_mapping.json"
    output.write_text(json.dumps(mapping, ensure_ascii=False, indent=2))

    print(f"[Drive] ✅ {len(mapping)} fichiers mappés → {output}")
    return mapping


def charger_mapping(project_id: str) -> dict:
    """Charge le mapping depuis le fichier JSON du projet."""
    path = PROJECT_DIR / project_id / "drive_mapping.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())
