"""
Gestion des projets.

Chaque projet est un dossier dans models/projets/<project_id>/ :
    ├── status.json     → état du projet
    ├── embeddings.csv  → embeddings générés (BLOC 1)
    └── photos/         → photos téléchargées depuis Drive
"""

import json
from datetime import datetime
from pathlib import Path

from config import settings

PROJECT_DIR = Path(settings.PROJECTS_DIR)
PROJECT_DIR.mkdir(parents=True, exist_ok=True)


def _status_path(project_id: str) -> Path:
    return PROJECT_DIR / project_id / "status.json"


def creer_projet(nom: str) -> dict | None:
    """Crée le dossier du projet. Retourne None si déjà existant."""
    project_id = nom.lower().replace(" ", "-")
    projet_dir = PROJECT_DIR / project_id
    if projet_dir.exists():
        return None

    (projet_dir / "photos").mkdir(parents=True)

    data = {
        "id": project_id,
        "nom": nom,
        "status": "created",
        "nb_embeddings": 0,
        "cree_le": datetime.now().isoformat(),
        "erreur": None,
    }
    _status_path(project_id).write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def get_projet(project_id: str) -> dict | None:
    path = _status_path(project_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def lister_projets() -> list[dict]:
    projets = []
    for d in PROJECT_DIR.iterdir():
        if d.is_dir() and (d / "status.json").exists():
            projets.append(json.loads((d / "status.json").read_text()))
    return sorted(projets, key=lambda p: p["cree_le"], reverse=True)


def set_status(project_id: str, status: str, nb_embeddings: int = 0, erreur: str | None = None):
    path = _status_path(project_id)
    if not path.exists():
        return
    data = json.loads(path.read_text())
    data["status"] = status
    if nb_embeddings:
        data["nb_embeddings"] = nb_embeddings
    if erreur:
        data["erreur"] = erreur
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def csv_path(project_id: str) -> Path:
    return PROJECT_DIR / project_id / "embeddings.csv"


def photos_dir(project_id: str) -> Path:
    return PROJECT_DIR / project_id / "photos"
